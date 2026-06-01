from __future__ import annotations

from datetime import date
import hashlib
import random
from urllib.parse import quote_plus, urlencode

from car_investment_tracker.constants import MIN_PRICE_FLOOR_GBP
from car_investment_tracker.models import Listing
from car_investment_tracker.services.cache import cache

SOURCES = [
    "Auto Trader UK",
    "Motors.co.uk",
    "eBay Motors UK",
    "PistonHeads",
]

DAMAGED_TITLE_PROBABILITY = 0.17

# Brand desirability premium applied on the fallback pricing path (i.e. when a
# model is not present in MODEL_BASE_PRICES_GBP). Keys must match the normalized
# (lower-cased) catalog make names – note the canonical make is "Mercedes-Benz",
# so the matching key is "mercedes-benz" (a "mercedes" alias is kept for safety).
BRAND_PRICE_MULTIPLIERS = {
    "aston martin": 1.65,
    "audi": 1.2,
    "bmw": 1.25,
    "ferrari": 2.4,
    "jaguar": 1.15,
    "lamborghini": 2.6,
    "land rover": 1.45,
    "mercedes-benz": 1.3,
    "mercedes": 1.3,
    "porsche": 1.55,
}

# Approximate "as-new" market value in today's GBP for each catalogued model.
# These anchor every downstream valuation (current listings + historical arc),
# so supercars/classics are no longer collapsed to a generic ~£3k–£38k band.
# Older/limited cars appreciate on top of this baseline via age_value_factor().
MODEL_BASE_PRICES_GBP = {
    # Porsche
    "911": 100_000.0,
    "carrera": 90_000.0,
    "turbo": 140_000.0,
    "911 rs": 200_000.0,
    "930": 90_000.0,
    "boxster": 50_000.0,
    "cayman": 55_000.0,
    "cayenne": 70_000.0,
    "panamera": 85_000.0,
    "macan": 55_000.0,
    # Ferrari
    "f430": 150_000.0,
    "f8 tributo": 230_000.0,
    "sf90 stradale": 380_000.0,
    "roma": 180_000.0,
    "296 gtb": 270_000.0,
    "testarossa": 120_000.0,
    "f40": 900_000.0,
    "f50": 1_500_000.0,
    # Lamborghini
    "aventador": 280_000.0,
    "huracán": 200_000.0,
    "huracan": 200_000.0,
    "revuelto": 450_000.0,
    "countach": 500_000.0,
    "diablo": 350_000.0,
    "murciélago": 250_000.0,
    "murcielago": 250_000.0,
    # BMW
    "m3": 60_000.0,
    "m5": 80_000.0,
    "m4": 75_000.0,
    "z3": 25_000.0,
    "z4": 45_000.0,
    "i8": 95_000.0,
    "3 series": 40_000.0,
    "5 series": 50_000.0,
    # Mercedes-Benz
    "sl": 90_000.0,
    "slr": 350_000.0,
    "amg gt": 130_000.0,
    "c63 amg": 75_000.0,
    "e63 amg": 95_000.0,
    "g-class": 130_000.0,
    "300 sl": 1_200_000.0,
    # Aston Martin
    "db9": 130_000.0,
    "dbs": 160_000.0,
    "vantage": 120_000.0,
    "db11": 150_000.0,
    "dbs superleggera": 230_000.0,
    "dbx": 160_000.0,
    "rapide": 140_000.0,
    # Jaguar
    "e-type": 150_000.0,
    "xk": 60_000.0,
    "xj": 55_000.0,
    "f-type": 70_000.0,
    "c-x75": 1_000_000.0,
    # Land Rover
    "defender": 60_000.0,
    "range rover": 100_000.0,
    "discovery": 55_000.0,
    "freelander": 25_000.0,
    "evoque": 45_000.0,
    # Audi
    "r8": 130_000.0,
    "s4": 50_000.0,
    "s5": 55_000.0,
    "rs6": 110_000.0,
    "tt": 40_000.0,
    "a1": 25_000.0,
}

# Fallback "as-new" price (today's GBP) for models not in the table above.
DEFAULT_BASE_PRICE_GBP = 40_000.0

# Age-driven value shape, shared with historical_data so the historical arc and
# today's market value stay consistent (no discontinuity at the current year).
ANNUAL_DEPRECIATION_FACTOR = 0.90   # value retained per year while depreciating
DEPRECIATION_FLOOR = 0.40           # value never drops below this fraction as-new
CLASSIC_AGE_THRESHOLD = 15          # cars at/over this age appreciate as classics
CLASSIC_APPRECIATION_PER_YEAR = 0.04  # compounding appreciation once classic

MODEL_FACTOR_BASE = 0.9
MODEL_FACTOR_BUCKETS = 25
MODEL_FACTOR_STEP = 0.01
CURRENT_YEAR = date.today().year
LISTING_ID_BASE = 10_000_000
LISTING_ID_RANGE = 90_000_000


def age_value_factor(age: int) -> float:
    """Relative value of a vehicle at a given age (age 0 == as-new == 1.0).

    Vehicles depreciate towards a floor; once they reach classic age they
    appreciate again (compounding), reflecting collectible demand for older
    and limited cars instead of flooring them at scrap value.
    """
    if age <= 0:
        return 1.0
    value_factor = DEPRECIATION_FLOOR + (1.0 - DEPRECIATION_FLOOR) * (ANNUAL_DEPRECIATION_FACTOR ** age)
    if age >= CLASSIC_AGE_THRESHOLD:
        years_classic = age - CLASSIC_AGE_THRESHOLD
        value_factor *= (1.0 + CLASSIC_APPRECIATION_PER_YEAR) ** years_classic
    return value_factor


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

    Resolves a realistic "as-new" baseline for the specific model (falling back
    to a brand-tier estimate for unknown models) and applies age-based
    depreciation/collectible appreciation. Exposed so other services (e.g.
    historical pricing) can anchor to the same basis and avoid discontinuities.
    """
    normalized_year = min(year, CURRENT_YEAR)
    age = CURRENT_YEAR - normalized_year

    model_key = model.strip().lower()
    base_price = MODEL_BASE_PRICES_GBP.get(model_key)
    if base_price is None:
        # Fallback: brand-tier estimate with deterministic per-model spread.
        brand_factor = BRAND_PRICE_MULTIPLIERS.get(brand.strip().lower(), 1.0)
        model_factor = MODEL_FACTOR_BASE + (
            (_stable_seed("model-factor", model) % MODEL_FACTOR_BUCKETS)
            * MODEL_FACTOR_STEP
        )
        base_price = DEFAULT_BASE_PRICE_GBP * brand_factor * model_factor

    value = base_price * age_value_factor(age)
    return round(max(MIN_PRICE_FLOOR_GBP, value), 2)


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
