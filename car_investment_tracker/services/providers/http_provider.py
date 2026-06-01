from __future__ import annotations

import logging
from typing import Any

from car_investment_tracker.models import Listing, MarketDiscussion, PricePoint
from car_investment_tracker.services.providers.config import ProviderConfig

logger = logging.getLogger(__name__)


class HttpMarketProvider:
    """Fetches real market data over HTTP from configured endpoints.

    The provider is feed-agnostic. Each configured endpoint is expected to accept
    the query parameters ``make``, ``model``, ``year`` and (optionally)
    ``variant`` and to return JSON in the shapes below. Any feed that conforms to
    these shapes (an Auto Trader partner API, a licensed valuations dataset, an
    internal aggregator, ...) can be plugged in via environment variables.

    Listings endpoint response::

        {"source": "Auto Trader",
         "listings": [
            {"listing_id": "202401011234567", "title": "2004 Porsche 911 Carrera",
             "url": "https://www.autotrader.co.uk/car-details/202401011234567",
             "price": 38995, "price_type": "asking", "mileage": 62000,
             "year": 2004, "variant": "Carrera", "transmission": "Manual",
             "fuel_type": "Petrol", "location": "London", "seller_type": "Trade",
             "clean_title": true, "date_collected": "2026-06-01"}
         ]}

    Historical endpoint response::

        {"points": [
            {"year": 2010, "average_price": 42000, "currency": "GBP",
             "price_type": "sold", "sample_size": 18,
             "source_name": "Auction Results DB",
             "source_url": "https://example-auctions/results?...",
             "confidence": "High"}
        ]}

    Discussions endpoint response::

        {"discussions": [
            {"title": "Are air-cooled 911s still climbing?",
             "url": "https://www.pistonheads.com/gassing/topic.asp?...",
             "source": "PistonHeads", "published_date": "2026-03-12",
             "summary": "Owners debate whether values have peaked...",
             "sentiment_score": 3.4, "price_outlook": "stable"}
        ]}
    """

    def __init__(self, config: ProviderConfig):
        self._config = config
        self.name = "Auto Trader / configured feeds"

    # -- public API -----------------------------------------------------------

    def fetch_historical_prices(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[PricePoint]:
        data = self._get(self._config.historical_url, brand, model, year, variant)
        if not data:
            return []
        points: list[PricePoint] = []
        for raw in data.get("points", []):
            try:
                points.append(
                    PricePoint(
                        year=int(raw["year"]),
                        average_price=float(raw["average_price"]),
                        nominal_price=float(raw.get("nominal_price", raw["average_price"])),
                        inflation_adjusted_price=float(
                            raw.get("inflation_adjusted_price", raw["average_price"])
                        ),
                        currency=str(raw.get("currency", "GBP")),
                        price_type=str(raw.get("price_type", "sold")),
                        sample_size=_opt_int(raw.get("sample_size")),
                        source_name=raw.get("source_name"),
                        source_url=raw.get("source_url"),
                        confidence=raw.get("confidence"),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Skipping malformed historical point: %s", exc)
        points.sort(key=lambda p: p.year)
        return points

    def fetch_listings(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[Listing]:
        data = self._get(self._config.listings_url, brand, model, year, variant)
        if not data:
            return []
        source_default = data.get("source", "Auto Trader")
        listings: list[Listing] = []
        for raw in data.get("listings", []):
            try:
                listings.append(
                    Listing(
                        source=str(raw.get("source", source_default)),
                        title=str(raw["title"]),
                        price=float(raw["price"]),
                        currency=str(raw.get("currency", "GBP")),
                        clean_title=bool(raw.get("clean_title", True)),
                        url=str(raw["url"]),
                        listing_id=_opt_str(raw.get("listing_id")),
                        price_type=str(raw.get("price_type", "asking")),
                        mileage=_opt_int(raw.get("mileage")),
                        year=_opt_int(raw.get("year")),
                        variant=_opt_str(raw.get("variant")),
                        transmission=_opt_str(raw.get("transmission")),
                        fuel_type=_opt_str(raw.get("fuel_type")),
                        location=_opt_str(raw.get("location")),
                        seller_type=_opt_str(raw.get("seller_type")),
                        date_collected=_opt_str(raw.get("date_collected")),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Skipping malformed listing: %s", exc)
        return _dedupe_listings(listings)

    def fetch_discussions(
        self, brand: str, model: str, year: int, variant: str | None = None
    ) -> list[MarketDiscussion]:
        data = self._get(self._config.discussions_url, brand, model, year, variant)
        if not data:
            return []
        discussions: list[MarketDiscussion] = []
        for raw in data.get("discussions", []):
            try:
                discussions.append(
                    MarketDiscussion(
                        title=str(raw["title"]),
                        url=str(raw["url"]),
                        source=str(raw.get("source", "Unknown")),
                        published_date=_opt_str(raw.get("published_date")),
                        summary=str(raw.get("summary", "")),
                        sentiment_score=_opt_float(raw.get("sentiment_score")),
                        price_outlook=_opt_str(raw.get("price_outlook")),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Skipping malformed discussion: %s", exc)
        return discussions

    # -- internals ------------------------------------------------------------

    def _get(
        self, url: str | None, brand: str, model: str, year: int, variant: str | None
    ) -> dict[str, Any] | None:
        if not url:
            return None
        try:
            import httpx  # imported lazily so the dependency is only needed live
        except ImportError:  # pragma: no cover - httpx is a declared dependency
            logger.error("httpx is required for live data fetching but is not installed")
            return None

        params = {"make": brand, "model": model, "year": year}
        if variant:
            params["variant"] = variant
        headers = {}
        if self._config.api_key:
            headers["Authorization"] = "Bearer " + self._config.api_key
        try:
            response = httpx.get(
                url,
                params=params,
                headers=headers,
                timeout=self._config.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # network/parse errors -> treated as unavailable
            logger.warning("Live data fetch from %s failed: %s", url, exc)
            return None


def _dedupe_listings(listings: list[Listing]) -> list[Listing]:
    """Deduplicate by provider listing id, falling back to the exact URL."""
    seen: dict[str, Listing] = {}
    for listing in listings:
        key = listing.listing_id or str(listing.url)
        if key not in seen:
            seen[key] = listing
    return list(seen.values())


def _opt_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _opt_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
