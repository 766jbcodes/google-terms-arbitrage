from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import json
import threading
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import db
from app import pullers
from app.seed_terms import SEED_TERMS

app = FastAPI(title="Niche Finance Dashboard")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
RUN_STATUS = {}
RUN_LOCK = threading.Lock()
SEEDS_SYNCED = False
SEEDS_LOCK = threading.Lock()


class RunTermRequest(BaseModel):
    term_id: int


class RunTermsRequest(BaseModel):
    term_ids: list[int]


def fetch_dashboard_data():
    db.init_db()
    _sync_seed_terms()
    conn = db.get_conn()

    rows = conn.execute("""
        SELECT
            t.id,
            t.term,
            t.source,
            t.first_seen,
            t.audience,
            t.intent,
            s.avg_interest,
            s.latest_interest,
            s.trend_direction,
            s.is_breakout,
            s.pulled_at,
            km.avg_monthly_searches,
            km.competition,
            km.competition_index,
            km.low_top_of_page_bid_micros,
            km.high_top_of_page_bid_micros,
            km.pulled_at as metrics_pulled_at,
            s.weekly_series
        FROM terms t
        LEFT JOIN trend_snapshots s
            ON s.id = (
                SELECT id FROM trend_snapshots
                WHERE term_id = t.id
                ORDER BY pulled_at DESC LIMIT 1
            )
        LEFT JOIN keyword_metrics km
            ON km.id = (
                SELECT id FROM keyword_metrics
                WHERE term_id = t.id
                ORDER BY pulled_at DESC LIMIT 1
            )
        WHERE t.active = 1
        ORDER BY
            CASE s.trend_direction WHEN 'rising' THEN 0 ELSE 1 END,
            s.avg_interest ASC
    """).fetchall()

    discovered = conn.execute("""
        SELECT query_text, query_type, value, pulled_at, promoted
        FROM related_queries
        WHERE query_type = 'rising'
        ORDER BY pulled_at DESC
        LIMIT 30
    """).fetchall()

    conn.close()
    return rows, discovered


def _parse_series(weekly_series_json):
    """Parse weekly_series JSON, return list or None."""
    if not weekly_series_json:
        return None
    try:
        s = json.loads(weekly_series_json) if isinstance(weekly_series_json, str) else weekly_series_json
        return s if s and len(s) >= 2 else None
    except (json.JSONDecodeError, TypeError):
        return None


def _series_confidence(series):
    """How many non-zero weeks exist. Returns (nonzero_count, total_weeks)."""
    if not series:
        return 0, 0
    return sum(1 for v in series if v > 0), len(series)


def interest_label(avg):
    """Show the actual number with a bucket label."""
    if avg is None or avg == 0:
        return "-", "No search data"
    rounded = round(avg, 1)
    if avg < 5:
        return f"{rounded}/100", f"Interest score {rounded} out of 100 — almost no search activity"
    if avg < 15:
        return f"{rounded}/100", f"Interest score {rounded} out of 100 — low search activity"
    if avg < 35:
        return f"{rounded}/100", f"Interest score {rounded} out of 100 — moderate search activity"
    if avg < 60:
        return f"{rounded}/100", f"Interest score {rounded} out of 100 — solid search activity"
    return f"{rounded}/100", f"Interest score {rounded} out of 100 — high search activity"


def trend_label(row, series):
    """Trend direction with confidence. series is the parsed weekly list or None."""
    direction = row["trend_direction"]
    avg = row["avg_interest"]

    if direction is None or direction == "insufficient_data" or avg is None:
        return "—", "muted", "Not enough search data to determine a trend"

    nonzero, total = _series_confidence(series)

    if direction == "too_sparse":
        return f"Too sparse ({nonzero} weeks)", "muted", \
            f"Only {nonzero} of {total} weeks had any searches — not enough to call a trend"

    conf_note = f" — based on {nonzero} of {total} active weeks" if series else ""

    if direction == "rising":
        return f"Rising ({nonzero}w)", "trend-rising", \
            f"Second half of the year averaged higher than the first{conf_note}"
    if direction == "falling":
        return f"Falling ({nonzero}w)", "trend-falling", \
            f"Second half of the year averaged lower than the first{conf_note}"
    return f"Steady ({nonzero}w)", "trend-flat", \
        f"No significant change between first and second half of the year{conf_note}"


def signal_label(row, series):
    """Plain-English signal with confidence gating.
    Without Ads data (search volume, CPC), signals describe the trend pattern only.
    With Ads data, they can make actual opportunity judgements."""
    avg = row["avg_interest"]
    direction = row["trend_direction"]
    breakout = row["is_breakout"]
    has_ads = row["avg_monthly_searches"] is not None

    if direction is None or direction == "insufficient_data" or avg is None:
        return "Waiting for data", "signal-waiting", 0, \
            "We haven't collected enough data on this keyword yet"

    if direction == "too_sparse":
        return "Not enough data", "signal-waiting", 0, \
            "Too few weeks with searches to judge — check back after the next pull"

    nonzero, _ = _series_confidence(series)

    if breakout:
        return "Breakout", "signal-breakout", 2, \
            "Sudden spike from near-zero. Could be a new trend — verify with the sparkline"

    if avg < 20 and direction == "rising":
        if has_ads:
            cpc_low = (row["low_top_of_page_bid_micros"] or 0) / 1_000_000
            comp = row["competition"] or ""
            if comp == "LOW" and cpc_low < 2.0:
                if nonzero >= 20:
                    return "Good opportunity", "signal-opportunity", 3, \
                        f"Rising interest ({nonzero} weeks), low competition, cheap ads — worth acting on"
                return "Possible opportunity", "signal-opportunity-low", 2, \
                    f"Rising but only {nonzero} active weeks. Low ad cost though — worth watching"
            return "Rising, check cost", "signal-established", 1, \
                f"Interest is growing but ad competition is {comp.lower()} — check if the cost makes sense"
        else:
            if nonzero >= 20:
                return "Rising (needs ad data)", "signal-opportunity-low", 2, \
                    f"Consistent growth across {nonzero} weeks — need ad cost data to judge if it's a real opportunity"
            return "Rising (low confidence)", "signal-waiting", 1, \
                f"Technically rising, but only {nonzero} active weeks and no ad data — too early to call"

    if avg < 5:
        return "Very quiet", "signal-quiet", 0, \
            "Almost no search activity"

    if avg < 10 and direction != "rising":
        return "Quiet niche", "signal-quiet", 0, \
            "Low volume, not growing"

    if avg >= 35 and direction == "rising":
        return "Popular + rising", "signal-popular", 2, \
            "Solid interest and growing — likely competitive"

    if avg >= 20:
        return "Established", "signal-established", 1, \
            "Steady search volume"

    return "", "", 0, ""


def _set_run_status(term_id, status, message=""):
    trimmed = message[:160] if message else ""
    RUN_STATUS[term_id] = {
        "status": status,
        "message": trimmed,
        "updated_at": datetime.utcnow().isoformat(),
    }


def _sync_seed_terms():
    global SEEDS_SYNCED
    if SEEDS_SYNCED:
        return
    with SEEDS_LOCK:
        if SEEDS_SYNCED:
            return
        for term in SEED_TERMS:
            db.upsert_term(
                term["term"],
                source="seed",
                audience=term["audience"],
                intent=term["intent"],
            )
        SEEDS_SYNCED = True


def _run_terms(term_ids):
    with RUN_LOCK:
        db.init_db()
        term_rows = db.get_terms_by_ids(term_ids)
        term_map = {row["id"]: row for row in term_rows}
        missing_ids = [term_id for term_id in term_ids if term_id not in term_map]
        for term_id in missing_ids:
            _set_run_status(term_id, "error", "Term not found")
        ordered_terms = [term_map[term_id] for term_id in term_ids if term_id in term_map]
        if not ordered_terms:
            return

        try:
            pytrends = pullers.get_pytrends()
        except Exception as e:
            for term_id in term_ids:
                _set_run_status(term_id, "error", f"pytrends init failed: {e}")
            return

        client = None
        try:
            client = pullers.get_google_ads_client()
        except Exception:
            pass

        for term_row in ordered_terms:
            term_id = term_row["id"]
            _set_run_status(term_id, "running")
            try:
                pullers.pull_trends_for_terms([term_row], pytrends=pytrends)
            except Exception as e:
                _set_run_status(term_id, "error", f"Trends failed: {e}")
                continue
            if client:
                try:
                    pullers.pull_keyword_metrics_for_terms([term_row], client=client)
                except Exception:
                    pass
            _set_run_status(term_id, "done")


def _escape_attr(value):
    if value is None:
        return ""
    return str(value).replace("&", "&amp;").replace('"', "&quot;")


def _sparkline_svg(series, direction):
    """Render an inline SVG sparkline. Always renders — shows flat line if no data."""
    w, h = 120, 28
    padding = 2
    if not series or len(series) < 2:
        # No data: render a dim dashed flat line
        mid = h / 2
        return (
            f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="vertical-align:middle">'
            f'<line x1="{padding}" y1="{mid}" x2="{w - padding}" y2="{mid}" '
            f'stroke="#333" stroke-width="1" stroke-dasharray="4,3" />'
            f'</svg>'
        )
    max_val = max(series) or 1
    n = len(series)
    step_x = (w - padding * 2) / (n - 1)
    points = []
    for i, v in enumerate(series):
        x = padding + i * step_x
        y = h - padding - ((v / max_val) * (h - padding * 2))
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)
    colors = {"rising": "#4ade80", "falling": "#f87171", "flat": "#888", "too_sparse": "#555"}
    color = colors.get(direction, "#555")
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="vertical-align:middle">'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5" />'
        f'</svg>'
    )


@app.get("/prototype", response_class=FileResponse)
def prototype():
    return STATIC_DIR / "prototype.html"


@app.get("/", response_class=HTMLResponse)
def dashboard():
    rows, discovered = fetch_dashboard_data()

    # Check if ANY row has Ads data — hide those columns entirely if not
    has_ads_data = any(r["avg_monthly_searches"] is not None for r in rows)

    # Build rows with parsed series and confidence score for sorting
    processed = []
    for r in rows:
        series = _parse_series(r["weekly_series"])
        interest_text, interest_tip = interest_label(r["avg_interest"])
        trend_text, trend_class, trend_tip = trend_label(r, series)
        signal_text, signal_class, confidence, signal_tip = signal_label(r, series)
        sparkline = _sparkline_svg(series, r["trend_direction"])
        processed.append((r, series, interest_text, interest_tip, trend_text,
                          trend_class, trend_tip, signal_text, signal_class,
                          confidence, signal_tip, sparkline))

    # Sort: high confidence signals first, then by confidence score desc
    processed.sort(key=lambda x: -x[9])

    table_rows = ""
    for (r, series, interest_text, interest_tip, trend_text, trend_class,
         trend_tip, signal_text, signal_class, confidence, signal_tip, sparkline) in processed:
        status = RUN_STATUS.get(r["id"], {})
        status_text = status.get("status", "-")
        status_message = _escape_attr(status.get("message", ""))
        status_title = f' title="{status_message}"' if status_message else ""
        audience = r["audience"] or "unknown"
        intent = r["intent"] or "unknown"
        term_attr = _escape_attr(r["term"])
        signal_attr = _escape_attr(signal_text)
        trend_attr = _escape_attr(r["trend_direction"] or "")

        ads_cells = ""
        if has_ads_data:
            cpc_low = f"${r['low_top_of_page_bid_micros'] / 1_000_000:.2f}" if r['low_top_of_page_bid_micros'] else '-'
            cpc_high = f"${r['high_top_of_page_bid_micros'] / 1_000_000:.2f}" if r['high_top_of_page_bid_micros'] else '-'
            ad_cost = f"{cpc_low} - {cpc_high}" if cpc_low != '-' else '-'
            searches = f"{r['avg_monthly_searches']:,}" if r['avg_monthly_searches'] is not None else '-'
            ads_cells = f"<td>{searches}</td><td>{ad_cost}</td>"

        table_rows += f"""
        <tr data-term-id="{r['id']}" data-term="{term_attr}" data-audience="{audience}"
            data-intent="{intent}" data-flag="{signal_attr}"
            data-trend="{trend_attr}">
            <td><input type="checkbox" class="row-select" data-term-id="{r['id']}"></td>
            <td>{r['term']}</td>
            <td>{sparkline}</td>
            <td title="{_escape_attr(interest_tip)}">{interest_text}</td>
            <td class="{trend_class}" title="{_escape_attr(trend_tip)}">{trend_text}</td>
            {ads_cells}
            <td class="{signal_class}" title="{_escape_attr(signal_tip)}">{signal_text}</td>
            <td class="run-status" data-term-id="{r['id']}"{status_title}>{status_text}</td>
            <td><button class="btn run-now" data-term-id="{r['id']}">Run</button></td>
            <td class="muted">{(r['pulled_at'] or '-')[:10]}</td>
        </tr>
        """

    discovered_rows = ""
    for d in discovered:
        raw_val = d['value']
        if str(raw_val).lower() == "breakout":
            growth = "Brand new"
            growth_class = "signal-breakout"
            growth_tip = "This keyword went from near-zero to notable searches — completely new demand"
        else:
            try:
                pct = int(raw_val)
                if pct >= 500:
                    growth = "Surging"
                    growth_class = "signal-breakout"
                    growth_tip = f"Up {pct}% — massive increase in searches"
                elif pct >= 200:
                    growth = "Fast growing"
                    growth_class = "signal-opportunity"
                    growth_tip = f"Up {pct}% — strong growth"
                else:
                    growth = "Growing"
                    growth_class = "trend-rising"
                    growth_tip = f"Up {pct}%"
            except (ValueError, TypeError):
                growth = str(raw_val)
                growth_class = "muted"
                growth_tip = ""
        tip_attr = f' title="{_escape_attr(growth_tip)}"' if growth_tip else ""
        discovered_rows += f"""
        <tr>
            <td>{d['query_text']}</td>
            <td class="{growth_class}"{tip_attr}>{growth}</td>
            <td class="muted">{d['pulled_at'][:10]}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <title>Niche Finance Keyword Dashboard</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #111; color: #ddd; padding: 2rem; }}
            h1 {{ font-size: 1.3rem; font-weight: 600; }}
            h2 {{ font-size: 1rem; margin-top: 2.5rem; color: #999; }}
            .controls {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 1rem 0 0.8rem; }}
            .controls input, .controls select {{ background: #151515; color: #ddd; border: 1px solid #333; padding: 6px 8px; border-radius: 6px; }}
            .btn {{ background: #1f2937; color: #ddd; border: 1px solid #2f3847; padding: 6px 10px; border-radius: 6px; cursor: pointer; }}
            .btn:hover {{ background: #273246; }}
            .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .small {{ font-size: 0.8rem; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
            th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #333; font-size: 0.9rem; }}
            th {{ color: #888; font-weight: 500; text-transform: uppercase; font-size: 0.75rem; }}
            .muted {{ color: #666; }}
            .signal-opportunity {{ color: #4ade80; font-weight: 600; }}
            .signal-opportunity-low {{ color: #a3e635; }}
            .signal-breakout {{ color: #facc15; font-weight: 600; }}
            .signal-quiet {{ color: #60a5fa; }}
            .signal-waiting {{ color: #555; }}
            .signal-popular {{ color: #f97316; }}
            .signal-established {{ color: #999; }}
            .trend-rising {{ color: #4ade80; }}
            .trend-falling {{ color: #f87171; }}
            .trend-flat {{ color: #999; }}
            td[title] {{ cursor: help; }}
        </style>
    </head>
    <body>
        <h1>Niche Finance Keyword Dashboard</h1>
        <p class="muted">Hover over any coloured cell for an explanation. Region: Australia.</p>
        <div class="controls">
            <input id="search" type="search" placeholder="Search terms (fuzzy)">
            <select id="filter-audience">
                <option value="all">All audiences</option>
                <option value="commercial">Commercial</option>
                <option value="consumer">Consumer</option>
                <option value="unknown">Unknown</option>
            </select>
            <select id="filter-intent">
                <option value="all">All intents</option>
                <option value="product">Product</option>
                <option value="problem">Problem</option>
                <option value="unknown">Unknown</option>
            </select>
            <select id="filter-trend">
                <option value="all">All trends</option>
                <option value="rising">Rising</option>
                <option value="falling">Falling</option>
                <option value="flat">Steady</option>
                <option value="too_sparse">Too sparse</option>
                <option value="insufficient_data">No data</option>
            </select>
            <select id="filter-flag">
                <option value="all">All signals</option>
                <option value="Good opportunity">Good opportunity</option>
                <option value="Possible opportunity">Possible opportunity</option>
                <option value="Breakout">Breakout</option>
                <option value="Popular + rising">Popular + rising</option>
                <option value="Established">Established</option>
                <option value="Quiet niche">Quiet niche</option>
                <option value="Very quiet">Very quiet</option>
                <option value="Not enough data">Not enough data</option>
                <option value="Waiting for data">Waiting for data</option>
            </select>
            <button class="btn" id="select-filtered">Select filtered</button>
            <button class="btn" id="clear-selection">Clear selection</button>
            <button class="btn" id="run-selected">Run now (selected)</button>
        </div>
        <div class="muted small" id="selection-count">0 selected</div>
        <table>
            <tr>
                <th></th><th>Term</th><th>12 months</th>
                <th>Interest</th><th>Trend</th>
                {"<th>Searches/mo</th><th>Ad Cost</th>" if has_ads_data else ""}
                <th>Signal</th><th>Status</th><th></th><th>Updated</th>
            </tr>
            {table_rows if table_rows else '<tr><td colspan="10" class="muted">No data yet. Run pull_trends.py.</td></tr>'}
        </table>

        <h2>Auto-discovered trending keywords</h2>
        <p class="muted small">New keywords Google flagged as rising or brand new, related to your tracked terms. Added automatically for future tracking.</p>
        <table>
            <tr><th>Keyword</th><th>Growth</th><th>Found</th></tr>
            {discovered_rows if discovered_rows else '<tr><td colspan="3" class="muted">None yet.</td></tr>'}
        </table>
        <script>
            const rows = Array.from(document.querySelectorAll("table tr[data-term-id]"));
            const searchInput = document.getElementById("search");
            const filterAudience = document.getElementById("filter-audience");
            const filterIntent = document.getElementById("filter-intent");
            const filterTrend = document.getElementById("filter-trend");
            const filterFlag = document.getElementById("filter-flag");
            const selectFilteredButton = document.getElementById("select-filtered");
            const clearSelectionButton = document.getElementById("clear-selection");
            const runSelectedButton = document.getElementById("run-selected");
            const selectionCount = document.getElementById("selection-count");

            const scoreMatch = (text, query) => {{
                if (!query) return 1;
                let score = 0;
                let t = 0;
                let q = 0;
                let streak = 0;
                while (t < text.length && q < query.length) {{
                    if (text[t] === query[q]) {{
                        streak += 1;
                        score += 1 + streak * 0.5;
                        q += 1;
                    }} else {{
                        streak = 0;
                    }}
                    t += 1;
                }}
                return q === query.length ? score : 0;
            }};

            const updateSelectionCount = () => {{
                const selected = document.querySelectorAll(".row-select:checked").length;
                selectionCount.textContent = `${{selected}} selected`;
            }};

            const applyFilters = () => {{
                const query = searchInput.value.trim().toLowerCase();
                const audience = filterAudience.value;
                const intent = filterIntent.value;
                const trend = filterTrend.value;
                const flag = filterFlag.value;

                rows.forEach((row) => {{
                    const term = row.dataset.term || "";
                    const rowAudience = row.dataset.audience || "unknown";
                    const rowIntent = row.dataset.intent || "unknown";
                    const rowTrend = row.dataset.trend || "";
                    const rowFlag = row.dataset.flag || "";
                    const matchesQuery = scoreMatch(term.toLowerCase(), query) > 0;
                    const matchesAudience = audience === "all" || rowAudience === audience;
                    const matchesIntent = intent === "all" || rowIntent === intent;
                    const matchesTrend = trend === "all" || rowTrend === trend;
                    const matchesFlag = flag === "all" || rowFlag === flag;
                    row.style.display = matchesQuery && matchesAudience && matchesIntent && matchesTrend && matchesFlag ? "" : "none";
                }});
            }};

            const selectFiltered = () => {{
                rows.forEach((row) => {{
                    if (row.style.display === "none") return;
                    const checkbox = row.querySelector(".row-select");
                    if (checkbox) checkbox.checked = true;
                }});
                updateSelectionCount();
            }};

            const clearSelection = () => {{
                document.querySelectorAll(".row-select").forEach((box) => {{
                    box.checked = false;
                }});
                updateSelectionCount();
            }};

            const runSelected = async () => {{
                const selectedIds = Array.from(document.querySelectorAll(".row-select:checked"))
                    .map((el) => Number(el.dataset.termId))
                    .filter((id) => Number.isFinite(id));
                if (!selectedIds.length) {{
                    alert("Select at least one term.");
                    return;
                }}
                runSelectedButton.disabled = true;
                const response = await fetch("/api/run-terms", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{ term_ids: selectedIds }}),
                }});
                if (!response.ok) {{
                    alert("Run now failed.");
                }}
                runSelectedButton.disabled = false;
                refreshStatuses();
            }};

            const refreshStatuses = async () => {{
                const response = await fetch("/api/run-status");
                if (!response.ok) return;
                const data = await response.json();
                document.querySelectorAll(".run-status").forEach((cell) => {{
                    const termId = cell.dataset.termId;
                    const status = data.statuses[String(termId)];
                    if (!status) {{
                        cell.textContent = "-";
                        cell.removeAttribute("title");
                        return;
                    }}
                    cell.textContent = status.status;
                    if (status.message) {{
                        cell.setAttribute("title", status.message);
                    }} else {{
                        cell.removeAttribute("title");
                    }}
                }});
            }};

            document.querySelectorAll(".run-now").forEach((button) => {{
                button.addEventListener("click", async () => {{
                    const termId = Number(button.dataset.termId);
                    button.disabled = true;
                    const response = await fetch("/api/run-term", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ term_id: termId }}),
                    }});
                    if (!response.ok) {{
                        alert("Run now failed.");
                    }}
                    button.disabled = false;
                    refreshStatuses();
                }});
            }});

            searchInput.addEventListener("input", applyFilters);
            filterAudience.addEventListener("change", applyFilters);
            filterIntent.addEventListener("change", applyFilters);
            filterTrend.addEventListener("change", applyFilters);
            filterFlag.addEventListener("change", applyFilters);
            selectFilteredButton.addEventListener("click", selectFiltered);
            clearSelectionButton.addEventListener("click", clearSelection);
            runSelectedButton.addEventListener("click", runSelected);
            document.querySelectorAll(".row-select").forEach((box) => {{
                box.addEventListener("change", updateSelectionCount);
            }});

            applyFilters();
            updateSelectionCount();
            refreshStatuses();
            setInterval(refreshStatuses, 15000);
        </script>
    </body>
    </html>
    """
    return html


@app.post("/api/run-term")
def api_run_term(request: RunTermRequest, background_tasks: BackgroundTasks):
    term = db.get_term(request.term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    _set_run_status(request.term_id, "queued")
    background_tasks.add_task(_run_terms, [request.term_id])
    return {"status": "queued"}


@app.post("/api/run-terms")
def api_run_terms(request: RunTermsRequest, background_tasks: BackgroundTasks):
    term_ids = [term_id for term_id in request.term_ids if isinstance(term_id, int)]
    if not term_ids:
        raise HTTPException(status_code=400, detail="No terms provided")
    for term_id in term_ids:
        _set_run_status(term_id, "queued")
    background_tasks.add_task(_run_terms, term_ids)
    return {"status": "queued", "count": len(term_ids)}


@app.get("/api/run-status")
def api_run_status():
    return {"statuses": RUN_STATUS}


@app.get("/api/terms")
def api_terms():
    rows, _ = fetch_dashboard_data()
    return [dict(r) for r in rows]
