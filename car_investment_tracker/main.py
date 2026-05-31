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
from car_investment_tracker.services.market_metrics import calculate_volatility_metrics
from car_investment_tracker.services.market_comparables import get_market_comparables
from car_investment_tracker.services.ownership_costs import calculate_ownership_costs
from car_investment_tracker.services.spec_adjustments import calculate_spec_adjustments, adjust_prices_for_specs
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
    transmission: str = Query(default="Automatic"),
    trim_level: str = Query(default="Standard"),
    condition: str = Query(default="Average"),
    mileage_bracket: str = Query(default="Normal"),
):
    _validate_vehicle_params(brand, model, year)
    historical = get_historical_prices(brand, model, year)
    listings = get_current_listings(brand, model, year)
    sentiment = get_sentiment_score(brand, model, year)

    if not historical or not listings:
        raise HTTPException(status_code=404, detail="Insufficient data for prediction")

    # Apply spec adjustments to historical prices
    adjusted_historical = adjust_prices_for_specs(
        [point.average_price for point in historical],
        transmission=transmission,
        trim_level=trim_level,
        condition=condition,
        mileage_bracket=mileage_bracket,
    )
    
    listing_avg = sum(item.price for item in listings) / len(listings)
    forecast, explanation = predict_prices(
        historical_prices=adjusted_historical,
        listing_avg=listing_avg,
        sentiment_score=float(sentiment["score"]),
    )
    
    return {
        "forecast": forecast,
        "explanation": explanation,
        "specs_applied": {
            "transmission": transmission,
            "trim_level": trim_level,
            "condition": condition,
            "mileage_bracket": mileage_bracket,
        }
    }


@app.get("/volatility-index")
def volatility_index(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Get auction volatility metrics for the vehicle."""
    _validate_vehicle_params(brand, model, year)
    historical = get_historical_prices(brand, model, year)
    
    if not historical:
        raise HTTPException(status_code=404, detail="Insufficient data for volatility analysis")
    
    prices = [point.average_price for point in historical]
    metrics = calculate_volatility_metrics(prices)
    
    return metrics


@app.get("/market-comparables")
def market_comparables(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Get recent comparable sales for the vehicle."""
    _validate_vehicle_params(brand, model, year)
    comparables = get_market_comparables(brand, model, year)
    
    if not comparables:
        raise HTTPException(status_code=404, detail="No comparable sales found")
    
    return {
        "comparables": comparables,
        "query": {"brand": brand, "model": model, "year": year},
    }


@app.get("/ownership-costs")
def ownership_costs(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    vehicle_price: float = Query(gt=0),
):
    """Calculate total cost of ownership."""
    _validate_vehicle_params(brand, model, year)
    
    costs = calculate_ownership_costs(
        vehicle_price=vehicle_price,
        vehicle_brand=brand,
        vehicle_year=year,
    )
    
    return costs


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
    transmission: str = Query(default="Automatic"),
    trim_level: str = Query(default="Standard"),
    condition: str = Query(default="Average"),
    mileage_bracket: str = Query(default="Normal"),
    vehicle_price: float = Query(default=None),
):
    _validate_vehicle_params(brand, model, year)
    try:
        historical = get_historical_prices(brand, model, year)
        listings = get_current_listings(brand, model, year)
        sentiment = get_sentiment_score(brand, model, year)
        undervalued = find_undervalued_listings(listings)
        
        if not historical or not listings:
            raise HTTPException(status_code=404, detail="Insufficient data for analysis")
        
        # Apply spec adjustments
        adjusted_historical = adjust_prices_for_specs(
            [point.average_price for point in historical],
            transmission=transmission,
            trim_level=trim_level,
            condition=condition,
            mileage_bracket=mileage_bracket,
        )
        
        listing_avg = sum(item.price for item in listings) / len(listings)
        forecast, explanation = predict_prices(
            historical_prices=adjusted_historical,
            listing_avg=listing_avg,
            sentiment_score=float(sentiment["score"]),
        )
        
        # Calculate volatility metrics
        volatility = calculate_volatility_metrics([point.average_price for point in historical])
        
        # Get market comparables
        comparables_data = get_market_comparables(brand, model, year)
        
        # Calculate ownership costs if price provided
        ownership = None
        if vehicle_price and vehicle_price > 0:
            ownership = calculate_ownership_costs(
                vehicle_price=vehicle_price,
                vehicle_brand=brand,
                vehicle_year=year,
            )
        
        # Spec adjustments info
        spec_adjustments_info = calculate_spec_adjustments(
            base_price=listing_avg,
            transmission=transmission,
            trim_level=trim_level,
            condition=condition,
            mileage_bracket=mileage_bracket,
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
        data_consistency="Consistent: historical prices inflation-adjusted; predictions protected against unrealistic spikes via ±15% sentiment clamping and price bounds",
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
        "volatility_metrics": volatility,
        "market_comparables": comparables_data,
        "spec_adjustments": spec_adjustments_info,
        "ownership_costs": ownership,
        "data_quality": data_quality,
        "data_sources": {
            "historical": "Market sales aggregators / fallback model (all prices inflation-adjusted to current year GBP)",
            "listings": "Marketplace APIs where available; compliant scraping where permitted (current market prices)",
            "sentiment": f"Forums, Reddit, owner communities, and review sites (weighted analysis of {sentiment['mentions_analyzed']} mentions)",
        },
        "methodology": {
            "forecast_model": "Linear regression with momentum smoothing",
            "spike_prevention": "Predicted prices constrained between -30% and +35% of baseline to prevent unrealistic jumps",
            "inflation_adjustment": "All historical data converted to current year GBP for fair long-term comparison",
            "sentiment_impact": "Sentiment score (0-5) adjusted to ±15% multiplier on forecast (clamped for stability)",
            "confidence_intervals": "±10% bands around predictions to show forecast uncertainty",
            "spec_adjustments": "Prices adjusted for transmission, trim level, condition, and mileage bracket",
        },
    }
