from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class MarketEvent(BaseModel):
    """Market event that affected vehicle prices."""
    year: int
    event_type: str = Field(description="Type: 'New Model Release', 'Market Crash', 'Regulation', 'Special Edition'")
    title: str = Field(description="Event title")
    description: str = Field(description="Detailed event description")
    impact: str = Field(description="'Positive', 'Negative', or 'Neutral'")
    severity: int = Field(ge=1, le=10, description="Impact severity (1=minor, 10=major)")


def get_market_events(brand: str, model: str, start_year: int, end_year: int) -> list[MarketEvent]:
    """Get major market events affecting vehicle valuations.
    
    In production, this would query a database of historical automotive events.
    Currently returns curated events based on brand/model.
    
    Args:
        brand: Vehicle brand
        model: Vehicle model
        start_year: Start year for events
        end_year: End year for events
        
    Returns:
        List of market events sorted by year
    """
    current_year = datetime.now(timezone.utc).year
    events: list[MarketEvent] = []
    
    # Generic events that affect all or most luxury/performance cars
    if start_year <= 2008 <= end_year:
        events.append(MarketEvent(
            year=2008,
            event_type="Market Crash",
            title="Global Financial Crisis",
            description="Major economic downturn significantly impacted luxury vehicle valuations",
            impact="Negative",
            severity=9,
        ))
    
    if start_year <= 2020 <= end_year:
        events.append(MarketEvent(
            year=2020,
            event_type="Market Crash",
            title="COVID-19 Pandemic",
            description="Global pandemic caused initial market disruption, later recovered with strong collector demand",
            impact="Neutral",
            severity=7,
        ))
    
    if start_year <= 2023 <= end_year:
        events.append(MarketEvent(
            year=2023,
            event_type="Regulation",
            title="EV Transition & Emissions Standards",
            description="Stricter emissions regulations increased interest in older collector vehicles",
            impact="Positive",
            severity=6,
        ))
    
    # Brand/Model specific events
    brand_lower = brand.lower()
    model_lower = model.lower()
    
    if brand_lower == "porsche":
        if start_year <= 2015 <= end_year and model_lower in ["911", "carrera", "turbo"]:
            events.append(MarketEvent(
                year=2015,
                event_type="New Model Release",
                title="991.1 Generation Peak Interest",
                description="Earlier 991 generation models peaked in collector value as newest generation started production",
                impact="Positive",
                severity=5,
            ))
        
        if start_year <= 1998 <= end_year and model_lower in ["911", "carrera"]:
            events.append(MarketEvent(
                year=1998,
                event_type="Model Change",
                title="996 Generation Introduction",
                description="Water-cooled engine introduction caused market disruption",
                impact="Negative",
                severity=7,
            ))
    
    if brand_lower == "ferrari":
        if start_year <= 2011 <= end_year:
            events.append(MarketEvent(
                year=2011,
                event_type="Market Event",
                title="Japanese Earthquake & Tsunami",
                description="Natural disaster in Japan temporarily impacted luxury market",
                impact="Negative",
                severity=4,
            ))
    
    if brand_lower == "bmw" and model_lower in ["m3", "m5", "m6"]:
        if start_year <= 2008 <= end_year:
            events.append(MarketEvent(
                year=2008,
                event_type="Model Change",
                title="E90/E92 M3 Generation Peak",
                description="Peak production year for high-demand M generation",
                impact="Positive",
                severity=5,
            ))
    
    # Sort by year
    events.sort(key=lambda e: e.year)
    
    return events
