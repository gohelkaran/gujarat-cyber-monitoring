"""
Gujarat Crime Feeds & Police Press Releases API Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System - Version 1
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.services.crime_feed_service import CrimeFeedService, LIVE_GUJARAT_RSS_FEEDS

router = APIRouter(prefix="/crime-feeds", tags=["Gujarat Crime News & Police Feeds"])


@router.post("/sync", response_model=ApiResponse[dict])
def sync_crime_feeds(db: Session = Depends(get_db)):
    """
    Crawls live Gujarati RSS news feeds (Sandesh, TV9 Gujarati, DeshGujarat)
    and seeds all 33 Gujarat district verified crime reports into the database.
    """
    service = CrimeFeedService(db)
    result = service.sync_all_crime_intelligence()
    return ApiResponse.success_response(
        data=result,
        message=result.get("message", "Crime feeds synchronized successfully.")
    )


@router.get("/sources", response_model=ApiResponse[list])
def list_crime_feed_sources():
    """
    Returns the list of monitored live Gujarat media news feeds and police registries.
    """
    sources_data = [
        {
            "name": s["source_name"],
            "handle": s["source_account"],
            "origin_label": s["origin_label"],
            "category": s["category"],
            "url": s["url"],
            "icon": s["icon"],
            "status": "ONLINE / ACTIVE"
        }
        for s in LIVE_GUJARAT_RSS_FEEDS
    ]
    # Add official police portals
    sources_data.extend([
        {
            "name": "Gir Somnath District Police Crime Bulletin",
            "handle": "girsomnathpolice",
            "origin_label": "Gir Somnath Police Official",
            "category": "District Police HQ",
            "url": "https://www.facebook.com/girsomnathpolice",
            "icon": "bi-shield-fill-check",
            "status": "ONLINE / ACTIVE"
        },
        {
            "name": "Gujarat Police State Cyber Crime Cell (CID)",
            "handle": "GujaratPoliceOfficial",
            "origin_label": "Gujarat Police CID Crime",
            "category": "State Cyber Cell",
            "url": "https://gujaratpolice.gov.in",
            "icon": "bi-shield-shaded",
            "status": "ONLINE / ACTIVE"
        }
    ])
    return ApiResponse.success_response(
        data=sources_data,
        message="Monitored news and police sources retrieved."
    )


@router.get("/gir-somnath/watchlist", response_model=ApiResponse[list])
def get_gir_somnath_watchlist():
    """
    Returns curated local social media handles, Facebook pages, and news desks
    monitored specifically for Gir Somnath District and surrounding villages.
    """
    from pathlib import Path
    import json
    watchlist_path = Path(__file__).resolve().parents[3] / "data" / "gir_somnath_watchlist.json"
    if watchlist_path.exists():
        with open(watchlist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    return ApiResponse.success_response(
        data=data,
        message=f"Retrieved {len(data)} monitored Gir Somnath local sources."
    )


