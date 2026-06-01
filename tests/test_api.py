from fastapi.testclient import TestClient

from car_investment_tracker.main import app
from car_investment_tracker.services.sentiment import get_sentiment_score
from car_investment_tracker.services.prediction import predict_prices, _calculate_recent_momentum
from car_investment_tracker.services.historical_data import get_historical_prices, _inflation_adjustment

client = TestClient(app)


def _query_params():
    return {"brand": "Porsche", "model": "911", "year": 2004}


# ---------------------------------------------------------------------------
# Catalog / dropdowns (reference taxonomy, always available)
# ---------------------------------------------------------------------------

def test_dropdown_makes_returns_catalog():
    response = client.get("/dropdown-makes")
    assert response.status_code == 200
    makes = response.json()
    assert "Porsche" in makes
    assert "Ferrari" in makes


def test_dropdown_variants_returns_known_variants():
    response = client.get("/dropdown-variants", params={"make": "Porsche", "model": "911"})
    assert response.status_code == 200
    variants = response.json()
    assert isinstance(variants, list)
    assert variants  # 911 has known variants
    assert any("Carrera" in v for v in variants)


def test_brand_themes_endpoint_includes_signature_colours():
    response = client.get("/brand-themes")
    assert response.status_code == 200
    themes = response.json()
    # Ferrari should be red; the UI relies on this exact key shape.
    assert "Ferrari" in themes
    assert "accent" in themes["Ferrari"]
    assert "_default" in themes


def test_dropdowns_can_use_live_catalog_api(monkeypatch):
    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "makes": [
                    {
                        "name": "TestMake",
                        "models": [
                            {
                                "name": "TestModel",
                                "years": [2024, 2025],
                                "variants": ["Base", "S"],
                            }
                        ],
                    }
                ]
            }

    captured = {}

    def fake_get(url, timeout, headers):
        captured["url"] = url
        captured["timeout"] = timeout
        captured["headers"] = headers
        return _Response()

    monkeypatch.setenv("CIT_CATALOG_API_URL", "https://catalog.example/vehicles")
    monkeypatch.setenv("CIT_DATA_API_KEY", "test-key")
    monkeypatch.setenv("CIT_DATA_TIMEOUT", "12")
    monkeypatch.setattr("httpx.get", fake_get)

    makes = client.get("/dropdown-makes")
    models = client.get("/dropdown-models", params={"make": "TestMake"})
    variants = client.get("/dropdown-variants", params={"make": "TestMake", "model": "TestModel"})
    years = client.get("/dropdown-years", params={"make": "TestMake", "model": "TestModel"})

    assert makes.status_code == 200
    assert models.status_code == 200
    assert variants.status_code == 200
    assert years.status_code == 200
    assert makes.json() == ["TestMake"]
    assert models.json() == ["TestModel"]
    assert variants.json() == ["Base", "S"]
    assert years.json() == [2024, 2025]
    assert captured["url"] == "https://catalog.example/vehicles"
    assert captured["timeout"] == 12.0
    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert captured["headers"]["Authorization"].endswith("test-key")


# ---------------------------------------------------------------------------
# Health / readiness probe (used by live deployments)
# ---------------------------------------------------------------------------

def test_healthz_reports_ok_and_null_mode_by_default():
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    # With no provider configured the app is up but not serving live market data.
    assert body["data_mode"] == "null"
    assert "version" in body
    assert "provider" in body


# ---------------------------------------------------------------------------
# No-fake-data behaviour: with no provider configured, nothing is fabricated
# ---------------------------------------------------------------------------

def test_no_provider_returns_no_historical_prices():
    response = client.get("/historical-prices", params=_query_params())
    assert response.status_code == 200
    assert response.json() == []


def test_no_provider_returns_no_listings():
    response = client.get("/current-listings", params=_query_params())
    assert response.status_code == 200
    assert response.json() == []


def test_no_provider_sentiment_is_unavailable():
    response = client.get("/sentiment-score", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is False
    assert payload["mentions_analyzed"] == 0


def test_analysis_without_provider_reports_unavailable_not_404():
    response = client.get("/analysis", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    availability = payload["data_availability"]
    assert availability["historical_prices"] is False
    assert availability["current_listings"] is False
    assert availability["warnings"]
    assert payload["historical_prices"] == []
    assert payload["current_listings"] == []
    assert payload["prediction"] == []
    assert payload["data_quality"]["confidence_level"] == "Unavailable"


# ---------------------------------------------------------------------------
# Real-data pipeline: provider data is surfaced faithfully (no fabrication)
# ---------------------------------------------------------------------------

def test_provider_listings_use_exact_advert_urls(fake_provider):
    response = client.get("/current-listings", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert payload
    for item in payload:
        assert item["currency"] == "GBP"
        # Exact advert detail pages, not generic search pages.
        assert item["url"].startswith("https://www.autotrader.co.uk/car-details/")
        assert "example.com" not in item["url"]


def test_provider_historical_prices_include_source_metadata(fake_provider):
    response = client.get("/historical-prices", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert payload
    for point in payload:
        assert point["price_type"] == "sold"
        assert point["source_name"]
        assert point["source_url"].startswith("https://")
        assert point["currency"] == "GBP"


def test_provider_sentiment_uses_real_sources(fake_provider):
    sentiment = get_sentiment_score("Porsche", "911", 2004)
    assert sentiment["available"] is True
    assert sentiment["mentions_analyzed"] > 0
    assert 0 < sentiment["score"] <= 5


def test_analysis_includes_market_discussions(fake_provider):
    response = client.get("/analysis", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    discussions = payload["market_discussions"]
    assert discussions
    assert discussions[0]["url"].startswith("https://")
    assert discussions[0]["price_outlook"] == "appreciating"


def test_analysis_passes_variant_through(fake_provider):
    params = {**_query_params(), "variant": "Carrera S"}
    response = client.get("/analysis", params=params)
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"]["variant"] == "Carrera S"
    # Listings should reflect the requested variant from the provider.
    assert payload["current_listings"]
    assert payload["current_listings"][0]["variant"] == "Carrera S"


def test_undervalued_listings_based_on_real_averages(fake_provider):
    response = client.get("/undervalued-listings", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    listings = client.get("/current-listings", params=_query_params()).json()
    avg = sum(item["price"] for item in listings) / len(listings)
    assert payload
    for item in payload:
        assert item["clean_title"] is True
        assert item["price"] < avg


def test_undervalued_endpoint_handles_empty_listings(monkeypatch):
    from car_investment_tracker import main

    monkeypatch.setattr(
        main, "get_current_listings", lambda brand, model, year, variant=None: []
    )
    response = client.get("/undervalued-listings", params=_query_params())
    assert response.status_code == 200
    assert response.json() == []


def test_market_comparables_only_returns_sold(fake_provider):
    # The fake provider exposes only "asking" listings, so no sold comparables.
    response = client.get("/market-comparables", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is False
    assert payload["comparables"] == []


# ---------------------------------------------------------------------------
# Pure prediction / inflation unit tests (provider-independent)
# ---------------------------------------------------------------------------

def test_consecutive_depreciation_does_not_forecast_sudden_rise():
    declining = [200000, 185000, 170000, 158000, 150000, 145000]
    forecast, explanation = predict_prices(declining, 148000, 1.5)

    assert forecast
    last_historical = declining[-1]
    assert all(p.predicted_price <= last_historical for p in forecast)
    prices = [p.predicted_price for p in forecast]
    assert prices == sorted(prices, reverse=True)
    assert explanation.driven_by_history is True
    assert "depreciat" in explanation.outlook.lower()


def test_strong_bullish_sentiment_can_lift_forecast():
    rising = [100000, 105000, 112000, 120000, 130000]
    forecast, explanation = predict_prices(rising, 128000, 4.5)
    assert forecast
    assert explanation.outlook


def test_inflation_adjustment_increases_past_prices():
    adjustment = _inflation_adjustment(2021, 2026)
    assert adjustment > 1.0
    assert 1.1 < adjustment < 1.15


def test_momentum_calculation_reflects_recent_trend():
    assert _calculate_recent_momentum([100, 110, 120, 130, 140]) > 0
    assert _calculate_recent_momentum([140, 130, 120, 110, 100]) < 0
    assert _calculate_recent_momentum([100, 100, 100, 100, 100]) == 0


def test_prediction_includes_explanation():
    historical = [15000, 14500, 14000, 13500, 13000]
    forecast, explanation = predict_prices(historical, 12000, 2.5)

    assert len(forecast) > 0
    assert explanation.historical_weight == 0.6
    assert explanation.listing_weight == 0.4
    assert explanation.inflation_adjusted is True
    assert "momentum" in explanation.model_type.lower()


def test_analysis_endpoint_includes_transparency(fake_provider):
    response = client.get("/analysis", params=_query_params())
    assert response.status_code == 200
    payload = response.json()

    assert "prediction_explanation" in payload
    assert payload["prediction_explanation"] is not None
    assert "model_type" in payload["prediction_explanation"]
    assert "inflation_adjusted" in payload["prediction_explanation"]
