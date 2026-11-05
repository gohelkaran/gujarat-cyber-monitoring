"""
API Version 1 Router Aggregator
Instagram Monitoring System - Version 1
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    system,
    auth,
    instagram,
    facebook,
    crime_feeds,
    social_harvester,
    sources,
    keywords,
    users,
    ai_hub,
)

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(system.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(ai_hub.router)
api_v1_router.include_router(instagram.router)
api_v1_router.include_router(facebook.router)
api_v1_router.include_router(crime_feeds.router)
api_v1_router.include_router(social_harvester.router)
api_v1_router.include_router(sources.router)
api_v1_router.include_router(keywords.router)
