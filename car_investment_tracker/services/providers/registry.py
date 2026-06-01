from __future__ import annotations

from car_investment_tracker.services.providers.base import MarketDataProvider
from car_investment_tracker.services.providers.config import load_config
from car_investment_tracker.services.providers.http_provider import HttpMarketProvider
from car_investment_tracker.services.providers.null_provider import NullProvider

# A process-wide override, primarily used by tests to inject a deterministic
# in-memory provider without hitting the network.
_override: MarketDataProvider | None = None
_cached: MarketDataProvider | None = None


def get_market_provider() -> MarketDataProvider:
    """Return the active market-data provider.

    Resolution order:
      1. An explicit override (e.g. set by tests).
      2. The live HTTP provider when configured via environment variables.
      3. The :class:`NullProvider`, which returns no data (everything reported
         as unavailable rather than fabricated).
    """
    global _cached
    if _override is not None:
        return _override
    if _cached is not None:
        return _cached

    config = load_config()
    if config.is_live:
        _cached = HttpMarketProvider(config)
    else:
        _cached = NullProvider()
    return _cached


def set_market_provider(provider: MarketDataProvider | None) -> None:
    """Override the active provider (used by tests)."""
    global _override
    _override = provider


def reset_market_provider() -> None:
    """Clear any override and cached provider (re-reads configuration)."""
    global _override, _cached
    _override = None
    _cached = None
