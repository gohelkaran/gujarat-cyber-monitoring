"""
Database Schema Initialization and Connectivity Test Utility
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import os
import sys

# Ensure project root is in sys.path so running directly from scripts/ works reliably
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config.settings import get_settings
from app.core.database import engine, Base, check_database_connection
from app.core.logging_config import setup_logging, get_logger

# Import models to register them on Base metadata
import app.models  # noqa

setup_logging()
logger = get_logger("db_init")


def init_database():
    """Initializes tables and confirms connection."""
    settings = get_settings()
    logger.info(f"Target Database Host: {settings.DB_HOST}:{settings.DB_PORT} (DB: {settings.DB_NAME})")

    check = check_database_connection()
    logger.info(f"Connection Status: {check.get('status')} - {check.get('message')}")

    if check.get("status") == "UP":
        logger.info("Synchronizing ORM metadata tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables verified and created successfully.")
        seed_default_sources()
        seed_default_keywords()
        seed_default_users()
        seed_default_instagram_monitoring()
    else:
        logger.warning(
            "Database server is currently offline or unreachable. "
            "Please check PostgreSQL service status and .env credentials."
        )


def seed_default_sources():
    """Seeds baseline legally authorized sources if table is empty."""
    from app.core.database import SessionLocal
    from app.services.source_service import SourceService
    from app.schemas.source import SourceCreate
    from app.core.constants import SourceType

    db = SessionLocal()
    try:
        service = SourceService(db)
        existing = service.repo.list_sources()
        if not existing:
            logger.info("Seeding initial statutory authorized sources for Gujarat SOC...")
            sources_to_seed = [
                SourceCreate(
                    name="Gujarat Police State CID Public Announcements",
                    source_type=SourceType.FACEBOOK,
                    target_identifier="GujaratPoliceOfficialPage",
                    authorization_ref="DGP-CYBER-MANDATE-2026-081",
                    authorized_by_badge="GJ-CYBER-8921",
                    description="Official public page advisory monitoring under CID Crime cyber cell purview.",
                    access_token="EAAG91829102930491823940192348a12",
                    app_id="981273641209",
                    token_scope=["pages_read_engagement", "public_profile"]
                ),
                SourceCreate(
                    name="Surat Cyber Crime Public Awareness Stream",
                    source_type=SourceType.INSTAGRAM,
                    target_identifier="surat_cyber_police",
                    authorization_ref="COMM-SURAT-CYBER-2026-012",
                    authorized_by_badge="GJ-CYBER-6420",
                    description="Public awareness campaign and fraudulent scheme comments monitoring.",
                    access_token="IGQV98129301928301928301293810239",
                    token_scope=["instagram_basic"]
                ),
                SourceCreate(
                    name="State Multi-Agency Center Emergency Feed",
                    source_type=SourceType.OTHER_AUTHORIZED_SOURCE,
                    target_identifier="GJ-SMAC-INTELLIGENCE-FEED-01",
                    authorization_ref="SEC-69-IT-ACT-SANCTION-2026-004",
                    authorized_by_badge="GJ-CYBER-8921",
                    description="Statutory inter-agency emergency warning broadcast stream."
                )
            ]
            for s_data in sources_to_seed:
                service.create_source(
                    data=s_data,
                    acting_officer_badge="GJ-CYBER-8921",
                    acting_officer_role="LEAD_INVESTIGATOR",
                    actor_ip="127.0.0.1"
                )
            logger.info("3 baseline authorized sources seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding sources: {e}")
    finally:
        db.close()


def seed_default_keywords():
    """Seeds baseline statutory threat taxonomy keywords."""
    from app.core.database import SessionLocal
    from app.services.keyword_service import KeywordService

    db = SessionLocal()
    try:
        service = KeywordService(db)
        count = service.seed_default_keywords()
        if count > 0:
            logger.info(f"Seeded {count} statutory cybercrime keywords across 5 threat taxonomies.")
        else:
            logger.info("Statutory cybercrime keywords already seeded.")
    except Exception as e:
        logger.error(f"Error seeding keywords: {e}")
    finally:
        db.close()


def seed_default_users():
    """Seeds default authorized officers for authentication."""
    from app.core.database import SessionLocal
    from app.api.v1.endpoints.auth import seed_default_users_if_empty
    db = SessionLocal()
    try:
        seed_default_users_if_empty(db)
        logger.info("Default cybercrime law enforcement officers verified.")
    except Exception as e:
        logger.error(f"Error seeding officers: {e}")
    finally:
        db.close()


def seed_default_instagram_monitoring():
    """Seeds baseline Instagram monitoring stream and initial sample collection."""
    from app.core.database import SessionLocal
    from app.services.instagram_service import InstagramService
    db = SessionLocal()
    try:
        service = InstagramService(db)
        # Ingest initial collection in mock sandbox mode
        res = service.collect_permitted_data(officer_badge="GJ-CYBER-8921")
        logger.info(f"Initial Instagram monitoring ingestion status: {res.get('status')} ({res.get('new_items_saved')} items, {res.get('keyword_matches_found')} matches).")
    except Exception as e:
        logger.error(f"Error seeding Instagram monitoring baseline: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()

