"""
Google Gemini AI Investigator Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.security.jwt import get_current_active_user_optional
from app.services.gemini_service import get_gemini_service, GeminiAIService
from app.models.instagram import CollectedItem
from app.utils.time_utils import utc_now
from app.core.logging_config import get_logger

logger = get_logger("ai_investigator_api")
router = APIRouter(prefix="/ai", tags=["Gemini AI Intelligence"])


class AnalyzePostRequest(BaseModel):
    url: Optional[str] = Field(default="", description="Instagram Reel, Facebook Post, or web link")
    claim_text: Optional[str] = Field(default="", description="Text caption or circulating message claim")
    district: Optional[str] = Field(default="All Gujarat", description="District jurisdiction focus")
    save_to_feed: Optional[bool] = Field(default=False, description="Persist analyzed evidence to database feed")


class GenerateDebunkRequest(BaseModel):
    claim_text: str = Field(..., description="Rumor or scam claim to debunk")
    threat_category: Optional[str] = Field(default="Public Safety", description="Detected category")
    district: Optional[str] = Field(default="All Gujarat", description="District context")


@router.get("/status", response_model=ApiResponse[dict])
def get_ai_status():
    """Returns Gemini AI service readiness and configuration status."""
    svc = get_gemini_service()
    return ApiResponse.success_response(
        data={
            "is_configured": svc.is_configured(),
            "model": svc.model,
            "search_grounding_enabled": True,
            "multimodal_vision_enabled": True
        },
        message="Gemini AI engine is ready." if svc.is_configured() else "Gemini running with local heuristic fallback (API Key not set)."
    )


@router.post("/investigate-post", response_model=ApiResponse[dict])
async def investigate_social_post(
    payload: AnalyzePostRequest,
    current_user: Optional[User] = Depends(get_current_active_user_optional),
    db: Session = Depends(get_db)
):
    """
    Analyzes any Instagram reel, Facebook post, or viral claim using Gemini AI.
    Returns veracity score, classification, extracted suspect IOCs, and police debunks.
    """
    raw_url = (payload.url or "").strip()
    claim_text = (payload.claim_text or "").strip()

    if not raw_url and not claim_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid URL or claim text to investigate."
        )

    svc = get_gemini_service()
    result = await svc.analyze_social_post(
        url=raw_url,
        claim_text=claim_text,
        district=payload.district or "All Gujarat"
    )

    # Attach requested URL/Claim info
    result["input_url"] = raw_url
    result["input_claim"] = claim_text
    result["district"] = payload.district or "All Gujarat"

    # Persist to database if requested
    if payload.save_to_feed:
        try:
            platform_val = "INSTAGRAM" if "instagram.com" in raw_url.lower() else ("FACEBOOK" if "facebook.com" in raw_url.lower() else "NEWS_FEED")
            new_item = CollectedItem(
                id=str(uuid.uuid4()),
                source_account=result.get("extracted_iocs", {}).get("suspect_handles", ["monitored_source"])[0] if result.get("extracted_iocs", {}).get("suspect_handles") else "monitored_source",
                platform=platform_val,
                city=payload.district or "All Gujarat",
                caption=f"{result.get('headline_gujarati', 'AI Investigation')} | {claim_text or raw_url}",
                permalink=raw_url or "https://sandesh.com/gujarat/crime",
                like_count=0,
                comments_count=0,
                collected_at=utc_now(),
                raw_metadata={
                    "origin_label": f"AI Monitored ({platform_val})",
                    "veracity_status": result.get("veracity_status"),
                    "veracity_score": result.get("veracity_score"),
                    "headline": result.get("headline_gujarati"),
                    "threat_category": result.get("threat_category"),
                    "ai_engine": result.get("ai_engine")
                }
            )
            db.add(new_item)
            db.commit()
            result["is_saved_in_db"] = True
            logger.info(f"Persisted AI investigated post to database: id={new_item.id}")
        except Exception as e:
            logger.warning(f"Error persisting investigated post: {e}")
            db.rollback()

    return ApiResponse.success_response(
        data=result,
        message=f"Post investigated: {result.get('veracity_label', 'Assessment complete')}"
    )


@router.post("/generate-debunk", response_model=ApiResponse[dict])
async def generate_police_debunk(
    payload: GenerateDebunkRequest,
    current_user: Optional[User] = Depends(get_current_active_user_optional)
):
    """Generates official 1-click Gujarat Police debunk statement in Gujarati and English."""
    svc = get_gemini_service()
    res = await svc.analyze_social_post(
        claim_text=payload.claim_text,
        district=payload.district or "All Gujarat"
    )
    return ApiResponse.success_response(
        data={
            "headline_gujarati": res.get("headline_gujarati"),
            "official_debunk_gu": res.get("official_debunk_gu"),
            "official_debunk_en": res.get("official_debunk_en"),
            "legal_sections": res.get("legal_sections", []),
            "action_guidance": res.get("action_guidance")
        },
        message="Official police debunk notice generated."
    )
