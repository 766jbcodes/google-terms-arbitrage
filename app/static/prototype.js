const opportunities = [
    {
        id: "dental",
        name: "Dental equipment finance",
        category: "Commercial · Equipment",
        audience: "commercial",
        region: "Australia",
        score: 86,
        strength: "high",
        signal: "Act this week",
        summary: "Consistent growth, clear borrower intent and lower estimated ad costs than the broader equipment-finance category.",
        movement: "+34%",
        movementClass: "positive",
        activeWeeks: "31 of 52 weeks",
        adCost: "$2.10–$4.80",
        intent: "High",
        nextReview: "22 July",
        reasons: [
            "Search activity strengthened across 31 active weeks, not just a single spike.",
            "Queries use product-led language associated with borrowers comparing finance options.",
            "Estimated top-of-page costs remain below the wider equipment-finance category."
        ],
        caution: "Demand is specialised and national. Test a focused campaign before increasing budget.",
        campaign: {
            borrower: "Practice owners upgrading chairs, imaging or sterilisation equipment",
            angle: "Preserve working capital while replacing revenue-critical equipment",
            content: "How Australian dental practices can finance an equipment upgrade",
            action: "Approach one dental equipment supplier about a referral partnership"
        }
    },
    {
        id: "horse",
        name: "Horse float finance",
        category: "Consumer · Vehicle",
        audience: "consumer",
        region: "Regional Victoria",
        score: 74,
        strength: "watch",
        signal: "Test carefully",
        summary: "A small but increasingly consistent regional niche. Useful for a tightly targeted content or referral experiment.",
        movement: "+22%",
        movementClass: "positive",
        activeWeeks: "19 of 52 weeks",
        adCost: "$1.40–$3.20",
        intent: "Medium",
        nextReview: "29 July",
        reasons: [
            "Regional Victorian interest has risen for four consecutive reporting periods.",
            "Advertising competition is low compared with general vehicle finance.",
            "Borrower language is specific enough for a focused landing page."
        ],
        caution: "Absolute search volume is modest and seasonal. Treat this as a watchlist signal, not a forecast.",
        campaign: {
            borrower: "Regional buyers replacing or purchasing their first horse float",
            angle: "Compare finance before committing to a new or used float",
            content: "What to check before financing a horse float in Victoria",
            action: "Test a referral conversation with one regional float dealer"
        }
    },
    {
        id: "tiny",
        name: "Tiny home finance",
        category: "Commercial · Specialist",
        audience: "commercial",
        region: "Australia",
        score: 68,
        strength: "steady",
        signal: "Keep watching",
        summary: "Interest is established and improving, but lender fit and borrower expectations make the opportunity harder to convert.",
        movement: "+11%",
        movementClass: "caution",
        activeWeeks: "38 of 52 weeks",
        adCost: "$3.80–$7.10",
        intent: "Medium",
        nextReview: "22 July",
        reasons: [
            "Search activity is established across most of the year.",
            "Recent movement is positive but not yet strong enough to call a breakout.",
            "Several related searches show borrowers are unclear about property classification."
        ],
        caution: "A campaign needs careful qualification and clear language about lender and property requirements.",
        campaign: {
            borrower: "Buyers researching movable dwellings and non-standard properties",
            angle: "Understand the finance questions before selecting a tiny home",
            content: "Why tiny home finance depends on land, mobility and property classification",
            action: "Create a qualification checklist before testing paid traffic"
        }
    }
];

const savedOpportunityIds = new Set(["dental", "tiny"]);

const opportunityFeed = document.querySelector("#opportunity-feed");
const watchlistBody = document.querySelector("#watchlist-body");
const watchlistCount = document.querySelector("#watchlist-count");
const detailPanel = document.querySelector("#detail-panel");
const detailTitle = document.querySelector("#detail-title");
const detailCategory = document.querySelector("#detail-category");
const detailContent = document.querySelector("#detail-content");
const scrim = document.querySelector("#scrim");
const toast = document.querySelector("#toast");
const sidebar = document.querySelector(".sidebar");
const mobileMenuButton = document.querySelector("#mobile-menu-button");

let activeFilter = "all";
let lastFocusedElement = null;
let toastTimer = null;

function renderOpportunities() {
    opportunityFeed.innerHTML = opportunities.map((opportunity) => {
        const isSaved = savedOpportunityIds.has(opportunity.id);
        const isHidden = activeFilter !== "all" && opportunity.audience !== activeFilter;

        return `
            <article class="opportunity-card" data-opportunity-id="${opportunity.id}" data-audience="${opportunity.audience}" data-strength="${opportunity.strength}" ${isHidden ? "hidden" : ""}>
                <div class="score-ring" aria-label="Opportunity score ${opportunity.score} out of 100">
                    <strong>${opportunity.score}</strong>
                    <span>Score</span>
                </div>
                <div class="opportunity-body">
                    <div class="opportunity-meta">
                        <span class="signal-label">${opportunity.signal}</span>
                        <span>${opportunity.category}</span>
                        <span>${opportunity.region}</span>
                    </div>
                    <h2>${opportunity.name}</h2>
                    <p>${opportunity.summary}</p>
                    <div class="metric-row" aria-label="Key opportunity metrics">
                        <span class="metric"><strong class="${opportunity.movementClass}">${opportunity.movement}</strong> 4-week movement</span>
                        <span class="metric"><strong>${opportunity.activeWeeks}</strong> active</span>
                        <span class="metric"><strong>${opportunity.adCost}</strong> est. click</span>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="save-button ${isSaved ? "is-saved" : ""}" data-save-opportunity="${opportunity.id}" type="button" aria-label="${isSaved ? "Remove" : "Add"} ${opportunity.name} ${isSaved ? "from" : "to"} watchlist" aria-pressed="${isSaved}">
                        <span aria-hidden="true">${isSaved ? "✓" : "+"}</span>
                    </button>
                    <button class="open-button" data-open-opportunity="${opportunity.id}" type="button">Review</button>
                </div>
            </article>
        `;
    }).join("");

    bindDynamicActions();
}

function renderWatchlist() {
    const savedOpportunities = opportunities.filter((opportunity) => savedOpportunityIds.has(opportunity.id));
    watchlistCount.textContent = String(savedOpportunities.length);

    if (!savedOpportunities.length) {
        watchlistBody.innerHTML = `
            <tr>
                <td class="empty-watchlist" colspan="5">Your watchlist is empty. Save an opportunity from the radar to track it here.</td>
            </tr>
        `;
        return;
    }

    watchlistBody.innerHTML = savedOpportunities.map((opportunity) => `
        <tr>
            <td>
                <div class="watchlist-name">
                    <strong>${opportunity.name}</strong>
                    <span>${opportunity.category} · ${opportunity.region}</span>
                </div>
            </td>
            <td>${opportunity.score} / 100</td>
            <td><span class="movement-up">${opportunity.movement}</span></td>
            <td>${opportunity.nextReview}</td>
            <td><button class="table-action" data-open-opportunity="${opportunity.id}" type="button">Review</button></td>
        </tr>
    `).join("");

    bindDynamicActions();
}

function bindDynamicActions() {
    document.querySelectorAll("[data-open-opportunity]").forEach((button) => {
        button.onclick = () => openOpportunity(button.dataset.openOpportunity, button);
    });

    document.querySelectorAll("[data-save-opportunity]").forEach((button) => {
        button.onclick = () => toggleSavedOpportunity(button.dataset.saveOpportunity);
    });
}

function toggleSavedOpportunity(opportunityId) {
    const opportunity = opportunities.find((item) => item.id === opportunityId);
    if (!opportunity) return;

    if (savedOpportunityIds.has(opportunityId)) {
        savedOpportunityIds.delete(opportunityId);
        showToast(`${opportunity.name} removed from your watchlist.`);
    } else {
        savedOpportunityIds.add(opportunityId);
        showToast(`${opportunity.name} added to your watchlist.`);
    }

    renderOpportunities();
    renderWatchlist();
}

function openOpportunity(opportunityId, triggerElement) {
    const opportunity = opportunities.find((item) => item.id === opportunityId);
    if (!opportunity) return;

    lastFocusedElement = triggerElement || document.activeElement;
    detailTitle.textContent = opportunity.name;
    detailCategory.textContent = `${opportunity.category} · ${opportunity.region}`;
    detailContent.innerHTML = `
        <section class="detail-score">
            <div class="detail-score-value" aria-label="Score ${opportunity.score} out of 100">${opportunity.score}</div>
            <div>
                <h3>${opportunity.signal}</h3>
                <p>${opportunity.summary}</p>
            </div>
        </section>
        <section class="detail-section">
            <h3>Why this signal ranked</h3>
            <ul class="reason-list">
                ${opportunity.reasons.map((reason) => `<li>${reason}</li>`).join("")}
            </ul>
        </section>
        <section class="detail-section">
            <h3>Important context</h3>
            <p>${opportunity.caution}</p>
        </section>
        <section class="detail-section">
            <span class="eyebrow">Sample campaign brief</span>
            <h3>Turn the signal into a practical test</h3>
            <div class="campaign-brief">
                <dl>
                    <dt>Borrower</dt><dd>${opportunity.campaign.borrower}</dd>
                    <dt>Campaign angle</dt><dd>${opportunity.campaign.angle}</dd>
                    <dt>Content idea</dt><dd>${opportunity.campaign.content}</dd>
                    <dt>First action</dt><dd>${opportunity.campaign.action}</dd>
                </dl>
            </div>
        </section>
        <div class="detail-actions">
            <button class="primary-button" id="use-brief-button" type="button">Use this campaign brief</button>
            <button class="save-button ${savedOpportunityIds.has(opportunity.id) ? "is-saved" : ""}" id="detail-save-button" type="button" aria-label="${savedOpportunityIds.has(opportunity.id) ? "Remove from" : "Add to"} watchlist">
                <span aria-hidden="true">${savedOpportunityIds.has(opportunity.id) ? "✓" : "+"}</span>
            </button>
        </div>
    `;

    detailPanel.classList.add("is-open");
    detailPanel.setAttribute("aria-hidden", "false");
    detailPanel.removeAttribute("inert");
    scrim.hidden = false;
    document.body.style.overflow = "hidden";
    document.querySelector("#close-detail-button").focus();

    document.querySelector("#detail-save-button").onclick = () => {
        toggleSavedOpportunity(opportunity.id);
        openOpportunity(opportunity.id, lastFocusedElement);
    };

    document.querySelector("#use-brief-button").onclick = () => {
        showToast("Prototype action: a campaign workspace would open here.");
    };
}

function closeOpportunity() {
    detailPanel.classList.remove("is-open");
    detailPanel.setAttribute("aria-hidden", "true");
    detailPanel.setAttribute("inert", "");
    scrim.hidden = true;
    document.body.style.overflow = "";
    if (lastFocusedElement) lastFocusedElement.focus();
}

function changeView(viewName) {
    document.querySelectorAll(".view").forEach((view) => {
        view.classList.toggle("is-active", view.dataset.viewPanel === viewName);
    });

    document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.toggle("is-active", item.dataset.view === viewName);
    });

    if (viewName === "watchlist") renderWatchlist();
    sidebar.classList.remove("is-open");
    mobileMenuButton.setAttribute("aria-expanded", "false");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function showToast(message) {
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add("is-visible");
    toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 2800);
}

document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => changeView(item.dataset.view));
});

document.querySelectorAll(".filter-chip").forEach((button) => {
    button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;
        document.querySelectorAll(".filter-chip").forEach((chip) => {
            chip.classList.toggle("is-active", chip === button);
        });
        renderOpportunities();
    });
});

document.querySelector("#open-briefing-button").addEventListener("click", () => changeView("briefing"));
document.querySelector("#close-detail-button").addEventListener("click", closeOpportunity);
scrim.addEventListener("click", () => {
    closeOpportunity();
    sidebar.classList.remove("is-open");
});

mobileMenuButton.addEventListener("click", () => {
    const isOpen = sidebar.classList.toggle("is-open");
    mobileMenuButton.setAttribute("aria-expanded", String(isOpen));
});

document.querySelector("#method-button").addEventListener("click", () => {
    document.querySelector("#method-dialog").showModal();
});

document.querySelector("#filter-control").addEventListener("click", () => {
    showToast("Prototype action: region, category and signal-strength filters would open here.");
});

document.querySelector("#edit-focus-button").addEventListener("click", () => {
    showToast("Prototype action: onboarding preferences would open here.");
});

document.querySelector(".icon-button").addEventListener("click", () => {
    showToast("Three sample signals have changed since last week.");
});

document.querySelector("#copy-briefing-button").addEventListener("click", async () => {
    try {
        await navigator.clipboard.writeText(window.location.href);
        showToast("Briefing link copied.");
    } catch {
        showToast("Prototype action: briefing sharing is ready to discuss.");
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && detailPanel.classList.contains("is-open")) {
        closeOpportunity();
    }
});

renderOpportunities();
renderWatchlist();
