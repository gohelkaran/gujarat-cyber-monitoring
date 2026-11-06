"""
Official Meta Integration Endpoints (Facebook & Instagram)
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.security.jwt import get_current_active_user_optional
from app.integrations.meta.client import get_meta_client, MetaGraphClient
from app.integrations.meta.webhook import MetaWebhookHandler
from app.config.settings import get_settings
from app.core.logging_config import get_logger

logger = get_logger("meta_api")
router = APIRouter(prefix="/meta", tags=["Official Meta Integration"])


class ConnectTokenRequest(BaseModel):
    access_token: str = Field(..., description="User or Page Access Token")
    page_id: Optional[str] = Field(default=None, description="Facebook Page ID or Instagram Business Account ID")


class ExchangeTokenRequest(BaseModel):
    short_lived_token: str = Field(..., description="Short-lived token from OAuth login")


@router.get("/status", response_model=ApiResponse[dict])
async def get_meta_status():
    """Validates Meta App credentials, access token status, and API health."""
    settings = get_settings()
    client = get_meta_client()
    
    token_info = await client.debug_token() if client.access_token else {"is_valid": False, "notice": "No access token configured."}

    return ApiResponse.success_response(
        data={
            "app_id_configured": bool(client.app_id),
            "app_secret_configured": bool(client.app_secret),
            "access_token_configured": bool(client.access_token),
            "api_version": client.api_version,
            "token_info": token_info
        },
        message="Meta Graph API status retrieved."
    )


@router.post("/exchange-token", response_model=ApiResponse[dict])
async def exchange_token(payload: ExchangeTokenRequest):
    """Exchanges a short-lived token for a long-lived (60-day) token."""
    client = get_meta_client()
    res = await client.exchange_for_long_lived_token(payload.short_lived_token)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return ApiResponse.success_response(data=res, message="Long-lived token obtained successfully.")


@router.get("/feed", response_model=ApiResponse[dict])
async def get_meta_feed(
    page_id: Optional[str] = Query(default=None, description="Page ID or Instagram ID"),
    platform: str = Query(default="FACEBOOK", regex="^(FACEBOOK|INSTAGRAM)$"),
    limit: int = Query(default=15, ge=1, le=50)
):
    """Fetches real-time authentic published feed items directly from Meta Graph API."""
    client = get_meta_client()
    target_id = page_id or (get_settings().INSTAGRAM_TARGET_ACCOUNT if platform == "INSTAGRAM" else "GujaratPoliceOfficial")

    if platform == "INSTAGRAM":
        res = await client.get_instagram_reels(target_id, limit=limit)
    else:
        res = await client.get_page_feed(target_id, limit=limit)

    return ApiResponse.success_response(
        data=res,
        message=f"Fetched {len(res.get('items', []))} authentic posts from Meta."
    )


# =============================================================================
# Meta Webhooks (Verification Handshake & Event Receiver)
# =============================================================================
@router.get("/webhook", include_in_schema=True)
async def meta_webhook_verification(request: Request):
    """
    Meta Webhook Verification Handshake.
    When configuring Webhooks in Meta Developer App:
    Meta sends: GET /api/v1/meta/webhook?hub.mode=subscribe&hub.challenge=1158201444&hub.verify_token=your_token
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    handler = MetaWebhookHandler()
    is_valid, challenge_resp = handler.verify_handshake(mode, token, challenge)

    if is_valid and challenge_resp:
        return Response(content=str(challenge_resp).strip(), media_type="text/plain", status_code=200)

    raise HTTPException(status_code=403, detail="Webhook verification failed.")


@router.post("/webhook", include_in_schema=True)
async def meta_webhook_receiver(request: Request):
    """
    Receives real-time push event notifications from Meta for new posts, mentions, or comments.
    Verifies X-Hub-Signature-256 for tamper prevention.
    """
    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    handler = MetaWebhookHandler()
    if not handler.verify_signature(body_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook HMAC signature.")

    try:
        import json
        payload = json.loads(body_bytes.decode("utf-8"))
        logger.info(f"Received valid Meta webhook event: object={payload.get('object')}")
        # Ingestion pipeline processes payload events here
        return {"status": "EVENT_RECEIVED"}
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        return {"status": "ERROR", "detail": str(e)}
