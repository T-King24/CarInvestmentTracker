from __future__ import annotations

import random

from car_investment_tracker.models import Listing
from car_investment_tracker.services.cache import cache

SOURCES = [
    "Autotrader",
    "eBay Motors",
    "Cars & Bids",
    "Bring a Trailer",
    "PistonHeads",
]


def _price_to_usd(value: float, currency: str) -> float:
    rates = {"USD": 1.0, "GBP": 1.28, "EUR": 1.1}
    return round(value * rates.get(currency, 1.0), 2)


@cache.cached
def get_current_listings(brand: str, model: str, year: int) -> list[Listing]:
    seed = hash(f"listings:{brand}:{model}:{year}") & 0xFFFFFFFF
    rng = random.Random(seed)

    listings: list[Listing] = []
    for idx in range(30):
        source = SOURCES[idx % len(SOURCES)]
        currency = "USD" if source in {"Autotrader", "Cars & Bids", "Bring a Trailer"} else rng.choice(["USD", "GBP", "EUR"])
        raw_price = rng.uniform(7000, 55000)
        title_status = rng.random() > 0.17
        price = _price_to_usd(raw_price, currency)

        listings.append(
            Listing(
                source=source,
                title=f"{year} {brand} {model} Listing #{idx + 1}",
                price=price,
                currency="USD",
                clean_title=title_status,
                url=f"https://example.com/{source.lower().replace(' ', '-')}/{brand.lower()}-{model.lower()}-{idx + 1}",
            )
        )

    deduped: dict[str, Listing] = {}
    for listing in listings:
        deduped[str(listing.url)] = listing

    return list(deduped.values())
