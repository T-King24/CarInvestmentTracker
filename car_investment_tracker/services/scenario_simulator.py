from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from car_investment_tracker.services.prediction import predict_prices


class ScenarioInput(BaseModel):
    """User-specified scenario for what-if analysis."""
    scenario_name: str = Field(description="Name of the scenario (e.g., 'Restoration Complete')")
    mileage_change_pct: float = Field(default=0, description="Mileage change as percentage (-100 to +100)")
    condition_improvement: int = Field(default=0, description="Condition improvement (0-4 grades: Poor->Fair->Average->Good->Excellent)")
    market_downturn_pct: float = Field(default=0, description="Market downturn percentage (0-100%)")
    storage_premium_years: int = Field(default=0, description="Years in storage (premium for rare vehicles)")


class ScenarioResult(BaseModel):
    """Result of a scenario simulation."""
    scenario_name: str
    base_price: float
    scenario_price: float
    price_change: float
    price_change_pct: float
    factors_applied: dict = Field(description="Breakdown of factors affecting the price")
    notes: str


def calculate_scenario_adjustment(
    base_price: float,
    scenario: ScenarioInput,
) -> ScenarioResult:
    """Calculate price adjustment for a specific scenario.
    
    Args:
        base_price: Current predicted price
        scenario: Scenario parameters
        
    Returns:
        ScenarioResult with adjusted price and explanation
    """
    adjusted_price = base_price
    factors = {}
    
    # Mileage impact: higher mileage = lower value
    # Each 10k miles reduces value by ~1.5%
    if scenario.mileage_change_pct != 0:
        mileage_multiplier = 1 - (abs(scenario.mileage_change_pct) / 100) * 0.015
        adjusted_price *= mileage_multiplier
        factors["mileage"] = {
            "change_pct": scenario.mileage_change_pct,
            "multiplier": round(mileage_multiplier, 3),
        }
    
    # Condition improvement: each grade improves value ~10%
    if scenario.condition_improvement > 0:
        condition_multiplier = 1 + (scenario.condition_improvement * 0.10)
        adjusted_price *= condition_multiplier
        factors["condition"] = {
            "grade_improvement": scenario.condition_improvement,
            "multiplier": round(condition_multiplier, 3),
        }
    
    # Market downturn: reduces value across the board
    if scenario.market_downturn_pct > 0:
        market_multiplier = 1 - (scenario.market_downturn_pct / 100)
        adjusted_price *= market_multiplier
        factors["market"] = {
            "downturn_pct": scenario.market_downturn_pct,
            "multiplier": round(market_multiplier, 3),
        }
    
    # Storage premium: classic cars stored gain value
    # ~3% per year if stored properly (up to 10 years)
    if scenario.storage_premium_years > 0:
        storage_years = min(scenario.storage_premium_years, 10)
        storage_multiplier = 1 + (storage_years * 0.03)
        adjusted_price *= storage_multiplier
        factors["storage"] = {
            "premium_years": storage_years,
            "multiplier": round(storage_multiplier, 3),
        }
    
    price_change = adjusted_price - base_price
    price_change_pct = (price_change / base_price * 100) if base_price > 0 else 0
    
    # Generate notes
    notes_parts = []
    if scenario.mileage_change_pct > 0:
        notes_parts.append(f"Mileage increase of {scenario.mileage_change_pct:.0f}%")
    elif scenario.mileage_change_pct < 0:
        notes_parts.append(f"Mileage decrease of {abs(scenario.mileage_change_pct):.0f}%")
    
    if scenario.condition_improvement > 0:
        notes_parts.append(f"Condition improved by {scenario.condition_improvement} grades")
    
    if scenario.market_downturn_pct > 0:
        notes_parts.append(f"Market downturn of {scenario.market_downturn_pct:.0f}%")
    
    if scenario.storage_premium_years > 0:
        notes_parts.append(f"Stored for {scenario.storage_premium_years} years (premium applied)")
    
    notes = "; ".join(notes_parts) if notes_parts else "No adjustments applied"
    
    return ScenarioResult(
        scenario_name=scenario.scenario_name,
        base_price=round(base_price, 2),
        scenario_price=round(adjusted_price, 2),
        price_change=round(price_change, 2),
        price_change_pct=round(price_change_pct, 2),
        factors_applied=factors,
        notes=notes,
    )


def compare_scenarios(
    base_price: float,
    scenarios: list[ScenarioInput],
) -> list[ScenarioResult]:
    """Compare multiple scenarios against a base price.
    
    Args:
        base_price: Current predicted price
        scenarios: List of scenarios to compare
        
    Returns:
        List of scenario results sorted by price change (best first)
    """
    results = []
    for scenario in scenarios:
        result = calculate_scenario_adjustment(base_price, scenario)
        results.append(result)
    
    # Sort by price change descending (best case first)
    results.sort(key=lambda r: r.price_change, reverse=True)
    
    return results
