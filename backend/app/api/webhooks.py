from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.limiter import limiter
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
    try:
        webhook, secret = await webhook_service.create(db, current_user, data)
    except ValueError as exc:
        raise HTTPException(status_code=402, detail=str(exc))
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
@limiter.limit("60/minute")
async def inbound_webhook(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
    x_gnkalgo_secret: str | None = Header(default=None),
    x_gnkalgo_signature: str | None = Header(default=None),
):
    raw = await request.body()
    try:
        payload = InboundWebhookPayload.model_validate_json(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    try:
        log = await webhook_service.handle_inbound(
            db, token, payload, request, raw, x_gnkalgo_signature, x_gnkalgo_secret
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return {"accepted": True, "log_id": str(log.id), "response": log.response}
