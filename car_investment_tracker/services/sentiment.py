from __future__ import annotations

from car_investment_tracker.models import MarketDiscussion
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import get_market_provider

# Price-outlook terms used to score real discussion text when a source does not
# already provide an explicit sentiment score. Weights reflect what the
# community expects prices to *do* (rise, hold, fall), keeping sentiment tied to
# price expectations rather than unrelated chatter.
POSITIVE_TERMS = {
    "appreciating": 2.5,
    "appreciate": 2.5,
    "rising": 2.0,
    "climbing": 2.0,
    "rebound": 2.0,
    "rebounding": 2.0,
    "bottomed": 2.0,
    "bottoming": 1.5,
    "undervalued": 2.0,
    "investment": 1.5,
    "sought-after": 1.5,
    "collectible": 1.5,
    "demand": 1.0,
}

NEGATIVE_TERMS = {
    "depreciating": -2.5,
    "depreciate": -2.5,
    "depreciation": -2.0,
    "falling": -2.0,
    "declining": -2.0,
    "softening": -2.0,
    "dropping": -2.0,
    "overpriced": -2.0,
    "oversupplied": -2.0,
    "weak": -1.5,
    "cooling": -1.5,
}

# Maps a provider-supplied ``price_outlook`` label onto a 0-5 sentiment score.
OUTLOOK_SCORES = {
    "appreciating": 4.5,
    "collectible-demand": 4.0,
    "undervalued": 4.0,
    "stable": 2.5,
    "depreciating": 1.0,
    "overvalued": 1.0,
}


def _score_text(text: str) -> float | None:
    """Score free text on the 0-5 price-outlook scale, or ``None`` if neutral/empty."""
    if not text:
        return None
    words = {token.strip(".,!?").lower() for token in text.split()}
    raw = 0.0
    matched = False
    for word, weight in {**POSITIVE_TERMS, **NEGATIVE_TERMS}.items():
        if word in words:
            raw += weight
            matched = True
    if not matched:
        return None
    return max(0.0, min(5.0, round(((raw + 15) / 30) * 5, 2)))


def _score_discussion(discussion: MarketDiscussion) -> float | None:
    """Resolve a 0-5 score for one real discussion using the best signal available."""
    if discussion.sentiment_score is not None:
        return max(0.0, min(5.0, float(discussion.sentiment_score)))
    if discussion.price_outlook:
        mapped = OUTLOOK_SCORES.get(discussion.price_outlook.strip().lower())
        if mapped is not None:
            return mapped
    return _score_text(f"{discussion.title} {discussion.summary}")


def _outlook_label(score: float) -> str:
    if score >= 3.5:
        return "Community expects values to appreciate"
    if score >= 2.0:
        return "Community expects values to stay broadly stable"
    return "Community expects values to keep depreciating"


@cache.cached
def get_sentiment_score(
    brand: str, model: str, year: int, variant: str | None = None
) -> dict[str, float | int | bool | str]:
    """Compute price-outlook sentiment from real discussion sources.

    Sentiment is derived from the same real news/forum discussions returned by
    the provider. When no real sources are available, sentiment is reported as
    unavailable (neutral 0-mentions) rather than invented.
    """
    provider = get_market_provider()
    discussions = provider.fetch_discussions(brand, model, year, variant)

    scores = [s for s in (_score_discussion(d) for d in discussions) if s is not None]
    if not scores:
        return {
            "score": 0.0,
            "mentions_analyzed": 0,
            "available": False,
            "outlook": "No market sentiment sources available for this vehicle.",
        }

    normalized = round(sum(scores) / len(scores), 2)
    return {
        "score": normalized,
        "mentions_analyzed": len(scores),
        "available": True,
        "outlook": _outlook_label(normalized),
    }
