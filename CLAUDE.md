# Google Terms Arbitrage

## Project
FastAPI dashboard that tracks Australian finance keyword opportunities using Google Trends and Google Ads API data.

## Structure
- `app/main.py` — FastAPI app, server-rendered dashboard + API endpoints
- `app/pullers.py` — Google Trends (pytrends) and Google Ads API data pullers
- `app/db.py` — SQLite database layer (`data/keywords.db`)
- `app/seed_terms.py` — seed keyword list
- `app/static/` — prototype UI (HTML/CSS/JS)
- `scripts/` — standalone pull scripts and OAuth token helper

## Secrets
Stored in 1Password. Vault: `google-terms-arbitrage`, item: `Google Ads`.

| Env var | 1Password reference |
|---|---|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | `op://google-terms-arbitrage/Google Ads/developer_token` |
| `GOOGLE_ADS_CLIENT_ID` | `op://google-terms-arbitrage/Google Ads/client_id` |
| `GOOGLE_ADS_CLIENT_SECRET` | `op://google-terms-arbitrage/Google Ads/client_secret` |
| `GOOGLE_ADS_REFRESH_TOKEN` | `op://google-terms-arbitrage/Google Ads/refresh_token` |
| `GOOGLE_ADS_CUSTOMER_ID` | `op://google-terms-arbitrage/Google Ads/customer_id` |

References are defined in `.env.tpl`. Never put real values in committed files.

## Running
```bash
# Production (secrets from 1Password)
op run --env-file=.env.tpl -- docker compose up -d

# Local dev (with .env file)
uvicorn app.main:app --reload --port 8420
```

## Repo
https://github.com/766jbcodes/google-terms-arbitrage
