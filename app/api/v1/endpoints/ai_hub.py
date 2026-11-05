"""
AI Free Developer Hub Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Exposes the Top 4 AI Capabilities:
1. POST /api/v1/ai/stack-architect (Zero-Dollar Stack Architect)
2. GET  /api/v1/ai/drift-sentinel/audit (Plan Drift Sentinel)
3. POST /api/v1/ai/submission-auditor (PR & Submission Compliance Auditor)
4. POST /api/v1/ai/semantic-search (Semantic Natural Language Discovery & Comparison Engine)
5. GET  /api/v1/ai/catalog (Catalog Listing & Categories)
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse
from app.services.ai_free_dev_service import free_dev_ai_service
from app.core.logging_config import get_logger

logger = get_logger("ai_hub_endpoints")
router = APIRouter(prefix="/ai", tags=["AI Free Developer Hub & Stack Architect"])


# -----------------------------------------------------------------------------
# Request Payloads
# -----------------------------------------------------------------------------
class StackArchitectRequest(BaseModel):
    project_description: str = Field(
        default="Gujarat Police Cyber Crime Intelligence & Social Media Monitoring platform with FastAPI, vector search, Gujarati NLP, and continuous crawlers.",
        description="Plain-English description of the software architecture you want to build at $0 cost."
    )
    tech_language: str = Field(
        default="Python / FastAPI",
        description="Primary programming language or backend framework."
    )
    target_use_case: str = Field(
        default="Cyber Crime Intelligence & Social Media Early Warning",
        description="Target domain or operational environment."
    )
    monthly_active_users: int = Field(
        default=500,
        description="Projected monthly users / officers."
    )


class SubmissionAuditorRequest(BaseModel):
    service_name: str = Field(..., description="Name of the developer service (e.g. Neon Postgres)")
    service_url: str = Field(..., description="Direct HTTPS link to the service or pricing page")
    category: str = Field(default="Managed Databases", description="Catalog category")
    claimed_free_tier: str = Field(..., description="Summary of the free tier allowance")
    requires_credit_card: bool = Field(default=False, description="Whether registration requires a credit card upfront")
    is_trial_only: bool = Field(default=False, description="Whether the free tier expires after a trial period")
    is_self_hosted: bool = Field(default=False, description="Whether it requires self-hosting instead of managed SaaS")


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query e.g. 'Free S3 storage with no egress fees'")
    limit: int = Field(default=6, ge=1, le=20, description="Maximum number of tools to return")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.post("/stack-architect", response_model=ApiResponse[Dict[str, Any]])
def synthesize_zero_dollar_stack(payload: StackArchitectRequest):
    """
    IDEA 1: Zero-Dollar Stack Architect
    Takes a natural language project description and synthesizes a complete,
    compatible multi-cloud production architecture running on $0/month free tiers.
    """
    try:
        result = free_dev_ai_service.generate_zero_dollar_stack(
            project_description=payload.project_description,
            tech_language=payload.tech_language,
            target_use_case=payload.target_use_case,
            monthly_active_users=payload.monthly_active_users
        )
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error in stack architect synthesis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate zero-dollar architecture: {str(e)}"
        )


@router.get("/drift-sentinel/audit", response_model=ApiResponse[Dict[str, Any]])
def run_plan_drift_audit():
    """
    IDEA 2: Autonomous Plan Drift Sentinel
    Audits all entries in the developer catalog, checks for SSL health,
    detects hidden trial countdowns or credit card requirements, and scores catalog stability.
    """
    try:
        result = free_dev_ai_service.audit_catalog_drift()
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error in plan drift audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute plan drift audit: {str(e)}"
        )


@router.post("/submission-auditor", response_model=ApiResponse[Dict[str, Any]])
def audit_tool_submission(payload: SubmissionAuditorRequest):
    """
    IDEA 3: AI-Powered Pull Request / Tool Submission Auditor
    Evaluates candidate developer tools against strict 'free-for-dev' repository rules:
    Must be SaaS, perpetual free tier, SSL included, and generate ready-to-paste PR review comments.
    """
    try:
        result = free_dev_ai_service.audit_tool_submission(
            service_name=payload.service_name,
            service_url=payload.service_url,
            category=payload.category,
            claimed_free_tier=payload.claimed_free_tier,
            requires_credit_card=payload.requires_credit_card,
            is_trial_only=payload.is_trial_only,
            is_self_hosted=payload.is_self_hosted
        )
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error in tool submission audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit tool submission: {str(e)}"
        )


@router.post("/semantic-search", response_model=ApiResponse[Dict[str, Any]])
def semantic_search_and_compare(payload: SemanticSearchRequest):
    """
    IDEA 4: Semantic Natural Language Discovery & Comparison Engine
    Natural language search across developer tools with multi-tool side-by-side
    comparison matrix and contextual recommendations.
    """
    try:
        result = free_dev_ai_service.semantic_search_and_compare(
            query=payload.query,
            limit=payload.limit
        )
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error in semantic tool search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute semantic search: {str(e)}"
        )


@router.get("/catalog", response_model=ApiResponse[Dict[str, Any]])
def get_free_tier_catalog(category: Optional[str] = Query(None, description="Optional category filter")):
    """Returns all verified developer services and categories in the knowledge base."""
    tools = free_dev_ai_service.get_catalog(category)
    categories = free_dev_ai_service.get_categories()
    return ApiResponse(
        success=True,
        data={
            "total_tools": len(tools),
            "categories": categories,
            "tools": tools
        }
    )
