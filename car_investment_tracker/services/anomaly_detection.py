from __future__ import annotations

import math
from pydantic import BaseModel, Field
from car_investment_tracker.models import Listing


class AnomalyDetectionResult(BaseModel):
    """Result of anomaly detection analysis."""
    listing: Listing
    is_anomaly: bool
    anomaly_score: float = Field(description="0-1, higher = more anomalous")
    z_score: float = Field(description="Standard deviations from mean")
    anomaly_type: str = Field(description="'Underpriced', 'Overpriced', 'Normal', or 'Unknown'")
    reasoning: str = Field(description="Explanation for anomaly detection")


def detect_listing_anomalies(listings: list[Listing], market_price: float = None) -> list[AnomalyDetectionResult]:
    """Detect anomalous listings using statistical methods (z-score).
    
    Args:
        listings: List of listings to analyze
        market_price: Optional predicted market price for comparison
        
    Returns:
        List of anomaly detection results
    """
    if not listings or len(listings) < 3:
        # Need at least 3 points for meaningful statistics
        return []
    
    prices = [l.price for l in listings]
    mean_price = sum(prices) / len(prices)
    
    # Calculate standard deviation
    variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
    std_dev = math.sqrt(variance)
    
    # Use market price if provided
    comparison_price = market_price if market_price else mean_price
    
    results = []
    
    for listing in listings:
        # Calculate z-score
        if std_dev > 0:
            z_score = (listing.price - mean_price) / std_dev
        else:
            z_score = 0
        
        # Calculate anomaly score (0-1)
        # |z-score| > 2.5 is very unusual (~1.2% of data), > 2 is unusual (~4.5% of data)
        abs_z = abs(z_score)
        if abs_z < 1:
            anomaly_score = 0
            is_anomaly = False
            anomaly_type = "Normal"
            reasoning = f"Price is within normal range (${listing.price:,.0f})"
        elif abs_z < 2:
            anomaly_score = (abs_z - 1) / 1
            is_anomaly = False
            anomaly_type = "Normal"
            reasoning = f"Price is slightly unusual but acceptable (z-score: {z_score:.2f})"
        elif abs_z < 2.5:
            anomaly_score = (abs_z - 2) / 0.5
            is_anomaly = True
            if z_score > 0:
                anomaly_type = "Overpriced"
                reasoning = f"Price is notably high compared to market (z-score: {z_score:.2f}). May indicate cosmetic issues or misrepresentation."
            else:
                anomaly_type = "Underpriced"
                reasoning = f"Price is notably low compared to market (z-score: {z_score:.2f}). Potential value opportunity, but verify condition."
        else:
            anomaly_score = 1.0
            is_anomaly = True
            if z_score > 0:
                anomaly_type = "Overpriced"
                reasoning = f"Price is extremely high (z-score: {z_score:.2f}). Likely misclassified or error in listing."
            else:
                anomaly_type = "Underpriced"
                reasoning = f"Price is extremely low (z-score: {z_score:.2f}). Verify vehicle status (salvage title, flood damage, etc.)."
        
        # Adjust reasoning based on comparison to market price
        if market_price and abs(listing.price - market_price) / market_price > 0.30:
            if listing.price > market_price:
                anomaly_type = "Overpriced"
                is_anomaly = True
                anomaly_score = max(anomaly_score, 0.7)
            else:
                anomaly_type = "Underpriced"
                is_anomaly = True
                anomaly_score = max(anomaly_score, 0.7)
        
        result = AnomalyDetectionResult(
            listing=listing,
            is_anomaly=is_anomaly,
            anomaly_score=round(anomaly_score, 3),
            z_score=round(z_score, 2),
            anomaly_type=anomaly_type,
            reasoning=reasoning,
        )
        results.append(result)
    
    # Sort by anomaly score descending (most anomalous first)
    results.sort(key=lambda r: r.anomaly_score, reverse=True)
    
    return results
