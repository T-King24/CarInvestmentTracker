from __future__ import annotations

from datetime import date
import hashlib
import random
from urllib.parse import quote_plus, urlencode

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

MODEL_FACTOR_BASE = 0.9
MODEL_FACTOR_BUCKETS = 25
MODEL_FACTOR_STEP = 0.01
CURRENT_YEAR = date.today().year
LISTING_ID_BASE = 10_000_000
LISTING_ID_RANGE = 90_000_000


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part).strip().lower() for part in parts).encode()).hexdigest()
    return int(digest[:16], 16)


def _build_source_url(source: str, brand: str, model: str, year: int, listing_index: int) -> str:
    query = quote_plus(f"{year} {brand} {model}")
    listing_id = LISTING_ID_BASE + (_stable_seed(source, brand, model, year, listing_index) % LISTING_ID_RANGE)
    source_urls: dict[str, str] = {
        "Auto Trader UK": f"https://www.autotrader.co.uk/car-details/{listing_id}?"
        + urlencode({"make": brand, "model": model, "year-from": year, "advertising-location": "at_cars"}),
        "Motors.co.uk": f"https://www.motors.co.uk/car-{listing_id}/{query}/",
        "eBay Motors UK": f"https://www.ebay.co.uk/itm/{listing_id}?_nkw={query}",
        "PistonHeads": f"https://www.pistonheads.com/buy/listing/{listing_id}?q={query}",
    }
    return source_urls[source]


def _estimate_market_price_gbp(brand: str, model: str, year: int, rng: random.Random) -> float:
    # Keep pricing variation deterministic for the same model while retaining believable spread.
    random_factor = rng.uniform(0.84, 1.16)
    return round(estimate_market_value_gbp(brand, model, year) * random_factor, 2)


def estimate_market_value_gbp(brand: str, model: str, year: int) -> float:
    """Deterministic current market value (the mean a listing fluctuates around).

    Exposed so other services (e.g. historical pricing) can anchor to the same
    market basis and avoid discontinuities between datasets.
    """
    normalized_year = min(year, CURRENT_YEAR)
    age = CURRENT_YEAR - normalized_year
    depreciation_base = max(2800.0, 38000.0 - (age * 900.0))
    brand_factor = BRAND_PRICE_MULTIPLIERS.get(brand.lower(), 1.0)
    model_factor = MODEL_FACTOR_BASE + (
        (_stable_seed("model-factor", model) % MODEL_FACTOR_BUCKETS)
        * MODEL_FACTOR_STEP
    )
    return round(depreciation_base * brand_factor * model_factor, 2)


@cache.cached
def get_current_listings(brand: str, model: str, year: int) -> list[Listing]:
    seed = _stable_seed("listings", brand, model, year) & 0xFFFFFFFF
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
