"""
Application Configuration Module
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Handles environment variable loading, validation, and separation between
Development, Staging, and Production environments using Pydantic Settings.
"""

from functools import lru_cache
from typing import List, Literal, Optional
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central Application Settings.
    Reads values from environment variables or .env file with type validation.
    Sensitive credentials are wrapped in SecretStr to prevent accidental leaking in logs.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Application Metadata
    APP_NAME: str = "Gujarat Cyber Crime Social Media Intelligence & Early Warning System"
    APP_DESCRIPTION: str = "Law Enforcement Intelligence & Early Warning System for Authorized Public Streams"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = False

    # Server Binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost"]

    # Security & Cryptography
    SECRET_KEY: SecretStr = Field(
        default=SecretStr("DEVELOPMENT_INSECURE_SECRET_KEY_MUST_BE_OVERRIDDEN_IN_PROD_1234567890"),
        description="Master secret key for cryptographic signatures and JWTs"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Configuration (PostgreSQL)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_USER: str = "cybercrime_app"
    DB_PASSWORD: SecretStr = Field(
        default=SecretStr(""),
        description="PostgreSQL user password"
    )
    DB_NAME: str = "gujarat_cyber_intel"
    DB_SCHEMA: str = "public"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False
    DATABASE_URL: Optional[str] = None

    # Timezone & Regional Settings
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # API Protection & Limits
    RATE_LIMIT_PER_MINUTE: int = 120
    MAX_CONTENT_LENGTH_BYTES: int = 10 * 1024 * 1024  # 10 MB payload limit

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    CORS_ALLOW_CREDENTIALS: bool = False

    # Security Headers & SSL
    ENFORCE_SSL: bool = False
    HSTS_MAX_AGE_SECONDS: int = 31536000
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = True

    # Meta / Facebook & Instagram Official Graph API Configuration
    META_APP_ID: Optional[str] = Field(default=None, description="Meta App / Client ID")
    META_APP_SECRET: Optional[SecretStr] = Field(default=None, description="Meta App Secret")
    META_API_VERSION: str = Field(default="v20.0", description="Meta Graph API Version")
    META_GRAPH_BASE_URL: str = Field(default="https://graph.facebook.com", description="Meta Graph API Base URL")
    META_DEFAULT_ACCESS_TOKEN: Optional[SecretStr] = Field(default=None, description="Default fallback Meta access token")
    META_WEBHOOK_VERIFY_TOKEN: str = Field(default="gujarat_cyber_webhook_2026", description="Meta Webhook Verification Token")
    INSTAGRAM_DEFAULT_ACCESS_TOKEN: Optional[SecretStr] = Field(default=None, description="Default fallback Instagram access token")
    INSTAGRAM_TARGET_ACCOUNT: Optional[str] = Field(default=None, description="Default monitored Instagram username or account ID")
    META_REQUEST_TIMEOUT_SECONDS: float = Field(default=10.0, description="HTTP Request Timeout in seconds")
    META_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts on transient network failures")
    META_BACKOFF_FACTOR: float = Field(default=1.5, description="Exponential backoff multiplier")
    META_RATE_LIMIT_THRESHOLD_PERCENT: float = Field(default=85.0, description="Usage percentage threshold to trigger rate limit protection")

    # Google Gemini AI Intelligence Configuration
    GEMINI_API_KEY: Optional[SecretStr] = Field(default=None, description="Google Gemini API Key for grounded verification & threat analysis")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash", description="Default Google Gemini model")
    GEMINI_PRO_MODEL: str = Field(default="gemini-pro-latest", description="Deep forensic reasoning Gemini model")
    GEMINI_ENABLE_SEARCH_GROUNDING: bool = Field(default=True, description="Enable Google Search grounding for real-time news fact-checking")

    # Government Audit & Data Governance
    DEFAULT_DATA_CLASSIFICATION: Literal["UNCLASSIFIED", "RESTRICTED", "CONFIDENTIAL", "SECRET"] = "RESTRICTED"
    AUDIT_LOG_RETENTION_DAYS: int = 730  # 2 years minimum statutory retention
    AUDIT_LOG_FILE_PATH: str = "logs/security_audit.log"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"
    MASK_SENSITIVE_DATA: bool = True

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def sync_database_uri(self) -> str:
        """Constructs synchronous PostgreSQL URI with connection credentials."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        pwd = self.DB_PASSWORD.get_secret_value() if self.DB_PASSWORD else ""
        auth = f"{self.DB_USER}:{pwd}@" if self.DB_USER else ""
        return f"postgresql+psycopg2://{auth}{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def async_database_uri(self) -> str:
        """Constructs asynchronous PostgreSQL URI."""
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql+asyncpg"):
            return self.DATABASE_URL
        pwd = self.DB_PASSWORD.get_secret_value() if self.DB_PASSWORD else ""
        auth = f"{self.DB_USER}:{pwd}@" if self.DB_USER else ""
        return f"postgresql+asyncpg://{auth}{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: SecretStr, info) -> SecretStr:
        val = v.get_secret_value()
        if len(val) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long for cryptographic security.")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton provider."""
    return Settings()
