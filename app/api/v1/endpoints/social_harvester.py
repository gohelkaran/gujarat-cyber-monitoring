"""
Public Social Harvester & Commercial Scraping API Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System - Version 1
"""

import os
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.services.social_harvester_service import SocialHarvesterService

router = APIRouter(prefix="/harvester", tags=["Social Harvester & Scraping API"])


@router.get("/status", response_model=ApiResponse[dict])
def get_harvester_status(db: Session = Depends(get_db)):
    """Returns telemetry and configuration status of public harvesters & commercial scraping gateways."""
    svc = SocialHarvesterService(db)
    return ApiResponse.success_response(
        data=svc.get_harvester_status(),
        message="Social harvester status retrieved."
    )


@router.post("/crawl-public", response_model=ApiResponse[dict])
def trigger_public_crawl(
    max_profiles: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Triggers direct Public Profile Web Harvester across Gujarat Police & Media handles.
    Crawls public Instagram reels and Facebook posts without requiring Meta tokens.
    """
    svc = SocialHarvesterService(db)
    result = svc.crawl_public_profiles(max_profiles=max_profiles)
    return ApiResponse.success_response(
        data=result,
        message=result.get("message", "Public profile crawl completed.")
    )


class ApifyCrawlPayload(BaseModel):
    api_token: Optional[str] = Field(None, description="Apify API Token (or leave blank to use configured .env token)")
    target_handles: Optional[List[str]] = Field(None, description="Target Instagram handles to scrape")
    target_hashtags: Optional[List[str]] = Field(None, description="Target hashtags e.g. ['girsomnath', 'gujaratpolice']")
    max_posts: int = Field(500, ge=10, le=2000, description="Maximum posts to ingest (up to 2,000)")


@router.post("/apify-sync", response_model=ApiResponse[dict])
def trigger_apify_sync(
    payload: Optional[ApifyCrawlPayload] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Triggers high-volume commercial crawl via Apify Instagram Scraper actor (1,000 to 2,000 posts).
    """
    svc = SocialHarvesterService(db)
    api_token = payload.api_token if payload else None
    handles = payload.target_handles if payload else None
    hashtags = payload.target_hashtags if payload else None
    max_posts = payload.max_posts if payload else 500

    result = svc.harvest_with_apify(
        api_token=api_token,
        target_handles=handles,
        target_hashtags=hashtags,
        max_posts=max_posts
    )
    return ApiResponse.success_response(
        data=result,
        message=result.get("message", "Apify scraping process executed.")
    )


class SaveKeysPayload(BaseModel):
    apify_token: Optional[str] = None
    scrapingbee_key: Optional[str] = None
    brightdata_key: Optional[str] = None


@router.post("/save-keys", response_model=ApiResponse[dict])
def save_scraping_keys(payload: SaveKeysPayload):
    """
    Persists commercial scraping API tokens (Apify, ScrapingBee) to .env and runtime environment.
    """
    env_file = ".env"
    updates = {}
    if payload.apify_token and payload.apify_token.strip():
        updates["APIFY_API_TOKEN"] = payload.apify_token.strip()
    if payload.scrapingbee_key and payload.scrapingbee_key.strip():
        updates["SCRAPINGBEE_API_KEY"] = payload.scrapingbee_key.strip()
    if payload.brightdata_key and payload.brightdata_key.strip():
        updates["BRIGHTDATA_API_KEY"] = payload.brightdata_key.strip()

    for k, v in updates.items():
        os.environ[k] = v

    if os.path.exists(env_file):
        lines = []
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        found = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _ = stripped.split("=", 1)
                k = k.strip()
                if k in updates:
                    new_lines.append(f"{k}={updates[k]}\n")
                    found.add(k)
                    continue
            new_lines.append(line)
        for k, v in updates.items():
            if k not in found:
                new_lines.append(f"{k}={v}\n")
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return ApiResponse.success_response(
        data={"updated_keys": list(updates.keys())},
        message="Commercial scraping keys saved successfully."
    )

