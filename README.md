# Gujarat Cyber Crime Instagram Monitoring System — Version 1
### Enterprise Law Enforcement Prototype & Authorized Intelligence Review Foundation

[![Classification: RESTRICTED](https://img.shields.io/badge/Classification-RESTRICTED-red.svg)](#)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](#)
[![Framework: FastAPI](https://img.shields.io/badge/Framework-FastAPI-green.svg)](#)
[![Database: SQLite%20%7C%20PostgreSQL](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-336791.svg)](#)
[![Security: OWASP Hardened](https://img.shields.io/badge/Security-OWASP%20Hardened-amber.svg)](#)

---

## 1. Executive Summary & Objective

The **Instagram Monitoring System (Version 1)** is an authorized cybercrime intelligence prototype built for the **Gujarat Police and State Cyber Crime Cell**.

The system provides a secure, modular platform to monitor permitted content from authorized Instagram accounts, run configurable keyword matching on public captions, flag search hits for mandatory human officer review, and dispatch basic notifications to cyber desks while maintaining an immutable forensic audit log.

### Statutory Compliance & Legal Principles
- **Authorized Legal Access Only:** Monitors strictly permitted public media and captions from connected professional/business accounts under statutory police mandate (Section 69 IT Act / 91 CrPC).
- **Zero Scraping & Bypasses:** Does not scrape HTML, bypass authentication, use session cookies, or evade rate limits. Uses the official Meta Graph API (v19.0) with OAuth 2.0 authorization.
- **Search Hit Disclaimer:** A keyword match is solely an operational search hit. It does **not** infer criminality, guilt, identity, or location. Mandatory human officer review is required.
- **Strict Data Minimization:** Collects only permitted public media captions, permalinks, published timestamps, and aggregate non-PII metrics (likes, comments). Zero personal profile scraping, zero follower lists, zero commenter personal data.
- **Safe Permalinks:** External links are never executed, visited, or fetched automatically by the server.
- **Clear Demo vs. Live Separation:** Synthetic records are prominently labeled with `[DEMO DATA]` badges.

---

## 2. System Architecture & Project Layout

```
social media monitoring/
├── .env.example             # Safe environment variable configuration template
├── .env                     # Local environment configuration (git-ignored)
├── requirements.txt          # Python dependencies
├── README.md                 # Operational manual & architecture specification
├── gujarat_cyber.db         # SQLite prototype database
├── app/
│   ├── main.py               # FastAPI factory, lifespan, security middleware & UI routes
│   ├── config/               # Pydantic Settings & environment management
│   │   └── settings.py
│   ├── core/                 # Database engine, constants, RFC 7807 exceptions, structured logging
│   │   ├── constants.py      # RBAC roles, Data Classification & AuditAction enums
│   │   ├── database.py       # SQLAlchemy 2.0 connection pooling & session factory
│   │   ├── exceptions.py     # RFC 7807 problem details & global handlers
│   │   └── logging_config.py # Structured JSON logging with credential masking
│   ├── security/             # Security enforcement and cryptographic helpers
│   │   ├── hashing.py        # Salted Bcrypt password hashing
│   │   ├── jwt.py            # Signed JWT access token creation & verification
│   │   ├── encryption.py     # Fernet AES-128-CBC token encryption at rest
│   │   ├── headers.py        # OWASP defense-in-depth headers
│   │   └── rbac.py           # Role-based access control engine
│   ├── middleware/           # HTTP request protection pipeline
│   │   ├── correlation.py    # X-Request-ID & X-Correlation-ID tracing
│   │   ├── rate_limit.py     # 120 req/min sliding-window rate limiter
│   │   ├── request_limit.py  # 10MB payload limit protection
│   │   └── security_headers.py # Injects CSP, HSTS, X-Frame-Options: DENY
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── base.py           # Base, AuditMixin (UUID, UTC times)
│   │   ├── user.py           # Authorized officer accounts with RBAC & lockout
│   │   ├── source.py         # SocialSource & encrypted credential vault
│   │   ├── keyword.py        # MonitoredKeyword registry & detection logs
│   │   ├── instagram.py      # CollectedItem, KeywordMatch, NotificationSetting
│   │   └── audit_log.py      # Immutable forensic audit trail
│   ├── schemas/              # Pydantic v2 DTO schemas
│   │   ├── common.py         # Standard ApiResponse[T] envelope
│   │   ├── user.py           # UserRead, LoginRequest, TokenResponse
│   │   ├── source.py         # SourceCreate, SourceRead, SourceSyncResult
│   │   ├── keyword.py        # KeywordCreate, KeywordRead, KeywordUpdate
│   │   └── audit.py          # AuditEventRead, AuditEventCreate
│   ├── repositories/         # Parameterized data access layer
│   │   ├── base.py
│   │   ├── source_repository.py
│   │   ├── keyword_repository.py
│   │   └── audit_repository.py
│   ├── services/             # Domain business logic
│   │   ├── base.py
│   │   ├── health_service.py # Database & API connectivity diagnostics
│   │   ├── audit_service.py  # Forensic audit logging service
│   │   ├── source_service.py # Monitored source management
│   │   ├── keyword_service.py# Statutory keyword registry
│   │   ├── instagram_service.py # Instagram Graph API integration & collection
│   │   └── notification_service.py # Keyword-hit notification dispatcher
│   ├── integrations/         # Official social platform adapters
│   │   └── adapters/
│   │       ├── base.py       # SocialSourceAdapter abstract base class
│   │       ├── instagram.py  # Official Meta Graph API v19.0 client
│   │       ├── mock.py       # Verified synthetic mock adapter
│   │       └── factory.py    # Adapter factory
│   └── api/                  # Versioned API routes
│       └── v1/
│           ├── router.py     # Aggregator mounting active v1 endpoints
│           └── endpoints/
│               ├── health.py    # /api/v1/health (UP/DOWN probes)
│               ├── system.py    # /api/v1/system/info
│               ├── auth.py      # /api/v1/auth/login, /logout, /me
│               ├── instagram.py # /api/v1/instagram/* (dashboard, collect, OAuth)
│               ├── sources.py   # /api/v1/sources/*
│               └── keywords.py  # /api/v1/keywords/*
├── frontend/
│   ├── templates/
│   │   ├── base.html              # Government layout, security classification banner, clocks
│   │   ├── dashboard.html         # Overview dashboard template
│   │   └── instagram_dashboard.html # Dedicated Instagram Monitoring Dashboard
│   └── static/
│       ├── css/main.css           # Control-room SOC theme (WCAG AA compliant)
│       └── js/instagram_dashboard.js # Real-time dashboard telemetry & review actions
├── scripts/
│   ├── init_db.py            # Database schema verification & seed data script
│   └── run_dev.ps1           # Development server startup script
└── tests/                    # Automated Pytest suite
    ├── conftest.py           # In-memory SQLite isolation fixtures
    ├── test_health.py        # System health & liveness probes
    ├── test_instagram_adapter.py # Instagram Graph API adapter unit tests
    ├── test_instagram_monitoring_v1.py # Comprehensive 12-point V1 test suite
    ├── test_keywords.py      # Keyword CRUD and matching tests
    ├── test_rate_limiter.py  # Rate limiter middleware tests
    ├── test_security_headers.py # Security headers & CSP tests
    └── test_sources.py       # Encrypted credential vault & source tests
```

---

## 3. Database Schema

The system uses only the tables required for Version 1:

| Table Name | Description | Key Fields |
|---|---|---|
| `users` | Law enforcement user accounts | `id`, `badge_number`, `full_name`, `email`, `hashed_password`, `role`, `is_active`, `is_locked`, `failed_login_attempts` |
| `social_sources` | Legally authorized monitored streams | `id`, `name`, `source_type`, `target_identifier`, `authorization_ref`, `authorized_by_badge`, `status`, `health_status` |
| `source_credentials_metadata` | Encrypted credential vault | `source_id`, `encrypted_access_token`, `token_masked`, `token_scope`, `token_expires_at` |
| `source_sync_status` | Ingestion telemetry & rate limits | `source_id`, `last_sync_at`, `last_successful_sync_at`, `total_items_fetched`, `api_latency_ms` |
| `source_errors` | Transient and API error records | `source_id`, `error_code`, `error_message`, `http_status_code`, `timestamp` |
| `monitored_keywords` | Configurable keyword registry | `id`, `keyword`, `category`, `severity`, `match_type`, `hits_count`, `authorization_ref` |
| `collected_items` | Permitted Instagram content | `id`, `source_id`, `external_id`, `source_account`, `caption`, `media_type`, `permalink`, `published_at`, `collected_at`, `is_demo_data` |
| `keyword_matches` | Operational search matches | `id`, `collected_item_id`, `keyword_text`, `matched_snippet`, `detected_at`, `review_status`, `reviewed_by_badge`, `review_notes` |
| `notification_settings`| Alert dispatch endpoints | `id`, `channel`, `recipient`, `is_enabled`, `notify_on_all_matches` |
| `audit_events` | Immutable forensic audit log | `id`, `timestamp`, `actor_id`, `actor_role`, `action`, `resource_type`, `resource_id`, `details` |

---

## 4. Setup & Installation Instructions

### Prerequisites
- Python 3.10+ (Python 3.12 verified)
- SQLite (built-in, default for prototype) or PostgreSQL 14+ (production)

### Step 1: Clone and Create Virtual Environment
```powershell
cd "c:\Personal Data\Gujarat Police Project\social media monitoring"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Default `.env` configuration uses SQLite (`gujarat_cyber.db`) out-of-the-box.

### Step 4: Initialize and Seed Database
Run the database synchronization script to create tables, seed authorized cybercrime officers, statutory keywords, and baseline notification settings:
```powershell
python scripts/init_db.py
```

### Step 5: Start Development Server
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```
Open your browser at `http://localhost:8080/` or `http://localhost:8080/instagram`.

---

## 5. Default Officer Credentials (Development Prototype)

The system seeds default authorized officers with password `Password@12345`:

| Badge Number | Name | Rank / Role | Department |
|---|---|---|---|
| `GJ-CYBER-8921` | Insp. R. K. Vala | `LEAD_INVESTIGATOR` | State Cyber Crime Cell, CID Crime, Gandhinagar |
| `GJ-CYBER-7410` | Analyst P. M. Dave | `CYBER_ANALYST` | State Cyber Crime Cell, Ahmedabad |
| `GJ-CYBER-0012` | SP Cyber CID | `NODAL_OFFICER` | CID Crime Headquarters, Gandhinagar |
| `GJ-AUDIT-004` | Auditor V. G. Patel | `AUDITOR` | Home Department Cyber Oversight |

---

## 6. Official Meta / Instagram API Integration vs. Mock Sandbox

### Real API Mode (When Approved Meta Credentials Are Provided)
When legitimate Meta App credentials and access tokens are configured in `.env`:
1. `META_APP_ID`: Your registered Meta App ID.
2. `META_APP_SECRET`: Your Meta App Secret.
3. `INSTAGRAM_DEFAULT_ACCESS_TOKEN`: A valid User Access Token with approved permissions:
   - `instagram_basic`: Reads basic account info and media.
   - `pages_show_list`: Discovers connected Facebook pages.
   - `pages_read_engagement`: Accesses permitted public media engagement.
4. The system executes live Graph API v19.0 calls (`https://graph.facebook.com/v19.0/{account_id}/media`).
5. Collected records are tagged with `is_demo_data = False` and rendered with a green `[LIVE API]` badge.

### Verified Mock Sandbox Mode (Default Safe Fallback)
If credentials are not yet provisioned, expired, or invalid (e.g. HTTP 400/401/403):
1. The system **never crashes or blocks the operator**.
2. It safely engages the verified sandbox test adapter.
3. Ingests synthetic cyber awareness media (digital arrest warnings, phishing advisories, TRAI impersonation scams).
4. All records are explicitly tagged with `is_demo_data = True` and rendered with prominent yellow `[DEMO DATA]` badges on the dashboard and API responses.

---

## 7. Running the Automated Test Suite

Run the complete test suite verifying all 56 tests across Version 1 modules:
```powershell
pytest
```

Run specifically the comprehensive 12-point Instagram Monitoring V1 suite:
```powershell
pytest tests/test_instagram_monitoring_v1.py -v
```

The test suite covers:
1. Login, password verification, lockout after 5 failed attempts, and JWT authorization
2. OAuth authorization URL generation and callback code exchange
3. Missing or insufficient Meta API permission handling
4. Expired and revoked token detection (error code 190 subcodes 460/463/467)
5. Rate limit header parsing (`X-App-Usage`) and exponential backoff retry
6. Duplicate collection prevention across multiple synchronization runs
7. Case-insensitive phrase, exact, and regex keyword matching on captions
8. Empty and malformed API payload handling
9. Notification failure isolation without pipeline interruptions
10. Data retention threshold calculation and cascade deletion
11. Secret leakage prevention (token masking in responses and logs)
12. Strict database separation of demo data and real API data

---

## 8. Deployment & Production Guidelines

### Environment Security
- In staging and production, set `APP_ENV=production` and `ENFORCE_SSL=true`.
- Generate a cryptographically strong 48-byte secret key:
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
- Set `DATABASE_URL` to your production PostgreSQL connection string (`postgresql+psycopg2://...`).
- Run behind a hardened reverse proxy (Nginx or AWS ALB) with TLS 1.3 terminated.
- Execute with high-performance ASGI server workers:
  ```powershell
  uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
  ```