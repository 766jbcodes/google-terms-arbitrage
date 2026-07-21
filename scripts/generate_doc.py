from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=25)
pdf.add_page()

# Title
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Google Ads API - Tool Documentation", new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# Subtitle
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, "Niche Finance Keyword Dashboard", new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0, 0, 0)
pdf.ln(6)

sections = [
    ("1. Application Overview", [
        "The Niche Finance Keyword Dashboard is a self-hosted, internal-use keyword research tool "
        "designed to identify underpriced advertising opportunities in niche finance verticals within "
        "the Australian market.",
        "The application tracks a curated list of niche finance search terms (e.g. 'jet ski finance', "
        "'vending machine finance', 'solar panel finance') and monitors their search volume, "
        "cost-per-click (CPC), and competition levels over time to surface keywords that are "
        "low-competition and rising in interest.",
    ]),
    ("2. How the Tool Uses the Google Ads API", [
        "The tool makes periodic calls (weekly) to the Google Ads API KeywordPlanIdeaService "
        "(GenerateKeywordIdeas) to retrieve keyword metrics for a maintained list of approximately "
        "30-50 niche finance terms.",
        "For each keyword, the following metrics are retrieved:\n"
        "  - Average monthly search volume\n"
        "  - Competition level (LOW / MEDIUM / HIGH)\n"
        "  - Top-of-page bid estimates (low range and high range CPC)\n"
        "  - Month-over-month and year-over-year search volume trends",
        "The retrieved data is stored in a local SQLite database and displayed on a private internal "
        "dashboard accessible only on the local network. No data is shared externally or with third parties.",
    ]),
    ("3. API Usage Volume", [
        "The tool is designed for minimal API usage:\n"
        "  - Approximately 1 API call per week (batch of 30-50 keywords per request)\n"
        "  - No real-time or high-frequency usage\n"
        "  - No automated bidding, campaign creation, or ad management\n"
        "  - Read-only access to keyword planning data only",
    ]),
    ("4. Architecture", [
        "The application consists of two lightweight Docker containers:\n"
        "  - A dashboard container serving a web UI (FastAPI/Python)\n"
        "  - A data puller container that runs the weekly keyword data retrieval",
        "All data is stored locally in a SQLite database. The application runs on a private home "
        "server and is accessible only via the local network and Tailscale VPN. There is no public-facing "
        "component.",
    ]),
    ("5. Users and Access", [
        "This is a single-user, internal tool. There are no external users, no customer-facing features, "
        "and no commercial redistribution of Google Ads data. The tool is used solely for personal "
        "keyword research to inform advertising strategy.",
    ]),
    ("6. Compliance", [
        "The tool complies with the Google Ads API Terms of Service:\n"
        "  - No caching of data beyond what is permitted\n"
        "  - No redistribution of API data to third parties\n"
        "  - No automated campaign or bidding operations\n"
        "  - Minimal API call volume, well within rate limits",
    ]),
    ("7. Contact", [
        "Developer: Jacob Bullen\n"
        "Email: jacobbullen1@gmail.com",
    ]),
]

for title, paragraphs in sections:
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10.5)
    for para in paragraphs:
        pdf.multi_cell(0, 6, para)
        pdf.ln(3)
    pdf.ln(2)

output_path = r"C:\Users\Jacob\Cursor Projects\homecloud server\google-terms-arbitrage\Google_Ads_API_Tool_Documentation.pdf"
pdf.output(output_path)
print(f"PDF saved to: {output_path}")
