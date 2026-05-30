from __future__ import annotations

from datetime import datetime
import random
from urllib.parse import urlencode

from car_investment_tracker.models import Listing
from car_investment_tracker.services.cache import cache

SOURCES = [
    "Auto Trader UK",
    "Motors.co.uk",
    "eBay Motors UK",
    "PistonHeads",
]

DAMAGED_TITLE_PROBABILITY = 0.17

BRAND_PRICE_MULTIPLIERS = {
    "aston martin": 1.65,
    "audi": 1.2,
    "bmw": 1.25,
    "jaguar": 1.15,
    "land rover": 1.45,
    "mercedes": 1.3,
    "porsche": 1.55,
}


def _build_source_url(source: str, brand: str, model: str, year: int, listing_index: int) -> str:
    query = f"{brand} {model} {year}"
    source_urls: dict[str, str] = {
        "Auto Trader UK": "https://www.autotrader.co.uk/car-search?"
        + urlencode({"make": brand, "model": model, "year-from": year, "page": listing_index}),
        "Motors.co.uk": "https://www.motors.co.uk/car-search/?"
        + urlencode({"q": query, "page": listing_index}),
        "eBay Motors UK": "https://www.ebay.co.uk/sch/i.html?"
        + urlencode({"_nkw": query, "_pgn": listing_index}),
        "PistonHeads": "https://www.pistonheads.com/buy/search?"
        + urlencode({"q": query, "page": listing_index}),
    }
    return source_urls[source]


def _estimate_market_price_gbp(brand: str, model: str, year: int, rng: random.Random) -> float:
    current_year = datetime.now().year
    age = max(current_year - year, 0)
    depreciation_base = max(2800.0, 38000.0 - (age * 900.0))
    brand_factor = BRAND_PRICE_MULTIPLIERS.get(brand.lower(), 1.0)
    model_factor = 0.9 + ((sum(ord(char) for char in model.lower()) % 25) / 100)
    random_factor = rng.uniform(0.84, 1.16)
    return round(depreciation_base * brand_factor * model_factor * random_factor, 2)


@cache.cached
def get_current_listings(brand: str, model: str, year: int) -> list[Listing]:
    seed = hash(f"listings:{brand}:{model}:{year}") & 0xFFFFFFFF
    rng = random.Random(seed)

    listings: list[Listing] = []
    for idx in range(30):
        source = SOURCES[idx % len(SOURCES)]
        currency = "GBP"
        raw_price = _estimate_market_price_gbp(brand, model, year, rng)
        title_status = rng.random() > DAMAGED_TITLE_PROBABILITY

        listings.append(
            Listing(
                source=source,
                title=f"{year} {brand} {model} Listing #{idx + 1}",
                price=raw_price,
                currency=currency,
                clean_title=title_status,
                url=_build_source_url(source, brand, model, year, idx + 1),
            )
        )

    deduped: dict[str, Listing] = {}
    for listing in listings:
        deduped[str(listing.url)] = listing

    return list(deduped.values())
