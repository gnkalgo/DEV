from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.trading import InboundWebhookPayload, WebhookCreateRequest, WebhookResponse
from app.services.webhook_service import webhook_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await webhook_service.list_webhooks(db, current_user)
    return [
        WebhookResponse(
            id=w.id,
            name=w.name,
            direction=w.direction,
            token=w.token,
            is_active=w.is_active,
            target_url=w.target_url,
            inbound_url=webhook_service.inbound_url(w.token) if w.direction == "INBOUND" else None,
            created_at=w.created_at,
        )
        for w in items
    ]


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    data: WebhookCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    webhook, secret = await webhook_service.create(db, current_user, data)
    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        direction=webhook.direction,
        token=webhook.token,
        is_active=webhook.is_active,
        target_url=webhook.target_url,
        inbound_url=webhook_service.inbound_url(webhook.token) if webhook.direction == "INBOUND" else None,
        secret=secret,
        created_at=webhook.created_at,
    )


@router.post("/in/{token}")
async def inbound_webhook(
    token: str,
    payload: InboundWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_gnkalgo_secret: str | None = Header(default=None),
    x_gnkalgo_signature: str | None = Header(default=None),
):
    raw = payload.model_dump_json().encode()
    try:
        log = await webhook_service.handle_inbound(
            db, token, payload, request, raw, x_gnkalgo_signature, x_gnkalgo_secret
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return {"accepted": True, "log_id": str(log.id), "response": log.response}
