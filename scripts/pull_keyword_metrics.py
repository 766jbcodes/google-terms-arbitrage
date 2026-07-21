"""
Pulls keyword metrics from Google Ads Keyword Planner (KeywordPlanIdeaService).
Returns actual monthly search volume, CPC bids, and competition for tracked terms.

Requires Basic Access developer token (test tokens won't return real data).
Run weekly alongside pull_trends.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import db
from app import pullers
from app.seed_terms import SEED_TERMS


def main():
    db.init_db()

    for term in SEED_TERMS:
        db.upsert_term(
            term["term"],
            source="seed",
            audience=term["audience"],
            intent=term["intent"],
        )

    terms = db.get_active_terms()
    print(f"Pulling keyword metrics for {len(terms)} terms...")

    try:
        client = pullers.get_google_ads_client()
        pullers.pull_keyword_metrics_for_terms(terms, client=client)
    except Exception as e:
        print(f"Keyword metrics pull failed: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
