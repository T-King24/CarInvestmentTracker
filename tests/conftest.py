import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from car_investment_tracker.models import Listing, MarketDiscussion, PricePoint
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import (
    reset_market_provider,
    set_market_provider,
)


class FakeProvider:
    """In-memory provider used by tests to exercise the real-data pipeline.

    It returns deterministic *fixture* data (clearly not the old synthetic
    generators) so tests can assert that the application surfaces provider data
    faithfully - exact URLs, source metadata, sold prices, etc.
    """

    name = "fake-test-provider"

    def fetch_historical_prices(self, brand, model, year, variant=None):
        return [
            PricePoint(
                year=y,
                nominal_price=10000 + (y - year) * 500,
                average_price=10000 + (y - year) * 500,
                currency="GBP",
                price_type="sold",
                sample_size=4,
                source_name="Test Auctions",
                source_url=f"https://auctions.example/{brand}/{model}/{y}",
                confidence="High",
            )
            for y in range(year, year + 20)
        ]

    def fetch_listings(self, brand, model, year, variant=None):
        return [
            Listing(
                source="Auto Trader",
                title=f"{year} {brand} {model} {variant or 'Base'}",
                price=22000,
                currency="GBP",
                clean_title=True,
                url="https://www.autotrader.co.uk/car-details/202401011234567",
                listing_id="AT-1",
                price_type="asking",
                mileage=42000,
                year=year,
                variant=variant or "Base",
                transmission="Manual",
                fuel_type="Petrol",
                location="London",
                seller_type="Trade",
                date_collected="2026-06-01",
            ),
            Listing(
                source="Auto Trader",
                title=f"{year} {brand} {model} {variant or 'Base'} (cheaper)",
                price=15000,
                currency="GBP",
                clean_title=True,
                url="https://www.autotrader.co.uk/car-details/202401019999999",
                listing_id="AT-2",
                price_type="asking",
                mileage=78000,
                year=year,
                variant=variant or "Base",
                transmission="Manual",
                fuel_type="Petrol",
                location="Leeds",
                seller_type="Private",
                date_collected="2026-06-01",
            ),
        ]

    def fetch_discussions(self, brand, model, year, variant=None):
        return [
            MarketDiscussion(
                title=f"Are {brand} {model} values appreciating?",
                url="https://www.pistonheads.com/gassing/topic12345",
                source="PistonHeads",
                published_date="2026-01-15",
                summary="Owners discuss the appreciating, collectible outlook.",
                sentiment_score=4.2,
                price_outlook="appreciating",
            )
        ]


@pytest.fixture(autouse=True)
def _reset_provider_and_cache():
    """Ensure each test starts with no provider configured and an empty cache."""
    cache.clear()
    reset_market_provider()
    yield
    cache.clear()
    reset_market_provider()


@pytest.fixture
def fake_provider():
    """Install the FakeProvider for the duration of a test."""
    provider = FakeProvider()
    set_market_provider(provider)
    cache.clear()
    yield provider
    reset_market_provider()
    cache.clear()
