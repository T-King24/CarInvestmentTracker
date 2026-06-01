from fastapi.testclient import TestClient

from car_investment_tracker.main import app
from car_investment_tracker.services.sentiment import get_sentiment_score
from car_investment_tracker.services.prediction import predict_prices, _calculate_recent_momentum
from car_investment_tracker.services.historical_data import get_historical_prices, _inflation_adjustment

client = TestClient(app)


def _query_params():
    return {"brand": "Porsche", "model": "911", "year": 2004}


def test_historical_prices_span_full_car_life():
    response = client.get("/historical-prices", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    # The series should span the car's whole life: model year (2004) -> current year.
    assert payload[0]["year"] == _query_params()["year"]
    assert payload[0]["year"] < payload[-1]["year"]
    expected_points = payload[-1]["year"] - _query_params()["year"] + 1
    assert len(payload) == expected_points


def test_sentiment_score_range_is_zero_to_five():
    response = client.get("/sentiment-score", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["score"] <= 5


def test_undervalued_listing_rules():
    response = client.get("/undervalued-listings", params=_query_params())
    assert response.status_code == 200
    payload = response.json()

    listings_response = client.get("/current-listings", params=_query_params())
    listings = listings_response.json()
    assert listings
    avg = sum(item["price"] for item in listings) / len(listings)

    assert payload
    for item in payload:
        assert item["clean_title"] is True
        assert item["price"] < avg


def test_undervalued_endpoint_handles_empty_listings(monkeypatch):
    from car_investment_tracker import main

    monkeypatch.setattr(main, "get_current_listings", lambda brand, model, year: [])
    response = client.get("/undervalued-listings", params=_query_params())
    assert response.status_code == 200
    assert response.json() == []


def test_current_listings_use_uk_currency_and_working_links():
    response = client.get("/current-listings", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert payload

    for item in payload:
        assert item["currency"] == "GBP"
        assert item["url"].startswith("https://")
        assert "example.com" not in item["url"]


def test_inflation_adjustment_increases_past_prices():
    """Test that inflation adjustment makes past prices higher in current value."""
    current_year = 2026
    five_years_ago = 2021
    adjustment = _inflation_adjustment(five_years_ago, current_year)
    # 2.5% annual inflation over 5 years should increase value
    assert adjustment > 1.0
    # Should be approximately 1.025^5 ≈ 1.131
    assert 1.1 < adjustment < 1.15


def test_sentiment_score_uses_weighted_terms():
    """Test sentiment scoring with improved weighted terms."""
    sentiment = get_sentiment_score("Porsche", "911", 2004)
    assert sentiment["score"] > 0
    assert sentiment["score"] <= 5
    assert sentiment["mentions_analyzed"] > 0


def test_momentum_calculation_reflects_recent_trend():
    """Test that momentum calculation reflects recent price changes."""
    # Test with increasing prices
    increasing_prices = [100, 110, 120, 130, 140]
    momentum = _calculate_recent_momentum(increasing_prices)
    assert momentum > 0, "Increasing prices should have positive momentum"
    
    # Test with decreasing prices
    decreasing_prices = [140, 130, 120, 110, 100]
    momentum = _calculate_recent_momentum(decreasing_prices)
    assert momentum < 0, "Decreasing prices should have negative momentum"
    
    # Test with flat prices
    flat_prices = [100, 100, 100, 100, 100]
    momentum = _calculate_recent_momentum(flat_prices)
    assert momentum == 0, "Flat prices should have zero momentum"


def test_prediction_includes_explanation():
    """Test that prediction returns both forecast and explanation."""
    historical = [15000, 14500, 14000, 13500, 13000]
    forecast, explanation = predict_prices(historical, 12000, 2.5)
    
    assert len(forecast) > 0, "Forecast should have predictions"
    assert explanation.historical_weight == 0.6
    assert explanation.listing_weight == 0.4
    assert explanation.inflation_adjusted is True
    assert "momentum" in explanation.model_type.lower()


def test_analysis_endpoint_includes_transparency():
    """Test that analysis endpoint includes model transparency explanation."""
    response = client.get("/analysis", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    
    assert "prediction_explanation" in payload
    assert "model_type" in payload["prediction_explanation"]
    assert "trend_momentum" in payload["prediction_explanation"]
    assert "inflation_adjusted" in payload["prediction_explanation"]


def test_supercar_pricing_is_realistic():
    """Halo/supercar models should be valued far above the old generic ~£3k-£38k band."""
    from car_investment_tracker.services.current_listings import estimate_market_value_gbp

    f40 = estimate_market_value_gbp("Ferrari", "F40", 1990)
    countach = estimate_market_value_gbp("Lamborghini", "Countach", 1985)
    sl300 = estimate_market_value_gbp("Mercedes-Benz", "300 SL", 1955)

    # These collectible cars are worth hundreds of thousands, not tens of thousands.
    assert f40 > 200_000
    assert countach > 200_000
    assert sl300 > 200_000


def test_brand_multiplier_keys_match_catalog():
    """Ferrari, Lamborghini and Mercedes-Benz must resolve to their fallback premium."""
    from car_investment_tracker.services.current_listings import BRAND_PRICE_MULTIPLIERS

    assert "ferrari" in BRAND_PRICE_MULTIPLIERS
    assert "lamborghini" in BRAND_PRICE_MULTIPLIERS
    # Canonical catalog make is "Mercedes-Benz" -> normalized key must match.
    assert "mercedes-benz" in BRAND_PRICE_MULTIPLIERS


def test_classic_car_appreciates_over_its_life():
    """An old classic should be worth more today than near the bottom of its depreciation."""
    response = client.get(
        "/historical-prices",
        params={"brand": "Jaguar", "model": "E-Type", "year": 1965},
    )
    assert response.status_code == 200
    payload = response.json()
    prices = [p["average_price"] for p in payload]
    # Latest value should exceed the cheapest (post-depreciation trough) point.
    assert prices[-1] > min(prices)
