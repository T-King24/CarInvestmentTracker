from __future__ import annotations

from pydantic import BaseModel, Field
from car_investment_tracker.models import Listing


class EnrichedListing(BaseModel):
    """Listing with additional analysis metadata."""
    source: str
    title: str
    price: float
    currency: str = "USD"
    clean_title: bool
    url: str
    discount_from_average: float = Field(description="Discount from market average (%)")
    discount_amount: float = Field(description="Discount from market average ($)")
    value_rank: str = Field(description="Best, Very Good, Good, or Fair value")


def find_undervalued_listings(listings: list[Listing], market_price: float = None) -> list[EnrichedListing]:
    """Find undervalued listings with detailed analysis.
    
    Args:
        listings: List of current listings
        market_price: Optional predicted market price for comparison
        
    Returns:
        List of undervalued listings with discount information
    """
    if not listings:
        return []

    avg_price = sum(listing.price for listing in listings) / len(listings)
    
    # Use market price if provided, otherwise use average
    comparison_price = market_price if market_price else avg_price
    
    enriched_listings = []
    for listing in listings:
        if listing.clean_title and listing.price < comparison_price:
            discount_amount = comparison_price - listing.price
            discount_pct = (discount_amount / comparison_price * 100) if comparison_price > 0 else 0
            
            # Rank based on discount percentage
            if discount_pct >= 20:
                value_rank = "Best"
            elif discount_pct >= 15:
                value_rank = "Very Good"
            elif discount_pct >= 10:
                value_rank = "Good"
            else:
                value_rank = "Fair"
            
            enriched = EnrichedListing(
                source=listing.source,
                title=listing.title,
                price=listing.price,
                currency=listing.currency,
                clean_title=listing.clean_title,
                url=str(listing.url),
                discount_from_average=round(discount_pct, 1),
                discount_amount=round(discount_amount, 2),
                value_rank=value_rank,
            )
            enriched_listings.append(enriched)
    
    # Sort by discount percentage (best value first)
    enriched_listings.sort(key=lambda item: item.discount_from_average, reverse=True)
    return enriched_listings
