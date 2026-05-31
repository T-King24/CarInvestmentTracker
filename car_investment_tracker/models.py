from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class VehicleQuery(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1900)


class PricePoint(BaseModel):
    year: int
    average_price: float
    nominal_price: float = Field(default=None, description="Nominal (non-adjusted) price")
    inflation_adjusted_price: float = Field(default=None, description="Inflation-adjusted price")


class Listing(BaseModel):
    source: str
    title: str
    price: float
    currency: str = "USD"
    clean_title: bool
    url: HttpUrl


class SentimentResult(BaseModel):
    score: float = Field(ge=0, le=5)
    mentions_analyzed: int


class SentimentSourceBreakdown(BaseModel):
    """Breakdown of sentiment sources with weights."""
    forums_score: float = Field(ge=0, le=5, description="Sentiment from forums and communities")
    forums_mentions: int = Field(description="Number of forum mentions")
    auction_score: float = Field(ge=0, le=5, description="Sentiment from auction commentary")
    auction_mentions: int = Field(description="Number of auction comments")
    news_score: float = Field(ge=0, le=5, description="Sentiment from news articles")
    news_mentions: int = Field(description="Number of news mentions")
    social_score: float = Field(ge=0, le=5, description="Sentiment from social media")
    social_mentions: int = Field(description="Number of social media mentions")
    overall_score: float = Field(ge=0, le=5, description="Weighted overall sentiment score")
    total_mentions: int = Field(description="Total mentions across all sources")


class PredictionPoint(BaseModel):
    year: int
    predicted_price: float
    lower_bound: float = Field(description="Lower confidence interval bound (±10%)")
    upper_bound: float = Field(description="Upper confidence interval bound (±10%)")


class PredictionExplanation(BaseModel):
    """Detailed explanation of how the prediction was calculated."""
    historical_weight: float = Field(description="Weight of historical trend (60%)")
    listing_weight: float = Field(description="Weight of current market average (40%)")
    sentiment_score: float = Field(description="Sentiment score (0-5) affecting forecast")
    sentiment_modifier: float = Field(description="Multiplier applied based on sentiment")
    last_historical_price: float = Field(description="Most recent historical price data")
    current_listing_average: float = Field(description="Average of current market listings")
    trend_momentum: float = Field(description="Recent price change momentum (noise-smoothed)")
    model_type: str = Field(description="Forecasting approach used")
    inflation_adjusted: bool = Field(description="Whether historical prices are inflation-adjusted")


class VolatilityMetrics(BaseModel):
    """Auction price volatility metrics."""
    coefficient_of_variation: float = Field(description="Std deviation / mean (0-1, higher = more volatile)")
    standard_deviation: float = Field(description="Standard deviation of historical prices")
    volatility_score: int = Field(ge=1, le=10, description="Volatility rating (1=very stable, 10=highly volatile)")
    price_range: float = Field(description="Max - Min historical price")
    stability_assessment: str = Field(description="Human-readable volatility assessment")


class OwnershipCostBreakdown(BaseModel):
    """Annual ownership costs breakdown."""
    vehicle_price: float = Field(description="Purchase price of vehicle")
    annual_depreciation: float = Field(description="Estimated annual depreciation (yearly)")
    annual_insurance: float = Field(description="Estimated annual insurance cost")
    annual_maintenance: float = Field(description="Estimated annual maintenance cost")
    annual_storage: float = Field(description="Estimated annual storage/parking cost")
    total_annual_cost: float = Field(description="Total annual ownership cost")
    cost_per_mile: float = Field(description="Estimated cost per mile driven (assuming 12k miles/year)")
    depreciation_rate: float = Field(description="Annual depreciation as % of vehicle price")


class DataQualityIndicator(BaseModel):
    """Assessment of data quality and prediction confidence."""
    historical_data_points: int = Field(description="Number of historical data points available")
    current_listings_count: int = Field(description="Number of current listings analyzed")
    data_consistency: str = Field(description="Overall data consistency assessment")
    confidence_level: str = Field(description="Low, Medium, or High confidence in prediction")
    notes: str = Field(description="Human-readable notes about data quality")
