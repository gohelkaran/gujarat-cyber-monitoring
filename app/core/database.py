"""
Database Engine and Session Factory
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides SQLAlchemy 2.0 session lifecycle management, connection pooling,
and connectivity health verification.
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config.settings import get_settings
from app.core.logging_config import get_logger

logger = get_logger("database")
settings = get_settings()

# SQLAlchemy Declarative Base for all ORM models
Base = declarative_base()

# Engine creation with connection pooling parameters
# Supports both PostgreSQL production setups and local/testing fallbacks
db_uri = settings.sync_database_uri

# If running in development without a configured PostgreSQL password/host, or test mode,
# handle configuration safely
engine_kwargs = {
    "pool_pre_ping": True,  # Checks connection liveness before checkout
    "echo": settings.DB_ECHO,
}

if "sqlite" not in db_uri:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
    })

try:
    engine = create_engine(db_uri, **engine_kwargs)
except Exception as e:
    logger.critical(f"Failed to initialize database engine with URI '{db_uri}': {e}")
    raise

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a managed SQLAlchemy session.
    Automatically rolls back on exception and closes when request finishes.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as exc:
        session.rollback()
        logger.error(f"Database session rollback due to exception: {exc}")
        raise
    finally:
        session.close()


def check_database_connection() -> dict:
    """
    Executes a simple low-overhead query (`SELECT 1`) to verify database health.
    Returns status dictionary for the health-check endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "UP",
            "message": "Database connection verified and operational.",
            "dialect": engine.dialect.name
        }
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {
            "status": "DOWN",
            "message": "Unable to communicate with database server.",
            "error_hint": str(e) if settings.is_development else "Database unreachable"
        }
