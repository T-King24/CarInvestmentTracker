from __future__ import annotations

from car_investment_tracker.models import Listing, MarketDiscussion, PricePoint


class NullProvider:
    """Provider used when no real data source is configured.

    Every method returns an empty list so the application reports data as
    *unavailable* rather than presenting fabricated values. This is the default
    behaviour and is what guarantees the app never shows made-up prices,
    listings or sentiment.
    """

    name = "unconfigured"

    def fetch_historical_prices(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[PricePoint]:
        return []

    def fetch_listings(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[Listing]:
        return []

    def fetch_discussions(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[MarketDiscussion]:
        return []
