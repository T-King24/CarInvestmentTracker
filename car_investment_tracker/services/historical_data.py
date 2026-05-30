from __future__ import annotations

from datetime import datetime, timezone
import random

from car_investment_tracker.constants import MIN_PRICE_FLOOR_USD
from car_investment_tracker.models import PricePoint
from car_investment_tracker.services.cache import cache

MIN_DEPRECIATION_RATE = 0.01
BASE_DEPRECIATION_RATE = 0.085
MAX_AGE_ADJUSTMENT_YEARS = 20
AGE_DEPRECIATION_ADJUSTMENT = 0.002


@cache.cached
def get_historical_prices(brand: str, model: str, year: int) -> list[PricePoint]:
    seed = hash(f"{brand}:{model}:{year}") & 0xFFFFFFFF
    rng = random.Random(seed)
    current_year = datetime.now(timezone.utc).year
    start_year = current_year - 19

    age = max(1, current_year - year)
    base = 12000 + (hash(brand + model) % 18000)
    depreciation = max(
        MIN_DEPRECIATION_RATE,
        BASE_DEPRECIATION_RATE - min(age, MAX_AGE_ADJUSTMENT_YEARS) * AGE_DEPRECIATION_ADJUSTMENT,
    )

    data: list[PricePoint] = []
    price = float(base)
    for yr in range(start_year, current_year + 1):
        market_noise = rng.uniform(-0.04, 0.05)
        collector_bump = 0.02 if age > 15 and yr > current_year - 8 else 0
        growth = collector_bump - depreciation + market_noise
        price = max(MIN_PRICE_FLOOR_USD, price * (1 + growth))
        data.append(PricePoint(year=yr, average_price=round(price, 2)))

    return data
