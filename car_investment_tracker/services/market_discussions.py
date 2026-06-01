from __future__ import annotations

from car_investment_tracker.models import MarketDiscussion
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import get_market_provider


@cache.cached
def get_market_discussions(
    brand: str, model: str, year: int, variant: str | None = None
) -> list[MarketDiscussion]:
    """Return real news articles and forum threads discussing the car's pricing.

    Each item links to the original article/thread so users can read the
    community and expert discussion behind the price outlook. Returns an empty
    list when no real sources are available (nothing is fabricated).
    """
    provider = get_market_provider()
    return list(provider.fetch_discussions(brand, model, year, variant))
