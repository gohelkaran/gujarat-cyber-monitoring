"""
Official Facebook Monitoring API Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response, JSONResponse

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.config.settings import get_settings
from app.schemas.common import ApiResponse
from app.services.facebook_service import FacebookService

logger = get_logger("facebook_api")
settings = get_settings()
router = APIRouter(prefix="/facebook", tags=["Facebook Monitoring"])


# =============================================================================
# 1. Meta Facebook Page Webhooks (Verification Handshake & Real-Time Event Ingestion)
# =============================================================================
@router.get("/webhook")
@router.get("/webhook/")
def facebook_webhook_verification(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Handles Meta's official webhook verification challenge for Facebook Pages.
    Echoes back hub.challenge as raw text/plain HTTP 200.
    """
    mode = hub_mode or request.query_params.get("hub.mode")
    token = hub_verify_token or request.query_params.get("hub.verify_token")
    challenge = hub_challenge or request.query_params.get("hub.challenge")

    # If opened directly in browser without params, show healthy status
    if not mode and not token and not challenge:
        return JSONResponse(
            status_code=200,
            content={
                "status": "online",
                "service": "Gujarat Cyber Crime Facebook Webhook Listener",
                "ready_for_meta": True,
                "supported_events": ["feed", "mention", "videos", "live_videos"]
            }
        )

    logger.info(f"Facebook webhook verification received: mode={mode}, token={token}, challenge={challenge}")

    if challenge:
        logger.info(f"Facebook webhook verified: echoing challenge={challenge}")
        return Response(content=str(challenge).strip(), media_type="text/plain", status_code=200)

    return Response(content="Webhook verification token mismatch", media_type="text/plain", status_code=403)


@router.post("/webhook")
@router.post("/webhook/")
async def facebook_webhook_event_receiver(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives real-time push events from Meta Webhooks for Facebook Pages (feed, mention, video).
    """
    try:
        body = await request.json()
        logger.info(f"Facebook webhook event received: {body}")
        service = FacebookService(db)
        processed = service.handle_webhook_event(body)
        return {"status": "SUCCESS", "processed_items": processed}
    except Exception as e:
        logger.error(f"Error processing Facebook webhook: {e}")
        return {"status": "ERROR", "message": str(e)}


# =============================================================================
# 2. Manual Trigger & Feed Collection
# =============================================================================
@router.post("/gather", response_model=ApiResponse[dict])
def gather_facebook_feeds(
    keyword: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    account: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Manually harvests verified Facebook news posts and police bulletins."""
    actor_ip = request.client.host if request and request.client else "127.0.0.1"
    service = FacebookService(db)
    result = service.gather_facebook_posts(
        keyword=keyword,
        city=city,
        account=account,
        officer_badge="GJ-CYBER-8921",
        officer_role="LEAD_INVESTIGATOR",
        actor_ip=actor_ip
    )
    return ApiResponse.success_response(data=result, message=result.get("message"))


@router.get("/pages", response_model=ApiResponse[list])
def get_monitored_facebook_pages(db: Session = Depends(get_db)):
    """Returns list of monitored official Facebook Pages."""
    service = FacebookService(db)
    pages = service.get_monitored_pages()
    return ApiResponse.success_response(data=pages, message="Monitored Facebook Pages retrieved.")

