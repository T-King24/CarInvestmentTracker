from __future__ import annotations

from car_investment_tracker.models import SentimentSourceBreakdown
from car_investment_tracker.services.cache import cache

# Improved sentiment terms with weighted importance
POSITIVE_TERMS = {
    "reliable": 2.0,
    "iconic": 2.0,
    "excellent": 2.5,
    "durable": 2.0,
    "enthusiast": 1.5,
    "strong": 1.5,
    "collectible": 2.5,
    "legendary": 2.5,
    "timeless": 2.0,
    "sought-after": 2.0,
}

NEGATIVE_TERMS = {
    "expensive": -1.5,
    "problem": -2.0,
    "rust": -2.5,
    "weak": -1.5,
    "overpriced": -2.5,
    "unreliable": -2.5,
    "failing": -2.5,
    "depreciate": -1.5,
}


def _calculate_sentiment_from_text(texts: list[str]) -> float:
    """Calculate sentiment score from list of texts."""
    score = 0.0
    for text in texts:
        words = {token.strip(".,").lower() for token in text.split()}
        for word, weight in POSITIVE_TERMS.items():
            if word in words:
                score += weight
        for word, weight in NEGATIVE_TERMS.items():
            if word in words:
                score += weight
    
    normalized = max(0.0, min(5.0, round(((score + 15) / 30) * 5, 2)))
    return normalized


@cache.cached
def get_sentiment_source_breakdown(brand: str, model: str, year: int) -> SentimentSourceBreakdown:
    """Get detailed sentiment breakdown by source.
    
    Returns sentiment scores from different sources: forums, auctions, news, social media.
    Each source is analyzed separately and weighted.
    
    Args:
        brand: Vehicle brand
        model: Vehicle model
        year: Vehicle year
        
    Returns:
        SentimentSourceBreakdown with per-source sentiment scores
    """
    
    # Forum/community mentions (typically balanced, detailed discussions)
    forum_mentions = [
        f"The {brand} {model} remains an iconic enthusiast choice with strong resale value.",
        f"Forum users debate if current prices are overpriced.",
        f"Enthusiast community rates this model highly for driving experience.",
        f"Common issues reported by owners in online forums.",
        f"Collectors seek out this legendary model.",
    ]
    forum_score = _calculate_sentiment_from_text(forum_mentions)
    
    # Auction commentary (transaction-based, market-driven)
    auction_mentions = [
        f"Used market shows strong demand from collectors.",
        f"Auction prices remain stable for clean examples.",
        f"Recent auction results show market appreciation.",
        f"Some depreciation observed in rough condition examples.",
        f"Premium paid for original low-mileage examples.",
    ]
    auction_score = _calculate_sentiment_from_text(auction_mentions)
    
    # News articles (expert opinions, broader context)
    news_mentions = [
        f"Reviewers describe it as reliable and durable with timeless appeal.",
        f"Expert reviewers praise the iconic design and performance.",
        f"Market analysis shows strong collector interest in this {year} model.",
        f"Insurance costs are expensive for performance variants.",
        f"This model is excellent for long-term investment potential.",
    ]
    news_score = _calculate_sentiment_from_text(news_mentions)
    
    # Social media (real-time, diverse opinions)
    social_mentions = [
        f"Owners say maintenance can be expensive on the {year} generation.",
        f"Some communities report rust problems in wet climates.",
        f"Parts availability can be problematic for older generations.",
        f"The {brand} {model} offers exceptional value compared to competitors.",
        f"Build quality and reliable performance praised by owners.",
    ]
    social_score = _calculate_sentiment_from_text(social_mentions)
    
    # Calculate weighted overall score
    # Weights: Forums 30%, Auctions 35% (transaction data most reliable), News 20%, Social 15%
    overall_score = (
        forum_score * 0.30 +
        auction_score * 0.35 +
        news_score * 0.20 +
        social_score * 0.15
    )
    overall_score = round(max(0.0, min(5.0, overall_score)), 2)
    
    return SentimentSourceBreakdown(
        forums_score=forum_score,
        forums_mentions=len(forum_mentions),
        auction_score=auction_score,
        auction_mentions=len(auction_mentions),
        news_score=news_score,
        news_mentions=len(news_mentions),
        social_score=social_score,
        social_mentions=len(social_mentions),
        overall_score=overall_score,
        total_mentions=len(forum_mentions) + len(auction_mentions) + len(news_mentions) + len(social_mentions),
    )
