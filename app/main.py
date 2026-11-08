"""
Application Entry Point and Lifecycle Manager
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.responses import HTMLResponse

from app.config.settings import get_settings
from app.core.logging_config import setup_logging, get_logger, correlation_id_ctx
from app.core.exceptions import (
    BaseAppException,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.core.database import Base, engine
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.request_limit import RequestSizeLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.router import api_v1_router
from app.utils.time_utils import format_timestamp_utc, format_localized_time

# 1. Initialize logging
setup_logging()
logger = get_logger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and graceful shutdown lifecycle."""
    current_settings = get_settings()
    logger.info(
        f"Starting {current_settings.APP_NAME} [Environment: {current_settings.APP_ENV}]",
        extra={"version": current_settings.APP_VERSION, "timezone": current_settings.DEFAULT_TIMEZONE}
    )

    # Automatically create tables for prototype development
    # In full production, this is orchestrated via Alembic migrations
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas verified successfully.")
    except Exception as e:
        logger.warning(f"Database schema auto-creation notice: {e}")

    # Start Automated Background Ingestion Scheduler for Gir Somnath & Gujarat
    scheduler = None
    if current_settings.APP_ENV not in ["testing", "test"]:
        from app.services.scheduler_service import BackgroundSchedulerService
        scheduler = BackgroundSchedulerService.get_instance()
        await scheduler.start()

    yield

    if scheduler:
        await scheduler.stop()
    logger.info("Shutting down Gujarat Cyber Crime Intelligence platform. Releasing resources.")


def create_application() -> FastAPI:
    """Factory function initializing the hardened FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Correlation-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # 3. Custom Security Middleware Stack (Order of execution: outermost to innermost)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # 4. Exception Handlers
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from starlette.responses import JSONResponse

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                }
            }
        )

    app.add_exception_handler(BaseAppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 5. Mount API Version 1 Routers
    app.include_router(api_v1_router, prefix="/api")

    # 6. Static files and Frontend template engine
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(base_dir, "frontend")
    static_dir = os.path.join(frontend_dir, "static")
    templates_dir = os.path.join(frontend_dir, "templates")

    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    templates = Jinja2Templates(directory=templates_dir)

    # 7. Web Dashboard & Root Webhook Handshake (Dual-compatibility for Meta Webhooks)
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/instagram", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard_view(request: Request):
        # Support Meta Webhook verification handshake if user configures root URL in Meta Developer portal
        hub_challenge = request.query_params.get("hub.challenge")
        if hub_challenge:
            from starlette.responses import Response
            logger.info(f"Root Meta webhook verification challenge validated: challenge={hub_challenge}")
            return Response(content=str(hub_challenge).strip(), media_type="text/plain", status_code=200)

        return templates.TemplateResponse(
            "instagram_dashboard.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "env": settings.APP_ENV,
                "classification": settings.DEFAULT_DATA_CLASSIFICATION,
                "current_time_localized": format_localized_time(),
                "current_time_utc": format_timestamp_utc(),
            }
        )

    @app.get("/connect-meta", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/meta-connect", response_class=HTMLResponse, include_in_schema=False)
    async def meta_connect_view(request: Request):
        return templates.TemplateResponse(
            "meta_connect.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "env": settings.APP_ENV,
                "classification": settings.DEFAULT_DATA_CLASSIFICATION,
                "current_time_localized": format_localized_time(),
                "current_time_utc": format_timestamp_utc(),
            }
        )

    @app.post("/", include_in_schema=False)
    async def root_webhook_receiver(request: Request):
        """Forward any webhook POST event hitting root to the official receiver."""
        from app.api.v1.endpoints.instagram import meta_webhook_event_receiver
        return await meta_webhook_event_receiver(request)

    return app


# Application entry point for ASGI servers (uvicorn app.main:app)
app = create_application()
