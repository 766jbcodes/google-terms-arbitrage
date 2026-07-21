# Broker Signal

Broker Signal is an early Australian finance-demand intelligence product. It helps mortgage and finance brokers identify emerging borrower searches and turn a credible signal into a practical marketing test.

The repository currently contains:

- A working keyword-data dashboard backed by Google Trends and Google Ads data
- A clickable sample frontend for broker discovery interviews

## Broker interview prototype

The sample is designed for product conversations. Its opportunity scores and campaign details are realistic demonstration data, not live recommendations.

### Start it on Windows

Open PowerShell in this project folder and run:

```powershell
docker compose up -d --build
```

Then open:

- Sample frontend: `http://localhost:8420/prototype`
- Existing data dashboard: `http://localhost:8420`

To stop the application:

```powershell
docker compose down
```

### Suggested interview flow

1. Give the broker the opening page without explaining it. Ask what they believe the product does.
2. Ask which of the three opportunities they would investigate first and why.
3. Open an opportunity and review the score explanation and campaign brief.
4. Add or remove an opportunity from the watchlist.
5. Open the weekly briefing and ask whether they would read this by email.
6. Ask what evidence they would need before spending money on a campaign.
7. Ask whether this would be worth $20 per month and what would prevent them subscribing.

Record observed behaviour separately from feature requests. A feature request is strongest when it is connected to a real task the broker already performs.

## What the data service does

- Pulls Australian Google Trends interest for a curated finance term list
- Flags rising, established, sparse and breakout search patterns
- Retrieves search-volume and estimated advertising-cost data from Google Ads when configured
- Discovers related rising searches for future tracking
- Runs scheduled pulls through Docker

## Important data limitations

- Google Trends values are relative scores from 0–100, not absolute search demand.
- `pytrends` is an unofficial Google Trends wrapper and may break when Google changes its service.
- Google Ads data requires an approved Ads account and developer token.
- Narrow regional data can be unreliable for low-volume searches.
- The product provides market intelligence, not credit advice, legal advice or a compliance determination.

## Maintaining tracked terms

Tracked seed terms are in `app/seed_terms.py`. After changing them, restart the data puller from PowerShell:

```powershell
docker compose restart puller
```

New breakout searches discovered by the puller are added automatically.
