"""
Tests for AI Free Developer Hub & Stack Architect Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import pytest
from app.services.ai_free_dev_service import free_dev_ai_service


def test_free_tier_catalog_loaded():
    """Verifies that the free tier catalog has been seeded with verified tools."""
    catalog = free_dev_ai_service.get_catalog()
    assert len(catalog) >= 15
    categories = free_dev_ai_service.get_categories()
    assert "Managed Databases" in categories
    assert "Generative AI & LLM APIs" in categories
    assert "Vector Databases & Search" in categories


def test_idea_1_stack_architect():
    """Verifies Idea 1: Zero-Dollar Stack Architect synthesizes a full $0 stack."""
    res = free_dev_ai_service.generate_zero_dollar_stack(
        project_description="Gujarat police cyber crime portal with vector search and AI translation",
        tech_language="Python / FastAPI"
    )
    assert res["success"] is True
    assert res["total_monthly_cost"] == "$0.00/month"
    assert len(res["stack_blueprint"]) >= 5
    providers = [c["provider"] for c in res["stack_blueprint"]]
    assert any("Supabase" in p for p in providers)
    assert any("Qdrant" in p or "Pinecone" in p for p in providers)


def test_idea_2_plan_drift_sentinel():
    """Verifies Idea 2: Plan Drift Sentinel scores catalog stability and flags drift."""
    res = free_dev_ai_service.audit_catalog_drift()
    assert res["success"] is True
    assert res["total_tools_audited"] >= 15
    assert res["drift_index_percentage"] > 50.0
    assert len(res["results"]) == res["total_tools_audited"]


def test_idea_3_submission_auditor_pass():
    """Verifies Idea 3: Submission Auditor passes compliant SaaS tools."""
    res = free_dev_ai_service.audit_tool_submission(
        service_name="Cloudflare Workers",
        service_url="https://workers.cloudflare.com",
        category="Compute & Web Hosting",
        claimed_free_tier="100,000 requests/day",
        requires_credit_card=False,
        is_trial_only=False,
        is_self_hosted=False
    )
    assert res["verdict"] == "PASS"
    assert res["score"] == 100
    assert len(res["violations"]) == 0
    assert "✅" in res["github_pr_comment_markdown"]


def test_idea_3_submission_auditor_fail():
    """Verifies Idea 3: Submission Auditor rejects trial-only or self-hosted submissions."""
    res = free_dev_ai_service.audit_tool_submission(
        service_name="FakeTrialService",
        service_url="http://insecure-trial.com",
        category="Managed Databases",
        claimed_free_tier="14-day trial only",
        requires_credit_card=True,
        is_trial_only=True,
        is_self_hosted=True
    )
    assert res["verdict"] == "FAIL"
    assert len(res["violations"]) >= 2
    assert "❌" in res["github_pr_comment_markdown"]


def test_idea_4_semantic_search_and_compare():
    """Verifies Idea 4: Semantic Discovery finds relevant tools and builds matrix."""
    res = free_dev_ai_service.semantic_search_and_compare(
        query="Free S3 storage with no egress fee",
        limit=5
    )
    assert res["success"] is True
    assert res["matches_found"] > 0
    names = [t["name"] for t in res["top_tools"]]
    assert any("R2" in n or "Cloudflare" in n or "Backblaze" in n for n in names)
    assert len(res["comparison_matrix"]) > 0
