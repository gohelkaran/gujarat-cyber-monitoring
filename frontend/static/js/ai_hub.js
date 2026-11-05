/**
 * AI Free Developer Hub & Stack Architect Client Controller
 * Gujarat Cyber Crime Social Media Intelligence & Early Warning System
 * Inspired by ripienaar/free-for-dev
 */

const AiHubManager = {
    currentTab: 'architect',

    open() {
        this.switchTab('architect');
    },

    switchTab(tabName) {
        this.currentTab = tabName;
        document.querySelectorAll('.ai-hub-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        document.querySelectorAll('.ai-hub-pane').forEach(pane => {
            pane.classList.toggle('d-none', pane.id !== `ai-pane-${tabName}`);
        });

        if (tabName === 'sentinel') {
            this.runDriftAudit();
        } else if (tabName === 'catalog') {
            this.loadCatalog();
        }
    },

    // ------------------------------------------------------------------------
    // IDEA 1: ZERO-DOLLAR STACK ARCHITECT
    // ------------------------------------------------------------------------
    async generateStack() {
        const desc = document.getElementById('ai-architect-desc')?.value.trim() || 
            "Gujarat Police Cyber Crime Intelligence portal with FastAPI, vector search, Gujarati NLP, and continuous crawlers.";
        const lang = document.getElementById('ai-architect-lang')?.value || "Python / FastAPI";
        const useCase = document.getElementById('ai-architect-usecase')?.value || "Cyber Intelligence & Early Warning";
        const users = parseInt(document.getElementById('ai-architect-users')?.value || "500", 10);

        const btn = document.getElementById('btn-generate-stack');
        const spinner = document.getElementById('stack-spinner');
        const resultDiv = document.getElementById('stack-result-container');

        if (btn) btn.disabled = true;
        if (spinner) spinner.classList.remove('d-none');
        if (resultDiv) resultDiv.innerHTML = '<div class="text-center py-5 text-secondary"><div class="spinner-border text-primary me-2"></div>Synthesizing zero-dollar multi-cloud architecture...</div>';

        try {
            const resp = await fetch('/api/v1/ai/stack-architect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_description: desc,
                    tech_language: lang,
                    target_use_case: useCase,
                    monthly_active_users: users
                })
            });

            const data = await resp.json();
            if (data.success && data.data) {
                this.renderStackBlueprint(data.data);
            } else {
                if (resultDiv) resultDiv.innerHTML = `<div class="alert alert-danger font-mono small">${data.error?.message || 'Synthesis failed.'}</div>`;
            }
        } catch (err) {
            if (resultDiv) resultDiv.innerHTML = `<div class="alert alert-danger font-mono small">Error generating architecture: ${err.message}</div>`;
        } finally {
            if (btn) btn.disabled = false;
            if (spinner) spinner.classList.add('d-none');
        }
    },

    renderStackBlueprint(data) {
        const container = document.getElementById('stack-result-container');
        if (!container) return;

        let tableRows = data.stack_blueprint.map(c => `
            <tr>
                <td class="fw-bold font-mono text-dark">${this.escape(c.layer)}</td>
                <td>
                    <div class="fw-semibold text-primary">${this.escape(c.component)}</div>
                    <div class="small text-secondary font-mono">${this.escape(c.optimization_tip)}</div>
                </td>
                <td>
                    <a href="${this.escape(c.url)}" target="_blank" rel="noopener noreferrer" class="fw-bold text-decoration-none">
                        ${this.escape(c.provider)} <i class="bi bi-box-arrow-up-right small"></i>
                    </a>
                    <div class="small text-muted font-mono" style="font-size: 0.72rem;">${this.escape(c.free_quota)}</div>
                </td>
                <td class="text-end">
                    <span class="badge bg-success-subtle text-success border border-success-subtle font-mono">${this.escape(c.cost)}</span>
                </td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="card border-0 shadow-sm mb-3">
                <div class="card-header bg-success-subtle text-success border-success-subtle d-flex justify-content-between align-items-center py-2">
                    <span class="fw-bold font-mono"><i class="bi bi-check-circle-fill me-1"></i> Synthesized Zero-Dollar Stack Blueprint</span>
                    <span class="badge bg-success text-white font-mono fs-6 px-3 py-1">TOTAL: ${data.total_monthly_cost}</span>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0 font-sans" style="font-size: 0.85rem;">
                            <thead class="table-light font-mono small text-secondary">
                                <tr>
                                    <th>Architecture Layer</th>
                                    <th>System Component &amp; Tip</th>
                                    <th>Recommended Free Provider</th>
                                    <th class="text-end">Monthly Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tableRows}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="card-footer bg-light py-2 small d-flex justify-content-between align-items-center">
                    <span class="text-secondary font-mono">Capacity: ${this.escape(data.estimated_capacity.daily_crime_bulletins)} &bull; ${this.escape(data.estimated_capacity.monthly_active_officers)}</span>
                    <button class="btn btn-sm btn-outline-secondary font-mono" onclick="navigator.clipboard.writeText(JSON.stringify(window._lastStack, null, 2)); alert('Architecture configuration copied to clipboard!');">
                        <i class="bi bi-clipboard me-1"></i> Copy Config JSON
                    </button>
                </div>
            </div>
        `;
        window._lastStack = data;
    },

    // ------------------------------------------------------------------------
    // IDEA 2: PLAN DRIFT SENTINEL
    // ------------------------------------------------------------------------
    async runDriftAudit() {
        const container = document.getElementById('sentinel-result-container');
        if (!container) return;
        container.innerHTML = '<div class="text-center py-5 text-secondary"><div class="spinner-border text-warning me-2"></div>Auditing free-tier catalog stability and TLS health...</div>';

        try {
            const resp = await fetch('/api/v1/ai/drift-sentinel/audit');
            const data = await resp.json();
            if (data.success && data.data) {
                const audit = data.data;
                const rows = audit.results.map(r => {
                    let badgeClass = 'bg-success-subtle text-success border-success-subtle';
                    if (r.status === 'DRIFT_WARNING') badgeClass = 'bg-danger-subtle text-danger border-danger-subtle';
                    else if (r.status === 'REQUIRES_ATTENTION') badgeClass = 'bg-warning-subtle text-dark border-warning-subtle';

                    return `
                        <tr>
                            <td class="fw-bold text-dark font-sans">
                                <a href="${this.escape(r.url)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none">
                                    ${this.escape(r.name)} <i class="bi bi-box-arrow-up-right small"></i>
                                </a>
                            </td>
                            <td class="font-mono small text-secondary">${this.escape(r.category)}</td>
                            <td>
                                <span class="badge ${badgeClass} font-mono px-2 py-1" style="font-size: 0.72rem;">${this.escape(r.status)}</span>
                            </td>
                            <td class="font-mono small fw-bold ${r.health_score >= 80 ? 'text-success' : 'text-danger'}">${r.health_score}%</td>
                            <td class="small font-mono text-secondary">
                                ${r.flags.map(f => `<div>&bull; ${this.escape(f)}</div>`).join('')}
                            </td>
                        </tr>
                    `;
                }).join('');

                container.innerHTML = `
                    <div class="row g-3 mb-3">
                        <div class="col-md-4">
                            <div class="card border-0 bg-success-subtle text-success p-3 text-center">
                                <div class="fs-4 fw-bold font-mono">${audit.healthy_stable_tools} / ${audit.total_tools_audited}</div>
                                <div class="small fw-semibold">Healthy Stable Free Tiers</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-0 bg-warning-subtle text-dark p-3 text-center">
                                <div class="fs-4 fw-bold font-mono">${audit.flagged_drift_tools}</div>
                                <div class="small fw-semibold">Flagged / Caveat Tiers</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-0 bg-primary-subtle text-primary p-3 text-center">
                                <div class="fs-4 fw-bold font-mono">${audit.drift_index_percentage}%</div>
                                <div class="small fw-semibold">Catalog Stability Index</div>
                            </div>
                        </div>
                    </div>

                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0 font-sans" style="font-size: 0.82rem;">
                            <thead class="table-light font-mono small text-secondary">
                                <tr>
                                    <th>Developer Tool</th>
                                    <th>Category</th>
                                    <th>Status</th>
                                    <th>Health</th>
                                    <th>Sentinel Flags &amp; Notes</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rows}
                            </tbody>
                        </table>
                    </div>
                `;
            }
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger font-mono small">Error running sentinel audit: ${err.message}</div>`;
        }
    },

    // ------------------------------------------------------------------------
    // IDEA 3: PULL REQUEST & SUBMISSION AUDITOR
    // ------------------------------------------------------------------------
    async auditSubmission() {
        const name = document.getElementById('auditor-name')?.value.trim();
        const url = document.getElementById('auditor-url')?.value.trim();
        const category = document.getElementById('auditor-cat')?.value || "Managed Databases";
        const freeTier = document.getElementById('auditor-tier')?.value.trim();
        const requiresCc = document.getElementById('auditor-cc')?.checked || false;
        const isTrial = document.getElementById('auditor-trial')?.checked || false;
        const isSelfHosted = document.getElementById('auditor-selfhosted')?.checked || false;

        const resultDiv = document.getElementById('auditor-result-container');
        if (!name || !url || !freeTier) {
            alert("Please provide Tool Name, Direct URL, and Free Tier specifications.");
            return;
        }

        if (resultDiv) resultDiv.innerHTML = '<div class="text-center py-4 text-secondary"><div class="spinner-border text-info me-2"></div>Evaluating submission against repository guidelines...</div>';

        try {
            const resp = await fetch('/api/v1/ai/submission-auditor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    service_name: name,
                    service_url: url,
                    category: category,
                    claimed_free_tier: freeTier,
                    requires_credit_card: requiresCc,
                    is_trial_only: isTrial,
                    is_self_hosted: isSelfHosted
                })
            });

            const data = await resp.json();
            if (data.success && data.data) {
                const res = data.data;
                let verdictBadge = 'bg-success text-white';
                if (res.verdict === 'FAIL') verdictBadge = 'bg-danger text-white';
                else if (res.verdict === 'CONDITIONAL_PASS') verdictBadge = 'bg-warning text-dark';

                resultDiv.innerHTML = `
                    <div class="card border-0 shadow-sm mt-3">
                        <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center py-2">
                            <span class="font-mono fw-bold fs-6">Audit Report: ${this.escape(res.service_name)}</span>
                            <span class="badge ${verdictBadge} font-mono fs-6 px-3 py-1">VERDICT: ${res.verdict} (${res.score}/100)</span>
                        </div>
                        <div class="card-body">
                            <h6 class="font-mono text-secondary small fw-bold text-uppercase">Checklist Compliance:</h6>
                            <ul class="list-unstyled mb-3 small font-mono">
                                ${res.passed_rules.map(p => `<li class="text-success mb-1"><i class="bi bi-check-circle-fill me-1"></i> ${this.escape(p)}</li>`).join('')}
                                ${res.warnings.map(w => `<li class="text-warning mb-1"><i class="bi bi-exclamation-triangle-fill me-1"></i> ${this.escape(w)}</li>`).join('')}
                                ${res.violations.map(v => `<li class="text-danger mb-1"><i class="bi bi-x-circle-fill me-1"></i> ${this.escape(v)}</li>`).join('')}
                            </ul>

                            <h6 class="font-mono text-secondary small fw-bold text-uppercase">Automated GitHub PR Comment (Markdown):</h6>
                            <pre class="bg-light p-3 border rounded font-mono small text-dark mb-0" style="white-space: pre-wrap;">${this.escape(res.github_pr_comment_markdown)}</pre>
                        </div>
                    </div>
                `;
            }
        } catch (err) {
            if (resultDiv) resultDiv.innerHTML = `<div class="alert alert-danger font-mono small">Error auditing submission: ${err.message}</div>`;
        }
    },

    // ------------------------------------------------------------------------
    // IDEA 4: SEMANTIC DISCOVERY & COMPARISON
    // ------------------------------------------------------------------------
    async searchTools() {
        const query = document.getElementById('ai-search-query')?.value.trim();
        const container = document.getElementById('search-result-container');
        if (!query) return;

        if (container) container.innerHTML = '<div class="text-center py-4 text-secondary"><div class="spinner-border text-primary me-2"></div>Searching developer tools semantically...</div>';

        try {
            const resp = await fetch('/api/v1/ai/semantic-search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, limit: 6 })
            });

            const data = await resp.json();
            if (data.success && data.data) {
                const res = data.data;
                let cards = res.top_tools.map(t => `
                    <div class="col-md-6 mb-3">
                        <div class="card h-100 border-0 shadow-sm p-3">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="fw-bold text-dark mb-0">${this.escape(t.name)}</h6>
                                <span class="badge bg-primary-subtle text-primary border font-mono small">${this.escape(t.category)}</span>
                            </div>
                            <div class="small text-secondary mb-2" style="font-size: 0.8rem;">
                                <strong class="text-dark">Free Tier:</strong> ${this.escape(t.free_tier)}
                            </div>
                            <div class="small text-muted mb-2 font-mono" style="font-size: 0.75rem;">
                                <i class="bi bi-info-circle me-1 text-primary"></i>${this.escape(t.ideal_for)}
                            </div>
                            <div class="mt-auto d-flex justify-content-between align-items-center pt-2 border-top">
                                <span class="badge ${t.credit_card_required ? 'bg-warning-subtle text-dark' : 'bg-success-subtle text-success'} font-mono" style="font-size: 0.7rem;">
                                    ${t.credit_card_required ? 'Card Required' : 'No Card Needed'}
                                </span>
                                <a href="${this.escape(t.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-primary font-mono py-0" style="font-size: 0.76rem;">
                                    Visit <i class="bi bi-box-arrow-up-right ms-1"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                `).join('');

                container.innerHTML = `
                    <div class="alert alert-info py-2 font-mono small d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-stars me-1 text-primary"></i> ${this.escape(res.recommendation_summary)}</span>
                        <span class="badge bg-primary">${res.matches_found} Results</span>
                    </div>
                    <div class="row">
                        ${cards}
                    </div>
                `;
            }
        } catch (err) {
            if (container) container.innerHTML = `<div class="alert alert-danger font-mono small">Error searching tools: ${err.message}</div>`;
        }
    },

    escape(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
};

window.AiHubManager = AiHubManager;
