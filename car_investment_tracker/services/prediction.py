from __future__ import annotations

from datetime import datetime, timezone

from car_investment_tracker.models import PredictionPoint


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
    sentiment_modifier = 1 + ((sentiment_score - 2.5) / 20)

    points: list[PredictionPoint] = []
    for year in range(current_year + 1, current_year + horizon_years + 1):
        baseline = slope * year + intercept
        blended = (baseline * 0.6 + listing_avg * 0.4) * sentiment_modifier
        points.append(PredictionPoint(year=year, predicted_price=round(max(2500.0, blended), 2)))

    return points
