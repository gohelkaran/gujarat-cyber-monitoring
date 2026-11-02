# Government Security & Compliance Checklist
## Gujarat Cyber Crime Social Media Intelligence & Early Warning System

**Standard:** Law Enforcement Web Platform Baseline Security  
**Aligned With:** Indian CERT-In Guidelines, OWASP Top 10, ISO 27001, MoHUA/MHA Police IT Security Directives  

---

## 1. Authentication & Identity Management
- [x] **No Hard-Coded Credentials:** All passwords, tokens, and keys loaded strictly via environment variables.
- [x] **Type-Safe Secret Masking:** Pydantic `SecretStr` prevents printing credentials in console or memory traces.
- [x] **Password Hashing:** Standard salted Bcrypt implementation (`pwd_context.hash()`).
- [x] **Brute-Force Lockout Defense:** User model tracks `failed_login_attempts` and `is_locked` status.
- [ ] **MFA Integration:** (Planned for Production) OTP / Hardware security key integration for Nodal Officers.

## 2. API Security & Transport Layer
- [x] **Strict Transport Security (HSTS):** Pre-configured 1-year max-age with subdomains and preload flags for HTTPS.
- [x] **Content Security Policy (CSP):** Strict script, style, frame-ancestor (`'none'`), and image policies.
- [x] **Anti-Clickjacking:** `X-Frame-Options: DENY` on all responses.
- [x] **Anti-MIME Sniffing:** `X-Content-Type-Options: nosniff`.
- [x] **Permissions Policy:** Disabled camera, microphone, geolocation, and USB hardware access.
- [x] **Request Size Limits:** Middleware drops payloads > 10 MB with HTTP 413 to prevent DoS memory spikes.
- [x] **Rate Limiting:** Sliding-window rate limiter (120 req/minute/IP) with HTTP 429 and `Retry-After` headers.
- [x] **Server Fingerprint Masking:** `Server` response header replaced with generic platform label.

## 3. Data Governance & Privacy Controls
- [x] **Strict Legal Compliance:** Zero offensive cyber capabilities, zero credential theft, zero private account scraping.
- [x] **Source Provenance:** Every ingested item records legal authority, API source, and requesting officer badge number.
- [x] **Data Classification:** Four-tier classification (`UNCLASSIFIED`, `RESTRICTED`, `CONFIDENTIAL`, `SECRET`).
- [x] **Soft-Deletion Architecture:** Preserves digital chain-of-custody by preventing physical record loss.
- [x] **Statutory Retention:** Pre-configured 2-year (730 days) log and incident retention baseline.

## 4. Audit & Forensic Integrity
- [x] **Correlation Tracing:** `X-Request-ID` and `X-Correlation-ID` propagate through asynchronous execution chains.
- [x] **Structured Logging:** Machine-readable JSON output in production for SIEM/SOC ingestion.
- [x] **Sensitive Data Redaction:** Regular expression filters intercept and mask passwords, tokens, and PII from log output.
- [x] **Dual Audit Persistence:** Events persist simultaneously to the relational database and an append-only flat file mirror.
- [x] **UTC Time Uniformity:** All timestamps generated and stored in UTC; localized rendering (IST) handled cleanly.

## 5. Input Validation & Database Protection
- [x] **Parameterized Queries:** Enforced exclusively through SQLAlchemy 2.0 ORM; zero raw string SQL concatenation.
- [x] **Strong Typing:** Pydantic v2 schemas strictly validate all incoming route parameters and bodies.
- [x] **Safe Error Envelopes:** Global exception handler catches unhandled errors and hides internal stack traces in production.
- [x] **Connection Pool Management:** Pre-ping connection health checks prevent stale socket drops.
