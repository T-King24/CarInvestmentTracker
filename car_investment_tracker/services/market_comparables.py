from __future__ import annotations

from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import get_market_provider


@cache.cached
def get_market_comparables(
    brand: str, model: str, year: int, variant: str | None = None
) -> list[dict]:
    """Return recent comparable *sold* transactions for the vehicle.

    Comparables are drawn from the provider's real data: any listing flagged as a
    completed sale (``price_type == "sold"``) is treated as a comparable
    transaction. When the provider exposes no sold transactions, an empty list is
    returned rather than fabricating auction results.
    """
    provider = get_market_provider()
    listings = provider.fetch_listings(brand, model, year, variant)

    comparables: list[dict] = []
    for listing in listings:
        if listing.price_type != "sold":
            continue
        comparables.append(
            {
                "sale_date": listing.date_collected,
                "price": round(listing.price, 2),
                "currency": listing.currency,
                "mileage": listing.mileage,
                "variant": listing.variant,
                "transmission": listing.transmission,
                "fuel_type": listing.fuel_type,
                "location": listing.location,
                "source": listing.source,
                "url": str(listing.url),
            }
        )

    comparables.sort(key=lambda c: (c["sale_date"] or ""), reverse=True)
    return comparables
