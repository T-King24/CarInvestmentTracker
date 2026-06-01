from __future__ import annotations

from typing import Protocol, runtime_checkable

from car_investment_tracker.models import Listing, MarketDiscussion, PricePoint


@runtime_checkable
class MarketDataProvider(Protocol):
    """Contract every real-data provider must satisfy.

    Implementations must return **only** real data. When a provider cannot
    obtain data for a query (no source, network error, not configured) it must
    return an empty list rather than fabricating values. Callers interpret an
    empty list as "data unavailable".
    """

    name: str

    def fetch_historical_prices(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[PricePoint]:
        """Real sold-price / auction-result history for the vehicle."""
        ...

    def fetch_listings(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[Listing]:
        """Live adverts for the vehicle, each linking to its exact detail page."""
        ...

    def fetch_discussions(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[MarketDiscussion]:
        """News articles / forum threads discussing the vehicle's value outlook."""
        ...
