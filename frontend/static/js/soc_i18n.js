/**
 * Gujarat Cyber Police Social Media Intelligence Platform
 * Bilingual Engine (English ⟷ ગુજરાતી), Dual Role Manager (Admin vs Officer),
 * In-Input Gujarati Phonetic Transliteration Engine, and Officer Accounts Management.
 */

(function (window) {
    'use strict';

    // =========================================================================
    // 1. GUJARATI PHONETIC TRANSLITERATION ENGINE
    // =========================================================================
    const GUJARATI_WORD_MAP = {
        // Districts & Cities
        "surat": "સુરત",
        "somnath": "સોમનાથ",
        "veraval": "વેરાવળ",
        "rajkot": "રાજકોટ",
        "ahmedabad": "અમદાવાદ",
        "vadodara": "વડોદરા",
        "baroda": "વડોદરા",
        "bhavnagar": "ભાવનગર",
        "jamnagar": "જામનગર",
        "junagadh": "જૂનાગઢ",
        "amreli": "અમરેલી",
        "porbandar": "પોરબંદર",
        "morbi": "મોરબી",
        "surendranagar": "સુરેન્દ્રનગર",
        "gandhinagar": "ગાંધીનગર",
        "valsad": "વલસાડ",
        "vapi": "વાપી",
        "kutch": "કચ્છ",
        "bhuj": "ભુજ",
        "una": "ઉના",
        "kodinar": "કોડીનાર",
        "talala": "તાલાલા",
        "sutrapada": "સુત્રાપાડા",
        "gir gadhada": "ગીર ગઢડા",
        "gadhada": "ગઢડા",
        "gir somnath": "ગીર સોમનાથ",
        "girsomnath": "ગીર સોમનાથ",
        "patan": "પાટણ",
        "mehsana": "મહેસાણા",
        "banaskantha": "બનાસકાંઠા",
        "palanpur": "પાલનપુર",
        "deesa": "ડીસા",
        "sabarkantha": "સાબરકાંઠા",
        "himatnagar": "હિંમતનગર",
        "bharuch": "ભરૂચ",
        "ankleshwar": "અંકલેશ્વર",
        "anand": "આણંદ",
        "kheda": "ખેડા",
        "nadiad": "નડિયાદ",
        "dahod": "દાહોદ",
        "panchmahal": "પંચમહાલ",
        "godhra": "ગોધરા",
        "botad": "બોટાદ",
        "aravalli": "અરવલ્લી",
        "modasa": "મોડાસા",
        "mahisagar": "મહીસાગર",
        "lunawada": "લુણાવાડા",
        "chhota udepur": "છોટાઉદેપુર",
        "narmada": "નર્મદા",
        "rajpipla": "રાજપીપળા",
        "navsari": "નવસારી",
        "tapi": "તાપી",
        "vyara": "વ્યારા",
        "dang": "ડાંગ",
        "ahwa": "આહવા",
        "dwarka": "દ્વારકા",

        // Crime & Police Terms
        "cyber": "સાયબર",
        "crime": "ક્રાઇમ",
        "police": "પોલીસ",
        "fraud": "ફ્રોડ",
        "scam": "કૌભાંડ",
        "chori": "ચોરી",
        "loot": "લૂંટ",
        "daru": "દારૂ",
        "drugs": "ડ્રગ્સ",
        "narcotics": "નાર્કોટિક્સ",
        "liquor": "દારૂ",
        "arrest": "ધરપકડ",
        "digital arrest": "ડિજિટલ અરેસ્ટ",
        "apk": "એપીકે",
        "otp": "ઓટીપી",
        "trading": "ટ્રેડિંગ",
        "share": "શેરબજાર",
        "bazaar": "બજાર",
        "murder": "હત્યા",
        "accident": "અકસ્માત",
        "fir": "એફઆઈઆર",
        "extortion": "ખંડણી",
        "blackmail": "બ્લેકમેઇલ",
        "honeytrap": "હનીટ્રેપ",
        "call center": "કોલ સેન્ટર",
        "mobile": "મોબાઇલ",
        "bank": "બેંક",
        "account": "ખાતું",
        "loan": "લોન",
        "fake": "ફેક",
        "raid": "દરોડા",
        "seizure": "જપ્તી",
        "cid": "સીઆઈડી",
        "sp": "એસપી",
        "pi": "પીઆઈ",
        "psi": "પીએસઆઈ",
        "advisory": "એડવાઇઝરી",
        "alert": "એલર્ટ",
        "veraval port": "વેરાવળ પોર્ટ",
        "somnath mandir": "સોમનાથ મંદિર"
    };

    const CONSONANTS = {
        "k": "ક", "kh": "ખ", "g": "ગ", "gh": "ઘ",
        "ch": "ચ", "chh": "છ", "j": "જ", "z": "ઝ", "jh": "ઝ",
        "t": "ત", "th": "થ", "d": "દ", "dh": "ધ", "n": "ન",
        "p": "પ", "f": "ફ", "ph": "ફ", "b": "બ", "bh": "ભ", "m": "મ",
        "y": "ય", "r": "ર", "l": "લ", "v": "વ", "w": "વ",
        "sh": "શ", "s": "સ", "h": "હ", "L": "ળ", "ld": "ળ",
        "ksh": "ક્ષ", "gn": "જ્ઞ", "gy": "જ્ઞ"
    };

    const VOWELS_INDEPENDENT = {
        "a": "અ", "aa": "આ", "A": "આ", "i": "ઇ", "ee": "ઈ", "I": "ઈ",
        "u": "ઉ", "oo": "ઊ", "U": "ઊ", "e": "એ", "ai": "ઐ", "o": "ઓ",
        "au": "ઔ", "am": "અં", "an": "અં"
    };

    const MATRAS = {
        "a": "", "aa": "ા", "A": "ા", "i": "િ", "ee": "ી", "I": "ી",
        "u": "ુ", "oo": "ૂ", "U": "ૂ", "e": "ે", "ai": "ૈ", "o": "ો",
        "au": "ૌ", "am": "ં", "an": "ં"
    };

    const GujaratiTransliterator = {
        enabled: false,

        transliterateWord(word) {
            if (!word) return "";
            const lower = word.toLowerCase().trim();
            if (GUJARATI_WORD_MAP[lower]) {
                return GUJARATI_WORD_MAP[lower];
            }

            let result = "";
            let i = 0;
            const len = word.length;

            while (i < len) {
                if (i + 3 <= len) {
                    const sub3 = word.substring(i, i + 3).toLowerCase();
                    if (CONSONANTS[sub3]) {
                        result += CONSONANTS[sub3];
                        i += 3;
                        continue;
                    }
                }
                if (i + 2 <= len) {
                    const sub2 = word.substring(i, i + 2).toLowerCase();
                    if (CONSONANTS[sub2]) {
                        result += CONSONANTS[sub2];
                        i += 2;
                        continue;
                    }
                    if (result === "" && VOWELS_INDEPENDENT[sub2]) {
                        result += VOWELS_INDEPENDENT[sub2];
                        i += 2;
                        continue;
                    }
                    if (result !== "" && MATRAS[sub2] !== undefined) {
                        result += MATRAS[sub2];
                        i += 2;
                        continue;
                    }
                }
                const char = word[i].toLowerCase();
                if (result === "" && VOWELS_INDEPENDENT[char]) {
                    result += VOWELS_INDEPENDENT[char];
                } else if (result !== "" && MATRAS[char] !== undefined) {
                    result += MATRAS[char];
                } else if (CONSONANTS[char]) {
                    result += CONSONANTS[char];
                } else {
                    result += word[i];
                }
                i += 1;
            }
            return result;
        },

        transliterateText(text) {
            if (!text) return "";
            return text.replace(/([A-Za-z]+)/g, (match) => {
                return this.transliterateWord(match);
            });
        },

        attachToInput(inputEl, toggleBtnEl) {
            if (!inputEl) return;
            const self = this;

            inputEl.addEventListener("keydown", (e) => {
                if (!self.enabled) return;

                if (e.key === " " || e.key === "Enter" || e.key === ",") {
                    const val = inputEl.value;
                    const caretPos = inputEl.selectionStart;
                    const textBefore = val.slice(0, caretPos);
                    const textAfter = val.slice(caretPos);

                    const match = textBefore.match(/([A-Za-z]+)$/);
                    if (match) {
                        const englishWord = match[1];
                        const gujaratiWord = self.transliterateWord(englishWord);
                        const newBefore = textBefore.slice(0, -englishWord.length) + gujaratiWord;
                        inputEl.value = newBefore + textAfter;
                        inputEl.selectionStart = inputEl.selectionEnd = newBefore.length;

                        // Trigger input event to update live search
                        inputEl.dispatchEvent(new Event("input", { bubbles: true }));
                    }
                }
            });

            if (toggleBtnEl) {
                toggleBtnEl.addEventListener("click", () => {
                    self.enabled = !self.enabled;
                    self.updateToggleButton(toggleBtnEl);
                    localStorage.setItem("soc_guj_keyboard", self.enabled ? "1" : "0");
                });
                const savedState = localStorage.getItem("soc_guj_keyboard");
                if (savedState === "1") {
                    self.enabled = true;
                    self.updateToggleButton(toggleBtnEl);
                }
            }
        },

        updateToggleButton(btn) {
            if (!btn) return;
            if (this.enabled) {
                btn.className = "btn btn-sm btn-primary font-mono fw-bold";
                btn.innerHTML = `<i class="bi bi-keyboard-fill me-1"></i>ગુજરાતી ટાઈપિંગ (ON)`;
                btn.title = "ગુજરાતી ટાઈપિંગ સક્રિય છે (English અક્ષરો આપોઆપ ગુજરાતી બનશે). Switch to English.";
            } else {
                btn.className = "btn btn-sm btn-outline-secondary font-mono";
                btn.innerHTML = `<i class="bi bi-keyboard me-1"></i>English Typing`;
                btn.title = "Standard English typing active. Click to enable Gujarati phonetic typing.";
            }
        }
    };


    // =========================================================================
    // 2. BILINGUAL LOCALIZATION DICTIONARY (English ⟷ ગુજરાતી)
    // =========================================================================
    const I18N_DICTIONARY = {
        en: {
            "app.title": "GUJARAT POLICE • STATE CYBER CRIME CELL",
            "app.subtitle": "Social Media Intelligence & Early Warning Command System (33 Districts)",
            "strip.classification": "RESTRICTED • LAW ENFORCEMENT INTELLIGENCE ONLY • GUJARAT STATE POLICE CYBER CRIME CELL",
            "nav.live": "Live Monitoring",
            "nav.dashboard": "Dashboard (Analysis)",
            "nav.connect": "Connect Meta API",
            "nav.officers": "Officer Accounts",
            "nav.settings": "Settings",
            
            // Filters
            "filter.keyword": "Crime Keyword-Search",
            "filter.keyword_placeholder": "Type search keywords in English or Gujarati (e.g. cyber, fraud, surat, somnath)...",
            "filter.district": "District / Taluka",
            "filter.district_all": "All Gujarat Statewide",
            "filter.date_from": "Date From",
            "filter.date_to": "Date To",
            "filter.platform": "Platform",
            "filter.platform_all": "All Platforms",
            "filter.apply": "Filter",
            "filter.reset": "Reset",
            "filter.gather_btn": "Gather News Feeds",
            "filter.monitor_all": "Search & Monitor All",

            // Table
            "table.header_origin": "ORIGIN & DISTRICT",
            "table.header_published": "PUBLISHED",
            "table.header_content": "CRIME INTELLIGENCE & REPORT CONTENT",
            "table.header_category": "THREAT CATEGORY",
            "table.header_db_status": "DB STATUS",
            "table.header_actions": "ACTIONS",
            "table.view_live": "LIVE STREAM",
            "table.view_saved": "SAVED TO DATABASE",
            "table.save_record": "Save Record",
            "table.saved": "Saved",
            "table.read_article": "Read Article",
            "table.watch_reel": "Watch Reel",
            "table.view_post": "View FB Post",
            "table.view_advisory": "View Advisory",
            "table.verify_news": "Verify",
            "table.intel": "Intel",

            // Badges
            "badge.ig_reel": "IG REEL",
            "badge.fb_post": "FB POST",
            "badge.news_article": "NEWS ARTICLE",
            "badge.police_advisory": "POLICE ADVISORY",

            // Roles
            "role.admin": "Administrator (IT Desk)",
            "role.officer": "Investigating Officer (Field)",
            "role.badge_prefix": "Badge: ",
            "role.mode_admin_desc": "Full Technical Access • API Credentials • Officer Management",
            "role.mode_officer_desc": "Operational Desk • Field Crime Monitoring • Clean View",

            // Officer Management Modal
            "officers.title": "Police Officers & System Users Management",
            "officers.add_btn": "Register New Officer",
            "officers.badge": "Badge Number",
            "officers.name": "Officer Name",
            "officers.email": "Official Email",
            "officers.role": "Assigned Role",
            "officers.status": "Account Status",
            "officers.actions": "Actions"
        },

        gu: {
            "app.title": "ગુજરાત પોલીસ • રાજ્ય સાયબર ક્રાઇમ સેલ",
            "app.subtitle": "સોશિયલ મીડિયા ઇન્ટેલિજન્સ અને અર્લી વોર્નિંગ કમાન્ડ સિસ્ટમ (૩૩ જિલ્લા)",
            "strip.classification": "પ્રતિબંધિત • માત્ર પોલીસ ગુપ્તચર ઉપયોગ માટે • ગુજરાત રાજ્ય સાયબર ક્રાઇમ સેલ",
            "nav.live": "લાઈવ ક્રાઈમ મોનિટરિંગ",
            "nav.dashboard": "વિશ્લેષણ ડેશબોર્ડ",
            "nav.connect": "મેટા એપીઆઈ સેટિંગ્સ",
            "nav.officers": "પોલીસ અધિકારી ખાતા",
            "nav.settings": "સિસ્ટમ સેટિંગ્સ",

            // Filters
            "filter.keyword": "ગુના કીવર્ડ સર્ચ",
            "filter.keyword_placeholder": "અંગ્રેજી અથવા ગુજરાતીમાં કીવર્ડ ટાઇપ કરો (દા.ત. સાયબર, ફ્રોડ, સુરત, સોમનાથ)...",
            "filter.district": "જિલ્લો / તાલુકો",
            "filter.district_all": "સમગ્ર ગુજરાત (તમામ જિલ્લાઓ)",
            "filter.date_from": "તારીખ થી",
            "filter.date_to": "તારીખ સુધી",
            "filter.platform": "પ્લેટફોર્મ",
            "filter.platform_all": "તમામ પ્લેટફોર્મ",
            "filter.apply": "ફિલ્ટર કરો",
            "filter.reset": "રીસેટ",
            "filter.gather_btn": "નવા સમાચાર મેળવો",
            "filter.monitor_all": "શોધો અને મોનિટર કરો",

            // Table
            "table.header_origin": "સ્ત્રોત અને જિલ્લો",
            "table.header_published": "પ્રકાશન સમય",
            "table.header_content": "ગુનાની વિગત અને અહેવાલ",
            "table.header_category": "સુરક્ષા વર્ગ",
            "table.header_db_status": "ડેટાબેઝ સ્થિતિ",
            "table.header_actions": "કાર્યવાહી",
            "table.view_live": "લાઈવ સ્ટ્રીમ",
            "table.view_saved": "ડેટાબેઝમાં સાચવેલ",
            "table.save_record": "રેકોર્ડ સાચવો",
            "table.saved": "સાચવેલ છે",
            "table.read_article": "સમાચાર વાંચો",
            "table.watch_reel": "રીલ જુઓ",
            "table.view_post": "ફેસબુક પોસ્ટ",
            "table.view_advisory": "એડવાઇઝરી જુઓ",
            "table.verify_news": "ચકાસો",
            "table.intel": "ગુપ્ત વિગત",

            // Badges
            "badge.ig_reel": "ઇન્સ્ટાગ્રામ રીલ",
            "badge.fb_post": "ફેસબુક પોસ્ટ",
            "badge.news_article": "સમાચાર અહેવાલ",
            "badge.police_advisory": "પોલીસ એડવાઇઝરી",

            // Roles
            "role.admin": "એડમિનિસ્ટ્રેટર (આઈટી ડેસ્ક)",
            "role.officer": "તપાસ અધિકારી (ફીલ્ડ)",
            "role.badge_prefix": "બેજ નં: ",
            "role.mode_admin_desc": "સંપૂર્ણ ટેકનિકલ કંટ્રોલ • API કન્ફિગરેશન • અધિકારી વ્યવસ્થાપન",
            "role.mode_officer_desc": "ઓપરેશનલ ડેસ્ક • ફીલ્ડ મોનિટરિંગ • સરળ સ્ક્રીન",

            // Officer Management Modal
            "officers.title": "પોલીસ અધિકારીઓ અને સિસ્ટમ વપરાશકર્તા સંચાલન",
            "officers.add_btn": "નવા અધિકારી ઉમેરો",
            "officers.badge": "બેજ નંબર",
            "officers.name": "અધિકારીનું નામ",
            "officers.email": "સત્તાવાર ઈમેલ",
            "officers.role": "સોંપાયેલ હોદ્દો",
            "officers.status": "ખાતાની સ્થિતિ",
            "officers.actions": "કાર્યવાહી"
        }
    };

    const SocI18n = {
        currentLang: localStorage.getItem("soc_lang") || "en",

        t(key, fallback = "") {
            const dict = I18N_DICTIONARY[this.currentLang] || I18N_DICTIONARY.en;
            return dict[key] !== undefined ? dict[key] : (I18N_DICTIONARY.en[key] || fallback || key);
        },

        setLanguage(lang) {
            if (lang !== "en" && lang !== "gu") lang = "en";
            this.currentLang = lang;
            localStorage.setItem("soc_lang", lang);
            this.applyTranslations();
            this.updateLanguageButton();
            SocRoleManager.updateRoleSwitcherUI();

            if (window.InstagramApp && typeof window.InstagramApp.loadDashboardData === "function") {
                window.InstagramApp.loadDashboardData(false);
            }
        },

        toggleLanguage() {
            const nextLang = this.currentLang === "en" ? "gu" : "en";
            this.setLanguage(nextLang);
        },

        applyTranslations() {
            document.querySelectorAll("[data-i18n]").forEach(el => {
                const key = el.getAttribute("data-i18n");
                if (key) el.textContent = this.t(key);
            });

            document.querySelectorAll("[data-i18n-title]").forEach(el => {
                const key = el.getAttribute("data-i18n-title");
                if (key) el.title = this.t(key);
            });

            document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
                const key = el.getAttribute("data-i18n-placeholder");
                if (key) el.placeholder = this.t(key);
            });
        },

        updateLanguageButton() {
            const btn = document.getElementById("soc-language-toggle-btn");
            if (!btn) return;
            if (this.currentLang === "gu") {
                btn.className = "btn btn-sm btn-outline-warning rounded-pill px-3 font-mono fw-bold";
                btn.innerHTML = `🇮🇳 <span class="d-none d-md-inline ms-1">ભાષા:</span> ગુજરાતી`;
                btn.title = "હાલમાં ગુજરાતી ભાષા સક્રિય છે. Switch to English.";
            } else {
                btn.className = "btn btn-sm btn-outline-secondary rounded-pill px-3 font-mono fw-bold";
                btn.innerHTML = `🇬🇧 <span class="d-none d-md-inline ms-1">Language:</span> English`;
                btn.title = "Currently in English. ગુજરાતી ભાષામાં બદલો.";
            }
        }
    };


    // =========================================================================
    // 3. DUAL ROLE MANAGER (Administrator vs. Investigating Officer)
    // =========================================================================
    const SocRoleManager = {
        currentRole: localStorage.getItem("soc_user_role") || "officer",

        init() {
            this.applyRoleView();
            this.updateRoleSwitcherUI();
        },

        setRole(role) {
            if (role !== "admin" && role !== "officer") role = "officer";
            this.currentRole = role;
            localStorage.setItem("soc_user_role", role);
            this.applyRoleView();
            this.updateRoleSwitcherUI();

            const roleName = role === "admin" 
                ? (SocI18n.currentLang === "gu" ? "એડમિનિસ્ટ્રેટર (આઈટી ડેસ્ક)" : "Administrator (IT Technical Desk)") 
                : (SocI18n.currentLang === "gu" ? "પોલીસ તપાસ અધિકારી (ફીલ્ડ)" : "Police Investigating Officer (Field Desk)");
            if (window.InstagramApp && typeof window.InstagramApp.showToast === "function") {
                window.InstagramApp.showToast(`Switched active desk to: ${roleName}`, "info");
            }
        },

        toggleRole() {
            const nextRole = this.currentRole === "admin" ? "officer" : "admin";
            this.setRole(nextRole);
        },

        applyRoleView() {
            const isAdmin = this.currentRole === "admin";

            document.querySelectorAll(".admin-only-feature").forEach(el => {
                el.style.display = isAdmin ? "" : "none";
            });

            document.querySelectorAll(".officer-only-feature").forEach(el => {
                el.style.display = isAdmin ? "none" : "";
            });

            const metaConnectBtn = document.getElementById("btn-open-meta-connect");
            if (metaConnectBtn) metaConnectBtn.style.display = isAdmin ? "" : "none";

            const navConnect = document.getElementById("nav-connect");
            if (navConnect) navConnect.style.display = isAdmin ? "" : "none";

            const navOfficers = document.getElementById("nav-officers");
            if (navOfficers) navOfficers.style.display = isAdmin ? "" : "none";
        },

        updateRoleSwitcherUI() {
            const btn = document.getElementById("soc-role-switcher-btn");
            const badge = document.getElementById("soc-current-role-badge");
            if (!btn) return;

            const isGu = SocI18n.currentLang === "gu";

            if (this.currentRole === "admin") {
                btn.className = "btn btn-sm btn-dark border-secondary rounded-pill px-3 font-mono fw-bold";
                btn.innerHTML = `<i class="bi bi-shield-shaded text-warning me-1"></i>${isGu ? "એડમિનિસ્ટ્રેટર (આઈટી ડેસ્ક)" : "Administrator (IT Desk)"}`;
                btn.title = isGu ? "ટેકનિકલ ડેસ્ક: API સેટિંગ્સ, સિસ્ટમ હેલ્થ, અધિકારી એકાઉન્ટ્સ સક્રિય છે." : "Technical Control Desk: Full API configuration, Officer accounts & System diagnostics.";
                if (badge) {
                    badge.textContent = "SUPER_ADMIN";
                    badge.className = "badge bg-danger-subtle text-danger border border-danger-subtle font-mono";
                }
            } else {
                btn.className = "btn btn-sm btn-primary-subtle text-primary border border-primary-subtle rounded-pill px-3 font-mono fw-bold";
                btn.innerHTML = `<i class="bi bi-person-badge-fill text-primary me-1"></i>${isGu ? "તપાસ અધિકારી (ફીલ્ડ)" : "Investigating Officer (Field)"}`;
                btn.title = isGu ? "ફીલ્ડ ડેસ્ક: સરળ ગુના મોનિટરિંગ અને કેસ સાચવવાની સ્ક્રીન." : "Field Investigation Desk: Zero-jargon operational monitoring and case dossier tools.";
                if (badge) {
                    badge.textContent = "LEAD_INVESTIGATOR";
                    badge.className = "badge bg-primary-subtle text-primary border border-primary-subtle font-mono";
                }
            }
        }
    };


    // =========================================================================
    // 4. OFFICER ACCOUNTS MANAGEMENT (ADMIN-ONLY)
    // =========================================================================
    const OfficerManager = {
        async loadOfficers() {
            const tbody = document.getElementById("officers-table-tbody");
            if (!tbody) return;
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-secondary font-mono"><div class="spinner-border spinner-border-sm me-2"></div>Loading police officers...</td></tr>`;

            try {
                const res = await fetch("/api/v1/users", {
                    headers: { "X-User-Role": "SUPER_ADMIN" }
                });
                const json = await res.json();
                if (json && json.status === "SUCCESS") {
                    this.renderOfficersTable(json.data || []);
                } else {
                    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-danger font-mono">Failed to load officers.</td></tr>`;
                }
            } catch (err) {
                console.error("Error loading officers:", err);
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-danger font-mono">Connection error loading officer accounts.</td></tr>`;
            }
        },

        renderOfficersTable(officers) {
            const tbody = document.getElementById("officers-table-tbody");
            if (!tbody) return;
            if (officers.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-secondary font-mono">No officer accounts registered.</td></tr>`;
                return;
            }

            tbody.innerHTML = officers.map((o, idx) => {
                const roleBadge = o.role === "SUPER_ADMIN" 
                    ? `<span class="badge bg-danger-subtle text-danger border border-danger-subtle font-mono">ADMIN</span>`
                    : (o.role === "LEAD_INVESTIGATOR" 
                        ? `<span class="badge bg-primary-subtle text-primary border border-primary-subtle font-mono">INVESTIGATOR</span>`
                        : `<span class="badge bg-info-subtle text-info border border-info-subtle font-mono">ANALYST</span>`);

                const statusBadge = o.is_active 
                    ? `<span class="badge bg-success font-mono">ACTIVE</span>`
                    : `<span class="badge bg-secondary font-mono">DEACTIVATED</span>`;

                const toggleBtn = `<button class="btn btn-xs btn-outline-${o.is_active ? 'danger' : 'success'} font-mono" onclick="OfficerManager.toggleStatus('${o.badge_number}', ${!o.is_active})">${o.is_active ? 'Deactivate' : 'Activate'}</button>`;

                return `
                    <tr>
                        <td class="font-mono fw-bold">${idx + 1}</td>
                        <td class="font-mono text-primary fw-bold">${o.badge_number}</td>
                        <td class="fw-semibold text-dark-emphasis">${o.full_name}</td>
                        <td class="font-mono small text-secondary">${o.email}</td>
                        <td>${roleBadge}</td>
                        <td>${statusBadge}</td>
                        <td class="text-end">${toggleBtn}</td>
                    </tr>
                `;
            }).join("");
        },

        async createOfficer() {
            const badge = (document.getElementById("new-officer-badge")?.value || "").trim().toUpperCase();
            const name = (document.getElementById("new-officer-name")?.value || "").trim();
            const email = (document.getElementById("new-officer-email")?.value || "").trim().toLowerCase();
            const role = document.getElementById("new-officer-role")?.value || "CYBER_ANALYST";

            if (!badge || !name || !email) {
                alert("Please fill all officer fields (Badge, Full Name, Email).");
                return;
            }

            try {
                const res = await fetch("/api/v1/users", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-User-Role": "SUPER_ADMIN"
                    },
                    body: JSON.stringify({
                        badge_number: badge,
                        full_name: name,
                        email: email,
                        role: role
                    })
                });
                const json = await res.json();
                if (json && json.status === "SUCCESS") {
                    if (window.InstagramApp) window.InstagramApp.showToast(`Officer ${badge} registered successfully!`, "success");
                    // Clear inputs
                    if (document.getElementById("new-officer-badge")) document.getElementById("new-officer-badge").value = "";
                    if (document.getElementById("new-officer-name")) document.getElementById("new-officer-name").value = "";
                    if (document.getElementById("new-officer-email")) document.getElementById("new-officer-email").value = "";
                    this.loadOfficers();
                } else {
                    alert(json.message || "Failed to create officer account.");
                }
            } catch (err) {
                console.error("Error creating officer:", err);
                alert("Error connecting to server to register officer.");
            }
        },

        async toggleStatus(badge, newActive) {
            try {
                const res = await fetch(`/api/v1/users/${badge}/status`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "X-User-Role": "SUPER_ADMIN"
                    },
                    body: JSON.stringify({ is_active: newActive })
                });
                const json = await res.json();
                if (json && json.status === "SUCCESS") {
                    this.loadOfficers();
                    if (window.InstagramApp) window.InstagramApp.showToast(`Officer ${badge} status updated.`, "info");
                }
            } catch (err) {
                console.error("Error updating officer status:", err);
            }
        }
    };

    // Export to global window object
    window.SocI18n = SocI18n;
    window.SocRoleManager = SocRoleManager;
    window.GujaratiTransliterator = GujaratiTransliterator;
    window.OfficerManager = OfficerManager;

    // Auto-initialize on DOMContentLoaded
    document.addEventListener("DOMContentLoaded", () => {
        SocI18n.applyTranslations();
        SocI18n.updateLanguageButton();
        SocRoleManager.init();

        const searchInput = document.getElementById("filter-keyword");
        const keyboardToggleBtn = document.getElementById("btn-guj-keyboard-toggle");
        if (searchInput && keyboardToggleBtn) {
            GujaratiTransliterator.attachToInput(searchInput, keyboardToggleBtn);
        }
    });

})(window);
