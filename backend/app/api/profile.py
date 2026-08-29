from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.profile import ProfileUpdateRequest
from app.services.profile_service import profile_service, UPLOAD_DIR

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.get_profile(db, current_user)


@router.patch("/")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await profile_service.update_profile(db, current_user, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await profile_service.upload_photo(db, current_user, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/photo")
async def remove_profile_photo(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await profile_service.remove_photo(db, current_user)


@router.get("/avatar/{user_id}")
async def get_avatar(user_id: UUID):
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = UPLOAD_DIR / f"{user_id}.{ext}"
        if path.exists():
            media = "image/png" if ext == "png" else "image/jpeg" if ext in ("jpg", "jpeg") else "image/webp"
            return FileResponse(path, media_type=media)
    raise HTTPException(status_code=404, detail="Photo not found")
