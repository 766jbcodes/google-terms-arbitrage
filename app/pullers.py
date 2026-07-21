import os
import statistics
import time

from dotenv import load_dotenv

from app import db

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
except ImportError:
    GoogleAdsClient = None
    GoogleAdsException = Exception

# Load .env for local dev; in production, secrets come from 1Password via `op run`
load_dotenv(db.DB_PATH.parent.parent / ".env", override=False)

GEO = "AU"
TIMEFRAME = "today 12-m"
SLEEP_BETWEEN_CALLS = 8

ADS_BATCH_SIZE = 20
ADS_LANGUAGE = "languageConstants/1000"
ADS_GEO = "geoTargetConstants/2036"


def get_pytrends():
    if TrendReq is None:
        raise RuntimeError("pytrends not installed")
    return TrendReq(hl="en-AU", tz=600)


def classify_trend(series):
    """Classify trend direction. Returns (direction, nonzero_weeks).
    direction: 'rising', 'falling', 'flat', 'too_sparse', 'insufficient_data'
    nonzero_weeks: how many of the 52 weeks had any search activity
    """
    if not series or len(series) < 4:
        return "insufficient_data", 0

    nonzero_weeks = sum(1 for v in series if v > 0)

    # Not enough real data points to claim any direction
    if nonzero_weeks < 8:
        return "too_sparse", nonzero_weeks

    first_half = series[: len(series) // 2]
    second_half = series[len(series) // 2 :]

    # Need activity in the second half too, not just legacy spikes
    second_half_nonzero = sum(1 for v in second_half if v > 0)
    if second_half_nonzero < 4:
        return "too_sparse", nonzero_weeks

    avg_first = statistics.mean(first_half) if first_half else 0
    avg_second = statistics.mean(second_half) if second_half else 0
    if avg_first == 0 and avg_second == 0:
        return "insufficient_data", nonzero_weeks
    delta = avg_second - avg_first
    if delta > avg_first * 0.15:
        return "rising", nonzero_weeks
    if delta < -avg_first * 0.15:
        return "falling", nonzero_weeks
    return "flat", nonzero_weeks


def pull_trends_for_term(pytrends, term_row):
    term_id = term_row["id"]
    term = term_row["term"]
    pytrends.build_payload([term], timeframe=TIMEFRAME, geo=GEO)

    interest_df = pytrends.interest_over_time()
    if not interest_df.empty and term in interest_df.columns:
        series = [int(v) for v in interest_df[term].tolist()]
        avg_interest = statistics.mean(series) if series else 0
        latest_interest = series[-1] if series else 0
        direction, _ = classify_trend(series)
    else:
        series = None
        avg_interest, latest_interest, direction = 0, 0, "insufficient_data"

    db.record_snapshot(term_id, avg_interest, latest_interest, direction, weekly_series=series)

    related = pytrends.related_queries()
    term_related = related.get(term, {})

    top_df = term_related.get("top")
    if top_df is not None:
        for _, row in top_df.iterrows():
            db.record_related_query(term_id, row["query"], "top", row["value"])

    rising_df = term_related.get("rising")
    is_any_breakout = False
    if rising_df is not None:
        for _, row in rising_df.iterrows():
            db.record_related_query(term_id, row["query"], "rising", row["value"])
            if str(row["value"]).lower() == "breakout":
                is_any_breakout = True
                db.upsert_term(row["query"], source="discovered", audience="unknown", intent="unknown")

    if is_any_breakout:
        db.record_snapshot(term_id, avg_interest, latest_interest, direction, is_breakout=True, weekly_series=series)

    time.sleep(SLEEP_BETWEEN_CALLS)


def pull_trends_for_terms(term_rows, pytrends=None):
    pytrends = pytrends or get_pytrends()
    for term_row in term_rows:
        pull_trends_for_term(pytrends, term_row)


def get_google_ads_client():
    if GoogleAdsClient is None:
        raise RuntimeError("google-ads not installed")
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def pull_ads_metrics(client, terms_batch):
    kp_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"]
    request.language = ADS_LANGUAGE
    request.geo_target_constants = [ADS_GEO]
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    request.keyword_seed.keywords.extend(terms_batch)

    results = {}
    try:
        response = kp_service.generate_keyword_ideas(request=request)
        for idea in response:
            keyword = idea.text
            metrics = idea.keyword_idea_metrics
            results[keyword.lower()] = {
                "avg_monthly_searches": metrics.avg_monthly_searches,
                "competition": metrics.competition.name,
                "competition_index": metrics.competition_index,
                "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros,
                "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros,
            }
    except GoogleAdsException as e:
        raise RuntimeError(f"Google Ads API error: {e.failure.errors[0].message}") from e
    except Exception as e:
        raise RuntimeError(f"Google Ads error: {e}") from e

    return results


def pull_keyword_metrics_for_terms(term_rows, client=None):
    if not term_rows:
        return
    client = client or get_google_ads_client()
    term_list = [(t["id"], t["term"]) for t in term_rows]

    for i in range(0, len(term_list), ADS_BATCH_SIZE):
        batch = term_list[i:i + ADS_BATCH_SIZE]
        batch_terms = [t[1] for t in batch]
        batch_map = {t[1].lower(): t[0] for t in batch}
        metrics = pull_ads_metrics(client, batch_terms)

        for term_str, term_id in batch_map.items():
            if term_str not in metrics:
                continue
            m = metrics[term_str]
            db.record_keyword_metrics(
                term_id=term_id,
                avg_monthly_searches=m["avg_monthly_searches"],
                competition=m["competition"],
                competition_index=m["competition_index"],
                low_top_of_page_bid_micros=m["low_top_of_page_bid_micros"],
                high_top_of_page_bid_micros=m["high_top_of_page_bid_micros"],
            )
