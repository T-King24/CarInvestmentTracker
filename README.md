# CarInvestmentTracker

App for evaluating vehicle investment potential using **real-world market data**.

> **No fabricated data.** Historical prices, current listings and sentiment are
> sourced from a configured external data provider. When no provider is
> configured (or a provider returns nothing for a vehicle), the app clearly
> reports the data as **unavailable** instead of generating synthetic numbers.

## Features
- Vehicle search by make, model, **variant/derivative** and year (Auto Trader-style taxonomy)
- Real historical **sold-price** trends with source metadata (source name, URL, sample size, confidence)
- Real current listings that link to the **exact advert detail page** (e.g. Auto Trader), deduplicated
- Price-outlook sentiment derived from **real news/forum/auction discussions**
- "Market Discussion Sources" panel linking to articles/threads about predicted pricing
- Brand-themed UI: selecting a make recolours the page to the brand colour (Ferrari red, Lamborghini yellow, ...)
- Data-availability transparency: every analysis states which data is real, partial or unavailable
- Price forecasting that anchors on sold prices and blends listing averages + sentiment
- One-click JSON export of the processed analysis payload
- Provider-aware TTL caching with fetch timestamps

## Backend architecture
`car_investment_tracker/services/`
- `providers/` - the real-data backbone:
  - `base.py` - `MarketDataProvider` protocol (`fetch_historical_prices`, `fetch_listings`, `fetch_discussions`)
  - `config.py` - reads provider configuration from environment variables
  - `null_provider.py` - default provider that returns nothing (-> "unavailable")
  - `http_provider.py` - generic HTTP/JSON provider for live feeds
  - `registry.py` - `get_market_provider` / `set_market_provider` / `reset_market_provider`
- `historical_data.py` - real sold-price ingestion (inflation-adjusted), no synthetic curves
- `current_listings.py` - real listing ingestion with exact URLs + dedupe
- `sentiment.py` - price-outlook sentiment derived from real discussions
- `sentiment_sources.py` - buckets real discussions into forums/auction/news/social
- `market_discussions.py` - real article/forum links about predicted pricing
- `market_comparables.py` - comparable **sold** transactions only
- `brand_themes.py` - per-brand UI colour map
- `prediction.py` - regression-based forecasting pipeline
- `listing_evaluation.py` - undervalued listing filtering
- `cache.py` - TTL caching for repeated queries

## Configuring a real data provider
By default the app runs with the `NullProvider` and reports all market data as
unavailable. To fetch real data, configure an HTTP/JSON provider via environment
variables:

| Variable | Purpose |
| --- | --- |
| `CIT_DATA_PROVIDER` | Set to `http` to enable the HTTP provider |
| `CIT_HISTORICAL_API_URL` | Endpoint returning historical sold-price points |
| `CIT_LISTINGS_API_URL` | Endpoint returning current listings |
| `CIT_DISCUSSIONS_API_URL` | Endpoint returning news/forum discussions |
| `CIT_DATA_API_KEY` | Optional bearer token sent as `Authorization` |
| `CIT_DATA_TIMEOUT` | Optional request timeout (seconds) |

Each endpoint receives `brand`, `model`, `year` and optional `variant` query
parameters and must return JSON in the shapes documented in
`services/providers/http_provider.py`. You can also plug in a custom provider in
code via `set_market_provider(...)`.

> **Legal note.** Use official/partner APIs or licensed datasets. Only scrape
> sites where their terms permit it, and enforce robots.txt and rate limits.

## API endpoints
Vehicle endpoints accept query params `brand`, `model`, `year` and optional `variant`.

- `GET /dropdown-makes`, `GET /dropdown-models`, `GET /dropdown-variants`, `GET /dropdown-years`
- `GET /brand-themes`
- `GET /historical-prices`
- `GET /current-listings`
- `GET /sentiment-score`
- `GET /sentiment-sources`
- `GET /market-discussions`
- `GET /market-comparables`
- `GET /prediction`
- `GET /undervalued-listings`
- `GET /analysis` (combined endpoint with `data_availability` transparency)

## Data flow
1. User selects make -> model -> variant -> year (taxonomy from the catalog).
2. The configured provider is queried for real sold prices, listings and discussions.
3. Historical sold prices are inflation-adjusted to current-year GBP.
4. Sentiment is computed from the real discussions (price-outlook focus).
5. Prediction anchors on sold prices and blends listing averages + sentiment.
6. The response includes a `data_availability` block describing what is real,
   partial or unavailable; nothing is fabricated to fill gaps.
7. The frontend recolours to the brand, shows availability badges, the
   discussions panel, and exposes a JSON download.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optional: configure a real data provider
export CIT_DATA_PROVIDER=http
export CIT_HISTORICAL_API_URL="https://your-feed/historical"
export CIT_LISTINGS_API_URL="https://your-feed/listings"
export CIT_DISCUSSIONS_API_URL="https://your-feed/discussions"
uvicorn car_investment_tracker.main:app --reload
```

## Test
```bash
pytest -q
```
