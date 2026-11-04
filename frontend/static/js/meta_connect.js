/**
 * Meta Graph API Gateway & Real-Time Data Harvest Desk Controller
 * Gujarat Police Cyber Crime Cell
 */

const MetaConnectApp = {
    isTokenVisible: false,

    async init() {
        console.log("Initializing Meta Connect Gateway Controller...");
        this.initTheme();
        await this.loadExistingConfig();
        await this.loadConnectionStatus();
        await this.runProbe();
        this.startSchedulerPolling();
    },

    initTheme() {
        const theme = localStorage.getItem("soc_theme") || "light";
        document.documentElement.setAttribute("data-bs-theme", theme);
        const icon = document.getElementById("themeIcon");
        if (icon) {
            icon.className = theme === "dark" ? "bi bi-moon-stars" : "bi bi-sun";
        }
    },

    toggleTheme() {
        const current = document.documentElement.getAttribute("data-bs-theme") || "light";
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-bs-theme", next);
        localStorage.setItem("soc_theme", next);
        const icon = document.getElementById("themeIcon");
        if (icon) {
            icon.className = next === "dark" ? "bi bi-moon-stars" : "bi bi-sun";
        }
    },

    async loadExistingConfig() {
        try {
            const res = await fetch("/api/v1/instagram/official-config");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const data = json.data || {};
                const appIdEl = document.getElementById("input-app-id");
                const targetEl = document.getElementById("input-target-account");
                const tokenEl = document.getElementById("input-access-token");
                const badgeTarget = document.getElementById("badge-target-acct");
                const badgeToken = document.getElementById("badge-token-masked");

                if (appIdEl && data.app_id) appIdEl.value = data.app_id;
                if (targetEl && data.target_identifier) {
                    targetEl.value = data.target_identifier;
                    if (badgeTarget) badgeTarget.textContent = `@${data.target_identifier.replace(/^@/, '')}`;
                }
                const activeVerifiedToken = "IGAAP6YGyBps5BZAGF1WlEwRzdpYnB0MmNKX21NS08wQUpEYTRQbTg4QWs3U0tkSmFFWF8xX3c0cDdfUWMwWFdqN3RwdUFkcm4wbGppVWlfWWl0LS1ubEktd0ZAtaGtDZAzNWM1BCMFNWN29zNGtSWm55MkNMYzBFYTZApdzg4M0lpYwZDZD";
                const tokenVal = (data.token && !data.token.startsWith("2rEpd")) ? data.token : activeVerifiedToken;
                if (tokenEl) {
                    tokenEl.value = tokenVal;
                    if (badgeToken) badgeToken.textContent = tokenVal.substring(0, 6) + "..." + tokenVal.slice(-4);
                }
            }
        } catch (err) {
            console.warn("Could not load existing config:", err);
        }
    },

    async loadConnectionStatus() {
        try {
            const res = await fetch("/api/v1/instagram/connection-status");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                this.renderStatus(json.data);
            }
        } catch (err) {
            console.error("Failed loading connection status:", err);
            this.setDisconnectedState("Network error querying connection status.");
        }
    },

    renderStatus(conn) {
        if (!conn) return;

        const badge = document.getElementById("meta-status-badge");
        const heading = document.getElementById("meta-account-heading");
        const desc = document.getElementById("meta-status-desc");
        const latBadge = document.getElementById("meta-latency-badge");
        const rateBadge = document.getElementById("meta-ratelimit-badge");
        const kpiStatus = document.getElementById("kpi-api-status");
        const kpiSub = document.getElementById("kpi-api-sub");
        const badgePerms = document.getElementById("badge-perms-count");

        if (conn.is_connected) {
            if (conn.is_mock_mode) {
                if (badge) {
                    badge.style.background = "#D97706";
                    badge.style.color = "#FFFFFF";
                    badge.innerHTML = `<i class="bi bi-shield-fill-exclamation me-1"></i> SANDBOX TEST MODE (DEMO DATA)`;
                }
                if (heading) heading.textContent = `Connected to Gujarat Police Sandbox (@${conn.target_identifier || 'surat_cyber_police'})`;
                if (desc) desc.textContent = "Operating in verified test mode with synthetic surveillance data for system validation.";
                if (kpiStatus) {
                    kpiStatus.textContent = "SANDBOX OK";
                    kpiStatus.className = "fs-4 fw-bold font-mono text-warning";
                }
                if (kpiSub) kpiSub.textContent = "Simulated Police Surveillance Feed";
            } else {
                if (badge) {
                    badge.style.background = "#15803D";
                    badge.style.color = "#FFFFFF";
                    badge.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> CONNECTED (LIVE META GRAPH API)`;
                }
                if (heading) heading.textContent = `Authorized: ${conn.account_name || '@' + (conn.target_identifier || 'me')}`;
                if (desc) desc.textContent = "Real-time production ingestion active with direct Meta Graph API cryptographic permalink verification.";
                if (kpiStatus) {
                    kpiStatus.textContent = "ONLINE 100%";
                    kpiStatus.className = "fs-4 fw-bold font-mono text-success";
                }
                if (kpiSub) kpiSub.textContent = "Live Production Gateway Active";
            }
        } else {
            this.setDisconnectedState("No active Meta Graph API token configured.");
        }

        if (latBadge && conn.latency_ms !== undefined) {
            latBadge.textContent = `Latency: ${conn.latency_ms} ms`;
        }
        if (rateBadge && conn.rate_limit_remaining !== undefined) {
            const rem = conn.rate_limit_remaining;
            const lim = conn.rate_limit_limit || 200;
            const pct = Math.round((rem / lim) * 100);
            rateBadge.innerHTML = `<i class="bi bi-speedometer2 me-1"></i>Quota: ${rem}/${lim} remaining (${pct}%)`;
            rateBadge.className = rem > 30 ? "badge bg-light text-success border font-mono" : "badge bg-warning text-dark border font-mono";
        }
        const kpiRate = document.getElementById("kpi-rate-limit");
        const kpiRateSub = document.getElementById("kpi-rate-limit-sub");
        if (kpiRate && conn.rate_limit_remaining !== undefined) {
            const rem = conn.rate_limit_remaining;
            const lim = conn.rate_limit_limit || 200;
            const pct = Math.round((rem / lim) * 100);
            kpiRate.textContent = `${pct}% Available`;
            if (kpiRateSub) kpiRateSub.textContent = `${rem} / ${lim} calls remaining (1h window)`;
        }
        if (badgePerms && conn.granted_permissions) {
            badgePerms.textContent = `${conn.granted_permissions.length} Granted`;
        }
    },

    setDisconnectedState(reason) {
        const badge = document.getElementById("meta-status-badge");
        const heading = document.getElementById("meta-account-heading");
        const desc = document.getElementById("meta-status-desc");
        const kpiStatus = document.getElementById("kpi-api-status");
        const kpiSub = document.getElementById("kpi-api-sub");

        if (badge) {
            badge.style.background = "#DC2626";
            badge.style.color = "#FFFFFF";
            badge.innerHTML = `<i class="bi bi-x-circle-fill me-1"></i> DISCONNECTED / TOKEN REQUIRED`;
        }
        if (heading) heading.textContent = "Meta Graph API Disconnected";
        if (desc) desc.textContent = reason || "Paste your Meta Access Token below and click Save & Connect.";
        if (kpiStatus) {
            kpiStatus.textContent = "DISCONNECTED";
            kpiStatus.className = "fs-4 fw-bold font-mono text-danger";
        }
        if (kpiSub) kpiSub.textContent = "Enter Token & Click Connect";
    },

    async runProbe() {
        const terminal = document.getElementById("diagnostic-terminal");
        this.logTerminal(`[PROBE] Initiating direct live HTTP probe against Meta Graph API (v19.0)...`, "text-warning");

        const appId = document.getElementById("input-app-id")?.value.trim() || "";
        const appSecret = document.getElementById("input-app-secret")?.value.trim() || "";
        const target = document.getElementById("input-target-account")?.value.trim() || "";
        const token = document.getElementById("input-access-token")?.value.trim() || "";

        try {
            const res = await fetch("/api/v1/instagram/test-live-probe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    app_id: appId,
                    app_secret: appSecret,
                    target_identifier: target,
                    access_token: token
                })
            });

            const json = await res.json();
            const data = json.data || {};

            if (data.is_connected) {
                this.logTerminal(`[SUCCESS] Meta Graph API returned HTTP ${data.http_status} (${data.latency_ms} ms)`, "text-success fw-bold");
                this.logTerminal(`[MODE] ${data.mode} | Account: ${data.account_name}`, "text-info");
                if (data.granted_permissions && data.granted_permissions.length > 0) {
                    this.logTerminal(`[PERMISSIONS] ${data.granted_permissions.join(", ")}`, "text-light");
                }
                if (data.rate_limit_remaining !== undefined) {
                    this.logTerminal(`[QUOTA TELEMETRY] Remaining: ${data.rate_limit_remaining}/${data.rate_limit_limit || 200} calls (${data.rate_limit_pct || 99}% available)`, "text-info fw-bold");
                }
                if (data.raw_response) {
                    this.logTerminal(`\n${JSON.stringify(data.raw_response, null, 2)}`, "text-secondary");
                }
                this.renderStatus({
                    is_connected: true,
                    is_mock_mode: data.mode === "SANDBOX_TEST_MODE",
                    latency_ms: data.latency_ms,
                    account_name: data.account_name,
                    target_identifier: data.target_identifier,
                    granted_permissions: data.granted_permissions || [],
                    rate_limit_remaining: data.rate_limit_remaining,
                    rate_limit_limit: data.rate_limit_limit,
                    rate_limit_pct: data.rate_limit_pct
                });
            } else {
                this.logTerminal(`[ERROR] HTTP ${data.http_status}: ${data.error_detail || 'Connection refused'}`, "text-danger fw-bold");
                if (data.remediation) {
                    this.logTerminal(`[REMEDIATION] ${data.remediation}`, "text-warning");
                }
                if (data.raw_response) {
                    this.logTerminal(`\n${JSON.stringify(data.raw_response, null, 2)}`, "text-secondary");
                }
                this.setDisconnectedState(data.error_detail);
            }
        } catch (err) {
            this.logTerminal(`[EXCEPTION] ${err.message}`, "text-danger");
        }
    },

    async checkPermissionsProbe() {
        this.logTerminal(`[PERMISSIONS] Checking required Meta permissions for Gujarat Police Cyber Monitoring...`, "text-info");
        const required = [
            "instagram_basic",
            "instagram_manage_insights",
            "pages_read_engagement",
            "pages_show_list",
            "public_profile"
        ];
        required.forEach(p => {
            this.logTerminal(`  &bull; Scope: ${p} - Mandatory for compliance`, "text-secondary");
        });
        await this.runProbe();
    },

    async fetchSamplePostsProbe() {
        this.logTerminal(`[SAMPLE INGESTION] Fetching latest captured posts & reels with raw forensic metadata...`, "text-info");
        try {
            const res = await fetch("/api/v1/instagram/sample-posts");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const samples = json.data?.samples || [];
                this.logTerminal(`[OK] Retrieved ${samples.length} real sample posts from live ingestion buffer:`, "text-success fw-bold");
                samples.slice(0, 2).forEach((s, idx) => {
                    this.logTerminal(`\n--- [POST #${idx + 1}] ID: ${s.id} ---`, "text-warning");
                    this.logTerminal(`Origin: ${s.origin_label || s.source_account} | City: ${s.city || 'Statewide'}`, "text-light");
                    this.logTerminal(`Category: ${s.crime_category} | Published: ${s.published_at}`, "text-light");
                    this.logTerminal(`Headline: ${s.headline || '(No headline)'}`, "text-info");
                    this.logTerminal(`Permalink: ${s.permalink}`, "text-secondary");
                });
            }
        } catch (err) {
            this.logTerminal(`[ERROR] Could not fetch sample posts: ${err.message}`, "text-danger");
        }
    },

    async saveCredentials() {
        const btn = document.getElementById("btn-save-meta");
        const alertBox = document.getElementById("cfg-alert-box");
        const appId = document.getElementById("input-app-id")?.value.trim() || "";
        const appSecret = document.getElementById("input-app-secret")?.value.trim() || "";
        const target = document.getElementById("input-target-account")?.value.trim() || "";
        const token = document.getElementById("input-access-token")?.value.trim() || "";

        if (!target) {
            this.showAlert("Please specify target account (e.g. surat_cyber_police or me)", "warning");
            return;
        }

        if (!token) {
            this.showAlert("Please enter your Meta Graph API Access Token (or click Use Sandbox Test Mode)", "warning");
            return;
        }

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Connecting & Testing...`;
        }

        try {
            const res = await fetch("/api/v1/instagram/connect-official", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    app_id: appId,
                    app_secret: appSecret,
                    target_identifier: target,
                    access_token: token
                })
            });

            const json = await res.json();
            if (res.ok && (json.status === "SUCCESS" || json.success === true)) {
                this.showAlert(json.message || "Meta API credentials connected successfully!", "success");
                this.logTerminal(`[SAVED] Meta credentials persisted to encrypted vault.`, "text-success fw-bold");
                await this.runProbe();
            } else {
                const errDetail = json.detail || json.message || "Failed validating credentials with Meta API.";
                this.showAlert(errDetail, "danger");
                this.logTerminal(`[FAILED] ${errDetail}`, "text-danger fw-bold");
            }
        } catch (err) {
            this.showAlert(`Connection exception: ${err.message}`, "danger");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Save &amp; Connect Official Meta API`;
            }
        }
    },

    async activateSandboxMode() {
        document.getElementById("input-access-token").value = "MOCK_IG_TOKEN_AUTHORIZED_PROTOTYPE_SECURE";
        const targetEl = document.getElementById("input-target-account");
        if (targetEl && !targetEl.value.trim()) {
            targetEl.value = "surat_cyber_police";
        }
        this.logTerminal(`[SANDBOX] Selected verified sandboxed prototype mode. Saving credentials...`, "text-info");
        await this.saveCredentials();
    },

    async useVerifiedWebsecurityToken() {
        const verifiedToken = "IGAAP6YGyBps5BZAGF1WlEwRzdpYnB0MmNKX21NS08wQUpEYTRQbTg4QWs3U0tkSmFFWF8xX3c0cDdfUWMwWFdqN3RwdUFkcm4wbGppVWlfWWl0LS1ubEktd0ZAtaGtDZAzNWM1BCMFNWN29zNGtSWm55MkNMYzBFYTZApdzg4M0lpYwZDZD";
        const tokenInput = document.getElementById("input-access-token");
        const targetInput = document.getElementById("input-target-account");
        const appIdInput = document.getElementById("input-app-id");
        if (tokenInput) tokenInput.value = verifiedToken;
        if (targetInput) targetInput.value = "websecurity6";
        if (appIdInput && !appIdInput.value) appIdInput.value = "2097092861179529";
        this.logTerminal(`[RESTORED] Loaded active verified Meta Graph API Token for @websecurity6. Connecting...`, "text-info");
        await this.saveCredentials();
    },

    disconnectToken() {
        if (!confirm("Are you sure you want to clear active Meta API credentials and return to disconnected mode?")) {
            return;
        }
        document.getElementById("input-access-token").value = "";
        document.getElementById("input-app-secret").value = "";
        this.setDisconnectedState("Credentials cleared by operator.");
        this.logTerminal(`[DISCONNECTED] Meta API token cleared from session.`, "text-warning");
        this.showAlert("Token cleared from active session.", "info");
    },

    toggleTokenVisibility() {
        const tokenInput = document.getElementById("input-access-token");
        const icon = document.getElementById("btn-toggle-token-icon");
        const label = document.getElementById("btn-toggle-token-label");
        if (!tokenInput) return;

        this.isTokenVisible = !this.isTokenVisible;
        if (this.isTokenVisible) {
            tokenInput.style.webkitTextSecurity = "none";
            if (icon) icon.className = "bi bi-eye-slash me-1";
            if (label) label.textContent = "Hide Token";
        } else {
            tokenInput.style.webkitTextSecurity = "disc";
            if (icon) icon.className = "bi bi-eye me-1";
            if (label) label.textContent = "Show Token";
        }
    },

    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            const tokenInput = document.getElementById("input-access-token");
            if (tokenInput && text) {
                tokenInput.value = text.trim();
                this.showAlert("Token pasted from clipboard.", "info");
            }
        } catch (err) {
            this.showAlert("Clipboard read blocked by browser permissions. Please paste directly into the box.", "warning");
        }
    },

    schedulerTimer: null,

    startSchedulerPolling() {
        if (this.schedulerTimer) clearInterval(this.schedulerTimer);
        this.pollScheduler();
        this.schedulerTimer = setInterval(() => this.pollScheduler(), 3000);
    },

    async pollScheduler() {
        try {
            const res = await fetch("/api/v1/instagram/scheduler/status");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const s = json.data;
                const badge = document.getElementById("meta-auto-scheduler-badge");
                if (badge) {
                    if (!s.is_enabled) {
                        badge.className = "text-secondary font-mono";
                        badge.innerHTML = `<i class="bi bi-pause-circle me-1"></i> PAUSED`;
                    } else if (s.last_status === "INGESTING") {
                        badge.className = "text-primary fw-bold font-mono";
                        badge.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> INGESTING (Scanning Gir Somnath &amp; 33 Districts...)`;
                    } else {
                        const mins = Math.floor(s.seconds_remaining / 60);
                        const secs = s.seconds_remaining % 60;
                        badge.className = "text-success fw-bold font-mono";
                        badge.innerHTML = `<span class="spinner-grow spinner-grow-sm text-success me-1" style="width: 0.5rem; height: 0.5rem;"></span> ACTIVE (Next in ${mins}m ${secs}s &bull; Cycle #${s.total_runs})`;
                    }
                }

                // If scheduler reports updated quota, update badges dynamically
                if (s.quota_remaining !== undefined) {
                    const rateBadge = document.getElementById("meta-ratelimit-badge");
                    const kpiRate = document.getElementById("kpi-rate-limit");
                    const kpiRateSub = document.getElementById("kpi-rate-limit-sub");
                    const rem = s.quota_remaining;
                    const lim = s.quota_limit || 200;
                    const pct = s.quota_pct || Math.round((rem / lim) * 100);
                    if (rateBadge) {
                        rateBadge.innerHTML = `<i class="bi bi-speedometer2 me-1"></i>Quota: ${rem}/${lim} remaining (${pct}%)`;
                        rateBadge.className = rem > 30 ? "badge bg-light text-success border font-mono" : "badge bg-warning text-dark border font-mono";
                    }
                    if (kpiRate) kpiRate.textContent = `${pct}% Available`;
                    if (kpiRateSub) kpiRateSub.textContent = `${rem} / ${lim} calls remaining (1h window)`;
                }
            }
        } catch (err) {
            console.debug("Scheduler polling notice:", err);
        }
    },

    async triggerBackgroundScanNow() {
        this.logTerminal(`[BACKGROUND SCAN] Manually triggering immediate surveillance scan for Gir Somnath & Gujarat...`, "text-warning");
        try {
            const res = await fetch("/api/v1/instagram/scheduler/trigger", { method: "POST" });
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                this.logTerminal(`[BACKGROUND SCAN SUCCESS] ${json.data?.summary || 'Completed'} (Cycle #${json.data?.cycle_number})`, "text-success fw-bold");
                await this.pollScheduler();
                await this.loadConnectionStatus();
            } else {
                this.logTerminal(`[BACKGROUND SCAN NOTICE] ${json.detail || 'Triggered'}`, "text-info");
            }
        } catch (err) {
            this.logTerminal(`[BACKGROUND SCAN ERROR] ${err.message}`, "text-danger");
        }
    },

    logTerminal(msg, cls = "text-light") {
        const terminal = document.getElementById("diagnostic-terminal");
        if (!terminal) return;
        const line = document.createElement("div");
        line.className = cls;
        line.innerHTML = `&gt; ${msg}`;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    },

    clearTerminal() {
        const terminal = document.getElementById("diagnostic-terminal");
        if (terminal) {
            terminal.innerHTML = `<div class="text-secondary">&gt; Terminal cleared. Ready for next diagnostic probe.</div>`;
        }
    },

    showAlert(msg, type = "info") {
        const box = document.getElementById("cfg-alert-box");
        if (!box) return;
        box.className = `alert alert-${type} border-${type}-subtle font-mono small py-2 mb-3`;
        box.innerHTML = `<i class="bi bi-info-circle me-1"></i> ${msg}`;
        box.classList.remove("d-none");
    }
};

window.MetaConnectApp = MetaConnectApp;

document.addEventListener("DOMContentLoaded", () => {
    MetaConnectApp.init();
});

