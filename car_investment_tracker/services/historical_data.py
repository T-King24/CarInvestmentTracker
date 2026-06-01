from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import random

from car_investment_tracker.constants import MIN_PRICE_FLOOR_GBP
from car_investment_tracker.models import PricePoint
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.current_listings import (
    age_value_factor,
    estimate_market_value_gbp,
)

# Upper bound on the number of historical points generated, guarding against
# absurd inputs (e.g. a year of 1900). Catalogued cars never reach this cap, so
# the chart still spans the entire life of the car since its model year.
MAX_HISTORY_YEARS = 80

# UK inflation rate (approximate annual average): 2.5%
ANNUAL_INFLATION_RATE = 0.025

# Pricing basis is shared with current_listings (see estimate_market_value_gbp
# and age_value_factor) so the most recent historical point lands on today's
# market average, preventing a discontinuous jump between the historical line
# and the forecast.


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part).strip().lower() for part in parts).encode()).hexdigest()
    return int(digest[:16], 16)


def _current_market_value(brand: str, model: str, year: int, current_year: int) -> float:
    """Today's market value, using the exact same basis as current_listings."""
    return max(MIN_PRICE_FLOOR_GBP, estimate_market_value_gbp(brand, model, year))


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

    # Span the entire life of the car: from its model year through to today,
    # rather than a fixed trailing window. Clamp so we never start after the
    # current year and never exceed the safety cap for extreme inputs.
    model_year = min(year, current_year)
    start_year = max(model_year, current_year - MAX_HISTORY_YEARS + 1)

    # Anchor: today's value, then derive an implied "as-new" price so the arc
    # passes through the current market value at the current year.
    anchor_value = _current_market_value(brand, model, year, current_year)
    age_now = max(0, current_year - model_year)
    as_new_price = anchor_value / age_value_factor(age_now)

    data: list[PricePoint] = []
    for yr in range(start_year, current_year + 1):
        age_in_year = max(0, yr - year)
        base_value = as_new_price * age_value_factor(age_in_year)

        # Small deterministic market noise for a believable, non-robotic line.
        market_noise = 1.0 + rng.uniform(-0.02, 0.02)
        nominal_price = max(MIN_PRICE_FLOOR_GBP, base_value * market_noise)

        inflation_factor = _inflation_adjustment(yr, current_year)
        inflation_adjusted_price = nominal_price * inflation_factor

        data.append(PricePoint(
            year=yr,
            average_price=round(nominal_price, 2),
            nominal_price=round(nominal_price, 2),
            inflation_adjusted_price=round(inflation_adjusted_price, 2),
        ))

    return data
