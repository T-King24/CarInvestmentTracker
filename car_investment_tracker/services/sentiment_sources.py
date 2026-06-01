from __future__ import annotations

from car_investment_tracker.models import MarketDiscussion, SentimentSourceBreakdown
from car_investment_tracker.services.cache import cache
from car_investment_tracker.services.providers import get_market_provider
from car_investment_tracker.services.sentiment import _score_discussion

# Keyword -> source category. Used to bucket real discussion sources so the
# breakdown reflects where each opinion actually came from.
_FORUM_HINTS = ("pistonheads", "forum", "reddit", "owners", "club", "community")
_AUCTION_HINTS = (
    "auction",
    "bonhams",
    "sotheby",
    "collecting cars",
    "bring a trailer",
    "car & classic",
    "hagerty price",
    "the market",
)
_SOCIAL_HINTS = ("twitter", "instagram", "youtube", "facebook", "tiktok", " x ")
_NEWS_HINTS = ("autocar", "evo", "top gear", "motor1", "carwow", "hagerty", "news", "review")


def _categorise(source: str) -> str:
    text = f" {source.strip().lower()} "
    if any(hint in text for hint in _AUCTION_HINTS):
        return "auction"
    if any(hint in text for hint in _FORUM_HINTS):
        return "forums"
    if any(hint in text for hint in _SOCIAL_HINTS):
        return "social"
    if any(hint in text for hint in _NEWS_HINTS):
        return "news"
    return "news"


def _avg(scores: list[float]) -> float:
    return round(sum(scores) / len(scores), 2) if scores else 0.0


@cache.cached
def get_sentiment_source_breakdown(
    brand: str, model: str, year: int, variant: str | None = None
) -> SentimentSourceBreakdown:
    """Break real discussion sentiment down by source type.

    Buckets the provider's real news/forum/auction/social discussions and scores
    each bucket. When no real sources are available, all scores are zero and
    ``available`` is ``False`` (nothing is fabricated).
    """
    provider = get_market_provider()
    discussions: list[MarketDiscussion] = provider.fetch_discussions(brand, model, year, variant)

    buckets: dict[str, list[float]] = {"forums": [], "auction": [], "news": [], "social": []}
    for discussion in discussions:
        score = _score_discussion(discussion)
        if score is None:
            continue
        buckets[_categorise(discussion.source)].append(score)

    forum_score = _avg(buckets["forums"])
    auction_score = _avg(buckets["auction"])
    news_score = _avg(buckets["news"])
    social_score = _avg(buckets["social"])

    total = sum(len(v) for v in buckets.values())
    if total == 0:
        return SentimentSourceBreakdown(
            forums_score=0.0, forums_mentions=0,
            auction_score=0.0, auction_mentions=0,
            news_score=0.0, news_mentions=0,
            social_score=0.0, social_mentions=0,
            overall_score=0.0, total_mentions=0, available=False,
        )

    # Weight only the buckets that actually have data so a missing source type
    # doesn't drag the overall score toward zero.
    weights = {"forums": 0.30, "auction": 0.35, "news": 0.20, "social": 0.15}
    weighted_sum = 0.0
    weight_total = 0.0
    for name, score in (
        ("forums", forum_score),
        ("auction", auction_score),
        ("news", news_score),
        ("social", social_score),
    ):
        if buckets[name]:
            weighted_sum += score * weights[name]
            weight_total += weights[name]
    overall = round(weighted_sum / weight_total, 2) if weight_total else 0.0

    return SentimentSourceBreakdown(
        forums_score=forum_score, forums_mentions=len(buckets["forums"]),
        auction_score=auction_score, auction_mentions=len(buckets["auction"]),
        news_score=news_score, news_mentions=len(buckets["news"]),
        social_score=social_score, social_mentions=len(buckets["social"]),
        overall_score=overall, total_mentions=total, available=True,
    )
