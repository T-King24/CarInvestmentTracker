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
