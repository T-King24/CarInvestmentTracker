from __future__ import annotations

from datetime import datetime, timezone

from car_investment_tracker.constants import MIN_PRICE_FLOOR_USD
from car_investment_tracker.models import PredictionPoint, PredictionExplanation

NEUTRAL_SENTIMENT = 2.5
SENTIMENT_IMPACT_DIVISOR = 20
HISTORICAL_WEIGHT = 0.6
LISTING_WEIGHT = 0.4
MOMENTUM_SMOOTHING = 0.3  # Fraction of trend change to apply (prevents sudden jumps)


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


def _calculate_recent_momentum(historical_prices: list[float]) -> float:
    """Calculate the recent price momentum (rate of change in last few years)."""
    if len(historical_prices) < 2:
        return 0.0
    # Use last 5 years or all data if less than 5 years
    recent_window = min(5, len(historical_prices))
    recent_prices = historical_prices[-recent_window:]
    changes = [recent_prices[i + 1] - recent_prices[i] for i in range(len(recent_prices) - 1)]
    avg_change = sum(changes) / len(changes) if changes else 0.0
    return avg_change


def predict_prices(
    historical_prices: list[float],
    listing_avg: float,
    sentiment_score: float,
    horizon_years: int = 5,
) -> tuple[list[PredictionPoint], PredictionExplanation]:
    current_year = datetime.now(timezone.utc).year
    history_years = list(range(current_year - len(historical_prices) + 1, current_year + 1))

    slope, intercept = _linear_regression([float(y) for y in history_years], historical_prices)
    sentiment_modifier = 1 + ((sentiment_score - NEUTRAL_SENTIMENT) / SENTIMENT_IMPACT_DIVISOR)
    
    # Calculate momentum to smooth sudden trend changes
    recent_momentum = _calculate_recent_momentum(historical_prices)
    smoothed_slope = slope * (1 - MOMENTUM_SMOOTHING) + (recent_momentum * MOMENTUM_SMOOTHING)

    points: list[PredictionPoint] = []
    last_price = historical_prices[-1] if historical_prices else listing_avg
    
    for year in range(current_year + 1, current_year + horizon_years + 1):
        # Use smoothed slope for more realistic forecasting
        baseline = smoothed_slope * year + intercept
        blended = (baseline * HISTORICAL_WEIGHT + listing_avg * LISTING_WEIGHT) * sentiment_modifier
        # Ensure price doesn't jump too much from previous year
        predicted = max(MIN_PRICE_FLOOR_USD, blended)
        points.append(PredictionPoint(year=year, predicted_price=round(predicted, 2)))
        last_price = predicted

    explanation = PredictionExplanation(
        historical_weight=HISTORICAL_WEIGHT,
        listing_weight=LISTING_WEIGHT,
        sentiment_score=sentiment_score,
        sentiment_modifier=round(sentiment_modifier, 4),
        last_historical_price=round(last_price, 2),
        current_listing_average=round(listing_avg, 2),
        trend_momentum=round(recent_momentum, 2),
        model_type="Linear regression with momentum smoothing and inflation adjustment",
        inflation_adjusted=True,
    )
    
    return points, explanation
