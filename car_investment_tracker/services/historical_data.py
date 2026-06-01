from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import random

from car_investment_tracker.constants import MIN_PRICE_FLOOR_USD
from car_investment_tracker.models import PricePoint
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.current_listings import estimate_market_value_gbp

# Number of calendar years shown in the historical window (ends at the current year).
HISTORY_WINDOW_YEARS = 20

# Depreciation/appreciation shape parameters used to build a realistic value arc.
ANNUAL_DEPRECIATION_FACTOR = 0.90  # value retained per year while the car is depreciating
DEPRECIATION_FLOOR = 0.30          # value never falls below this fraction of the "as-new" price
CLASSIC_AGE_THRESHOLD = 15         # cars at/over this age start to appreciate as classics
CLASSIC_APPRECIATION_PER_YEAR = 0.03

# Pricing basis is shared with current_listings (see estimate_market_value_gbp) so the
# most recent historical point lands on today's market average, preventing a
# discontinuous jump between the historical line and the forecast.

# UK inflation rate (approximate annual average): 2.5%
ANNUAL_INFLATION_RATE = 0.025


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part).strip().lower() for part in parts).encode()).hexdigest()
    return int(digest[:16], 16)


def _current_market_value(brand: str, model: str, year: int, current_year: int) -> float:
    """Today's market value, using the exact same basis as current_listings."""
    return max(MIN_PRICE_FLOOR_USD, estimate_market_value_gbp(brand, model, year))


def _age_value_factor(age: int) -> float:
    """Relative value of a vehicle at a given age (age 0 == as-new == 1.0).

    Vehicles depreciate towards a floor; once they reach classic age they
    gently appreciate again.
    """
    if age <= 0:
        return 1.0
    depreciated = DEPRECIATION_FLOOR + (1.0 - DEPRECIATION_FLOOR) * (ANNUAL_DEPRECIATION_FACTOR ** age)
    if age >= CLASSIC_AGE_THRESHOLD:
        depreciated *= 1.0 + (age - CLASSIC_AGE_THRESHOLD) * CLASSIC_APPRECIATION_PER_YEAR
    return depreciated


def _inflation_adjustment(year: int, base_year: int) -> float:
    """Inflation multiplier converting a price from ``year`` into ``base_year`` money.

    E.g. a £1000 car in 2000 is worth £1000 * adjustment_factor in today's money.
    """
    years_difference = base_year - year
    return (1 + ANNUAL_INFLATION_RATE) ** years_difference


@cache.cached
def get_historical_prices(brand: str, model: str, year: int) -> list[PricePoint]:
    seed = _stable_seed("historical", brand, model, year) & 0xFFFFFFFF
    rng = random.Random(seed)
    current_year = datetime.now(timezone.utc).year

    # Fixed 20-year window ending at the current year.
    start_year = current_year - HISTORY_WINDOW_YEARS + 1

    # Anchor: today's value, then derive an implied "as-new" price so the arc
    # passes through the current market value at the current year.
    anchor_value = _current_market_value(brand, model, year, current_year)
    age_now = max(0, current_year - min(year, current_year))
    as_new_price = anchor_value / _age_value_factor(age_now)

    data: list[PricePoint] = []
    for yr in range(start_year, current_year + 1):
        age_in_year = yr - year  # negative before the car existed -> treated as as-new
        base_value = as_new_price * _age_value_factor(age_in_year)

        # Small deterministic market noise for a believable, non-robotic line.
        market_noise = 1.0 + rng.uniform(-0.02, 0.02)
        nominal_price = max(MIN_PRICE_FLOOR_USD, base_value * market_noise)

        inflation_factor = _inflation_adjustment(yr, current_year)
        inflation_adjusted_price = nominal_price * inflation_factor

        data.append(PricePoint(
            year=yr,
            average_price=round(nominal_price, 2),
            nominal_price=round(nominal_price, 2),
            inflation_adjusted_price=round(inflation_adjusted_price, 2),
        ))

    return data
