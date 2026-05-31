from __future__ import annotations

import math
from car_investment_tracker.models import VolatilityMetrics


def calculate_volatility_metrics(prices: list[float]) -> VolatilityMetrics:
    """Calculate volatility metrics from historical prices.
    
    Args:
        prices: List of historical prices
        
    Returns:
        VolatilityMetrics with coefficient of variation and volatility score
    """
    if not prices or len(prices) < 2:
        return VolatilityMetrics(
            coefficient_of_variation=0.0,
            standard_deviation=0.0,
            volatility_score=1,
            price_range=0.0,
            stability_assessment="Insufficient data"
        )
    
    # Calculate mean
    mean_price = sum(prices) / len(prices)
    
    # Calculate standard deviation
    variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
    std_dev = math.sqrt(variance)
    
    # Calculate coefficient of variation (std dev / mean)
    # Handles edge case where mean is near zero
    if mean_price > 0:
        cv = std_dev / mean_price
    else:
        cv = 0.0
    
    # Price range (max - min)
    price_range = max(prices) - min(prices)
    
    # Map CV to 1-10 volatility score
    # CV < 0.05: Very Stable (1-2)
    # CV 0.05-0.10: Stable (3-4)
    # CV 0.10-0.15: Moderate (5-6)
    # CV 0.15-0.20: Volatile (7-8)
    # CV > 0.20: Highly Volatile (9-10)
    
    if cv < 0.05:
        volatility_score = 1
        assessment = "Very Stable - Predictable pricing, low market volatility"
    elif cv < 0.10:
        volatility_score = 3
        assessment = "Stable - Consistent pricing with minor fluctuations"
    elif cv < 0.15:
        volatility_score = 5
        assessment = "Moderate - Moderate price variations across auctions"
    elif cv < 0.20:
        volatility_score = 7
        assessment = "Volatile - Significant price variations, higher risk"
    else:
        volatility_score = 9
        assessment = "Highly Volatile - Prices vary widely, unpredictable market"
    
    return VolatilityMetrics(
        coefficient_of_variation=round(cv, 4),
        standard_deviation=round(std_dev, 2),
        volatility_score=volatility_score,
        price_range=round(price_range, 2),
        stability_assessment=assessment
    )
