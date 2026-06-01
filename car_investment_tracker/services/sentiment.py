from __future__ import annotations

from car_investment_tracker.services.cache import cache

# Price-outlook sentiment terms. Rather than rewarding generic praise ("iconic",
# "reliable"), these weights reflect what the community expects prices to *do*:
# whether values are seen as rising, holding steady, or falling. This keeps the
# forecast tied to price expectations instead of unrelated chatter.
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


@cache.cached
def get_sentiment_score(brand: str, model: str, year: int) -> dict[str, float | int]:
    # In production this should mine forums, auction commentary and market reports
    # for what people expect prices to do, then run transformer NLP over them.
    # These sample mentions focus on price-outlook signals (rising/falling/stable).
    sample_mentions = [
        f"Owners feel values of the {brand} {model} have been depreciating year on year.",
        f"Auction watchers say prices are softening for the {year} cars.",
        f"Some collectors think this model is undervalued and could rebound.",
        f"Forum users expect prices to keep falling before they stabilise.",
        f"Demand remains for clean low-mileage examples, supporting prices.",
        f"Market reports describe the segment as cooling after recent highs.",
        f"Enthusiasts argue the {brand} {model} is a long-term investment.",
        f"Recent sales suggest the market may be bottoming out.",
        f"Several listings are seen as overpriced and slow to sell.",
        f"Commentators note the {year} generation is still declining in value.",
    ]

    score = 0.0
    for text in sample_mentions:
        words = {token.strip(".,").lower() for token in text.split()}
        # Add weighted positive (appreciation) sentiment
        for word, weight in POSITIVE_TERMS.items():
            if word in words:
                score += weight
        # Add weighted negative (depreciation) sentiment
        for word, weight in NEGATIVE_TERMS.items():
            if word in words:
                score += weight  # weight is already negative

    # Maps sentiment range [-15, 15] onto [0, 5] with smooth scaling.
    normalized = max(0.0, min(5.0, round(((score + 15) / 30) * 5, 2)))
    return {"score": normalized, "mentions_analyzed": len(sample_mentions)}
