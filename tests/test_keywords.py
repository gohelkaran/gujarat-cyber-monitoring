"""
Keyword and Threat Intelligence Test Suite
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Tests:
- Default statutory threat taxonomies (Financial Fraud, Phishing, Account Compromise, Identity Abuse, Extortion)
- Manual keyword creation with statutory legal mandate tracking
- Case-insensitivity and regex word boundary matching (e.g. 'OTP' vs 'HOTPOT')
- Threat severity scoring and multi-category detection
- RBAC authorization clearance and immutable audit logging
"""

import pytest
from fastapi import status


def test_default_seeded_keywords_exist(client):
    """Verifies that the statutory threat taxonomies and default keywords are present."""
    response = client.get("/api/v1/keywords")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]

    registered_keywords = {item["keyword"].lower() for item in data}

    # 1. Financial Fraud
    assert "upi fraud" in registered_keywords
    assert "otp" in registered_keywords
    assert "kyc" in registered_keywords
    assert "bank fraud" in registered_keywords
    assert "investment scam" in registered_keywords

    # 2. Phishing
    assert "phishing" in registered_keywords
    assert "malicious link" in registered_keywords
    assert "fake login" in registered_keywords

    # 3. Account Compromise
    assert "hacked account" in registered_keywords
    assert "account takeover" in registered_keywords
    assert "instagram hacked" in registered_keywords

    # 4. Identity Abuse
    assert "fake profile" in registered_keywords
    assert "impersonation" in registered_keywords
    assert "identity theft" in registered_keywords

    # 5. Extortion
    assert "sextortion" in registered_keywords
    assert "blackmail" in registered_keywords
    assert "threatening images" in registered_keywords


def test_keyword_category_summaries(client):
    """Verifies aggregate category statistics endpoint."""
    response = client.get("/api/v1/keywords/categories")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]

    cat_names = {c["category"] for c in data}
    assert "Financial Fraud" in cat_names
    assert "Phishing" in cat_names
    assert "Account Compromise" in cat_names
    assert "Identity Abuse" in cat_names
    assert "Extortion" in cat_names

    # Check financial fraud count
    fin_fraud = next(c for c in data if c["category"] == "Financial Fraud")
    assert fin_fraud["total_keywords"] >= 5
    assert fin_fraud["active_keywords"] >= 5


def test_manual_keyword_creation(client):
    """Verifies manual keyword entry by an authorized officer with statutory mandate."""
    payload = {
        "keyword": "crypto pump and dump",
        "category": "Financial Fraud",
        "severity": "CRITICAL",
        "match_type": "PHRASE",
        "language": "en",
        "description": "Telegram / WhatsApp syndicated crypto manipulation scheme",
        "authorization_ref": "GJ-CYBER-MANDATE-CRYPTO-2026-99",
        "authorizing_officer_badge": "GJ-CYBER-8921"
    }
    response = client.post(
        "/api/v1/keywords",
        json=payload,
        headers={"X-User-Role": "LEAD_INVESTIGATOR", "X-Officer-Badge": "GJ-CYBER-8921"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()["data"]
    assert data["keyword"] == "crypto pump and dump"
    assert data["category"] == "Financial Fraud"
    assert data["severity"] == "CRITICAL"
    assert data["authorization_ref"] == "GJ-CYBER-MANDATE-CRYPTO-2026-99"

    # Verify retrieval
    kw_id = data["id"]
    get_res = client.get(f"/api/v1/keywords/{kw_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["data"]["id"] == kw_id


def test_reject_duplicate_keyword(client):
    """Verifies that duplicate keyword registration is rejected."""
    payload = {
        "keyword": "UPI fraud",
        "category": "Financial Fraud",
        "severity": "CRITICAL",
        "match_type": "PHRASE",
        "authorization_ref": "MANDATE-DUP-TEST",
        "authorizing_officer_badge": "GJ-CYBER-8921"
    }
    response = client.post("/api/v1/keywords", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_toggle_and_delete_keyword(client):
    """Verifies toggling active status and deleting a manual keyword."""
    # Create keyword for testing toggle/delete
    create_payload = {
        "keyword": "temporary test threat keyword",
        "category": "Other",
        "severity": "LOW",
        "match_type": "PHRASE",
        "authorization_ref": "MANDATE-TEMP-TEST",
        "authorizing_officer_badge": "GJ-CYBER-8921"
    }
    create_res = client.post("/api/v1/keywords", json=create_payload)
    assert create_res.status_code == status.HTTP_201_CREATED
    kw_id = create_res.json()["data"]["id"]

    # Toggle to inactive
    toggle_res = client.post(f"/api/v1/keywords/{kw_id}/toggle?is_active=false")
    assert toggle_res.status_code == status.HTTP_200_OK
    assert toggle_res.json()["data"]["is_active"] is False

    # Delete
    del_res = client.delete(f"/api/v1/keywords/{kw_id}")
    assert del_res.status_code == status.HTTP_200_OK

    # Confirm not found
    get_res = client.get(f"/api/v1/keywords/{kw_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_threat_scanner_word_boundary_precision(client):
    """
    Verifies that the scanning engine uses word boundary matching
    to avoid false positives on acronyms like OTP and KYC.
    """
    # 1. Hotpot should NOT trigger OTP
    clean_payload = {
        "text": "We enjoyed a delicious hotpot dinner with friends in Ahmedabad yesterday.",
        "platform": "FACEBOOK"
    }
    clean_res = client.post("/api/v1/keywords/scan", json=clean_payload)
    assert clean_res.status_code == status.HTTP_200_OK
    data = clean_res.json()["data"]
    assert data["total_matches"] == 0
    assert data["threat_severity"] == "LOW"
    assert data["threat_score"] == 0.0

    # 2. Urgent message asking for OTP should trigger OTP match
    fraud_payload = {
        "text": "Urgent: Your SBI account has been locked. Please send your OTP to verify immediately.",
        "platform": "INSTAGRAM"
    }
    fraud_res = client.post("/api/v1/keywords/scan", json=fraud_payload)
    assert fraud_res.status_code == status.HTTP_200_OK
    fraud_data = fraud_res.json()["data"]
    assert fraud_data["total_matches"] >= 1
    assert "Financial Fraud" in fraud_data["categories_detected"]
    assert any(m["keyword"].lower() == "otp" for m in fraud_data["matches"])


def test_threat_scanner_multi_category_and_scoring(client):
    """
    Verifies detection of multiple threats (e.g. sextortion + blackmail + UPI fraud)
    and proper threat severity scoring aggregation.
    """
    text = (
        "This is an emergency. I have your threatening images and will blackmail your family. "
        "Pay 50,000 INR via UPI fraud or facing viral exposure on hacked account."
    )
    payload = {
        "text": text,
        "platform": "FACEBOOK"
    }
    res = client.post("/api/v1/keywords/scan", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()["data"]

    assert data["total_matches"] >= 3
    assert data["threat_severity"] == "CRITICAL"
    assert data["threat_score"] >= 0.8
    assert "Extortion" in data["categories_detected"]
    assert "Financial Fraud" in data["categories_detected"]
    assert "Account Compromise" in data["categories_detected"]

    # Verify snippet presence
    assert len(data["matches"]) > 0
    for match in data["matches"]:
        assert match["matched_snippet"] != ""
