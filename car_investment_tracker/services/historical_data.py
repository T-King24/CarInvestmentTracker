from __future__ import annotations

from datetime import datetime, timezone

from car_investment_tracker.models import PricePoint
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import get_market_provider

# UK inflation rate (approximate annual average): 2.5%. Applied only to real,
# provider-supplied nominal prices so historical values can be compared in
# today's money. No prices are ever generated here.
ANNUAL_INFLATION_RATE = 0.025


def _inflation_adjustment(year: int, base_year: int) -> float:
    """Inflation multiplier converting a price from ``year`` into ``base_year`` money."""
    years_difference = base_year - year
    return (1 + ANNUAL_INFLATION_RATE) ** years_difference


@cache.cached
def get_historical_prices(
    brand: str, model: str, year: int, variant: str | None = None
) -> list[PricePoint]:
    """Return real sold-price / auction-result history from the active provider.

    The provider supplies actual transaction prices. We additionally compute an
    inflation-adjusted figure for each point so older prices can be compared in
    today's money, but we never invent prices: if the provider returns nothing,
    this returns an empty list and the caller reports "insufficient data".
    """
    provider = get_market_provider()
    points = provider.fetch_historical_prices(brand, model, year, variant)
    if not points:
        return []

    current_year = datetime.now(timezone.utc).year
    enriched: list[PricePoint] = []
    for point in points:
        nominal = point.nominal_price if point.nominal_price is not None else point.average_price
        inflation_adjusted = point.inflation_adjusted_price
        if inflation_adjusted is None:
            inflation_adjusted = nominal * _inflation_adjustment(point.year, current_year)
        enriched.append(
            PricePoint(
                year=point.year,
                # Use the inflation-adjusted value as the headline average so
                # long-term trends are comparable in today's money.
                average_price=round(inflation_adjusted, 2),
                nominal_price=round(nominal, 2),
                inflation_adjusted_price=round(inflation_adjusted, 2),
                currency=point.currency,
                price_type=point.price_type,
                sample_size=point.sample_size,
                source_name=point.source_name,
                source_url=point.source_url,
                confidence=point.confidence,
            )
        )
    enriched.sort(key=lambda p: p.year)
    return enriched
