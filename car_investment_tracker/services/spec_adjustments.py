from __future__ import annotations

from pydantic import BaseModel, Field


class SpecAdjustments(BaseModel):
    """Vehicle specification adjustments."""
    transmission: str = Field(default="Manual", description="Manual, Automatic, or Tiptronic")
    trim_level: str = Field(default="Base", description="Base, Standard, Premium, or Sport")
    condition: str = Field(default="Average", description="Poor, Fair, Average, Good, or Excellent")
    mileage_bracket: str = Field(default="Normal", description="Low (0-50k), Normal (50-100k), High (100k+)")


class PriceAdjustmentFactors(BaseModel):
    """Price adjustment multipliers based on specs."""
    transmission_factor: float = Field(description="Price multiplier for transmission type")
    trim_factor: float = Field(description="Price multiplier for trim level")
    condition_factor: float = Field(description="Price multiplier for condition")
    mileage_factor: float = Field(description="Price multiplier for mileage bracket")
    total_adjustment: float = Field(description="Combined adjustment factor")
    adjusted_price: float = Field(description="Price after all adjustments")


# Specification adjustment multipliers
TRANSMISSION_MULTIPLIERS = {
    "manual": 0.95,  # Typically less valuable in modern market
    "automatic": 1.0,  # Baseline
    "tiptronic": 1.05,  # Premium for semi-automatic
    "dct": 1.08,  # Dual-clutch transmission premium
}

TRIM_MULTIPLIERS = {
    "base": 0.90,
    "standard": 1.0,
    "premium": 1.10,
    "sport": 1.15,
    "rs": 1.25,  # High-performance versions
    "turbo": 1.20,
    "carrera": 1.15,
}

CONDITION_MULTIPLIERS = {
    "poor": 0.70,  # Major issues, needs work
    "fair": 0.80,  # Notable wear, some issues
    "average": 1.0,  # Normal wear for age/mileage
    "good": 1.10,  # Well-maintained, minor cosmetic wear
    "excellent": 1.25,  # Showroom condition or very well preserved
}

MILEAGE_MULTIPLIERS = {
    "low": 1.15,  # 0-50k miles: higher value
    "normal": 1.0,  # 50-100k miles: baseline
    "high": 0.85,  # 100k+ miles: lower value
}


def calculate_spec_adjustments(
    base_price: float,
    transmission: str = "Automatic",
    trim_level: str = "Standard",
    condition: str = "Average",
    mileage_bracket: str = "Normal",
) -> PriceAdjustmentFactors:
    """Calculate price adjustments based on vehicle specifications.
    
    Args:
        base_price: Base vehicle price before adjustments
        transmission: Transmission type
        trim_level: Trim level variant
        condition: Vehicle condition
        mileage_bracket: Mileage bracket
        
    Returns:
        PriceAdjustmentFactors with adjustment multipliers and adjusted price
    """
    # Get multipliers, default to 1.0 if not found
    trans_mult = TRANSMISSION_MULTIPLIERS.get(transmission.lower(), 1.0)
    trim_mult = TRIM_MULTIPLIERS.get(trim_level.lower(), 1.0)
    cond_mult = CONDITION_MULTIPLIERS.get(condition.lower(), 1.0)
    mileage_mult = MILEAGE_MULTIPLIERS.get(mileage_bracket.lower(), 1.0)
    
    # Calculate combined adjustment
    # Specs work multiplicatively: base * trans * trim * condition * mileage
    total_adjustment = trans_mult * trim_mult * cond_mult * mileage_mult
    adjusted_price = base_price * total_adjustment
    
    return PriceAdjustmentFactors(
        transmission_factor=round(trans_mult, 3),
        trim_factor=round(trim_mult, 3),
        condition_factor=round(cond_mult, 3),
        mileage_factor=round(mileage_mult, 3),
        total_adjustment=round(total_adjustment, 3),
        adjusted_price=round(adjusted_price, 2),
    )


def adjust_prices_for_specs(
    prices: list[float],
    transmission: str = "Automatic",
    trim_level: str = "Standard",
    condition: str = "Average",
    mileage_bracket: str = "Normal",
) -> list[float]:
    """Apply spec adjustments to a list of historical prices.
    
    Args:
        prices: List of historical prices
        transmission: Transmission type
        trim_level: Trim level
        condition: Condition
        mileage_bracket: Mileage bracket
        
    Returns:
        List of adjusted prices
    """
    # Get adjustment factor
    adjustment = calculate_spec_adjustments(
        1.0,  # Use 1.0 as base to get just the multiplier
        transmission=transmission,
        trim_level=trim_level,
        condition=condition,
        mileage_bracket=mileage_bracket,
    )
    
    return [round(p * adjustment.total_adjustment, 2) for p in prices]
