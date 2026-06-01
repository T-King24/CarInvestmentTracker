from __future__ import annotations

from car_investment_tracker.models import Listing
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import get_market_provider


@cache.cached
def get_current_listings(
    brand: str, model: str, year: int, variant: str | None = None
) -> list[Listing]:
    """Return real, live adverts for the vehicle from the configured provider.

    Listings are fetched from the active data provider and each carries the exact
    advert detail URL (not a generic search page). When no provider is configured
    or the provider returns nothing, an empty list is returned so the rest of the
    app reports listings as *unavailable* instead of fabricating them.
    """
    provider = get_market_provider()
    listings = provider.fetch_listings(brand, model, year, variant)
    return list(listings)
