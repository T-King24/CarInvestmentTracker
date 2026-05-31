from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class OwnershipCostBreakdown(BaseModel):
    """Annual ownership costs breakdown."""
    vehicle_price: float = Field(description="Purchase price of vehicle")
    annual_depreciation: float = Field(description="Estimated annual depreciation (yearly)")
    annual_insurance: float = Field(description="Estimated annual insurance cost")
    annual_maintenance: float = Field(description="Estimated annual maintenance cost")
    annual_storage: float = Field(description="Estimated annual storage/parking cost")
    total_annual_cost: float = Field(description="Total annual ownership cost")
    cost_per_mile: float = Field(description="Estimated cost per mile driven (assuming 12k miles/year)")
    depreciation_rate: float = Field(description="Annual depreciation as % of vehicle price")


def calculate_ownership_costs(
    vehicle_price: float,
    vehicle_brand: str,
    vehicle_year: int,
    annual_miles: int = 12000,
) -> OwnershipCostBreakdown:
    """Calculate total cost of ownership for a vehicle.
    
    Args:
        vehicle_price: Current purchase price in USD
        vehicle_brand: Vehicle brand (affects insurance/maintenance)
        vehicle_year: Vehicle year
        annual_miles: Expected annual miles (default 12k)
        
    Returns:
        OwnershipCostBreakdown with all cost components
    """
    current_year = datetime.now(timezone.utc).year
    age = current_year - vehicle_year
    
    # Depreciation: typically 15-20% first year, then 10-15% annually for used cars
    # For older vehicles, depreciation slows
    if age < 1:
        annual_depreciation_rate = 0.15
    elif age < 5:
        annual_depreciation_rate = 0.12
    else:
        annual_depreciation_rate = 0.08
    
    annual_depreciation = vehicle_price * annual_depreciation_rate
    
    # Insurance varies by brand and age
    # Base: ~$1000-1500/year for typical vehicles
    # Luxury brands (Porsche, BMW, Mercedes) 25-50% higher
    # Classic/older vehicles sometimes cheaper
    
    insurance_base = 1200
    brand_multiplier = 1.0
    
    if vehicle_brand.lower() in ["porsche", "ferrari", "lamborghini", "bentley"]:
        brand_multiplier = 1.5
    elif vehicle_brand.lower() in ["bmw", "mercedes", "audi", "jaguar"]:
        brand_multiplier = 1.3
    elif vehicle_brand.lower() in ["lexus", "cadillac"]:
        brand_multiplier = 1.1
    
    # Age can reduce insurance on older vehicles (25+ years)
    if age >= 25:
        brand_multiplier *= 0.8
    
    annual_insurance = insurance_base * brand_multiplier
    
    # Maintenance: ~0.5-1.5% of vehicle price annually
    # Luxury/performance brands higher, older vehicles higher
    maintenance_rate = 0.01
    if vehicle_brand.lower() in ["porsche", "ferrari", "lamborghini"]:
        maintenance_rate = 0.03
    elif vehicle_brand.lower() in ["bmw", "mercedes", "audi"]:
        maintenance_rate = 0.02
    
    # Age increases maintenance needs
    if age > 10:
        maintenance_rate *= 1.3
    if age > 20:
        maintenance_rate *= 1.5
    
    annual_maintenance = vehicle_price * maintenance_rate
    
    # Storage/Parking: $50-150/month depending on location
    # Classic cars stored indoors more often
    if age >= 25:
        monthly_storage = 120  # Climate-controlled for classics
    else:
        monthly_storage = 0  # Assume owner has driveway/parking
    
    annual_storage = monthly_storage * 12
    
    # Total annual cost
    total_annual_cost = annual_depreciation + annual_insurance + annual_maintenance + annual_storage
    
    # Cost per mile
    cost_per_mile = total_annual_cost / annual_miles if annual_miles > 0 else 0
    
    return OwnershipCostBreakdown(
        vehicle_price=round(vehicle_price, 2),
        annual_depreciation=round(annual_depreciation, 2),
        annual_insurance=round(annual_insurance, 2),
        annual_maintenance=round(annual_maintenance, 2),
        annual_storage=round(annual_storage, 2),
        total_annual_cost=round(total_annual_cost, 2),
        cost_per_mile=round(cost_per_mile, 2),
        depreciation_rate=round(annual_depreciation_rate * 100, 1),
    )
