from fastapi.testclient import TestClient

from car_investment_tracker.main import app

client = TestClient(app)


def _query_params():
    return {"brand": "Porsche", "model": "911", "year": 2004}


def test_historical_prices_returns_20_years():
    response = client.get("/historical-prices", params=_query_params())
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 20
    assert payload[0]["year"] < payload[-1]["year"]


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
    avg = sum(item["price"] for item in listings) / len(listings)

    assert payload
    for item in payload:
        assert item["clean_title"] is True
        assert item["price"] < avg
