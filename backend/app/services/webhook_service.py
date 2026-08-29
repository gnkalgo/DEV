import hashlib
import hmac
import json
import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import generate_secure_token, hash_token
from app.models import User, Webhook, WebhookLog
from app.schemas.trading import InboundWebhookPayload, PlaceOrderRequest, WebhookCreateRequest
from app.services.order_service import order_service


class WebhookService:
    async def list_webhooks(self, db: AsyncSession, user: User) -> list[Webhook]:
        result = await db.execute(select(Webhook).where(Webhook.user_id == user.id))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, user: User, data: WebhookCreateRequest) -> tuple[Webhook, str]:
        raw_secret = generate_secure_token()
        webhook = Webhook(
            user_id=user.id,
            name=data.name,
            direction=data.direction,
            token=generate_secure_token()[:24],
            secret_hash=hash_token(raw_secret),
            target_url=data.target_url,
        )
        db.add(webhook)
        await db.flush()
        return webhook, raw_secret

    def inbound_url(self, token: str) -> str:
        return f"{settings.backend_public_url}/api/v1/webhooks/in/{token}"

    def verify_signature(self, secret: str, body: bytes, provided: str | None) -> bool:
        if not provided:
            return False
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, provided)

    async def handle_inbound(
        self,
        db: AsyncSession,
        token: str,
        payload: InboundWebhookPayload,
        request: Request,
        raw_body: bytes,
        signature: str | None,
        raw_secret: str | None,
    ) -> WebhookLog:
        result = await db.execute(
            select(Webhook).where(Webhook.token == token, Webhook.is_active.is_(True), Webhook.direction == "INBOUND")
        )
        webhook = result.scalar_one_or_none()
        if not webhook:
            raise ValueError("Webhook not found")

        if raw_secret and hash_token(raw_secret) != webhook.secret_hash:
            raise ValueError("Invalid webhook secret")
        if signature and raw_secret and not self.verify_signature(raw_secret, raw_body, signature):
            raise ValueError("Invalid HMAC signature")

        user_result = await db.execute(select(User).where(User.id == webhook.user_id))
        user = user_result.scalar_one()
        order = await order_service.place_order(
            db,
            user,
            PlaceOrderRequest(
                symbol=payload.symbol,
                side=payload.action,
                quantity=payload.qty,
                price=payload.price,
                paper_mode=payload.paper_mode,
                broker="paper" if payload.paper_mode else "dhan",
            ),
            request=request,
            source="webhook",
            webhook_id=webhook.id,
        )
        log = WebhookLog(
            webhook_id=webhook.id,
            payload=json.dumps(payload.model_dump()),
            response=json.dumps({"order_id": str(order.id), "status": order.status}),
            status_code=202,
        )
        db.add(log)
        await db.flush()
        return log


webhook_service = WebhookService()
