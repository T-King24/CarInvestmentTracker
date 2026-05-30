from __future__ import annotations

from car_investment_tracker.models import Listing


def find_undervalued_listings(listings: list[Listing]) -> list[Listing]:
    if not listings:
        return []

    avg_price = sum(listing.price for listing in listings) / len(listings)
    filtered = [
        listing
        for listing in listings
        if listing.clean_title and listing.price < avg_price
    ]
    return sorted(filtered, key=lambda item: item.price)
