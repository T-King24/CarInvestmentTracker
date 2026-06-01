"""Real-world data provider layer.

This package replaces the previous synthetic/fallback data generators. Market
data (historical sold prices, current listings, sentiment/discussion sources) is
fetched from configured external providers. When no provider is configured or a
provider returns nothing, the application surfaces an "unavailable" state instead
of fabricating data.
"""

from car_investment_tracker.services.providers.base import MarketDataProvider
from car_investment_tracker.services.providers.registry import (
    get_market_provider,
    reset_market_provider,
    set_market_provider,
)

__all__ = [
    "MarketDataProvider",
    "get_market_provider",
    "set_market_provider",
    "reset_market_provider",
]
