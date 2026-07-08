# semis-dashboard

Live semiconductor sector dashboard — sub-sector heatmaps, hyperscaler capex, and cycle indicators.

## Live sites

| Site | URL |
|---|---|
| **Semis Cockpit** (main dashboard) | https://aokunyade.github.io/semis-dashboard/ |
| **Retro UI** (experimental reskin, same data) | https://aokunyade.github.io/semis-dashboard/ui-retro.html |
| **AI Monetization Tracker** (sister site) | https://aokunyade.github.io/ai-monetization-tracker/ |

## Tabs

Table (prices / returns / valuation / 1M notes) · Heatmap (daily & YTD) · Cycle (composite cycle read + indicators) · FactSet (China/Asia exposure + supply chain) · TW Monthly (Taiwan monthly revenue, AI supply chain) · Case Studies (corrections + tech-cycle winners/losers)

## How it works

Data is refreshed weekdays after US close by GitHub Actions (`.github/workflows/refresh.yml`):

- `fetch_market_data.py` → `market.json` / `sectors.json` — prices, returns, valuation (Yahoo Finance)
- `fetch_cycle_data.py` → `cycle.json` — SOX/SPX, inventory days, capex YoY, FRED production, headlines
- `fetch_tw_monthlies.py` → `monthlies.json` — Taiwan monthly revenue (TWSE/MOPS, days 1–15)
- `fetch_casestudies.py` → `casestudies.json` — historical corrections & cycle studies (one-time, rebuilt only if missing)
- `fetch_deals.py` → `deals.json` — neocloud deal tracker
- `factset.json` / `notes.json` — updated on demand via FactSet MCP / manual notes

Not investment advice.
