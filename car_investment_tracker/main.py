from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from car_investment_tracker.car_data import get_makes, get_models, get_variants, get_years
from car_investment_tracker.services.current_listings import get_current_listings
from car_investment_tracker.services.historical_data import get_historical_prices
from car_investment_tracker.services.listing_evaluation import find_undervalued_listings
from car_investment_tracker.services.prediction import predict_prices
from car_investment_tracker.services.sentiment import get_sentiment_score
from car_investment_tracker.services.market_metrics import calculate_volatility_metrics
from car_investment_tracker.services.market_comparables import get_market_comparables
from car_investment_tracker.services.market_discussions import get_market_discussions
from car_investment_tracker.services.ownership_costs import calculate_ownership_costs
from car_investment_tracker.services.spec_adjustments import calculate_spec_adjustments, adjust_prices_for_specs
from car_investment_tracker.services.market_events import get_market_events
from car_investment_tracker.services.sentiment_sources import get_sentiment_source_breakdown
from car_investment_tracker.services.scenario_simulator import calculate_scenario_adjustment, ScenarioInput, compare_scenarios
from car_investment_tracker.services.export_service import export_to_csv, export_investor_report
from car_investment_tracker.services.anomaly_detection import detect_listing_anomalies
from car_investment_tracker.services.macro_economics import get_macroeconomic_context, calculate_economic_price_adjustment
from car_investment_tracker.services.rarity_projection import calculate_rarity_projection
from car_investment_tracker.services.brand_themes import get_all_brand_themes, get_brand_theme
from car_investment_tracker.services.providers import get_market_provider
from car_investment_tracker.services.providers.config import load_config
from car_investment_tracker.models import DataAvailability, DataQualityIndicator

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


@app.get("/healthz")
def healthz() -> dict:
    """Liveness/readiness probe.

    Returns service status and whether a live market-data provider is
    configured. ``data_mode`` is ``"live"`` when an external provider is wired
    up via environment variables, otherwise ``"null"`` (catalog works, but
    market data is reported as unavailable rather than fabricated).
    """
    config = load_config()
    provider = get_market_provider()
    return {
        "status": "ok",
        "version": app.version,
        "data_mode": "live" if config.is_live else "null",
        "provider": getattr(provider, "name", provider.__class__.__name__),
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/dropdown-makes")
def dropdown_makes() -> list[str]:
    """Get all available car makes for dropdown selection."""
    return get_makes()


@app.get("/dropdown-models")
def dropdown_models(make: str = Query(min_length=1)) -> list[str]:
    """Get all available models for a given make."""
    models = get_models(make)
    if not models:
        raise HTTPException(status_code=404, detail=f"No models found for make: {make}")
    return models


@app.get("/dropdown-years")
def dropdown_years(make: str = Query(min_length=1), model: str = Query(min_length=1)) -> list[int]:
    """Get all available years for a given make and model."""
    years = get_years(make, model)
    if not years:
        raise HTTPException(status_code=404, detail=f"No years found for {make} {model}")
    return years


@app.get("/dropdown-variants")
def dropdown_variants(make: str = Query(min_length=1), model: str = Query(min_length=1)) -> list[str]:
    """Get all available variants/derivatives for a given make and model."""
    return get_variants(make, model)


@app.get("/brand-themes")
def brand_themes() -> dict:
    """Get the per-brand colour themes applied by the UI when a make is selected."""
    return get_all_brand_themes()


@app.get("/historical-prices")
def historical_prices(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
    inflation_adjusted: bool = Query(default=True, description="Return inflation-adjusted prices (default) or nominal"),
):
    _validate_vehicle_params(brand, model, year)
    prices = get_historical_prices(brand, model, year, variant)

    if not inflation_adjusted:
        # Return nominal prices instead
        return [{"year": p.year, "average_price": p.nominal_price} for p in prices]

    return prices


@app.get("/current-listings")
def current_listings(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
):
    _validate_vehicle_params(brand, model, year)
    return get_current_listings(brand, model, year, variant)


@app.get("/sentiment-score")
def sentiment_score(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
):
    _validate_vehicle_params(brand, model, year)
    return get_sentiment_score(brand, model, year, variant)


@app.get("/sentiment-sources")
def sentiment_sources(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
):
    """Get detailed sentiment breakdown by source (forums, auctions, news, social media)."""
    _validate_vehicle_params(brand, model, year)
    return get_sentiment_source_breakdown(brand, model, year, variant)


@app.get("/market-discussions")
def market_discussions(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
):
    """Get real news articles and forum threads discussing the car's pricing outlook."""
    _validate_vehicle_params(brand, model, year)
    return {
        "query": {"brand": brand, "model": model, "year": year, "variant": variant},
        "discussions": get_market_discussions(brand, model, year, variant),
    }


@app.get("/prediction")
def prediction(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
    transmission: str = Query(default="Automatic"),
    trim_level: str = Query(default="Standard"),
    condition: str = Query(default="Average"),
    mileage_bracket: str = Query(default="Normal"),
):
    _validate_vehicle_params(brand, model, year)
    historical = get_historical_prices(brand, model, year, variant)
    listings = get_current_listings(brand, model, year, variant)
    sentiment = get_sentiment_score(brand, model, year, variant)

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
    variant: str | None = Query(default=None),
):
    """Get recent comparable *sold* transactions for the vehicle.

    Returns an empty list when the provider exposes no real sold transactions,
    rather than fabricating comparable sales.
    """
    _validate_vehicle_params(brand, model, year)
    comparables = get_market_comparables(brand, model, year, variant)

    return {
        "comparables": comparables,
        "available": bool(comparables),
        "query": {"brand": brand, "model": model, "year": year, "variant": variant},
    }


@app.get("/market-events")
def market_events(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Get major market events affecting vehicle valuations."""
    _validate_vehicle_params(brand, model, year)
    start_year = 2026 - 20
    end_year = 2026
    events = get_market_events(brand, model, start_year, end_year)
    
    return {
        "events": events,
        "query": {"brand": brand, "model": model, "year": year},
        "time_range": {"start": start_year, "end": end_year},
    }


@app.post("/scenario-simulator")
def scenario_simulator(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    base_price: float = Query(gt=0, description="Current predicted price to simulate against"),
    scenarios: list[ScenarioInput] = None,
):
    """Simulate price changes based on what-if scenarios.
    
    Supports scenarios like:
    - Mileage changes (increase/decrease)
    - Condition improvements (restoration)
    - Market downturns
    - Storage premium
    """
    _validate_vehicle_params(brand, model, year)
    
    if not scenarios:
        # Default scenarios if none provided
        scenarios = [
            ScenarioInput(
                scenario_name="Condition Restoration",
                condition_improvement=2,
            ),
            ScenarioInput(
                scenario_name="5 Years Storage",
                storage_premium_years=5,
            ),
            ScenarioInput(
                scenario_name="Market Downturn 20%",
                market_downturn_pct=20,
            ),
        ]
    
    results = compare_scenarios(base_price, scenarios)
    
    return {
        "query": {"brand": brand, "model": model, "year": year},
        "base_price": round(base_price, 2),
        "scenarios": results,
        "best_case": results[0] if results else None,
        "worst_case": results[-1] if results else None,
    }


@app.get("/export/csv")
def export_csv(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Export analysis data to CSV format."""
    _validate_vehicle_params(brand, model, year)
    
    try:
        historical = get_historical_prices(brand, model, year)
        listings = get_current_listings(brand, model, year)
        sentiment = get_sentiment_score(brand, model, year)
        
        if not historical or not listings:
            raise HTTPException(status_code=404, detail="Insufficient data for export")
        
        listing_avg = sum(item.price for item in listings) / len(listings)
        forecast, _ = predict_prices(
            historical_prices=[point.average_price for point in historical],
            listing_avg=listing_avg,
            sentiment_score=float(sentiment["score"]),
        )
        
        csv_content = export_to_csv(
            brand=brand,
            model=model,
            year=year,
            historical_prices=[p.dict() for p in historical],
            predictions=[p.dict() for p in forecast],
            sentiment_score=float(sentiment["score"]),
            current_listing_avg=listing_avg,
        )
        
        return {
            "format": "csv",
            "filename": f"{brand}_{model}_{year}_analysis.csv",
            "data": csv_content,
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("CSV export failed")
        raise HTTPException(status_code=500, detail="Export failed") from exc


@app.get("/export/report")
def export_report(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Export formatted investor report."""
    _validate_vehicle_params(brand, model, year)
    
    try:
        # Get full analysis
        analysis_data = analysis(brand=brand, model=model, year=year)
        
        report_content = export_investor_report(
            brand=brand,
            model=model,
            year=year,
            analysis_data=analysis_data,
        )
        
        return {
            "format": "text",
            "filename": f"{brand}_{model}_{year}_investor_report.txt",
            "data": report_content,
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Report export failed")
        raise HTTPException(status_code=500, detail="Export failed") from exc


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


@app.get("/anomalies")
def anomalies(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Detect anomalous listings using statistical analysis.
    
    Returns listings ranked by anomaly score, identifying underpriced deals
    and overpriced outliers compared to market statistics.
    """
    _validate_vehicle_params(brand, model, year)
    
    listings = get_current_listings(brand, model, year)
    if not listings:
        raise HTTPException(status_code=404, detail="No listings found for analysis")
    
    # Get market price prediction for context
    historical = get_historical_prices(brand, model, year)
    sentiment = get_sentiment_score(brand, model, year)
    
    market_price = None
    if historical and listings:
        listing_avg = sum(item.price for item in listings) / len(listings)
        forecast, _ = predict_prices(
            historical_prices=[point.average_price for point in historical],
            listing_avg=listing_avg,
            sentiment_score=float(sentiment["score"]),
        )
        if forecast:
            market_price = forecast[0].predicted_price if forecast else None
    
    anomalies = detect_listing_anomalies(listings, market_price=market_price)
    
    return {
        "query": {"brand": brand, "model": model, "year": year},
        "market_price": market_price,
        "total_listings_analyzed": len(listings),
        "anomalies_detected": sum(1 for a in anomalies if a.is_anomaly),
        "anomalies": anomalies,
    }


@app.get("/macro-economic-context")
def macro_economic_context():
    """Get current macro-economic context and its impact on vehicle valuations.
    
    Returns economic indicators, sentiment analysis, and projections
    for how macro factors affect luxury vehicle pricing.
    """
    context = get_macroeconomic_context()
    return {
        "timestamp": "2026-05-31",
        "context": context,
        "interpretation": {
            "outlook": context.economic_outlook,
            "impact": context.impact_on_vehicle_prices,
            "sentiment": context.luxury_market_sentiment,
        },
    }


@app.post("/economic-price-adjustment")
def economic_price_adjustment(
    base_price: float = Query(gt=0, description="Base vehicle price"),
    gdp_growth: float = Query(default=None, description="GDP growth rate (%)"),
    unemployment_rate: float = Query(default=None, description="Unemployment rate (%)"),
    interest_rates: float = Query(default=None, description="Interest rates (%)"),
):
    """Calculate price adjustment based on macro-economic factors.
    
    Adjusts a base price according to current economic conditions
    (GDP growth, unemployment, interest rates).
    """
    result = calculate_economic_price_adjustment(
        base_price=base_price,
        gdp_growth=gdp_growth,
        unemployment_rate=unemployment_rate,
        interest_rates=interest_rates,
    )
    
    return result


@app.get("/rarity-projection")
def rarity_projection(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Project long-term rarity and scarcity of a vehicle.
    
    Estimates production volumes, survival rates, and future rarity scores
    to assess long-term value appreciation potential due to scarcity.
    """
    _validate_vehicle_params(brand, model, year)
    
    projection = calculate_rarity_projection(brand, model, year)
    
    return {
        "query": {"brand": brand, "model": model, "year": year},
        "projection": projection,
        "value_implications": {
            "current_rarity": f"{projection.rarity_score}/10",
            "expected_5yr": f"{projection.future_rarity_score_5yr}/10",
            "expected_10yr": f"{projection.future_rarity_score_10yr}/10",
            "rarity_driven_upside": "High" if projection.rarity_score >= 7 else "Medium" if projection.rarity_score >= 5 else "Low",
        },
    }



@app.get("/analysis")
def analysis(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
    variant: str | None = Query(default=None),
    transmission: str = Query(default="Automatic"),
    trim_level: str = Query(default="Standard"),
    condition: str = Query(default="Average"),
    mileage_bracket: str = Query(default="Normal"),
    vehicle_price: float = Query(default=None),
    inflation_adjusted: bool = Query(default=True),
):
    _validate_vehicle_params(brand, model, year)

    provider = get_market_provider()
    provider_name = getattr(provider, "name", "unconfigured")
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        historical = get_historical_prices(brand, model, year, variant)
        listings = get_current_listings(brand, model, year, variant)
        sentiment = get_sentiment_score(brand, model, year, variant)
        sentiment_breakdown = get_sentiment_source_breakdown(brand, model, year, variant)
        discussions = get_market_discussions(brand, model, year, variant)
        undervalued = find_undervalued_listings(listings)

        # Build data-availability transparency. Real data may be partially or
        # wholly unavailable; we never fabricate values to fill the gaps.
        warnings: list[str] = []
        if not historical:
            warnings.append("No real historical sold-price data is available for this vehicle.")
        if not listings:
            warnings.append("No live listings are available for this vehicle from the configured provider.")
        if not sentiment.get("available"):
            warnings.append("No market sentiment/discussion sources are available for this vehicle.")
        if provider_name == "unconfigured":
            warnings.append(
                "No live data provider is configured. Set CIT_DATA_PROVIDER and the "
                "feed URLs to fetch real prices, listings and discussions."
            )

        availability = DataAvailability(
            provider=provider_name,
            fetched_at=fetched_at,
            historical_prices=bool(historical),
            current_listings=bool(listings),
            sentiment=bool(sentiment.get("available")),
            discussions=bool(discussions),
            warnings=warnings,
        )

        # Forecasting requires at least real historical data and listings. Without
        # them we return a structured "data unavailable" response instead of a
        # synthetic forecast.
        forecast = []
        explanation = None
        volatility = None
        comparables_data = []
        listing_anomalies = []
        econ_adjustment = None
        spec_adjustments_info = None
        listing_avg = 0.0

        if historical and listings:
            if inflation_adjusted:
                historical_prices = [point.average_price for point in historical]
            else:
                historical_prices = [point.nominal_price for point in historical]

            adjusted_historical = adjust_prices_for_specs(
                historical_prices,
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

            volatility = calculate_volatility_metrics([point.average_price for point in historical])
            comparables_data = get_market_comparables(brand, model, year, variant)
            listing_anomalies = detect_listing_anomalies(
                listings, market_price=forecast[0].predicted_price if forecast else None
            )
            econ_adjustment = calculate_economic_price_adjustment(base_price=listing_avg)
            spec_adjustments_info = calculate_spec_adjustments(
                base_price=listing_avg,
                transmission=transmission,
                trim_level=trim_level,
                condition=condition,
                mileage_bracket=mileage_bracket,
            )

        # These reference datasets do not depend on live market availability.
        start_year = 2026 - 20
        events = get_market_events(brand, model, start_year, 2026)
        rarity_proj = calculate_rarity_projection(brand, model, year)
        macro_context = get_macroeconomic_context()

        ownership = None
        if vehicle_price and vehicle_price > 0:
            ownership = calculate_ownership_costs(
                vehicle_price=vehicle_price,
                vehicle_brand=brand,
                vehicle_year=year,
            )

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Analysis failed for %s %s %s", brand, model, year)
        raise HTTPException(status_code=500, detail="Unable to complete analysis: processing_error") from exc

    # Determine confidence level based on real data availability. Confidence
    # scoring rewards more sold-price history, more live listings, recent data
    # and available sentiment; sparse data yields low confidence.
    historical_count = len(historical)
    listings_count = len(listings)
    discussions_count = len(discussions)

    if not historical or not listings:
        confidence = "Unavailable"
        consistency_note = "Insufficient real data to produce a confident valuation."
    elif historical_count >= 15 and listings_count >= 5 and discussions_count >= 3:
        confidence = "High"
        consistency_note = "Comprehensive sold-price history, live listings and discussion coverage"
    elif historical_count >= 8 and listings_count >= 3:
        confidence = "Medium"
        consistency_note = "Adequate sold-price history with moderate market coverage"
    else:
        confidence = "Low"
        consistency_note = "Limited real sold-price history or live listings"

    data_quality = DataQualityIndicator(
        historical_data_points=historical_count,
        current_listings_count=listings_count,
        data_consistency=(
            "Real sold-price history (inflation-adjusted) anchors valuation; live "
            "listings provide current market context; predictions are clamped to "
            "realistic bounds. No values are fabricated when data is missing."
        ),
        confidence_level=confidence,
        notes=consistency_note,
    )

    return {
        "query": {"brand": brand, "model": model, "year": year, "variant": variant},
        "summary": {
            "sentiment_score": f"{sentiment['score']}/5" if sentiment.get("available") else "Unavailable",
            "prediction_confidence": confidence,
            "price_trend": (
                "Based on real sold-price history with sentiment adjustment"
                if forecast else "Unavailable: insufficient real market data"
            ),
        },
        "data_availability": availability,
        "sentiment": sentiment,
        "sentiment_breakdown": sentiment_breakdown,
        "market_discussions": discussions,
        "historical_prices": historical,
        "prediction": forecast,
        "prediction_explanation": explanation,
        "current_listing_average": round(listing_avg, 2),
        "current_listings": listings,
        "undervalued_listings": undervalued,
        "listing_anomalies": listing_anomalies,
        "volatility_metrics": volatility,
        "market_comparables": comparables_data,
        "market_events": events,
        "spec_adjustments": spec_adjustments_info,
        "ownership_costs": ownership,
        "rarity_projection": rarity_proj,
        "macro_economic_context": macro_context,
        "economic_price_adjustment": econ_adjustment,
        "data_quality": data_quality,
        "data_sources": {
            "provider": provider_name,
            "historical": "Real sold-price / auction-result feeds (inflation-adjusted to current year GBP)",
            "listings": "Live adverts from the configured provider (e.g. Auto Trader), each linking to the exact advert",
            "sentiment": (
                f"Real news/forum/auction/social discussions (analysis of {sentiment['mentions_analyzed']} sources)"
                if sentiment.get("available") else "No real sentiment sources available"
            ),
        },
        "methodology": {
            "forecast_model": "Linear regression with momentum smoothing",
            "valuation_anchor": "Sold-price history is the primary valuation anchor; live listings provide current supply/demand context",
            "spike_prevention": "Predicted prices constrained between -30% and +35% of baseline to prevent unrealistic jumps",
            "inflation_adjustment": "Real historical prices converted to current year GBP for fair long-term comparison",
            "sentiment_impact": "Sentiment score (0-5) adjusted to ±10% multiplier on forecast (clamped for stability)",
            "confidence_intervals": "±10% bands around predictions to show forecast uncertainty",
            "no_fabrication": "When real data is unavailable, results are reported as unavailable rather than estimated",
        },
    }



def run() -> None:
    """Production entrypoint.

    Binds to ``0.0.0.0`` and honours the ``PORT`` environment variable used by
    most hosting platforms (Railway, Render, Heroku, Fly, Cloud Run, ...).
    """
    import os

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "car_investment_tracker.main:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    run()
