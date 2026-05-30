from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from car_investment_tracker.services.current_listings import get_current_listings
from car_investment_tracker.services.historical_data import get_historical_prices
from car_investment_tracker.services.listing_evaluation import find_undervalued_listings
from car_investment_tracker.services.prediction import predict_prices
from car_investment_tracker.services.sentiment import get_sentiment_score

logger = logging.getLogger(__name__)

app = FastAPI(title="Investment Car Tracker", version="1.0.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/historical-prices")
def historical_prices(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    return get_historical_prices(brand, model, year)


@app.get("/current-listings")
def current_listings(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    return get_current_listings(brand, model, year)


@app.get("/sentiment-score")
def sentiment_score(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    return get_sentiment_score(brand, model, year)


@app.get("/prediction")
def prediction(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    historical = get_historical_prices(brand, model, year)
    listings = get_current_listings(brand, model, year)
    sentiment = get_sentiment_score(brand, model, year)

    if not historical or not listings:
        raise HTTPException(status_code=404, detail="Insufficient data for prediction")

    listing_avg = sum(item.price for item in listings) / len(listings)
    result = predict_prices(
        historical_prices=[point.average_price for point in historical],
        listing_avg=listing_avg,
        sentiment_score=float(sentiment["score"]),
    )
    return result


@app.get("/undervalued-listings")
def undervalued_listings(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    listings = get_current_listings(brand, model, year)
    return find_undervalued_listings(listings)


@app.get("/analysis")
def analysis(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    try:
        historical = get_historical_prices(brand, model, year)
        listings = get_current_listings(brand, model, year)
        sentiment = get_sentiment_score(brand, model, year)
        undervalued = find_undervalued_listings(listings)
        if not historical or not listings:
            raise HTTPException(status_code=404, detail="Insufficient data for analysis")
        listing_avg = sum(item.price for item in listings) / len(listings)
        forecast = predict_prices(
            historical_prices=[point.average_price for point in historical],
            listing_avg=listing_avg,
            sentiment_score=float(sentiment["score"]),
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Analysis failed for %s %s %s", brand, model, year)
        raise HTTPException(status_code=500, detail="Unable to complete analysis: processing_error") from exc

    return {
        "query": {"brand": brand, "model": model, "year": year},
        "sentiment": sentiment,
        "historical_prices": historical,
        "prediction": forecast,
        "current_listing_average": round(listing_avg, 2),
        "undervalued_listings": undervalued,
        "data_sources": {
            "historical": "Market sales aggregators / fallback model",
            "listings": "Marketplace APIs where available; compliant scraping where permitted",
            "sentiment": "Forums, Reddit, owner communities, and review sites",
        },
    }
