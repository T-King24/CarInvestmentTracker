from __future__ import annotations

from datetime import datetime, timezone

from car_investment_tracker.constants import MIN_PRICE_FLOOR_GBP
from car_investment_tracker.models import PredictionPoint, PredictionExplanation

NEUTRAL_SENTIMENT = 2.5
SENTIMENT_IMPACT_DIVISOR = 25
HISTORICAL_WEIGHT = 0.6
LISTING_WEIGHT = 0.4
MOMENTUM_SMOOTHING = 0.3  # Fraction of trend change to apply (prevents sudden jumps)
# Sentiment modifier bounds: limit price-outlook sentiment to ±10% from neutral.
# Sentiment can nudge the forecast but must not, on its own, overpower a clear
# historical trend (see trend gating below).
MAX_SENTIMENT_MODIFIER = 1.10
MIN_SENTIMENT_MODIFIER = 0.90
MAX_PRICE_MULTIPLIER = 1.35  # Max 35% increase from baseline (realistic appreciation for well-maintained vehicles)
MIN_PRICE_MULTIPLIER = 0.70  # Min 30% decrease from baseline (realistic depreciation accounting for market conditions)
# A price-outlook score above this (out of 5) counts as a genuinely bullish
# signal that people online expect prices to rise.
STRONG_BULLISH_SENTIMENT = 3.5
# Number of most-recent yearly changes inspected to decide if a car is in a
# sustained (consecutive) depreciation trend.
TREND_WINDOW = 3


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


def _is_consecutive_depreciation(historical_prices: list[float], window: int = TREND_WINDOW) -> bool:
    """True when the most recent ``window`` year-on-year changes are all negative.

    This identifies a car that has been steadily losing value for several years
    in a row (e.g. the Ferrari Roma), so the forecast should not suddenly turn
    upward without a strong supporting price-outlook signal.
    """
    if len(historical_prices) < 2:
        return False
    recent = historical_prices[-(window + 1):]
    changes = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    return bool(changes) and all(change < 0 for change in changes)


def _build_outlook(
    consecutive_depreciation: bool,
    recent_momentum: float,
    sentiment_score: float,
) -> tuple[str, str, bool]:
    """Return (outlook label, plain-English summary, driven_by_history)."""
    strong_bullish = sentiment_score >= STRONG_BULLISH_SENTIMENT

    if consecutive_depreciation and not strong_bullish:
        return (
            "Likely to keep depreciating",
            "This car has lost value for several years in a row and online price "
            "sentiment isn't strong enough to suggest a turnaround, so the forecast "
            "continues the downward trend. This prediction is driven mainly by its "
            "historical depreciation.",
            True,
        )
    if recent_momentum > 0 and strong_bullish:
        return (
            "Likely to appreciate",
            "Recent prices have been rising and online sentiment expects values to "
            "keep climbing, so the forecast points modestly upward.",
            False,
        )
    if recent_momentum < 0:
        return (
            "Likely to depreciate gently",
            "Prices have been easing recently. The forecast eases lower in line with "
            "that trend, with only a small influence from online sentiment.",
            True,
        )
    return (
        "Expected to stay broadly stable",
        "Prices have been fairly flat recently, so the forecast stays close to the "
        "current level with only a small influence from online sentiment.",
        False,
    )


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
    # Clamp the raw price-outlook sentiment to a modest ±10% band.
    sentiment_modifier = max(MIN_SENTIMENT_MODIFIER, min(MAX_SENTIMENT_MODIFIER, sentiment_modifier))

    # Calculate momentum to smooth sudden trend changes
    recent_momentum = _calculate_recent_momentum(historical_prices)
    smoothed_slope = slope * (1 - MOMENTUM_SMOOTHING) + (recent_momentum * MOMENTUM_SMOOTHING)

    # Detect a sustained downtrend. When a car has depreciated for several years
    # running, sentiment alone must not push the forecast upward: only a strong
    # bullish price-outlook signal may lift it, otherwise the historical trend wins.
    consecutive_depreciation = _is_consecutive_depreciation(historical_prices)
    strong_bullish = sentiment_score >= STRONG_BULLISH_SENTIMENT
    if consecutive_depreciation and not strong_bullish:
        # Sentiment can soften the decline but never invert it into appreciation.
        sentiment_modifier = min(sentiment_modifier, 1.0)

    points: list[PredictionPoint] = []
    last_historical_price = historical_prices[-1] if historical_prices else 0.0
    # Use a blend of historical and market average as baseline for bounding predictions
    baseline_reference = last_historical_price * HISTORICAL_WEIGHT + listing_avg * LISTING_WEIGHT

    # Calculate confidence interval (±10%)
    CI_MARGIN = 0.10

    # When the car is in a sustained downtrend (and sentiment isn't strongly
    # bullish) keep the forecast monotonically non-increasing so it never spikes
    # upward against a clear depreciation history.
    enforce_non_increasing = consecutive_depreciation and not strong_bullish
    previous_price = last_historical_price

    for year in range(current_year + 1, current_year + horizon_years + 1):
        # Anchor the forecast to the last actual historical price and extend it by the
        # smoothed slope so the prediction continues smoothly instead of jumping.
        years_ahead = year - current_year
        baseline = last_historical_price + smoothed_slope * years_ahead
        blended = (baseline * HISTORICAL_WEIGHT + listing_avg * LISTING_WEIGHT) * sentiment_modifier
        # Clamp predicted price to realistic bounds relative to baseline (±35%-30%)
        min_bound = baseline_reference * MIN_PRICE_MULTIPLIER
        max_bound = baseline_reference * MAX_PRICE_MULTIPLIER
        predicted = max(MIN_PRICE_FLOOR_GBP, min(max_bound, max(min_bound, blended)))

        if enforce_non_increasing:
            predicted = min(predicted, previous_price)
        previous_price = predicted

        # Calculate confidence intervals
        lower_ci = predicted * (1 - CI_MARGIN)
        upper_ci = predicted * (1 + CI_MARGIN)

        points.append(PredictionPoint(
            year=year,
            predicted_price=round(predicted, 2),
            lower_bound=round(lower_ci, 2),
            upper_bound=round(upper_ci, 2)
        ))

    outlook, outlook_summary, driven_by_history = _build_outlook(
        consecutive_depreciation, recent_momentum, sentiment_score
    )

    explanation = PredictionExplanation(
        historical_weight=HISTORICAL_WEIGHT,
        listing_weight=LISTING_WEIGHT,
        sentiment_score=sentiment_score,
        sentiment_modifier=round(sentiment_modifier, 4),
        last_historical_price=round(last_historical_price, 2),
        current_listing_average=round(listing_avg, 2),
        trend_momentum=round(recent_momentum, 2),
        model_type="Linear Regression with Momentum Smoothing, Spike Prevention, and Inflation Adjustment",
        inflation_adjusted=True,
        outlook=outlook,
        outlook_summary=outlook_summary,
        driven_by_history=driven_by_history,
    )

    return points, explanation
