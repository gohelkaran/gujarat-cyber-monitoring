# System Architecture Specification
## Gujarat Cyber Crime Social Media Intelligence & Early Warning System

**Classification:** RESTRICTED &bull; Law Enforcement Prototype &bull; Official Use Only  
**Jurisdiction:** Gujarat State Cyber Crime Cell, CID Crime, Gandhinagar, Gujarat, India  

---

## 1. System Mission & Architectural Philosophy

The **Gujarat Cyber Crime Social Media Intelligence & Early Warning System** is an enterprise-grade platform engineered to assist law enforcement agencies in monitoring **authorized, legally accessible, and public API data streams** for early detection of cyber threats, financial frauds, communal disharmony, and digital impersonation.

### Core Architecture Axioms:
1. **Defensive & Analytical Only:** Strictly zero offensive cyber capabilities. No unauthorized scraping, credential harvesting, private account intrusion, or API rate limit bypassing.
2. **Modular Pluggability:** Designed so that official legal authorizations, subpoena data hooks, and platform-provided enterprise API credentials can be plugged in without refactoring core services.
3. **Forensic Evidence Integrity:** All stored intelligence and audit trails preserve source provenance, UTC timestamps, and cryptographic chain-of-custody hashes.
4. **Least Privilege & RBAC:** Access control mirrors the hierarchy of Gujarat Police (Super Admin, Nodal Officer, Lead Investigator, Cyber Analyst, Compliance Auditor).

---

## 2. Layered Architecture Overview

The system implements a decoupled, multi-tier service-oriented architecture:

```
[ Clients: Police Command Browser / Mobile / API Consumers ]
                           │
                           ▼
          [ Security & Protection Middleware Stack ]
   ┌────────────────────────────────────────────────────────┐
   │ • Correlation ID Middleware (X-Request-ID propagation) │
   │ • Security Headers (CSP, HSTS, X-Frame-Options: DENY)  │
   │ • Request Payload Size Limiting (Max 10 MB)            │
   │ • Sliding Window Rate Limiting (120 req/min/IP)        │
   │ • CORS Configuration (Strict Whitelist)                │
   └────────────────────────────────────────────────────────┘
                           │
                           ▼
               [ FastAPI Routing Gateway ]
   ┌────────────────────────────────────────────────────────┐
   │ • API Versioning: /api/v1/health, /api/v1/system       │
   │ • Global Exception Handling (RFC 7807 Clean Envelopes) │
   │ • Input Validation via Pydantic v2 Models              │
   └────────────────────────────────────────────────────────┘
                           │
                           ▼
           [ Business & Domain Service Layer ]
   ┌────────────────────────────────────────────────────────┐
   │ • HealthService: Subsystem health & uptime diagnostics │
   │ • AuditService: Forensic logging & disk redundancy     │
   │ • RBAC Engine: Role hierarchy & classification filters │
   └────────────────────────────────────────────────────────┘
                           │
                           ▼
       [ Data Access & Repository Layer (SQLAlchemy 2.0) ]
   ┌────────────────────────────────────────────────────────┐
   │ • BaseRepository: Parameterized ORM queries            │
   │ • AuditRepository: Append-only event store             │
   │ • AuditMixin: UUID, UTC times, Provenance, Soft-Delete │
   └────────────────────────────────────────────────────────┘
                           │
                           ▼
              [ PostgreSQL Database Engine ]
   ┌────────────────────────────────────────────────────────┐
   │ • Connection Pooling (pre-ping liveness, max overflow) │
   │ • Tables: audit_events, users                          │
   └────────────────────────────────────────────────────────┘
```

---

## 3. Directory Layout & Module Responsibilities

| Directory | Responsibility |
|---|---|
| `app/config/` | Environment variable management via `pydantic-settings`, credentials masking (`SecretStr`), and dev/prod profile management. |
| `app/core/` | Database engine creation, structured logging configuration, domain exceptions, and constants. |
| `app/security/` | Role-based access control (RBAC), password hashing (bcrypt), and HTTP security headers. |
| `app/middleware/` | Request correlation tracing, payload limits, rate limiting, and security headers injection. |
| `app/models/` | SQLAlchemy ORM declarative models, including `AuditMixin`, `AuditEvent`, and `User`. |
| `app/schemas/` | Pydantic data transfer objects (DTOs) for request/response serialization and validation. |
| `app/repositories/` | Data access layer encapsulating all direct database interactions using parameterized queries. |
| `app/services/` | Business logic orchestration, health telemetry, and audit event processing. |
| `app/api/v1/` | Versioned REST API endpoints for health diagnostics and system security metadata. |
| `app/utils/` | Shared utilities: UTC time handling, timezone localization, and sensitive data masking. |
| `app/workers/` | Placeholder for asynchronous task runners (Celery / ARQ / background daemons). |
| `app/integrations/` | Placeholder for authorized third-party social media platform API clients. |
| `app/intelligence/` | Placeholder for NLP sentiment analysis, Gujarati text processing, and threat categorization. |
| `app/alerts/` | Placeholder for multi-channel incident notifications (SMS, WhatsApp, Command Webhooks). |
| `frontend/` | Web interface prototype utilizing Bootstrap 5, Leaflet.js, and Chart.js. |
| `tests/` | Automated test suite (Pytest, TestClient) covering security headers, rate limiting, and health probes. |
| `docs/` | Architectural blueprints, security checklists, and data governance policies. |
| `scripts/` | Shell and PowerShell utilities for environment provisioning and test automation. |

---

## 4. Government Security Design Features

### 4.1. Role-Based Access Control (RBAC)
The system categorizes users into five strict law enforcement roles:
1. **SUPER_ADMIN**: Platform infrastructure and user credential provisioning.
2. **NODAL_OFFICER**: Senior commanding officers (SP / DySP / PI) with high-level intelligence clearance.
3. **LEAD_INVESTIGATOR**: Investigation leads creating and managing case dossiers.
4. **CYBER_ANALYST**: Frontline analysts monitoring authorized intelligence flags.
5. **AUDITOR**: Independent compliance officers with read-only access to immutable forensic audit trails.

### 4.2. Data Classification Tiers
Every entity inherits `classification_level` from `AuditMixin`:
- `UNCLASSIFIED`: Public notifications and general advisories.
- `RESTRICTED`: Default tier for authorized social media streams and early warnings.
- `CONFIDENTIAL`: Active investigation files and suspect profiles.
- `SECRET`: Inter-agency coordinated intelligence and high-sensitivity operations.

### 4.3. Source Provenance & Legal Traceability
All intelligence ingested must record:
```json
{
  "source_type": "OFFICIAL_API",
  "platform": "x_corp_enterprise",
  "endpoint": "/2/tweets/search/recent",
  "authorization_mandate": "DGP-CYBER-CRIME-MANDATE-2026-04",
  "queried_by_badge": "GJ-CYBER-8921"
}
```

### 4.4. Evidence Preservation (Soft Deletion)
In compliance with digital evidence standards (Section 65B, Indian Evidence Act / Bharatiya Sakshya Adhiniyam), records cannot be physically deleted by standard operations. They are soft-deleted with an officer attribution tag and timestamp.
