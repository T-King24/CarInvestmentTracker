from __future__ import annotations

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


@cache.cached
def get_sentiment_score(brand: str, model: str, year: int) -> dict[str, float | int]:
    # In production this should use API-backed forum ingestion and transformer NLP sentiment.
    sample_mentions = [
        f"The {brand} {model} remains an iconic enthusiast choice with strong resale value.",
        f"Owners say maintenance can be expensive on the {year} generation.",
        f"Reviewers describe it as reliable and durable with timeless appeal.",
        f"Forum users debate if current prices are overpriced.",
        f"Some communities report rust problems in wet climates.",
        f"Collectors seek out this legendary model.",
        f"Sought-after by enthusiasts despite depreciation trends.",
    ]

    score = 0.0
    for text in sample_mentions:
        words = {token.strip(".,").lower() for token in text.split()}
        # Add weighted positive sentiment
        for word, weight in POSITIVE_TERMS.items():
            if word in words:
                score += weight
        # Add weighted negative sentiment
        for word, weight in NEGATIVE_TERMS.items():
            if word in words:
                score += weight  # weight is already negative

    # Maps sentiment range [-15, 15] onto [0, 5] with smooth scaling.
    normalized = max(0.0, min(5.0, round(((score + 15) / 30) * 5, 2)))
    return {"score": normalized, "mentions_analyzed": len(sample_mentions)}
