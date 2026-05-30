from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import random

from car_investment_tracker.constants import MIN_PRICE_FLOOR_USD
from car_investment_tracker.models import PricePoint
from car_investment_tracker.services.cache import cache

MIN_DEPRECIATION_RATE = 0.01
BASE_DEPRECIATION_RATE = 0.085
MAX_AGE_ADJUSTMENT_YEARS = 20
AGE_DEPRECIATION_ADJUSTMENT = 0.002
CLASSIC_AGE_THRESHOLD = 15
CLASSIC_APPRECIATION_WINDOW_YEARS = 7
MODEL_FACTOR_BASE = 0.9
MODEL_FACTOR_BUCKETS = 24
MODEL_FACTOR_STEP = 0.0125
TREND_PENALTY_FACTOR = 0.012
MAX_AGE_FOR_FACTOR = 30
AGE_FACTOR_MULTIPLIER = 0.015

BRAND_VALUE_MULTIPLIERS = {
    "aston martin": 1.35,
    "audi": 1.05,
    "bmw": 1.1,
    "jaguar": 1.0,
    "land rover": 1.2,
    "mercedes": 1.15,
    "porsche": 1.4,
}


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part).strip().lower() for part in parts).encode()).hexdigest()
    return int(digest[:16], 16)


def _base_market_price(brand: str, model: str, year: int, current_year: int) -> float:
    age = max(0, current_year - year)
    brand_factor = BRAND_VALUE_MULTIPLIERS.get(brand.lower(), 1.0)
    model_factor = MODEL_FACTOR_BASE + (
        (_stable_seed("model", model) % MODEL_FACTOR_BUCKETS) * MODEL_FACTOR_STEP
    )
    age_factor = 1.0 + min(age, MAX_AGE_FOR_FACTOR) * AGE_FACTOR_MULTIPLIER
    return max(MIN_PRICE_FLOOR_USD, 16000.0 * brand_factor * model_factor * age_factor)


@cache.cached
def get_historical_prices(brand: str, model: str, year: int) -> list[PricePoint]:
    seed = _stable_seed("historical", brand, model, year) & 0xFFFFFFFF
    rng = random.Random(seed)
    current_year = datetime.now(timezone.utc).year
    start_year = current_year - 19

    age = max(1, current_year - year)
    base = _base_market_price(brand, model, year, current_year)
    depreciation = max(
        MIN_DEPRECIATION_RATE,
        BASE_DEPRECIATION_RATE - min(age, MAX_AGE_ADJUSTMENT_YEARS) * AGE_DEPRECIATION_ADJUSTMENT,
    )

    data: list[PricePoint] = []
    price = float(base)
    for yr in range(start_year, current_year + 1):
        years_from_now = current_year - yr
        market_noise = rng.uniform(-0.03, 0.03)
        in_classic_window = age >= CLASSIC_AGE_THRESHOLD and yr >= current_year - CLASSIC_APPRECIATION_WINDOW_YEARS
        collector_bump = 0.018 if in_classic_window else 0.0
        trend_penalty = depreciation * (1 + (years_from_now * TREND_PENALTY_FACTOR))
        growth = collector_bump - trend_penalty + market_noise
        price = max(MIN_PRICE_FLOOR_USD, price * (1 + growth))
        data.append(PricePoint(year=yr, average_price=round(price, 2)))

    return data
