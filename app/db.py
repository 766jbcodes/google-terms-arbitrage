import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "keywords.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL DEFAULT 'seed',  -- 'seed' or 'discovered'
    active INTEGER NOT NULL DEFAULT 1,
    first_seen TEXT NOT NULL,
    audience TEXT NOT NULL DEFAULT 'unknown',  -- 'commercial', 'consumer', 'unknown'
    intent TEXT NOT NULL DEFAULT 'unknown'     -- 'product', 'problem', 'unknown'
);

CREATE TABLE IF NOT EXISTS trend_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    pulled_at TEXT NOT NULL,
    avg_interest REAL,       -- 0-100 relative interest, avg over window
    latest_interest REAL,    -- most recent data point
    trend_direction TEXT,    -- 'rising', 'falling', 'flat', 'insufficient_data'
    is_breakout INTEGER DEFAULT 0,  -- came from a "Breakout" related query
    weekly_series TEXT,              -- JSON array of 52 weekly interest values
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

CREATE TABLE IF NOT EXISTS keyword_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    pulled_at TEXT NOT NULL,
    avg_monthly_searches INTEGER,
    competition TEXT,            -- 'LOW', 'MEDIUM', 'HIGH', 'UNSPECIFIED'
    competition_index INTEGER,   -- 0-100
    low_top_of_page_bid_micros INTEGER,
    high_top_of_page_bid_micros INTEGER,
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

CREATE TABLE IF NOT EXISTS related_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_term_id INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    query_type TEXT NOT NULL,   -- 'top' or 'rising'
    value TEXT,                  -- relative score or 'Breakout'
    pulled_at TEXT NOT NULL,
    promoted INTEGER DEFAULT 0,  -- 1 if added to terms table
    FOREIGN KEY (parent_term_id) REFERENCES terms(id)
);
"""

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    _ensure_terms_columns(conn)
    conn.commit()
    conn.close()


def _ensure_terms_columns(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(terms)").fetchall()}
    if "audience" not in columns:
        conn.execute("ALTER TABLE terms ADD COLUMN audience TEXT DEFAULT 'unknown'")
    if "intent" not in columns:
        conn.execute("ALTER TABLE terms ADD COLUMN intent TEXT DEFAULT 'unknown'")
    conn.execute("UPDATE terms SET audience = 'unknown' WHERE audience IS NULL")
    conn.execute("UPDATE terms SET intent = 'unknown' WHERE intent IS NULL")

    snap_columns = {row["name"] for row in conn.execute("PRAGMA table_info(trend_snapshots)").fetchall()}
    if "weekly_series" not in snap_columns:
        conn.execute("ALTER TABLE trend_snapshots ADD COLUMN weekly_series TEXT")


def upsert_term(term: str, source: str = "seed", audience: str = "unknown", intent: str = "unknown"):
    conn = get_conn()
    conn.execute(
        """INSERT INTO terms (term, source, first_seen, audience, intent)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(term) DO UPDATE SET
               source = CASE
                   WHEN terms.source = 'discovered' AND excluded.source = 'seed' THEN 'seed'
                   ELSE terms.source
               END,
               audience = CASE
                   WHEN terms.audience = 'unknown' THEN excluded.audience
                   ELSE terms.audience
               END,
               intent = CASE
                   WHEN terms.intent = 'unknown' THEN excluded.intent
                   ELSE terms.intent
               END
        """,
        (term, source, datetime.utcnow().isoformat(), audience, intent),
    )
    conn.commit()
    conn.close()

def get_active_terms():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM terms WHERE active = 1").fetchall()
    conn.close()
    return rows


def get_term(term_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM terms WHERE id = ?", (term_id,)).fetchone()
    conn.close()
    return row


def get_terms_by_ids(term_ids):
    if not term_ids:
        return []
    placeholders = ",".join("?" for _ in term_ids)
    conn = get_conn()
    rows = conn.execute(
        f"SELECT * FROM terms WHERE id IN ({placeholders})",
        term_ids,
    ).fetchall()
    conn.close()
    return rows

def record_snapshot(term_id, avg_interest, latest_interest, trend_direction, is_breakout=False, weekly_series=None):
    import json
    series_json = json.dumps(weekly_series) if weekly_series else None
    conn = get_conn()
    conn.execute(
        """INSERT INTO trend_snapshots
           (term_id, pulled_at, avg_interest, latest_interest, trend_direction, is_breakout, weekly_series)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (term_id, datetime.utcnow().isoformat(), avg_interest, latest_interest, trend_direction, int(is_breakout), series_json),
    )
    conn.commit()
    conn.close()

def record_keyword_metrics(term_id, avg_monthly_searches, competition, competition_index,
                           low_top_of_page_bid_micros, high_top_of_page_bid_micros):
    conn = get_conn()
    conn.execute(
        """INSERT INTO keyword_metrics
           (term_id, pulled_at, avg_monthly_searches, competition, competition_index,
            low_top_of_page_bid_micros, high_top_of_page_bid_micros)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (term_id, datetime.utcnow().isoformat(), avg_monthly_searches, competition,
         competition_index, low_top_of_page_bid_micros, high_top_of_page_bid_micros),
    )
    conn.commit()
    conn.close()

def record_related_query(parent_term_id, query_text, query_type, value):
    conn = get_conn()
    conn.execute(
        """INSERT INTO related_queries
           (parent_term_id, query_text, query_type, value, pulled_at)
           VALUES (?, ?, ?, ?, ?)""",
        (parent_term_id, query_text, query_type, str(value), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
