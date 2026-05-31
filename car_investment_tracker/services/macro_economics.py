from __future__ import annotations

from pydantic import BaseModel, Field


class EconomicIndicator(BaseModel):
    """Economic indicator affecting vehicle valuations."""
    year: int
    indicator_name: str
    value: float
    unit: str = Field(description="Unit of measurement (e.g., '%', 'index points')")
    impact_on_luxury_cars: str = Field(description="'Positive', 'Negative', 'Neutral'")


class MacroEconomicContext(BaseModel):
    """Macro-economic context for vehicle valuations."""
    current_gdp_growth: float = Field(description="Current GDP growth rate (%)")
    unemployment_rate: float = Field(description="Current unemployment rate (%)")
    inflation_rate: float = Field(description="Current inflation rate (%)")
    interest_rates: float = Field(description="Current interest rates (%)")
    consumer_confidence: float = Field(description="Consumer confidence index (0-100)")
    luxury_market_sentiment: str = Field(description="'Strong', 'Neutral', or 'Weak'")
    economic_outlook: str = Field(description="Short-term economic outlook")
    impact_on_vehicle_prices: str = Field(description="Expected impact on this asset class")
    historical_correlations: dict = Field(description="Historical correlation with vehicle prices")


def get_macroeconomic_context() -> MacroEconomicContext:
    """Get current macro-economic context and its impact on vehicle valuations.
    
    In production, this would fetch real-time data from FRED, World Bank, etc.
    Currently returns simulated data based on 2026 estimates.
    
    Returns:
        MacroEconomicContext with current indicators and outlook
    """
    # Simulated 2026 data (for demonstration)
    # In production, fetch from APIs like:
    # - Federal Reserve Economic Data (FRED)
    # - World Bank API
    # - OECD Statistics
    # - Bloomberg
    
    current_year = 2026
    
    # Simulated economic indicators for 2026
    # Note: These are illustrative values
    gdp_growth = 2.1  # Moderate growth
    unemployment_rate = 4.2  # Stable
    inflation_rate = 2.8  # Slightly elevated
    interest_rates = 4.5  # Moderately high
    consumer_confidence = 68.5  # Below historical average of 100
    
    # Determine luxury market sentiment
    if gdp_growth > 2.5 and unemployment_rate < 4.0:
        luxury_sentiment = "Strong"
    elif gdp_growth < 1.5 or unemployment_rate > 5.0:
        luxury_sentiment = "Weak"
    else:
        luxury_sentiment = "Neutral"
    
    # Economic outlook
    if gdp_growth > 2.5:
        outlook = "Expansion expected"
    elif gdp_growth < 0.5:
        outlook = "Recession risk"
    else:
        outlook = "Moderate growth continuation"
    
    # Impact on vehicle prices
    # High interest rates reduce financing appeal
    # Low unemployment supports collector purchases
    # Inflation affects maintenance/ownership costs
    if interest_rates > 5.0:
        vehicle_impact = "Headwinds: High rates reduce financing appeal, especially for expensive vehicles"
    elif unemployment_rate > 5.0:
        vehicle_impact = "Headwinds: Higher unemployment reduces collector purchasing power"
    elif inflation_rate > 3.5:
        vehicle_impact = "Mixed: Inflation increases maintenance costs but can drive collector interest"
    else:
        vehicle_impact = "Tailwinds: Favorable conditions support luxury vehicle demand and values"
    
    # Historical correlations
    correlations = {
        "gdp_growth": 0.68,  # Moderate positive correlation
        "unemployment": -0.55,  # Negative correlation (rising unemployment = lower prices)
        "inflation": 0.42,  # Positive correlation (can drive scarcity value)
        "interest_rates": -0.38,  # Negative correlation (discourages financing)
        "consumer_confidence": 0.72,  # Strong positive correlation
    }
    
    return MacroEconomicContext(
        current_gdp_growth=gdp_growth,
        unemployment_rate=unemployment_rate,
        inflation_rate=inflation_rate,
        interest_rates=interest_rates,
        consumer_confidence=consumer_confidence,
        luxury_market_sentiment=luxury_sentiment,
        economic_outlook=outlook,
        impact_on_vehicle_prices=vehicle_impact,
        historical_correlations=correlations,
    )


def calculate_economic_price_adjustment(
    base_price: float,
    gdp_growth: float = None,
    unemployment_rate: float = None,
    interest_rates: float = None,
) -> dict:
    """Calculate price adjustment based on macro-economic factors.
    
    Args:
        base_price: Base vehicle price
        gdp_growth: GDP growth rate (%)
        unemployment_rate: Unemployment rate (%)
        interest_rates: Current interest rates (%)
        
    Returns:
        Dict with adjusted price and adjustment factors
    """
    if not (gdp_growth or unemployment_rate or interest_rates):
        context = get_macroeconomic_context()
        gdp_growth = context.current_gdp_growth
        unemployment_rate = context.unemployment_rate
        interest_rates = context.interest_rates
    
    adjustment_factor = 1.0
    factors = {}
    
    # GDP impact (±3% for 1% growth change)
    if gdp_growth:
        # Compare to historical average of ~2.5%
        gdp_delta = gdp_growth - 2.5
        gdp_adjustment = 1 + (gdp_delta * 0.03)
        adjustment_factor *= gdp_adjustment
        factors["gdp"] = {
            "rate": gdp_growth,
            "multiplier": round(gdp_adjustment, 3),
        }
    
    # Unemployment impact (±4% for 1% unemployment change)
    if unemployment_rate:
        # Compare to historical average of ~4%
        unemployment_delta = unemployment_rate - 4.0
        unemployment_adjustment = 1 - (unemployment_delta * 0.04)
        adjustment_factor *= unemployment_adjustment
        factors["unemployment"] = {
            "rate": unemployment_rate,
            "multiplier": round(unemployment_adjustment, 3),
        }
    
    # Interest rate impact (±2% for 1% rate change)
    if interest_rates:
        # Compare to historical average of ~4%
        rate_delta = interest_rates - 4.0
        rate_adjustment = 1 - (rate_delta * 0.02)
        adjustment_factor *= rate_adjustment
        factors["interest_rates"] = {
            "rate": interest_rates,
            "multiplier": round(rate_adjustment, 3),
        }
    
    adjusted_price = base_price * adjustment_factor
    
    return {
        "base_price": round(base_price, 2),
        "adjusted_price": round(adjusted_price, 2),
        "total_adjustment": round(adjustment_factor, 3),
        "price_change": round(adjusted_price - base_price, 2),
        "factors": factors,
    }
