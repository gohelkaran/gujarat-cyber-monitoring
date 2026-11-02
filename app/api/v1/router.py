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
    sources,
    keywords,
)

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(system.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(instagram.router)
api_v1_router.include_router(sources.router)
api_v1_router.include_router(keywords.router)
