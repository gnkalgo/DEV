import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import BrokerConnection, User
from app.schemas.profile import ProfileUpdateRequest, TradingSegmentResponse
from app.services.user_meta import client_id_for_user, normalize_phone

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "profiles"
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024


class ProfileService:
    async def get_profile(self, db: AsyncSession, user: User) -> dict:
        broker = await self._primary_broker(db, user)
        segments = self._trading_segments(broker)
        photo_url = user.profile_photo_url

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "display_name": user.display_name or user.full_name,
            "phone": user.phone,
            "gender": user.gender,
            "date_of_birth": user.date_of_birth,
            "profile_photo_url": photo_url,
            "theme_preference": user.theme_preference or "background-1",
            "is_verified": user.is_verified,
            "mfa_enabled": user.mfa_enabled,
            "client_id": broker.client_id if broker and broker.client_id else client_id_for_user(user.id),
            "email_verified": user.is_verified,
            "phone_verified": bool(user.phone),
            "created_at": user.created_at,
            "trading_segments": segments,
        }

    async def update_profile(
        self, db: AsyncSession, user: User, data: ProfileUpdateRequest
    ) -> dict:
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.gender is not None:
            user.gender = data.gender
        if data.date_of_birth is not None:
            user.date_of_birth = data.date_of_birth
        if data.phone is not None:
            user.phone = normalize_phone(data.phone)
        if data.theme_preference is not None:
            user.theme_preference = data.theme_preference
        await db.flush()
        return await self.get_profile(db, user)

    async def upload_photo(self, db: AsyncSession, user: User, file: UploadFile) -> dict:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Use PNG, JPG, or WEBP (max 5 MB)")
        content = await file.read()
        if len(content) > MAX_PHOTO_BYTES:
            raise ValueError("Image must be 5 MB or smaller")

        ext = "jpg"
        if file.content_type == "image/png":
            ext = "png"
        elif file.content_type == "image/webp":
            ext = "webp"

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{user.id}.{ext}"
        path = UPLOAD_DIR / filename
        path.write_bytes(content)

        user.profile_photo_url = f"/api/v1/profile/avatar/{user.id}"
        await db.flush()
        return await self.get_profile(db, user)

    async def remove_photo(self, db: AsyncSession, user: User) -> dict:
        if user.profile_photo_url:
            for ext in ("png", "jpg", "jpeg", "webp"):
                p = UPLOAD_DIR / f"{user.id}.{ext}"
                if p.exists():
                    p.unlink()
        user.profile_photo_url = None
        await db.flush()
        return await self.get_profile(db, user)

    async def _primary_broker(self, db: AsyncSession, user: User) -> BrokerConnection | None:
        result = await db.execute(
            select(BrokerConnection).where(
                BrokerConnection.user_id == user.id,
                BrokerConnection.is_active.is_(True),
            )
        )
        return result.scalars().first()

    def _trading_segments(self, broker: BrokerConnection | None) -> list[TradingSegmentResponse]:
        connected = broker is not None and broker.is_active
        defs = [
            ("equity", "Equity", "E", connected),
            ("fno", "F&O", "F", connected),
            ("currency", "Currency", "C", False),
            ("commodities", "Commodities", "M", False),
            ("mf", "MF", "MF", connected),
            ("ipo", "IPO", "I", connected),
        ]
        items = []
        for code, name, icon, active in defs:
            status = "ACTIVE" if active else "INACTIVE"
            if not connected and code in ("currency", "commodities"):
                status = "NOT_AVAILABLE"
        items.append(
                TradingSegmentResponse(code=code, name=name, status=status, icon=icon).model_dump()
            )
        return items


profile_service = ProfileService()
