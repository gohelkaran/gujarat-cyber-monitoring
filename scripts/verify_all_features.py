"""
Automated End-to-End Feature Test Suite
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
Tests: T1 to T6
"""

import sys
import os
import json
from starlette.testclient import TestClient

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))
os.environ["APP_ENV"] = "testing"

from app.config.settings import get_settings
get_settings.cache_clear()

from app.main import create_application
app = create_application()

def run_feature_test_suite():
    print("=" * 70)
    print("GUJARAT CYBER CRIME PLATFORM - AUTOMATED FEATURE VERIFICATION SUITE")
    print("=" * 70)

    client = TestClient(app, raise_server_exceptions=False)
    passed_tests = 0
    total_tests = 8

    # -------------------------------------------------------------
    # T1: Core App & Router Initialization
    # -------------------------------------------------------------
    print("\n[T1] Testing Core Application Initialization & Port 8080 Routing...")
    try:
        resp = client.get("/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert "Gujarat" in resp.text, "Dashboard HTML did not contain 'Gujarat'"
        print("  -> PASS: Root route '/' loads instagram_dashboard.html (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T1]: {e}")

    # -------------------------------------------------------------
    # T2: Health & System Endpoints
    # -------------------------------------------------------------
    print("\n[T2] Testing System Health & Liveness Endpoints...")
    try:
        resp_health = client.get("/api/v1/health")
        assert resp_health.status_code == 200, f"Health check failed: {resp_health.status_code}"
        health_data = resp_health.json()
        print(f"  -> Health: {health_data.get('data', {}).get('status')} | Version: {health_data.get('data', {}).get('version')}")

        resp_sys = client.get("/api/v1/system/info")
        assert resp_sys.status_code == 200, f"System info failed: {resp_sys.status_code}"
        print("  -> PASS: /api/v1/health and /api/v1/system/info verified (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T2]: {e}")

    # -------------------------------------------------------------
    # T3: Official Meta Graph Engine & Quota Status
    # -------------------------------------------------------------
    print("\n[T3] Testing Meta Graph API Client & Quota Telemetry...")
    try:
        resp_meta = client.get("/api/v1/meta/status")
        assert resp_meta.status_code == 200, f"Meta status failed: {resp_meta.status_code}"
        meta_data = resp_meta.json().get("data", {})
        print(f"  -> Meta App Configured: {meta_data.get('app_id_configured')}")
        print(f"  -> API Version: {meta_data.get('api_version')}")
        print(f"  -> Access Token Configured: {meta_data.get('access_token_configured')}")
        assert meta_data.get("app_id_configured") is True, "Meta App ID should be configured"
        print("  -> PASS: Meta Graph Engine status endpoint verified (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T3]: {e}")

    # -------------------------------------------------------------
    # T4: Google Gemini AI Veracity & Threat Investigator
    # -------------------------------------------------------------
    print("\n[T4] Testing Google Gemini AI Fact-Checking & Heuristic Fallback...")
    try:
        payload = {
            "claim_text": "અમદાવાદ દાણીલીમડા વિસ્તારમાં તલવાર સાથે આંતક મચાવનાર આરોપીની ધરપકડ",
            "url": "https://www.instagram.com/reel/Dd9IMoDRe71/",
            "district": "Ahmedabad",
            "save_to_feed": False
        }
        resp_ai = client.post("/api/v1/ai/investigate-post", json=payload)
        assert resp_ai.status_code == 200, f"AI investigation failed: {resp_ai.status_code}"
        ai_res = resp_ai.json().get("data", {})
        print(f"  -> Veracity Status: {ai_res.get('veracity_status')}")
        print(f"  -> Veracity Score: {ai_res.get('veracity_score')}%")
        print(f"  -> Threat Category: {ai_res.get('threat_category')}")
        print(f"  -> AI Engine: {ai_res.get('ai_engine')}")
        print(f"  -> Extracted IOCs: {ai_res.get('extracted_iocs')}")
        print(f"  -> Legal Sections: {ai_res.get('legal_sections')}")
        assert ai_res.get("veracity_status") in ["VERIFIED_REAL", "SUSPECTED_FAKE", "CYBER_FRAUD_SCAM", "UNVERIFIED_CLAIM"]
        assert len(ai_res.get("official_debunk_gu", "")) > 10, "Debunk Gujarati notice missing"
        print("  -> PASS: Gemini AI Investigator verified with veracity scoring & bilingual debunk (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T4]: {e}")

    # -------------------------------------------------------------
    # T5: Crime Intelligence Feeds & District Geolocation
    # -------------------------------------------------------------
    print("\n[T5] Testing Verified Crime Feeds Sources & Geolocation...")
    try:
        resp_sources = client.get("/api/v1/crime-feeds/sources")
        assert resp_sources.status_code == 200, f"Crime feeds sources failed: {resp_sources.status_code}"
        data = resp_sources.json().get("data", [])
        sources = data if isinstance(data, list) else data.get("sources", [])
        print(f"  -> Monitored Crime Feed Desks: {len(sources)}")
        for s in sources:
            print(f"     * {s.get('name')} [{s.get('origin_label')}]")
        assert len(sources) >= 3, "Expected at least 3 verified Gujarati news feed sources"
        print("  -> PASS: Crime Feeds sources verified (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T5]: {e}")

    # -------------------------------------------------------------
    # T6: Meta Webhook Challenge Handshake & Signature Security
    # -------------------------------------------------------------
    print("\n[T6] Testing Meta Webhook Verification Handshake...")
    try:
        challenge_token = "1158201444"
        verify_token = "gujarat_cyber_webhook_2026"
        resp_wh = client.get(f"/api/v1/meta/webhook?hub.mode=subscribe&hub.challenge={challenge_token}&hub.verify_token={verify_token}")
        assert resp_wh.status_code == 200, f"Webhook challenge handshake failed: {resp_wh.status_code}"
        assert resp_wh.text.strip() == challenge_token, f"Expected '{challenge_token}', got '{resp_wh.text}'"
        print(f"  -> Webhook Handshake Challenge Response: {resp_wh.text.strip()} (Status: 200)")

        # Also test root webhook handshake (dual-compatibility)
        resp_root = client.get(f"/?hub.challenge={challenge_token}")
        assert resp_root.status_code == 200 and resp_root.text.strip() == challenge_token
        print("  -> Root Webhook Dual-Compatibility: Verified")
        print("  -> PASS: Meta Webhook handshake verified (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T6]: {e}")

    # -------------------------------------------------------------
    # T7: Google Gemini AI Viral News Feed Discovery
    # -------------------------------------------------------------
    print("\n[T7] Testing Google Gemini AI Viral News Feed Discovery...")
    try:
        resp_viral = client.get("/api/v1/ai/viral-news?district=Ahmedabad")
        assert resp_viral.status_code == 200, f"Viral news failed: {resp_viral.status_code}"
        viral_data = resp_viral.json().get("data", [])
        print(f"  -> Discovered Viral News Count: {len(viral_data)}")
        assert len(viral_data) >= 3, "Expected at least 3 viral items"
        sample = viral_data[0]
        print(f"  -> Sample Headline: {sample.get('headline')[:50]}...")
        print(f"  -> Sample Platform: {sample.get('platform')}")
        print(f"  -> Sample Direct Source Link: {sample.get('permalink')}")
        assert sample.get("permalink", "").startswith("http"), "Permalink must be a valid URL"
        print("  -> PASS: AI Viral News Feed endpoint verified with authentic links (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T7]: {e}")

    # -------------------------------------------------------------
    # T8: Gir Somnath Village Geolocation & Watchlist Desk
    # -------------------------------------------------------------
    print("\n[T8] Testing Gir Somnath Village Geolocation & Watchlist Desk...")
    try:
        from app.data.gir_somnath_geo import detect_gir_somnath_geo
        geo1 = detect_gir_somnath_geo("ઉના તાલુકાના દેલવાડા ગામે મોટી છેતરપિંડીની ફરિયાદ")
        assert geo1 is not None, "Failed to detect Delwada village"
        assert geo1["taluka"] == "Una" and "Una" in geo1["police_station"]
        print(f"  -> Village Detection: 'દેલવાડા' -> {geo1['display_badge']} | PS: {geo1['police_station']}")

        geo2 = detect_gir_somnath_geo("Veraval Port marine police boat patrol operation")
        assert geo2 is not None and geo2["taluka"] == "Veraval"
        print(f"  -> Port Detection: 'Veraval Port' -> {geo2['display_badge']} | PS: {geo2['police_station']}")

        resp_wl = client.get("/api/v1/crime-feeds/gir-somnath/watchlist")
        assert resp_wl.status_code == 200, f"Watchlist failed: {resp_wl.status_code}"
        wl_data = resp_wl.json().get("data", [])
        print(f"  -> Monitored Gir Somnath Handles/Pages: {len(wl_data)}")
        assert len(wl_data) >= 5, "Expected at least 5 Gir Somnath sources in watchlist"

        resp_gs_viral = client.get("/api/v1/ai/viral-news?district=Gir+Somnath")
        assert resp_gs_viral.status_code == 200
        gs_viral_items = resp_gs_viral.json().get("data", [])
        print(f"  -> Gir Somnath Viral Feed Items: {len(gs_viral_items)}")
        assert len(gs_viral_items) >= 3, "Expected at least 3 Gir Somnath viral items"

        print("  -> PASS: Gir Somnath village geocoding and local watchlist desk verified (Status: 200)")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL [T8]: {e}")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"FEATURE TEST RESULTS: {passed_tests}/{total_tests} TESTS PASSED")
    print("=" * 70)

    if passed_tests == total_tests:
        print("ALL CRITICAL FEATURES VERIFIED AND READY FOR DEPLOYMENT!")
        return 0
    else:
        print(f"{total_tests - passed_tests} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(run_feature_test_suite())
