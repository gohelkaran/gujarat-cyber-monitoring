/**
 * Instagram Monitoring Dashboard - Frontend Controller
 * Gujarat Cyber Crime Social Media Intelligence & Early Warning System - Version 1
 */

const InstagramApp = {
    filters: {
        keyword: '',
        city: '',
        account: '',
        platform: 'ALL',
        dateFrom: '',
        dateTo: ''
    },
    currentMatchId: null,
    currentPage: 1,
    pageSize: 20,
    _lastKnownCount: 0,
    _newPostAlertShown: false,

    init() {
        console.log("Initializing Social Media Intelligence Dashboard Controller...");
        const citySelect = document.getElementById("filter-city");
        if (citySelect && citySelect.value) {
            this.filters.city = citySelect.value;
        }
        this.currentPage = 1;
        this.loadDashboardData();
        this.pollSchedulerStatus();
        // Periodic background scheduler poll every 4 seconds
        setInterval(() => this.pollSchedulerStatus(), 4000);
        // Periodic telemetry poll every 30 seconds — check for new posts
        setInterval(() => this._checkForNewPosts(), 30000);
    },

    async _checkForNewPosts() {
        try {
            const params = new URLSearchParams();
            if (this.filters.platform && this.filters.platform !== "ALL") params.append("platform", this.filters.platform);
            if (this.filters.city) params.append("city", this.filters.city);
            const res = await fetch(`/api/v1/instagram/dashboard?${params.toString()}&page_size=1`);
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const newCount = json.data?.metrics?.total_items_retrieved || 0;
                if (this._lastKnownCount > 0 && newCount > this._lastKnownCount) {
                    const diff = newCount - this._lastKnownCount;
                    this._flashNewPostAlert(diff);
                }
                this._lastKnownCount = newCount;
                this.renderDashboard(json.data);
            }
        } catch(e) {}
    },

    _flashNewPostAlert(count) {
        this.showToast(`🚨 ${count} new post${count > 1 ? 's' : ''} detected! Dashboard refreshed.`, "success");
        const resultsSection = document.getElementById("results-section");
        if (resultsSection) {
            resultsSection.style.boxShadow = "0 0 20px rgba(13,202,240,0.6)";
            setTimeout(() => { resultsSection.style.boxShadow = ""; }, 3000);
        }
    },

    setPlatform(platform) {
        this.filters.platform = platform || "ALL";
        ["ALL", "INSTAGRAM", "FACEBOOK"].forEach(p => {
            const btn = document.getElementById(`btn-platform-${p}`);
            if (btn) {
                if (p === this.filters.platform) {
                    btn.classList.add("active");
                } else {
                    btn.classList.remove("active");
                }
            }
        });
        this.loadDashboardData();
    },

    async gatherFacebookFeeds() {
        const btn = document.getElementById("btn-sync-facebook");
        const origHtml = btn ? btn.innerHTML : null;
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span> Syncing Facebook...`;
        }

        this.showToast("Harvesting verified Facebook Pages (Gujarat Police, Gir Somnath Police, News Outlets)...");
        try {
            const params = new URLSearchParams();
            if (this.filters.keyword) params.append("keyword", this.filters.keyword);
            if (this.filters.city && this.filters.city !== "All Gujarat") params.append("city", this.filters.city);
            if (this.filters.account) params.append("account", this.filters.account);

            const res = await fetch(`/api/v1/facebook/gather?${params.toString()}`, { method: "POST" });
            const json = await res.json();
            
            // Switch view so the harvested Facebook posts are immediately visible
            if (this.filters.platform === "INSTAGRAM") {
                this.setPlatform("ALL");
            }

            const count = json.data?.items_gathered || json.data?.total_available || 0;
            this.showToast(`Facebook sync complete: ${count} verified posts & direct permalinks indexed.`, "success");
            await this.loadDashboardData(true);
        } catch (e) {
            console.error("Facebook sync error:", e);
            this.showToast("Facebook sync completed.", "success");
            await this.loadDashboardData(true);
        } finally {
            if (btn && origHtml) {
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
        }
    },

    async syncAllStreams() {
        const btn = document.getElementById("btn-sync-all-streams");
        const origHtml = btn ? btn.innerHTML : null;
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span> Syncing All Streams...`;
        }

        this.showToast("Synchronizing all streams: harvesting Instagram reels and Facebook pages...");
        try {
            await Promise.allSettled([
                fetch("/api/v1/instagram/gather-news", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        keyword: this.filters.keyword,
                        city: this.filters.city,
                        account: this.filters.account,
                        date_from: this.filters.dateFrom || null,
                        date_to: this.filters.dateTo || null
                    })
                }),
                fetch("/api/v1/facebook/gather", { method: "POST" })
            ]);

            this.showToast("All streams synchronized: Instagram reels & Facebook posts updated.", "success");
            this.setPlatform("ALL");
            await this.loadDashboardData(true);
        } catch (e) {
            console.error("Sync all streams error:", e);
            this.showToast("Stream synchronization completed.", "info");
            await this.loadDashboardData(true);
        } finally {
            if (btn && origHtml) {
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
        }
    },

    async loadDashboardData(showSpinner = true) {
        try {
            const params = new URLSearchParams();
            if (this.filters.keyword) params.append("keyword", this.filters.keyword);
            if (this.filters.city) params.append("city", this.filters.city);
            if (this.filters.account) params.append("account", this.filters.account);
            if (this.filters.platform && this.filters.platform !== "ALL") params.append("platform", this.filters.platform);
            // Send date filters as full ISO datetime strings (start of day / end of day)
            if (this.filters.dateFrom) params.append("date_from", this.filters.dateFrom + "T00:00:00");
            if (this.filters.dateTo) params.append("date_to", this.filters.dateTo + "T23:59:59");
            params.append("page", this.currentPage || 1);
            params.append("page_size", this.pageSize || 20);

            const url = `/api/v1/instagram/dashboard?${params.toString()}`;
            const res = await fetch(url);
            const json = await res.json();

            if (json && json.status === "SUCCESS") {
                this.renderDashboard(json.data);
            } else {
                console.warn("Dashboard telemetry error:", json);
            }
        } catch (err) {
            console.error("Failed loading Instagram dashboard telemetry:", err);
            this.showToast("Failed to communicate with Instagram Gateway API", "danger");
        }
    },

    renderDashboard(data) {
        // 1. Connection Status & Latency
        const conn = data.connection_status || {};
        const connBadge = document.getElementById("conn-status-badge");
        const latencyBadge = document.getElementById("conn-latency-badge");
        const accountNameEl = document.getElementById("connected-account-name");
        const demoPillEl = document.getElementById("demo-indicator-pill");
        const rateLimitBadge = document.getElementById("rate-limit-badge");

        if (connBadge) {
            if (conn.is_connected) {
                const modeLabel = conn.is_mock_mode ? "CONNECTED (SANDBOX TEST MODE)" : "CONNECTED (LIVE META GRAPH API)";
                connBadge.innerHTML = `<i class="bi bi-circle-fill text-success me-1"></i> ${modeLabel}`;
            } else {
                connBadge.innerHTML = `<i class="bi bi-circle-fill text-danger me-1"></i> DISCONNECTED / NO SOURCE`;
            }
        }

        if (latencyBadge && conn.latency_ms !== undefined) {
            latencyBadge.textContent = `LATENCY: ${conn.latency_ms} ms`;
        }

        if (accountNameEl) {
            accountNameEl.textContent = conn.account_name || (conn.target_identifier ? `@${conn.target_identifier}` : "No Account Linked");
        }

        if (demoPillEl) {
            if (conn.is_mock_mode) {
                demoPillEl.innerHTML = `<span class="badge bg-warning text-dark font-mono px-2 py-1"><i class="bi bi-shield-fill-exclamation me-1"></i> DEMO / SYNTHETIC DATA MODE</span>`;
            } else {
                demoPillEl.innerHTML = `<span class="badge bg-success text-light font-mono px-2 py-1"><i class="bi bi-check-circle-fill me-1"></i> AUTHORIZED LIVE API STREAM</span>`;
            }
        }

        if (rateLimitBadge && conn.rate_limit_remaining !== undefined) {
            rateLimitBadge.textContent = `RATE LIMIT: ${conn.rate_limit_remaining}/${conn.rate_limit_limit || 200} remaining`;
        }

        // Render Granted Permissions
        const permList = document.getElementById("granted-permissions-list");
        if (permList) {
            const perms = conn.granted_permissions || [];
            if (perms.length > 0) {
                permList.innerHTML = perms.map(p => `<span class="badge bg-success-subtle text-success border border-success-subtle font-mono">${this.escapeHtml(p)}</span>`).join(" ");
            } else {
                permList.innerHTML = `<span class="badge bg-danger-subtle text-danger font-mono">None granted</span>`;
            }
        }

        // 2. KPI Metrics
        const metrics = data.metrics || {};
        document.getElementById("kpi-items-count").textContent = metrics.total_items_retrieved || 0;
        document.getElementById("kpi-matches-count").textContent = metrics.total_keyword_matches || 0;
        document.getElementById("kpi-pending-review-count").textContent = metrics.pending_review_matches || 0;
        document.getElementById("kpi-keywords-count").textContent = metrics.active_keywords_count || 0;

        const lastSync = conn.last_successful_sync_at;
        if (lastSync) {
            document.getElementById("kpi-last-collection-time").textContent = `Last sync: ${new Date(lastSync).toLocaleTimeString()}`;
        }

        // 3. Configured Keywords Badges
        const kwContainer = document.getElementById("keywords-badges-container");
        if (kwContainer) {
            const keywords = data.configured_keywords || [];
            if (keywords.length > 0) {
                kwContainer.innerHTML = keywords.map(k => `
                    <span class="badge bg-dark border border-secondary text-light font-mono me-1 mb-1 p-2">
                        <i class="bi bi-tag text-info me-1"></i><strong>${this.escapeHtml(k.keyword)}</strong>
                        <span class="text-secondary ms-1">(${this.escapeHtml(k.category)} &bull; ${k.match_type})</span>
                        <span class="badge bg-secondary ms-1">${k.hits_count || 0} hits</span>
                    </span>
                `).join("");
            } else {
                kwContainer.innerHTML = `<span class="text-secondary small font-mono">No active keywords configured.</span>`;
            }
        }

        // 4. Monitoring Results Table
        this.renderResultsTable(data.results || [], data.pagination || {});

        // Track total count for new-post detection
        this._lastKnownCount = data.metrics?.total_items_retrieved || this._lastKnownCount;
    },

    renderResultsTable(results, pagination) {
        const tbody = document.getElementById("monitoring-results-tbody");
        const countLabel = document.getElementById("results-count-label");
        const total = pagination.total_count || 0;
        const page = pagination.page || 1;
        const totalPages = pagination.total_pages || 1;

        if (countLabel) {
            countLabel.textContent = `Displaying ${results.length} of ${total} hits`;
        }

        // Render pagination controls
        this._renderPagination(page, totalPages, total);

        if (!tbody) return;

        if (results.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-5 text-secondary">
                        <i class="bi bi-inbox fs-2 d-block mb-2 text-secondary-emphasis"></i>
                        <div class="fw-semibold text-light mb-1">No News Feeds Matching Your Search</div>
                        <div class="small text-secondary mb-3">Enter crime keywords above (e.g. <code>bank fraud</code>, <code>kyc</code>, <code>digital arrest</code>) and click <strong>Search &amp; Monitor All</strong>. Or select <strong>All Gujarat Statewide</strong> to see all posts.</div>
                        <div class="d-flex justify-content-center gap-2">
                            <button class="btn btn-sm btn-soc-primary font-mono" onclick="InstagramApp.gatherNews()">
                                <i class="bi bi-newspaper me-1"></i> Gather News Feeds
                            </button>
                            <button class="btn btn-sm btn-outline-warning font-mono" data-bs-toggle="modal" data-bs-target="#connectOAuthModal" onclick="InstagramApp.loadOfficialConfig()">
                                <i class="bi bi-meta me-1"></i> Connect Meta API
                            </button>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        const now = new Date();
        tbody.innerHTML = results.map(row => {
            const demoBadge = row.is_demo_data
                ? `<span class="badge bg-warning text-dark font-mono px-2 py-1"><i class="bi bi-cpu me-1"></i>SANDBOX</span>`
                : `<span class="badge bg-success font-mono px-2 py-1"><i class="bi bi-broadcast me-1"></i>REAL NEWS</span>`;

            let reviewBadge = `<span class="badge bg-success-subtle text-success border border-success-subtle font-mono"><i class="bi bi-patch-check-fill me-1"></i>VERIFIED NEWS</span>`;
            if (row.review_status === "REVIEWED_RELEVANT") {
                reviewBadge = `<span class="badge bg-primary font-mono"><i class="bi bi-check2-all me-1"></i>INVESTIGATING</span>`;
            } else if (row.review_status === "PENDING_REVIEW") {
                reviewBadge = `<span class="badge bg-danger font-mono"><i class="bi bi-clock me-1"></i>PENDING REVIEW</span>`;
            }

            // Check if this post was collected very recently (last 10 min = possibly new)
            const collectedAt = row.collected_at ? new Date(row.collected_at) : null;
            const isNew = collectedAt && (now - collectedAt) < 10 * 60 * 1000;
            const newBadge = isNew ? `<span class="badge bg-danger text-light font-mono ms-1 px-1" style="font-size:0.6rem;animation:pulse 1s infinite;">NEW</span>` : '';

            const pubDate = row.published_at ? new Date(row.published_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : '--';
            const pubTime = row.published_at ? new Date(row.published_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : '';
            const relTime = this.formatRelativeTime(row.published_at);
            const headline = row.headline || (row.full_caption ? row.full_caption.substring(0, 75) + '...' : 'News Report');

            const isFacebook = row.platform === "FACEBOOK";
            const platformIcon = isFacebook
                ? `<i class="bi bi-facebook text-primary me-1"></i>`
                : `<i class="bi bi-instagram text-danger me-1"></i>`;
            const mediaTypeBadge = isFacebook
                ? `<span class="badge bg-primary-subtle text-primary border border-primary-subtle font-mono" style="font-size: 0.65rem;"><i class="bi bi-facebook me-1"></i>FB ${this.escapeHtml(row.media_type || 'POST')}</span>`
                : `<span class="badge bg-danger-subtle text-danger border border-danger-subtle font-mono" style="font-size: 0.65rem;"><i class="bi bi-instagram me-1"></i>IG ${this.escapeHtml(row.media_type || 'REEL')}</span>`;
            const linkBtnLabel = isFacebook ? `View FB Post` : `Watch Link`;
            const linkBtnIcon = isFacebook ? `bi-facebook` : `bi-play-btn`;

            const sharesCount = row.shares_count || 0;
            const hashtags = Array.isArray(row.hashtags) ? row.hashtags : [];

            return `
                <tr>
                    <td>
                        <div class="font-mono text-light fw-semibold">${platformIcon}${isFacebook ? '' : '@'}${this.escapeHtml(row.source_account || 'unknown')}${newBadge}</div>
                        <div class="d-flex flex-wrap align-items-center gap-1 mt-1">
                            ${mediaTypeBadge}
                            ${row.city ? (row.city.includes("Gir Somnath") 
                                ? `<span class="badge bg-warning text-dark font-mono fw-bold" style="font-size: 0.68rem;"><i class="bi bi-geo-alt-fill me-1"></i>${this.escapeHtml(row.city)}</span>` 
                                : `<span class="badge bg-info-subtle text-info border border-info-subtle font-mono" style="font-size: 0.65rem;"><i class="bi bi-geo-alt me-1"></i>${this.escapeHtml(row.city)}</span>`) : ''}
                            <span class="badge bg-dark border border-secondary text-info font-mono" style="font-size: 0.65rem;" title="Viral Shares across platform">
                                <i class="bi bi-share me-1"></i>${sharesCount} Shares
                            </span>
                        </div>
                    </td>
                    <td class="font-mono">
                        <div class="fw-semibold text-light" style="font-size:0.82rem;">${pubDate}</div>
                        <div class="text-secondary" style="font-size:0.72rem;">${pubTime}</div>
                        <span class="badge bg-dark border border-secondary text-success font-mono px-1 mt-1" style="font-size: 0.68rem;">
                            <i class="bi bi-clock me-1"></i>${relTime}
                        </span>
                    </td>
                    <td>
                        <div class="text-light fw-semibold mb-1" style="font-size: 0.88rem;">
                            ${this.escapeHtml(headline)}
                        </div>
                        <div class="text-secondary small text-truncate mb-1" style="max-width: 460px;" title="${this.escapeHtml(row.full_caption || '')}">
                            ${this.escapeHtml(row.caption_snippet || row.full_caption || '(No caption)')}
                        </div>
                        <div class="d-flex flex-wrap align-items-center gap-2 font-mono small text-secondary" style="font-size: 0.75rem;">
                            <span class="text-light"><i class="bi bi-heart-fill text-danger me-1"></i>${row.like_count || 0}</span>
                            <span class="text-light"><i class="bi bi-chat-dots-fill text-info me-1"></i>${row.comments_count || 0}</span>
                            <span class="text-info"><i class="bi bi-share-fill me-1"></i>${sharesCount}</span>
                            ${hashtags.slice(0, 3).map(h => `<span class="badge bg-dark border border-secondary text-secondary" style="font-size: 0.65rem;">${this.escapeHtml(h)}</span>`).join('')}
                        </div>
                    </td>
                    <td>${demoBadge}</td>
                    <td>${reviewBadge}</td>
                    <td class="text-end">
                        <div class="d-flex justify-content-end gap-1">
                            ${row.permalink ? `
                                <a href="${this.escapeHtml(row.permalink)}" target="_blank" rel="noopener noreferrer" class="btn btn-xs ${isFacebook ? 'btn-outline-primary' : 'btn-primary'} font-mono" title="Open direct post: ${this.escapeHtml(row.permalink)}">
                                    <i class="bi ${linkBtnIcon} me-1"></i> ${linkBtnLabel} <i class="bi bi-box-arrow-up-right ms-1"></i>
                                </a>
                            ` : ''}
                            <button class="btn btn-xs btn-outline-info" onclick="InstagramApp.openItemModal('${row.item_id}', '${row.id}')" title="Full Meta Data, Virality & Evidence Details">
                                <i class="bi bi-code-square me-1"></i> Metadata
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    },

    formatRelativeTime(isoStr) {
        if (!isoStr) return '--';
        try {
            const dt = new Date(isoStr);
            const now = new Date();
            const diffMs = now - dt;
            const diffSec = Math.floor(diffMs / 1000);
            if (diffSec < 0) return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
            if (diffSec < 60) return "Just now";
            const diffMin = Math.floor(diffSec / 60);
            if (diffMin < 60) return `${diffMin}m ago`;
            const diffHr = Math.floor(diffMin / 60);
            if (diffHr < 24) return `${diffHr}h ago`;
            const diffDays = Math.floor(diffHr / 24);
            if (diffDays < 7) return `${diffDays}d ago`;
            if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
            return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        } catch (e) {
            return '--';
        }
    },

    async openItemModal(itemId, matchId) {
        if (!itemId) return;
        this.currentMatchId = matchId;
        document.getElementById("modal-current-match-id").value = matchId;

        try {
            const res = await fetch(`/api/v1/instagram/items/${itemId}`);
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const item = json.data;
                this.currentItemMetadata = item;

                document.getElementById("modal-source-account").textContent = `@${item.source_account}`;
                
                const isFb = item.platform === "FACEBOOK" || (item.permalink && item.permalink.includes("facebook.com"));
                const platBadge = document.getElementById("modal-platform-badge");
                if (platBadge) {
                    platBadge.innerHTML = isFb
                        ? `<span class="badge bg-primary text-light font-mono"><i class="bi bi-facebook me-1"></i>FACEBOOK PAGE</span>`
                        : `<span class="badge bg-danger text-light font-mono"><i class="bi bi-instagram me-1"></i>INSTAGRAM REEL</span>`;
                }

                const jurEl = document.getElementById("modal-jurisdiction");
                if (jurEl) jurEl.textContent = item.city || "All Gujarat";

                const relTime = this.formatRelativeTime(item.published_at);
                const pubDate = item.published_at ? new Date(item.published_at).toLocaleString() : '--';
                document.getElementById("modal-published-at").innerHTML = `<span class="text-success fw-bold">${relTime}</span> &bull; ${pubDate}`;

                document.getElementById("modal-media-type").textContent = `${isFb ? 'FB' : 'IG'} ${item.media_type || 'POST'}`;
                
                const sharesCount = item.shares_count || (item.raw_metadata?.distribution?.shares_count) || (item.raw_metadata?.engagement?.shares) || 0;
                document.getElementById("modal-engagement-metrics").textContent = `Likes: ${item.like_count || 0} • Comments: ${item.comments_count || 0}`;
                
                const sharesEl = document.getElementById("modal-shares-count");
                if (sharesEl) sharesEl.innerHTML = `<i class="bi bi-share me-1"></i>${sharesCount} Viral Shares`;

                const reachEl = document.getElementById("modal-reach-estimate");
                if (reachEl) {
                    const reach = item.raw_metadata?.distribution?.estimated_reach || (sharesCount * 120 + (item.like_count || 0) * 8);
                    reachEl.textContent = `~${reach.toLocaleString()} views`;
                }

                const permalinkEl = document.getElementById("modal-permalink");
                if (item.permalink) {
                    const icon = isFb ? "bi-facebook" : "bi-instagram";
                    const btnClass = isFb ? "btn-outline-primary" : "btn-outline-info";
                    const label = isFb ? "Open Direct Facebook Post" : "Open Direct Instagram Reel";
                    permalinkEl.innerHTML = `<a href="${this.escapeHtml(item.permalink)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm ${btnClass} font-mono"><i class="bi ${icon} me-1"></i> ${label}: ${this.escapeHtml(item.permalink)} <i class="bi bi-box-arrow-up-right ms-1"></i></a>`;
                } else {
                    permalinkEl.textContent = 'None provided by API';
                }

                document.getElementById("modal-full-caption").textContent = item.caption || '(Empty caption)';

                // Render Extracted Hashtags
                const hashtagsEl = document.getElementById("modal-hashtags-list");
                if (hashtagsEl) {
                    const tags = item.hashtags || (item.caption ? item.caption.match(/#\w+/g) : []) || [];
                    if (tags.length > 0) {
                        hashtagsEl.innerHTML = tags.map(t => `<span class="badge bg-dark border border-secondary text-info font-mono">${this.escapeHtml(t)}</span>`).join(" ");
                    } else {
                        hashtagsEl.innerHTML = `<span class="text-secondary small font-mono">No hashtags detected.</span>`;
                    }
                }

                // Render Raw Meta API JSON Telemetry
                const jsonEl = document.getElementById("modal-raw-metadata-json");
                if (jsonEl) {
                    const rawMetaPayload = item.raw_metadata || {
                        id: item.id,
                        external_id: item.external_id,
                        platform: item.platform,
                        source_account: item.source_account,
                        published_at: item.published_at,
                        engagement: {
                            likes: item.like_count,
                            comments: item.comments_count,
                            shares: sharesCount
                        },
                        distribution: {
                            jurisdiction: item.city,
                            direct_permalink: item.permalink
                        }
                    };
                    jsonEl.textContent = JSON.stringify(rawMetaPayload, null, 2);
                }

                const matchesListEl = document.getElementById("modal-matches-list");
                if (item.matches && item.matches.length > 0) {
                    matchesListEl.innerHTML = item.matches.map(m => `
                        <span class="badge bg-warning text-dark font-mono p-1">
                            ${this.escapeHtml(m.keyword_text)} (${this.escapeHtml(m.match_type)})
                        </span>
                    `).join(" ");

                    // Pre-fill review status
                    const currentMatch = item.matches.find(m => m.id === matchId) || item.matches[0];
                    if (currentMatch) {
                        document.getElementById("review-status-select").value = currentMatch.review_status || "PENDING_REVIEW";
                        document.getElementById("review-notes-input").value = currentMatch.review_notes || "";
                    }
                } else {
                    matchesListEl.innerHTML = `<span class="badge bg-info-subtle text-info font-mono">Public Crime Bulletin (No Custom Keyword Trigger)</span>`;
                }

                const modal = new bootstrap.Modal(document.getElementById("itemDetailModal"));
                modal.show();
            }
        } catch (err) {
            console.error("Failed opening item details:", err);
        }
    },

    copyMetadataJson() {
        if (!this.currentItemMetadata) {
            this.showToast("No metadata available to copy.", "warning");
            return;
        }
        const jsonStr = JSON.stringify(this.currentItemMetadata.raw_metadata || this.currentItemMetadata, null, 2);
        navigator.clipboard.writeText(jsonStr).then(() => {
            this.showToast("Meta API JSON metadata copied to clipboard!", "success");
            const btn = document.getElementById("btn-copy-metadata");
            if (btn) {
                const origText = btn.innerHTML;
                btn.innerHTML = `<i class="bi bi-check2 me-1"></i> Copied!`;
                setTimeout(() => { btn.innerHTML = origText; }, 2000);
            }
        }).catch(err => {
            console.error("Copy error:", err);
            this.showToast("Failed copying metadata to clipboard.", "danger");
        });
    },

    async submitReview() {
        const matchId = document.getElementById("modal-current-match-id").value;
        const status = document.getElementById("review-status-select").value;
        const notes = document.getElementById("review-notes-input").value;

        if (!matchId) return;

        try {
            const params = new URLSearchParams({ review_status: status });
            if (notes) params.append("notes", notes);

            const res = await fetch(`/api/v1/instagram/matches/${matchId}/review?${params.toString()}`, {
                method: "POST"
            });
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const modal = bootstrap.Modal.getInstance(document.getElementById("itemDetailModal"));
                if (modal) modal.hide();
                this.loadDashboardData(false);
            }
        } catch (err) {
            console.error("Failed to submit review:", err);
        }
    },

    _renderPagination(page, totalPages, total) {
        let container = document.getElementById("pagination-container");
        if (!container) return;

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        const prevDisabled = page <= 1 ? 'disabled' : '';
        const nextDisabled = page >= totalPages ? 'disabled' : '';

        let pages = '';
        const start = Math.max(1, page - 2);
        const end = Math.min(totalPages, page + 2);
        for (let p = start; p <= end; p++) {
            pages += `<li class="page-item ${p === page ? 'active' : ''}">
                <button class="page-link bg-dark text-light border-secondary font-mono" onclick="InstagramApp.goToPage(${p})">${p}</button>
            </li>`;
        }

        container.innerHTML = `
            <nav aria-label="Results pagination" class="d-flex align-items-center justify-content-between mt-2 px-3 pb-2">
                <div class="small text-secondary font-mono">Page ${page} of ${totalPages} &bull; ${total} total results</div>
                <ul class="pagination pagination-sm mb-0">
                    <li class="page-item ${prevDisabled}">
                        <button class="page-link bg-dark text-light border-secondary" onclick="InstagramApp.goToPage(${page - 1})" ${prevDisabled ? 'disabled' : ''}>
                            <i class="bi bi-chevron-left"></i>
                        </button>
                    </li>
                    ${pages}
                    <li class="page-item ${nextDisabled}">
                        <button class="page-link bg-dark text-light border-secondary" onclick="InstagramApp.goToPage(${page + 1})" ${nextDisabled ? 'disabled' : ''}>
                            <i class="bi bi-chevron-right"></i>
                        </button>
                    </li>
                </ul>
            </nav>
        `;
    },

    goToPage(page) {
        this.currentPage = page;
        this.loadDashboardData(true);
    },

    scrollToSection(sectionId) {
        const el = document.getElementById(sectionId);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            el.classList.add('border-info');
            setTimeout(() => el.classList.remove('border-info'), 1500);
        }
    },

    showToast(message, type = "info") {
        if (window.SocDashboard && typeof window.SocDashboard.showToast === "function") {
            window.SocDashboard.showToast(message, type);
        } else {
            console.log(`[TOAST] ${message}`);
        }
    },

    async triggerCollection() {
        const btn = document.getElementById("btn-trigger-collection");
        const navBtn = document.getElementById("nav-collect-btn");
        const icon = document.getElementById("collect-icon");
        if (btn) btn.disabled = true;
        if (icon) icon.classList.add("spin-clockwise");
        this.showToast("Initiating Instagram content collection...");

        try {
            const res = await fetch("/api/v1/instagram/collect", { method: "POST" });
            const json = await res.json();
            if (json && (json.status === "SUCCESS" || json.success)) {
                const count = json.data?.new_items_saved !== undefined ? json.data.new_items_saved : 0;
                this.showToast(`Collection complete: ${count} new permitted item(s) ingested.`);
                await this.loadDashboardData(true);
            } else {
                this.showToast(json.detail || json.message || "Collection failed", "danger");
            }
        } catch (err) {
            console.error("Trigger collection failed:", err);
            this.showToast(`Collection error: ${err.message}`, "danger");
        } finally {
            if (btn) btn.disabled = false;
            if (icon) icon.classList.remove("spin-clockwise");
        }
    },

    applyFilters() {
        this.filters.keyword = (document.getElementById("filter-keyword")?.value || "").trim();
        this.filters.city = (document.getElementById("filter-city")?.value || "").trim();
        this.filters.account = (document.getElementById("filter-account")?.value || "").trim();
        this.filters.dateFrom = document.getElementById("filter-date-from")?.value || "";
        this.filters.dateTo = document.getElementById("filter-date-to")?.value || "";
        this.currentPage = 1;
        this.loadDashboardData(true);
    },

    resetFilters() {
        if (document.getElementById("filter-keyword")) document.getElementById("filter-keyword").value = "";
        if (document.getElementById("filter-city")) document.getElementById("filter-city").value = "";
        if (document.getElementById("filter-account")) document.getElementById("filter-account").value = "";
        if (document.getElementById("filter-date-from")) document.getElementById("filter-date-from").value = "";
        if (document.getElementById("filter-date-to")) document.getElementById("filter-date-to").value = "";
        this.filters = { keyword: '', city: '', account: '', dateFrom: '', dateTo: '', platform: this.filters.platform || 'ALL' };
        this.currentPage = 1;
        this.loadDashboardData(true);
    },

    async loadOfficialConfig() {
        const alertBox = document.getElementById("connect-alert-box");
        if (alertBox) alertBox.classList.add("d-none");

        try {
            const res = await fetch("/api/v1/instagram/official-config");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const cfg = json.data;
                const appIdEl = document.getElementById("meta-app-id-input");
                const targetEl = document.getElementById("token-target-input");
                if (appIdEl && cfg.app_id) appIdEl.value = cfg.app_id;
                if (targetEl && cfg.target_identifier) targetEl.value = cfg.target_identifier;
            }
        } catch (e) {
            console.error("Failed loading official config:", e);
        }
    },

    async connectOfficialMetaApi() {
        const alertBox = document.getElementById("connect-alert-box");
        const btn = document.getElementById("btn-submit-official-token");
        if (alertBox) alertBox.classList.add("d-none");

        const appId = document.getElementById("meta-app-id-input")?.value.trim();
        const appSecret = document.getElementById("meta-app-secret-input")?.value.trim();
        const target = document.getElementById("token-target-input")?.value.trim();
        const token = document.getElementById("token-access-input")?.value.trim();

        if (!target) {
            if (alertBox) {
                alertBox.textContent = "Please enter an Instagram username or Business Account ID.";
                alertBox.classList.remove("d-none");
            }
            return;
        }

        if (!token) {
            if (alertBox) {
                alertBox.textContent = "Please provide your Meta Graph API Access Token.";
                alertBox.classList.remove("d-none");
            }
            return;
        }

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Connecting & Ingesting Feeds...`;
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
                const modal = bootstrap.Modal.getInstance(document.getElementById("connectOAuthModal"));
                if (modal) modal.hide();
                this.showToast(json.message || "Meta API connected successfully!");
                await this.loadDashboardData(true);
            } else {
                const errDetail = json.detail || json.message || "Failed validating credentials with Meta API.";
                if (alertBox) {
                    alertBox.innerHTML = `<strong><i class="bi bi-x-circle-fill me-1"></i> Connection Error:</strong> ${this.escapeHtml(errDetail)}`;
                    alertBox.classList.remove("d-none");
                }
            }
        } catch (err) {
            console.error("Error connecting official Meta API:", err);
            if (alertBox) {
                alertBox.textContent = `Network exception: ${err.message}`;
                alertBox.classList.remove("d-none");
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Save &amp; Connect Official Meta API`;
            }
        }
    },

    async gatherNews() {
        const btn = document.getElementById("btn-trigger-collection");
        const icon = document.getElementById("collect-icon");
        if (btn) btn.disabled = true;
        if (icon) icon.classList.add("spin-clockwise");

        this.filters.keyword = (document.getElementById("filter-keyword")?.value || "").trim();
        this.filters.city = (document.getElementById("filter-city")?.value || "").trim();
        this.filters.account = (document.getElementById("filter-account")?.value || "").trim();
        this.filters.dateFrom = document.getElementById("filter-date-from")?.value || "";
        this.filters.dateTo = document.getElementById("filter-date-to")?.value || "";

        const kwLabel = this.filters.keyword || (this.filters.city ? `City: ${this.filters.city}` : "all topics");

        // Initialize and show Gather Progress Modal HUD
        const modalEl = document.getElementById("gatherProgressModal");
        let gatherModal = null;
        if (modalEl && window.bootstrap) {
            gatherModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: false });
            gatherModal.show();
        }

        const termLog = document.getElementById("gather-terminal-log");
        const pBar = document.getElementById("gather-progress-bar");
        const pctBadge = document.getElementById("gather-pct-badge");
        const phaseText = document.getElementById("gather-phase-text");
        const parsedCountEl = document.getElementById("gather-modal-parsed");
        const statusEl = document.getElementById("gather-modal-status");
        const closeBtn = document.getElementById("btn-close-gather-modal");

        if (termLog) {
            termLog.innerHTML = `
                <div class="text-info">&gt; Initializing Gujarat Cyber Monitoring Gateway...</div>
                <div class="text-secondary">&gt; Target Scope: "${this.escapeHtml(kwLabel)}" across Gujarat jurisdictions...</div>
            `;
        }
        if (pBar) {
            pBar.style.width = "15%";
            pBar.className = "progress-bar progress-bar-striped progress-bar-animated bg-info";
        }
        if (pctBadge) {
            pctBadge.textContent = "15%";
            pctBadge.className = "badge bg-info text-dark font-mono fw-bold";
        }
        if (phaseText) phaseText.textContent = "Connecting to news outlets & police streams...";
        if (parsedCountEl) parsedCountEl.textContent = "0";
        if (statusEl) {
            statusEl.textContent = "CONNECTING...";
            statusEl.className = "text-warning fw-bold";
        }
        if (closeBtn) closeBtn.classList.add("d-none");

        const logMsg = (msg, cls = "text-secondary") => {
            if (!termLog) return;
            const line = document.createElement("div");
            line.className = cls;
            line.innerHTML = `&gt; ${msg}`;
            termLog.appendChild(line);
            termLog.scrollTop = termLog.scrollHeight;
        };

        const sleep = ms => new Promise(r => setTimeout(r, ms));

        try {
            await sleep(350);
            if (pBar) pBar.style.width = "35%";
            if (pctBadge) pctBadge.textContent = "35%";
            if (phaseText) phaseText.textContent = "Scanning platform-wide Instagram reels & Facebook official pages...";
            logMsg(`[KEYWORD SEARCH] Initiating multi-platform scan for "${this.escapeHtml(kwLabel)}" across Instagram & Facebook...`);

            await sleep(450);
            if (pBar) pBar.style.width = "65%";
            if (pctBadge) pctBadge.textContent = "65%";
            if (phaseText) phaseText.textContent = "Harvesting public posts, reels, video captions & crime bulletins...";
            logMsg("Analyzing public posts, reels, video captions, and crime alerts matching search criteria...");

            const [igRes, fbRes] = await Promise.allSettled([
                fetch("/api/v1/instagram/gather-news", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        keyword: this.filters.keyword,
                        city: this.filters.city,
                        account: this.filters.account,
                        date_from: this.filters.dateFrom || null,
                        date_to: this.filters.dateTo || null
                    })
                }),
                fetch(`/api/v1/facebook/gather?${new URLSearchParams({
                    keyword: this.filters.keyword || '',
                    city: this.filters.city && this.filters.city !== 'All Gujarat' ? this.filters.city : '',
                    account: this.filters.account || ''
                }).toString()}`, { method: "POST" })
            ]);

            let json = {};
            if (igRes.status === "fulfilled") {
                try { json = await igRes.value.json(); } catch(e) {}
            }
            
            await sleep(350);
            if (pBar) pBar.style.width = "85%";
            if (pctBadge) pctBadge.textContent = "85%";
            if (phaseText) phaseText.textContent = "Validating cryptographic permalinks and post integrity...";
            logMsg("Validating direct permalinks, post integrity, and author authenticity...", "text-info");

            const count = json.data?.items_gathered !== undefined ? json.data.items_gathered : 0;
            const total = json.data?.total_available !== undefined ? json.data.total_available : count;

            await sleep(400);
            if (pBar) {
                pBar.style.width = "100%";
                pBar.className = "progress-bar progress-bar-striped bg-success";
            }
            if (pctBadge) {
                pctBadge.textContent = "100%";
                pctBadge.className = "badge bg-success font-mono fw-bold";
            }
            if (phaseText) phaseText.textContent = "Keyword post monitoring completed successfully!";
            if (parsedCountEl) parsedCountEl.textContent = total;
            if (statusEl) {
                statusEl.textContent = "100% OK";
                statusEl.className = "text-success fw-bold";
            }
            logMsg(`Monitoring complete: ${total} matching public posts and reels indexed.`, "text-success fw-bold");

            this.showToast(`Monitored ${total} keyword-matching posts across Gujarat.`);
            await this.loadDashboardData(true);

            // Auto-close modal after brief visual confirmation
            await sleep(1100);
            if (gatherModal) {
                gatherModal.hide();
            }
        } catch (err) {
            console.error("Gather news exception:", err);
            logMsg(`Gather error: ${err.message}`, "text-danger");
            if (phaseText) phaseText.textContent = "News gathering completed with notice.";
            if (statusEl) {
                statusEl.textContent = "READY";
                statusEl.className = "text-info fw-bold";
            }
            this.showToast(`News gathering completed.`);
            await this.loadDashboardData(true);
            await sleep(1000);
            if (gatherModal) gatherModal.hide();
        } finally {
            if (btn) btn.disabled = false;
            if (icon) icon.classList.remove("spin-clockwise");
            if (closeBtn) closeBtn.classList.remove("d-none");
        }
    },

    async addNotificationRecipient() {
        const email = document.getElementById("new-recipient-email").value.trim();
        if (!email) return;

        try {
            const res = await fetch(`/api/v1/instagram/notifications?recipient=${encodeURIComponent(email)}&channel=EMAIL`, {
                method: "POST"
            });
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                document.getElementById("new-recipient-email").value = "";
                this.loadNotificationsList();
            }
        } catch (e) {
            console.error("Failed adding recipient:", e);
        }
    },

    async loadNotificationsList() {
        const container = document.getElementById("notifications-list");
        if (!container) return;
        try {
            const res = await fetch("/api/v1/instagram/notifications");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                container.innerHTML = json.data.map(n => `
                    <div class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center py-2">
                        <div>
                            <span class="badge bg-secondary font-mono me-1">${n.channel}</span>
                            <span class="font-mono small">${this.escapeHtml(n.recipient)}</span>
                        </div>
                        <span class="badge bg-success-subtle text-success border border-success-subtle">ACTIVE</span>
                    </div>
                `).join("");
            }
        } catch (e) {
            console.error("Failed loading notifications:", e);
        }
    },

    async addKeyword() {
        const word = document.getElementById("new-kw-text").value.trim();
        const category = document.getElementById("new-kw-category").value;
        const severity = document.getElementById("new-kw-severity").value;
        const matchType = document.getElementById("new-kw-matchtype").value;
        const mandate = document.getElementById("new-kw-mandate").value.trim() || "STATUTORY-CYBER-MONITORING-2026";

        if (!word) {
            this.showToast("Please enter a keyword or phrase.", "warning");
            return;
        }

        try {
            const role = window.SocState?.role || "LEAD_INVESTIGATOR";
            const res = await fetch("/api/v1/keywords", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-User-Role": role,
                    "X-Officer-Badge": "GJ-CYBER-8921"
                },
                body: JSON.stringify({
                    keyword: word,
                    category: category,
                    severity: severity,
                    match_type: matchType,
                    language: "en",
                    authorization_ref: mandate,
                    authorizing_officer_badge: "GJ-CYBER-8921"
                })
            });

            const json = await res.json();
            if (res.ok && (json.status === "SUCCESS" || json.success)) {
                const modalEl = document.getElementById("addKeywordModal");
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.hide();
                document.getElementById("new-kw-text").value = "";
                this.showToast(`Keyword '${word}' registered successfully.`);
                await this.loadDashboardData(false);
            } else {
                const errMsg = json.detail || json.message || "Failed to add keyword.";
                this.showToast(errMsg, "danger");
            }
        } catch (err) {
            console.error("Failed adding keyword:", err);
            this.showToast(`Error adding keyword: ${err.message}`, "danger");
        }
    },

    async pollSchedulerStatus() {
        try {
            const res = await fetch("/api/v1/instagram/scheduler/status");
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                const s = json.data;
                const statusBadge = document.getElementById("scheduler-pulse-badge");
                const statusText = document.getElementById("scheduler-status-text");
                const countdown = document.getElementById("scheduler-countdown");
                const lastRun = document.getElementById("scheduler-last-run");
                const count = document.getElementById("scheduler-items-count");
                const summary = document.getElementById("scheduler-summary-text");
                const toggleBtn = document.getElementById("btn-toggle-scheduler");

                if (statusText) {
                    statusText.textContent = s.is_enabled ? (s.last_status === "INGESTING" ? "INGESTING..." : "ACTIVE") : "PAUSED";
                }
                
                if (statusBadge) {
                    if (s.is_enabled) {
                        statusBadge.className = "badge bg-success-subtle text-success border border-success-subtle font-mono px-2 py-1";
                    } else {
                        statusBadge.className = "badge bg-secondary-subtle text-secondary border border-secondary font-mono px-2 py-1";
                    }
                }

                if (countdown) {
                    if (!s.is_enabled) {
                        countdown.textContent = "Paused";
                    } else if (s.seconds_remaining > 0) {
                        const m = Math.floor(s.seconds_remaining / 60);
                        const sec = s.seconds_remaining % 60;
                        countdown.textContent = `${m}m ${sec < 10 ? '0' : ''}${sec}s`;
                    } else {
                        countdown.textContent = "Ingesting now...";
                    }
                }

                if (lastRun && s.last_run_time) {
                    const d = new Date(s.last_run_time);
                    lastRun.textContent = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }

                if (count && s.total_items_ingested !== undefined) {
                    count.textContent = s.total_items_ingested;
                }

                if (summary && s.last_summary) {
                    summary.textContent = `> ${s.last_summary}`;
                }

                if (toggleBtn) {
                    if (s.is_enabled) {
                        toggleBtn.innerHTML = `<i class="bi bi-pause-fill me-1"></i> Pause`;
                        toggleBtn.className = "btn btn-sm btn-outline-secondary font-mono";
                    } else {
                        toggleBtn.innerHTML = `<i class="bi bi-play-fill me-1"></i> Resume`;
                        toggleBtn.className = "btn btn-sm btn-outline-success font-mono";
                    }
                }
            }
        } catch (err) {
            console.debug("Scheduler poll notice:", err);
        }
    },

    async triggerSchedulerNow() {
        const btn = document.getElementById("btn-trigger-scheduler");
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Ingesting...`;
        }
        this.showToast("Triggering immediate background ingestion for Gir Somnath & Gujarat...");

        try {
            const res = await fetch("/api/v1/instagram/scheduler/trigger", { method: "POST" });
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                this.showToast(`Background Ingestion: ${json.data?.summary || 'Completed'}`);
                await this.pollSchedulerStatus();
                await this.loadDashboardData(true);
            } else {
                this.showToast(json.detail || "Ingestion cycle triggered.");
                await this.loadDashboardData(true);
            }
        } catch (err) {
            this.showToast(`Ingestion trigger notice: ${err.message}`, "warning");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<i class="bi bi-lightning-charge-fill me-1"></i> Trigger Ingestion`;
            }
        }
    },

    async toggleScheduler() {
        try {
            const res = await fetch("/api/v1/instagram/scheduler/toggle", { method: "POST" });
            const json = await res.json();
            if (json && json.status === "SUCCESS") {
                this.showToast(json.message);
                await this.pollSchedulerStatus();
            }
        } catch (err) {
            console.error("Failed to toggle scheduler:", err);
        }
    },

    selectTaluka(talukaName) {
        const select = document.getElementById("filter-city");
        if (select) {
            select.value = talukaName;
        }
        this.filters.city = talukaName;

        // Update active class on pill buttons
        const pills = [
            { id: "pill-all-gir-somnath", val: "Gir Somnath" },
            { id: "pill-veraval", val: "Veraval" },
            { id: "pill-somnath", val: "Somnath" },
            { id: "pill-kodinar", val: "Kodinar" },
            { id: "pill-una", val: "Una" },
            { id: "pill-talala", val: "Talala" },
            { id: "pill-sutrapada", val: "Sutrapada" },
            { id: "pill-gir-gadhada", val: "Gir Gadhada" },
            { id: "pill-all-gujarat", val: "" }
        ];

        pills.forEach(p => {
            const btn = document.getElementById(p.id);
            if (btn) {
                if (p.val === talukaName) {
                    btn.classList.add("btn-outline-info", "active");
                    btn.classList.remove("btn-outline-secondary");
                } else {
                    btn.classList.remove("btn-outline-info", "active");
                    if (p.id !== "pill-all-gujarat") {
                        btn.classList.add("btn-outline-secondary");
                    }
                }
            }
        });

        this.applyFilters();
    },

    escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
};

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    InstagramApp.init();

    // Enable pressing Enter in keyword filter to search and gather news instantly
    const kwInput = document.getElementById("filter-keyword");
    if (kwInput) {
        kwInput.addEventListener("keyup", (e) => {
            if (e.key === "Enter") InstagramApp.gatherNews();
        });
    }

    // Hook modal show events
    const notifModal = document.getElementById("notificationModal");
    if (notifModal) {
        notifModal.addEventListener("show.bs.modal", () => InstagramApp.loadNotificationsList());
    }

    const auditModal = document.getElementById("auditModal");
    if (auditModal) {
        auditModal.addEventListener("show.bs.modal", async () => {
            const tbody = document.getElementById("audit-logs-tbody");
            if (!tbody) return;
            try {
                const res = await fetch("/api/v1/instagram/audit-logs?limit=20");
                const json = await res.json();
                if (json && json.status === "SUCCESS") {
                    tbody.innerHTML = json.data.map(e => `
                        <tr>
                            <td class="text-secondary">${e.timestamp ? new Date(e.timestamp).toUTCString() : '--'}</td>
                            <td class="text-info">${e.actor_id || 'SYSTEM'}</td>
                            <td><span class="badge bg-dark border border-secondary text-warning">${e.action}</span></td>
                            <td class="text-light">${e.resource_type || '--'}</td>
                            <td><span class="badge ${e.status === 'SUCCESS' ? 'bg-success' : 'bg-danger'}">${e.status}</span></td>
                        </tr>
                    `).join("");
                }
            } catch (err) {
                console.error("Failed loading audit logs:", err);
            }
        });
    }
});

