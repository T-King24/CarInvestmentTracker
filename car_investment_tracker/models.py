from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class VehicleQuery(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1900)


class PricePoint(BaseModel):
    year: int
    average_price: float


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


class PredictionPoint(BaseModel):
    year: int
    predicted_price: float


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


class DataQualityIndicator(BaseModel):
    """Assessment of data quality and prediction confidence."""
    historical_data_points: int = Field(description="Number of historical data points available")
    current_listings_count: int = Field(description="Number of current listings analyzed")
    data_consistency: str = Field(description="Overall data consistency assessment")
    confidence_level: str = Field(description="Low, Medium, or High confidence in prediction")
    notes: str = Field(description="Human-readable notes about data quality")
