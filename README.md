# CarInvestmentTracker

Production-ready starter app for evaluating vehicle investment potential using modular services.

## Features
- Vehicle input: brand, model, year
- Full-life historical price trend generation (from the model year to today)
- Current listing aggregation from major UK marketplace categories
- Sentiment scoring (0-5) from automotive-community-style sources
- Price forecasting that blends historical data, listing averages, and sentiment
- Undervalued listing detection (clean title + below average listing price)
- Responsive web UI with line chart + undervalued listings table
- One-click JSON export of processed analysis payload
- Query caching to reduce repeated computation

## Backend architecture
`car_investment_tracker/services/`
- `historical_data.py` – historical sales ingestion/fallback modeling
- `current_listings.py` – marketplace aggregation, normalization, deduplication
- `sentiment.py` – sentiment ingestion + score mapping (0-5)
- `prediction.py` – regression-based forecasting pipeline
- `listing_evaluation.py` – undervalued listing filtering
- `cache.py` – TTL caching for repeated queries

## API endpoints
All endpoints accept query params: `brand`, `model`, `year`.

- `GET /historical-prices`
- `GET /current-listings`
- `GET /sentiment-score`
- `GET /prediction`
- `GET /undervalued-listings`
- `GET /analysis` (combined convenience endpoint)

## Data flow
1. User submits vehicle input.
2. Historical service returns the car's full-life normalized historical price points (from the model year to today).
3. Listings service combines UK marketplace sources, returns GBP listing prices, and deduplicates listings.
4. Sentiment service analyzes community-style mentions and maps sentiment to 0-5.
5. Prediction service applies regression over historical prices and blends listing averages + sentiment.
6. Evaluation service filters undervalued clean-title listings.
7. Frontend visualizes trend and prediction and exposes JSON download.

## Scraping/legal note
Use marketplace APIs where available. If scraping is enabled in production, enforce robots.txt and site terms compliance.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn car_investment_tracker.main:app --reload
```

## Test
```bash
pytest -q
```
