"""
Standard API Response Schemas
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    """Detailed machine and human readable error descriptor."""
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable explanation of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional context or validation details")


class ApiResponse(BaseModel, Generic[DataT]):
    """Standardized API response envelope for all endpoints."""
    success: bool = Field(default=True, description="Indicates whether the request was successful")
    status: str = Field(default="SUCCESS", description="Status string for frontend compatibility")
    data: Optional[DataT] = Field(default=None, description="Payload data returned on success")
    message: Optional[str] = Field(default=None, description="Human-readable summary message")
    pagination: Optional[Dict[str, Any]] = Field(default=None, description="Pagination metadata")
    error: Optional[ErrorDetail] = Field(default=None, description="Error information returned on failure")
    correlation_id: str = Field(..., description="Tracking ID for end-to-end audit tracing")
    timestamp: str = Field(..., description="Response generation timestamp in ISO 8601 UTC")

    @classmethod
    def success_response(
        cls,
        data: Optional[DataT] = None,
        message: Optional[str] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> "ApiResponse[DataT]":
        from app.core.logging_config import correlation_id_ctx
        from app.utils.time_utils import format_timestamp_utc
        return cls(
            success=True,
            status="SUCCESS",
            data=data,
            message=message,
            pagination=pagination,
            correlation_id=correlation_id_ctx.get(),
            timestamp=format_timestamp_utc(),
        )


class ComponentHealth(BaseModel):
    """Health status of an individual subsystem component."""
    status: str = Field(..., example="UP")
    message: str = Field(..., example="Component operational")
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Overall system health payload."""
    status: str = Field(..., example="HEALTHY")
    environment: str = Field(..., example="development")
    version: str = Field(..., example="0.1.0")
    timestamp_utc: str = Field(..., description="Current UTC timestamp")
    timestamp_localized: str = Field(..., description="Current timestamp in designated police timezone")
    uptime_seconds: float = Field(..., description="Seconds since application startup")
    components: Dict[str, ComponentHealth] = Field(..., description="Subsystem health statuses")
