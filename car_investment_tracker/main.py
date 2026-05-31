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
from car_investment_tracker.models import DataQualityIndicator

logger = logging.getLogger(__name__)

app = FastAPI(title="Investment Car Tracker", version="1.0.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def _validate_vehicle_params(brand: str, model: str, year: int) -> None:
    """Validate vehicle input parameters."""
    if not brand or not brand.strip():
        raise HTTPException(status_code=400, detail="Brand cannot be empty")
    if not model or not model.strip():
        raise HTTPException(status_code=400, detail="Model cannot be empty")
    current_year = 2026  # Approximate current year
    if year < 1900 or year > current_year:
        raise HTTPException(status_code=400, detail=f"Year must be between 1900 and {current_year}")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/historical-prices")
def historical_prices(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    _validate_vehicle_params(brand, model, year)
    return get_historical_prices(brand, model, year)


@app.get("/current-listings")
def current_listings(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    _validate_vehicle_params(brand, model, year)
    return get_current_listings(brand, model, year)


@app.get("/sentiment-score")
def sentiment_score(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    _validate_vehicle_params(brand, model, year)
    return get_sentiment_score(brand, model, year)


@app.get("/prediction")
def prediction(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    _validate_vehicle_params(brand, model, year)
    historical = get_historical_prices(brand, model, year)
    listings = get_current_listings(brand, model, year)
    sentiment = get_sentiment_score(brand, model, year)

    if not historical or not listings:
        raise HTTPException(status_code=404, detail="Insufficient data for prediction")

    listing_avg = sum(item.price for item in listings) / len(listings)
    forecast, explanation = predict_prices(
        historical_prices=[point.average_price for point in historical],
        listing_avg=listing_avg,
        sentiment_score=float(sentiment["score"]),
    )
    return {
        "forecast": forecast,
        "explanation": explanation,
    }


@app.get("/undervalued-listings")
def undervalued_listings(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    _validate_vehicle_params(brand, model, year)
    listings = get_current_listings(brand, model, year)
    return find_undervalued_listings(listings)


@app.get("/analysis")
def analysis(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    _validate_vehicle_params(brand, model, year)
    try:
        historical = get_historical_prices(brand, model, year)
        listings = get_current_listings(brand, model, year)
        sentiment = get_sentiment_score(brand, model, year)
        undervalued = find_undervalued_listings(listings)
        if not historical or not listings:
            raise HTTPException(status_code=404, detail="Insufficient data for analysis")
        listing_avg = sum(item.price for item in listings) / len(listings)
        forecast, explanation = predict_prices(
            historical_prices=[point.average_price for point in historical],
            listing_avg=listing_avg,
            sentiment_score=float(sentiment["score"]),
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Analysis failed for %s %s %s", brand, model, year)
        raise HTTPException(status_code=500, detail="Unable to complete analysis: processing_error") from exc

    # Determine confidence level based on data availability
    historical_count = len(historical)
    listings_count = len(listings)
    if historical_count >= 15 and listings_count >= 5:
        confidence = "High"
        consistency_note = "Comprehensive historical data and current market listings"
    elif historical_count >= 10 and listings_count >= 3:
        confidence = "Medium"
        consistency_note = "Adequate historical data with moderate market coverage"
    else:
        confidence = "Low"
        consistency_note = "Limited historical data or current market listings"

    data_quality = DataQualityIndicator(
        historical_data_points=historical_count,
        current_listings_count=listings_count,
        data_consistency="Consistent (historical inflation-adjusted, predictions spike-clamped)",
        confidence_level=confidence,
        notes=consistency_note,
    )

    return {
        "query": {"brand": brand, "model": model, "year": year},
        "summary": {
            "sentiment_score": f"{sentiment['score']}/5",
            "prediction_confidence": confidence,
            "price_trend": "Estimated based on historical data with sentiment adjustment",
        },
        "sentiment": sentiment,
        "historical_prices": historical,
        "prediction": forecast,
        "prediction_explanation": explanation,
        "current_listing_average": round(listing_avg, 2),
        "undervalued_listings": undervalued,
        "data_quality": data_quality,
        "data_sources": {
            "historical": "Market sales aggregators / fallback model (all prices inflation-adjusted to current year GBP)",
            "listings": "Marketplace APIs where available; compliant scraping where permitted (current market prices)",
            "sentiment": "Forums, Reddit, owner communities, and review sites (weighted analysis of {} mentions)".format(sentiment["mentions_analyzed"]),
        },
        "methodology": {
            "forecast_model": "Linear regression with momentum smoothing",
            "spike_prevention": "Predicted prices constrained within ±35% to ±30% of baseline to prevent unrealistic jumps",
            "inflation_adjustment": "All historical data converted to current year GBP for fair long-term comparison",
            "sentiment_impact": "Sentiment score (0-5) adjusted to ±15% multiplier on forecast (clamped for stability)",
        },
    }
