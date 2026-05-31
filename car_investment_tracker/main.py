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
from car_investment_tracker.services.market_events import get_market_events
from car_investment_tracker.services.sentiment_sources import get_sentiment_source_breakdown
from car_investment_tracker.services.scenario_simulator import calculate_scenario_adjustment, ScenarioInput, compare_scenarios
from car_investment_tracker.services.export_service import export_to_csv, export_investor_report
from car_investment_tracker.services.anomaly_detection import detect_listing_anomalies
from car_investment_tracker.services.macro_economics import get_macroeconomic_context, calculate_economic_price_adjustment
from car_investment_tracker.services.rarity_projection import calculate_rarity_projection
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
    inflation_adjusted: bool = Query(default=True, description="Return inflation-adjusted prices (default) or nominal"),
):
    _validate_vehicle_params(brand, model, year)
    prices = get_historical_prices(brand, model, year)
    
    if not inflation_adjusted:
        # Return nominal prices instead
        return [{"year": p.year, "average_price": p.nominal_price} for p in prices]
    
    return prices


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


@app.get("/sentiment-sources")
def sentiment_sources(
    brand: str = Query(min_length=1),
    model: str = Query(min_length=1),
    year: int = Query(ge=1900),
):
    """Get detailed sentiment breakdown by source (forums, auctions, news, social media)."""
    _validate_vehicle_params(brand, model, year)
    return get_sentiment_source_breakdown(brand, model, year)


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
    transmission: str = Query(default="Automatic"),
    trim_level: str = Query(default="Standard"),
    condition: str = Query(default="Average"),
    mileage_bracket: str = Query(default="Normal"),
    vehicle_price: float = Query(default=None),
    inflation_adjusted: bool = Query(default=True),
):
    _validate_vehicle_params(brand, model, year)
    try:
        historical = get_historical_prices(brand, model, year)
        listings = get_current_listings(brand, model, year)
        sentiment = get_sentiment_score(brand, model, year)
        undervalued = find_undervalued_listings(listings)
        
        if not historical or not listings:
            raise HTTPException(status_code=404, detail="Insufficient data for analysis")
        
        # Select price data based on inflation_adjusted flag
        if inflation_adjusted:
            historical_prices = [point.average_price for point in historical]
        else:
            historical_prices = [point.nominal_price for point in historical]
        
        # Apply spec adjustments
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
        
        # Calculate volatility metrics
        volatility = calculate_volatility_metrics([point.average_price for point in historical])
        
        # Get market comparables
        comparables_data = get_market_comparables(brand, model, year)
        
        # Get market events
        start_year = 2026 - 20
        events = get_market_events(brand, model, start_year, 2026)
        
        # Get sentiment source breakdown
        sentiment_breakdown = get_sentiment_source_breakdown(brand, model, year)
        
        # Get rarity projection
        rarity_proj = calculate_rarity_projection(brand, model, year)
        
        # Get anomalies
        listing_anomalies = detect_listing_anomalies(listings, market_price=forecast[0].predicted_price if forecast else None)
        
        # Get macro-economic context
        macro_context = get_macroeconomic_context()
        
        # Calculate economic price adjustment
        listing_avg = sum(item.price for item in listings) / len(listings)
        econ_adjustment = calculate_economic_price_adjustment(
            base_price=listing_avg,
        )
        
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
        "sentiment_breakdown": sentiment_breakdown,
        "historical_prices": historical,
        "prediction": forecast,
        "prediction_explanation": explanation,
        "current_listing_average": round(listing_avg, 2),
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
            "volatility_tracking": "Coefficient of variation and volatility score (1-10) indicate market stability",
            "event_markers": "Major market events annotated to explain price movements",
            "sentiment_sources": "Weighted sentiment from forums (30%), auctions (35%), news (20%), and social media (15%)",
            "anomaly_detection": "Z-score based statistical analysis to identify outlier listings",
            "rarity_analysis": "Production volume and survival rate modeling for long-term value projection",
            "macro_economic": "Economic indicators and their historical correlations with luxury vehicle valuations",
        },
    }
