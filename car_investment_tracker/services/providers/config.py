from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for the live HTTP data provider, read from the environment.

    The application is provider-agnostic: point these variables at any feed that
    returns the documented JSON shape (see ``http_provider`` docstrings) — for
    example an Auto Trader partner API, a licensed valuations dataset, or an
    internal aggregation service.
    """

    provider: str  # "http"/"live" to enable HTTP fetching | "null" (default)
    listings_url: str | None
    historical_url: str | None
    discussions_url: str | None
    api_key: str | None
    timeout_seconds: float

    # Values of CIT_DATA_PROVIDER that enable live HTTP fetching.
    _LIVE_PROVIDERS = ("http", "live")

    @property
    def is_live(self) -> bool:
        return self.provider in self._LIVE_PROVIDERS and bool(
            self.listings_url or self.historical_url or self.discussions_url
        )


def load_config() -> ProviderConfig:
    """Load provider configuration from environment variables.

    Variables:
        CIT_DATA_PROVIDER       "http" (alias "live") to enable HTTP fetching, otherwise null
        CIT_LISTINGS_API_URL    endpoint returning live adverts
        CIT_HISTORICAL_API_URL  endpoint returning sold-price history
        CIT_DISCUSSIONS_API_URL endpoint returning news/forum discussions
        CIT_DATA_API_KEY        optional bearer/api key sent to all endpoints
        CIT_DATA_TIMEOUT        per-request timeout in seconds (default 8)
    """
    provider = (os.getenv("CIT_DATA_PROVIDER") or "null").strip().lower()
    try:
        timeout = float(os.getenv("CIT_DATA_TIMEOUT", "8"))
    except ValueError:
        timeout = 8.0
    return ProviderConfig(
        provider=provider,
        listings_url=_clean(os.getenv("CIT_LISTINGS_API_URL")),
        historical_url=_clean(os.getenv("CIT_HISTORICAL_API_URL")),
        discussions_url=_clean(os.getenv("CIT_DISCUSSIONS_API_URL")),
        api_key=_clean(os.getenv("CIT_DATA_API_KEY")),
        timeout_seconds=timeout,
    )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
