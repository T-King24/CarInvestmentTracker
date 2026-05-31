from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime


class PortfolioVehicle(BaseModel):
    """Vehicle in a user's portfolio."""
    id: str = Field(description="Unique vehicle ID")
    brand: str
    model: str
    year: int
    purchase_price: float
    current_estimated_value: float
    acquisition_date: str = Field(description="ISO date string")
    notes: str = Field(default="")


class PortfolioMetrics(BaseModel):
    """Portfolio-level performance metrics."""
    total_vehicles: int = Field(description="Number of vehicles in portfolio")
    total_acquisition_cost: float = Field(description="Total purchase price")
    total_current_value: float = Field(description="Total estimated current value")
    portfolio_gain_loss: float = Field(description="Total gain or loss")
    portfolio_return_pct: float = Field(description="Overall return percentage")
    average_annual_return: float = Field(description="Average annual return")
    best_performing_vehicle: str = Field(description="Best performing vehicle ID")
    worst_performing_vehicle: str = Field(description="Worst performing vehicle ID")


def calculate_portfolio_metrics(vehicles: list[PortfolioVehicle]) -> PortfolioMetrics:
    """Calculate aggregate metrics for a vehicle portfolio.
    
    Args:
        vehicles: List of vehicles in portfolio
        
    Returns:
        PortfolioMetrics with aggregate performance data
    """
    if not vehicles:
        return PortfolioMetrics(
            total_vehicles=0,
            total_acquisition_cost=0,
            total_current_value=0,
            portfolio_gain_loss=0,
            portfolio_return_pct=0,
            average_annual_return=0,
            best_performing_vehicle="",
            worst_performing_vehicle="",
        )
    
    total_acquisition_cost = sum(v.purchase_price for v in vehicles)
    total_current_value = sum(v.current_estimated_value for v in vehicles)
    
    portfolio_gain_loss = total_current_value - total_acquisition_cost
    portfolio_return_pct = (
        (portfolio_gain_loss / total_acquisition_cost * 100)
        if total_acquisition_cost > 0
        else 0
    )
    
    # Calculate years held (average)
    current_date = datetime.now()
    total_years = 0
    for vehicle in vehicles:
        try:
            acq_date = datetime.fromisoformat(vehicle.acquisition_date)
            years_held = (current_date - acq_date).days / 365.25
            total_years += years_held
        except:
            pass
    
    avg_years = total_years / len(vehicles) if vehicles else 0
    average_annual_return = (
        portfolio_return_pct / avg_years if avg_years > 0 else 0
    )
    
    # Find best and worst performers
    vehicle_returns = []
    for v in vehicles:
        return_amt = v.current_estimated_value - v.purchase_price
        return_pct = (
            (return_amt / v.purchase_price * 100)
            if v.purchase_price > 0
            else 0
        )
        vehicle_returns.append((v.id, return_pct))
    
    best_vehicle = max(vehicle_returns, key=lambda x: x[1]) if vehicle_returns else ("", 0)
    worst_vehicle = min(vehicle_returns, key=lambda x: x[1]) if vehicle_returns else ("", 0)
    
    return PortfolioMetrics(
        total_vehicles=len(vehicles),
        total_acquisition_cost=round(total_acquisition_cost, 2),
        total_current_value=round(total_current_value, 2),
        portfolio_gain_loss=round(portfolio_gain_loss, 2),
        portfolio_return_pct=round(portfolio_return_pct, 2),
        average_annual_return=round(average_annual_return, 2),
        best_performing_vehicle=best_vehicle[0],
        worst_performing_vehicle=worst_vehicle[0],
    )


def add_vehicle_to_portfolio(
    portfolio: list[PortfolioVehicle],
    brand: str,
    model: str,
    year: int,
    purchase_price: float,
    current_value: float = None,
    notes: str = "",
) -> tuple[str, PortfolioVehicle]:
    """Add a new vehicle to the portfolio.
    
    Args:
        portfolio: Current portfolio
        brand: Vehicle brand
        model: Vehicle model
        year: Vehicle year
        purchase_price: Purchase price
        current_value: Current estimated value (defaults to purchase price)
        notes: Optional notes
        
    Returns:
        Tuple of (vehicle_id, PortfolioVehicle)
    """
    # Generate ID
    vehicle_id = f"{brand}_{model}_{year}_{len(portfolio) + 1}"
    
    # Use current_value = purchase_price if not provided
    if current_value is None:
        current_value = purchase_price
    
    vehicle = PortfolioVehicle(
        id=vehicle_id,
        brand=brand,
        model=model,
        year=year,
        purchase_price=purchase_price,
        current_estimated_value=current_value,
        acquisition_date=datetime.now().isoformat(),
        notes=notes,
    )
    
    portfolio.append(vehicle)
    return vehicle_id, vehicle
