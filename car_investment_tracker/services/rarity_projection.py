from __future__ import annotations

from pydantic import BaseModel, Field


class RarityProjection(BaseModel):
    """Long-term rarity and scarcity projection."""
    vehicle_model: str
    year: int
    production_year: int
    production_count_estimate: int = Field(description="Estimated production quantity")
    survival_rate_pct: float = Field(description="Estimated percentage still in existence")
    estimated_surviving_count: int = Field(description="Estimated count surviving today")
    rarity_score: int = Field(ge=1, le=10, description="Current rarity (1=common, 10=ultra-rare)")
    future_rarity_score_5yr: int = Field(description="Projected rarity in 5 years")
    future_rarity_score_10yr: int = Field(description="Projected rarity in 10 years")
    scarcity_drivers: list[str] = Field(description="Factors driving scarcity")
    value_driver_confidence: str = Field(description="Low, Medium, or High confidence in rarity driver")


def calculate_rarity_projection(brand: str, model: str, year: int) -> RarityProjection:
    """Project long-term scarcity based on production and survival data.
    
    Args:
        brand: Vehicle brand
        model: Vehicle model
        year: Vehicle year
        
    Returns:
        RarityProjection with current and future rarity scores
    """
    current_year = 2026
    age = current_year - year
    
    # Estimate production count based on brand/model/year
    # These are rough estimates; real data would come from production databases
    production_estimates = {
        ("porsche", "911"): 3000,
        ("porsche", "carrera"): 2500,
        ("porsche", "turbo"): 1200,
        ("porsche", "911rs"): 500,
        ("porsche", "930"): 2100,
        ("ferrari", "f40"): 311,
        ("ferrari", "f50"): 349,
        ("ferrari", "testarossa"): 4947,
        ("lamborghini", "countach"): 1999,
        ("lamborghini", "diablo"): 2884,
        ("bmw", "m3"): 4000,
        ("bmw", "m5"): 3500,
        ("mercedes", "sl"): 5000,
        ("jaguar", "xj220"): 282,
    }
    
    # Get production estimate
    prod_estimate = production_estimates.get(
        (brand.lower(), model.lower()),
        2500  # Default middle estimate
    )
    
    # Survival rate depends on age and brand durability
    # Classic cars from the 90s and 2000s have ~80-95% survival
    # Older cars have lower survival rates (50-80%)
    # Performance cars sometimes higher (collectors preserve them)
    if age < 10:
        survival_rate = 0.98
    elif age < 15:
        survival_rate = 0.95
    elif age < 20:
        survival_rate = 0.90
    elif age < 25:
        survival_rate = 0.85
    else:
        survival_rate = 0.75
    
    # Premium brands have higher survival (collectors preserve)
    if brand.lower() in ["porsche", "ferrari", "lamborghini"]:
        survival_rate = min(0.98, survival_rate + 0.10)
    
    estimated_surviving = int(prod_estimate * survival_rate)
    
    # Calculate rarity score
    # Fewer surviving = higher rarity
    # 1-100 surviving = 10/10 (ultra-rare)
    # 100-500 surviving = 8-9/10 (very rare)
    # 500-1000 surviving = 7-8/10 (rare)
    # 1000-2000 surviving = 5-7/10 (semi-rare)
    # 2000+ surviving = 1-5/10 (common to uncommon)
    
    if estimated_surviving < 100:
        rarity_score = 10
        scarcity_drivers = ["Very low production", "High attrition rate", "Collector scarcity"]
    elif estimated_surviving < 300:
        rarity_score = 9
        scarcity_drivers = ["Low production", "Active collector interest", "Age-related attrition"]
    elif estimated_surviving < 600:
        rarity_score = 8
        scarcity_drivers = ["Moderate production", "Collector demand", "Natural attrition"]
    elif estimated_surviving < 1200:
        rarity_score = 6
        scarcity_drivers = ["Growing scarcity", "Continued collector interest"]
    else:
        rarity_score = 4
        scarcity_drivers = ["Relatively common", "Still affordable for enthusiasts"]
    
    # Project future rarity (assuming 3-5% annual attrition)
    attrition_rate = 0.035
    
    # 5-year projection
    surviving_5yr = int(estimated_surviving * ((1 - attrition_rate) ** 5))
    if surviving_5yr < 100:
        future_rarity_5yr = 10
    elif surviving_5yr < 300:
        future_rarity_5yr = 9
    elif surviving_5yr < 600:
        future_rarity_5yr = 8
    elif surviving_5yr < 1200:
        future_rarity_5yr = 6
    else:
        future_rarity_5yr = 4
    
    # 10-year projection
    surviving_10yr = int(estimated_surviving * ((1 - attrition_rate) ** 10))
    if surviving_10yr < 100:
        future_rarity_10yr = 10
    elif surviving_10yr < 300:
        future_rarity_10yr = 9
    elif surviving_10yr < 600:
        future_rarity_10yr = 8
    elif surviving_10yr < 1200:
        future_rarity_10yr = 6
    else:
        future_rarity_10yr = 4
    
    # Confidence assessment
    if age > 25:
        confidence = "High"
    elif age > 15:
        confidence = "Medium"
    else:
        confidence = "Low"  # Too recent to have reliable data
    
    return RarityProjection(
        vehicle_model=f"{brand} {model}",
        year=year,
        production_year=year,
        production_count_estimate=prod_estimate,
        survival_rate_pct=round(survival_rate * 100, 1),
        estimated_surviving_count=estimated_surviving,
        rarity_score=rarity_score,
        future_rarity_score_5yr=future_rarity_5yr,
        future_rarity_score_10yr=future_rarity_10yr,
        scarcity_drivers=scarcity_drivers,
        value_driver_confidence=confidence,
    )
