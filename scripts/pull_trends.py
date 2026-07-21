"""
Pulls Google Trends data for all active terms, records interest snapshots,
and discovers related/rising queries as new candidate terms.

Run this on a schedule (weekly recommended, monthly minimum).
Uses pytrends, an unofficial wrapper. No API key needed, but Google
rate-limits aggressively, so this script sleeps between calls and
should not be run more than once a day.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import db
from app import pullers
from app.seed_terms import SEED_TERMS


def main():
    db.init_db()

    # Ensure all seed terms exist in DB
    for term in SEED_TERMS:
        db.upsert_term(
            term["term"],
            source="seed",
            audience=term["audience"],
            intent=term["intent"],
        )

    terms = db.get_active_terms()
    print(f"Pulling trends for {len(terms)} active terms...")

    try:
        pytrends = pullers.get_pytrends()
        pullers.pull_trends_for_terms(terms, pytrends=pytrends)
    except Exception as e:
        print(f"Trends pull failed: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
