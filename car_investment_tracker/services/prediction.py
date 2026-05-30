from __future__ import annotations

from datetime import datetime, timezone

from car_investment_tracker.constants import MIN_PRICE_FLOOR_USD
from car_investment_tracker.models import PredictionPoint

NEUTRAL_SENTIMENT = 2.5
SENTIMENT_IMPACT_DIVISOR = 20
HISTORICAL_WEIGHT = 0.6
LISTING_WEIGHT = 0.4


def _linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0, y_mean

    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - slope * x_mean
    return slope, intercept


def predict_prices(
    historical_prices: list[float],
    listing_avg: float,
    sentiment_score: float,
    horizon_years: int = 5,
) -> list[PredictionPoint]:
    current_year = datetime.now(timezone.utc).year
    history_years = list(range(current_year - len(historical_prices) + 1, current_year + 1))

    slope, intercept = _linear_regression([float(y) for y in history_years], historical_prices)
    sentiment_modifier = 1 + ((sentiment_score - NEUTRAL_SENTIMENT) / SENTIMENT_IMPACT_DIVISOR)

    points: list[PredictionPoint] = []
    for year in range(current_year + 1, current_year + horizon_years + 1):
        baseline = slope * year + intercept
        blended = (baseline * HISTORICAL_WEIGHT + listing_avg * LISTING_WEIGHT) * sentiment_modifier
        points.append(PredictionPoint(year=year, predicted_price=round(max(MIN_PRICE_FLOOR_USD, blended), 2)))

    return points
