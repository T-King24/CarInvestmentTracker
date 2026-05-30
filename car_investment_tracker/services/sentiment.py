from __future__ import annotations

from car_investment_tracker.services.cache import cache

POSITIVE_TERMS = {"reliable", "iconic", "excellent", "durable", "enthusiast", "strong"}
NEGATIVE_TERMS = {"expensive", "problem", "rust", "weak", "overpriced", "unreliable"}


@cache.cached
def get_sentiment_score(brand: str, model: str, year: int) -> dict[str, float | int]:
    # In production this should use API-backed forum ingestion and transformer NLP sentiment.
    sample_mentions = [
        f"The {brand} {model} remains an iconic enthusiast choice.",
        f"Owners say maintenance can be expensive on the {year} generation.",
        f"Reviewers describe it as reliable and durable with strong resale.",
        f"Forum users debate if current prices are overpriced.",
        f"Some communities report rust problems in wet climates.",
    ]

    score = 0
    for text in sample_mentions:
        words = {token.strip(".,").lower() for token in text.split()}
        score += len(words & POSITIVE_TERMS)
        score -= len(words & NEGATIVE_TERMS)

    normalized = max(0.0, min(5.0, round(((score + 6) / 12) * 5, 2)))
    return {"score": normalized, "mentions_analyzed": len(sample_mentions)}
