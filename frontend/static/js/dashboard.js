/**
 * Gujarat Cyber Crime Social Media Intelligence & Early Warning System
 * Control Room Base Shell Controller (Clocks, Theme, Role Simulation, Notifications)
 * Instagram Monitoring System - Version 1
 */

const SocState = {
    role: localStorage.getItem("soc_officer_role") || "LEAD_INVESTIGATOR",
    officerLabel: localStorage.getItem("soc_officer_label") || "Insp. R. K. Vala",
    theme: localStorage.getItem("soc_theme") || "dark"
};

const SocDashboard = {
    init() {
        this.applyTheme(SocState.theme);
        this.applyRole(SocState.role, SocState.officerLabel);
        this.startClocks();
    },

    startClocks() {
        const updateClocks = () => {
            const now = new Date();

            // Indian Standard Time (IST) Clock
            const istOptions = {
                timeZone: "Asia/Kolkata",
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            };
            try {
                const istStr = new Intl.DateTimeFormat("en-GB", istOptions).format(now);
                const istEl = document.getElementById("soc-ist-clock");
                if (istEl) istEl.textContent = `${istStr} IST`;
            } catch (e) {
                const istEl = document.getElementById("soc-ist-clock");
                if (istEl) istEl.textContent = now.toLocaleTimeString();
            }

            // UTC Clock
            const utcStr = now.toISOString().replace("T", " ").substring(0, 19);
            const utcEl = document.getElementById("soc-utc-clock");
            if (utcEl) utcEl.textContent = `${utcStr}Z`;
        };

        updateClocks();
        setInterval(updateClocks, 1000);
    },

    setRole(role, label) {
        SocState.role = role;
        SocState.officerLabel = label;
        localStorage.setItem("soc_officer_role", role);
        localStorage.setItem("soc_officer_label", label);

        this.applyRole(role, label);
        this.showToast(`Security clearance updated: ${role}`);
        window.location.reload();
    },

    applyRole(role, label) {
        const roleBadge = document.getElementById("active-role-badge");
        const officerLabel = document.getElementById("active-officer-label");

        if (roleBadge) roleBadge.textContent = role;
        if (officerLabel) officerLabel.textContent = label.split(" [")[0];
    },

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute("data-bs-theme") || "dark";
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        this.applyTheme(newTheme);
    },

    applyTheme(theme) {
        document.documentElement.setAttribute("data-bs-theme", theme);
        SocState.theme = theme;
        localStorage.setItem("soc_theme", theme);

        const icon = document.getElementById("themeIcon");
        if (icon) {
            icon.className = theme === "dark" ? "bi bi-moon-stars" : "bi bi-sun";
        }
    },

    showToast(message, type = "info") {
        const body = document.getElementById("socToastBody");
        const toastEl = document.getElementById("socToast");
        if (body && toastEl) {
            body.textContent = message;
            const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 4000 });
            toast.show();
        }
    }
};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    SocDashboard.init();
});
