from __future__ import annotations

from datetime import datetime, timezone
import random

from car_investment_tracker.models import PricePoint
from car_investment_tracker.services.cache import cache


@cache.cached
def get_historical_prices(brand: str, model: str, year: int) -> list[PricePoint]:
    seed = hash(f"{brand}:{model}:{year}") & 0xFFFFFFFF
    rng = random.Random(seed)
    current_year = datetime.now(timezone.utc).year
    start_year = current_year - 19

    age = max(1, current_year - year)
    base = 12000 + (hash(brand + model) % 18000)
    depreciation = max(0.01, 0.085 - min(age, 20) * 0.002)

    data: list[PricePoint] = []
    price = float(base)
    for yr in range(start_year, current_year + 1):
        market_noise = rng.uniform(-0.04, 0.05)
        collector_bump = 0.02 if age > 15 and yr > current_year - 8 else 0
        growth = collector_bump - depreciation + market_noise
        price = max(2500.0, price * (1 + growth))
        data.append(PricePoint(year=yr, average_price=round(price, 2)))

    return data
