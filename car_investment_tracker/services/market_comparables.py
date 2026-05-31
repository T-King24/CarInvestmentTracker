from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import random

from car_investment_tracker.models import Listing
from car_investment_tracker.services.cache import cache


def _stable_seed(*parts: object) -> int:
    """Generate stable seed from vehicle parameters for reproducible data."""
    digest = hashlib.sha256(":".join(str(part).strip().lower() for part in parts).encode()).hexdigest()
    return int(digest[:16], 16)


@cache.cached
def get_market_comparables(brand: str, model: str, year: int) -> list[dict]:
    """Fetch recent sales of comparable vehicles (same model, year, mileage bracket).
    
    In production, this would query an auction database or API.
    Currently returns simulated comparable sales data.
    
    Args:
        brand: Vehicle brand
        model: Vehicle model
        year: Vehicle year
        
    Returns:
        List of comparable sales with date, price, mileage, condition
    """
    seed = _stable_seed("comparables", brand, model, year) & 0xFFFFFFFF
    rng = random.Random(seed)
    current_year = datetime.now(timezone.utc).year
    age = current_year - year
    
    # Generate 8-15 recent comparable sales
    num_comparables = rng.randint(8, 15)
    comparables = []
    
    # Base price estimate
    base_price = 15000 + (age * 1000) + rng.randint(-5000, 5000)
    base_mileage = age * 12000  # ~12k miles/year
    
    current_date = datetime.now(timezone.utc)
    
    for i in range(num_comparables):
        # Simulate sale dates in last 90 days
        days_ago = rng.randint(1, 90)
        sale_date = current_date - timedelta(days=days_ago)
        
        # Price varies ±10% from base
        price = base_price * (1 + rng.uniform(-0.10, 0.10))
        
        # Mileage varies ±20% from base
        mileage = int(base_mileage * (1 + rng.uniform(-0.20, 0.20)))
        
        # Condition rating 1-5 (5 is best)
        condition = rng.choices([1, 2, 3, 4, 5], weights=[5, 15, 40, 30, 10])[0]
        
        # Auction source
        sources = ["Copart", "IAA", "Local Auction", "Private Dealer", "Estate Sale"]
        source = rng.choice(sources)
        
        comparables.append({
            "sale_date": sale_date.strftime("%Y-%m-%d"),
            "days_ago": days_ago,
            "price": round(price, 2),
            "mileage": mileage,
            "condition": condition,  # 1=Poor, 5=Excellent
            "source": source,
            "currency": "USD"
        })
    
    # Sort by date (most recent first)
    comparables.sort(key=lambda x: x["days_ago"])
    
    return comparables
