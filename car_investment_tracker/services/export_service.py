from __future__ import annotations

import csv
from io import StringIO
from datetime import datetime
from typing import Any


def export_to_csv(
    brand: str,
    model: str,
    year: int,
    historical_prices: list[dict],
    predictions: list[dict],
    sentiment_score: float,
    current_listing_avg: float,
) -> str:
    """Export analysis data to CSV format.
    
    Args:
        brand: Vehicle brand
        model: Vehicle model
        year: Vehicle year
        historical_prices: Historical price points
        predictions: Price predictions
        sentiment_score: Sentiment score (0-5)
        current_listing_avg: Current market average
        
    Returns:
        CSV content as string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Header section
    writer.writerow(["CarInvestmentTracker Export Report"])
    writer.writerow([])
    writer.writerow(["Vehicle Information"])
    writer.writerow(["Brand", brand])
    writer.writerow(["Model", model])
    writer.writerow(["Year", year])
    writer.writerow(["Report Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    # Summary section
    writer.writerow(["Market Summary"])
    writer.writerow(["Current Listing Average", f"${current_listing_avg:,.2f}"])
    writer.writerow(["Sentiment Score", f"{sentiment_score}/5"])
    writer.writerow([])
    
    # Historical prices section
    writer.writerow(["Historical Prices (Last 20 Years)"])
    writer.writerow(["Year", "Price"])
    for point in historical_prices:
        year_val = point.get("year", point.get("year", ""))
        price = point.get("average_price", point.get("average_price", ""))
        writer.writerow([year_val, f"${price:,.2f}"])
    writer.writerow([])
    
    # Predictions section
    writer.writerow(["Price Predictions (5-Year Forecast)"])
    writer.writerow(["Year", "Predicted Price", "Lower Bound", "Upper Bound"])
    for point in predictions:
        year_val = point.get("year", "")
        predicted = point.get("predicted_price", "")
        lower = point.get("lower_bound", "")
        upper = point.get("upper_bound", "")
        writer.writerow([
            year_val,
            f"${predicted:,.2f}" if predicted else "",
            f"${lower:,.2f}" if lower else "",
            f"${upper:,.2f}" if upper else "",
        ])
    
    return output.getvalue()


def export_investor_report(
    brand: str,
    model: str,
    year: int,
    analysis_data: dict,
) -> str:
    """Export a formatted investor report.
    
    Args:
        brand: Vehicle brand
        model: Vehicle model
        year: Vehicle year
        analysis_data: Full analysis data from /analysis endpoint
        
    Returns:
        Formatted report as text
    """
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("INVESTMENT CAR VALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Vehicle Details
    report_lines.append("VEHICLE DETAILS")
    report_lines.append("-" * 80)
    report_lines.append(f"Brand:     {brand}")
    report_lines.append(f"Model:     {model}")
    report_lines.append(f"Year:      {year}")
    report_lines.append(f"Age:       {2026 - year} years")
    report_lines.append("")
    
    # Market Summary
    report_lines.append("MARKET SUMMARY")
    report_lines.append("-" * 80)
    summary = analysis_data.get("summary", {})
    report_lines.append(f"Sentiment Score:           {summary.get('sentiment_score', 'N/A')}")
    report_lines.append(f"Prediction Confidence:     {summary.get('prediction_confidence', 'N/A')}")
    current_avg = analysis_data.get("current_listing_average", 0)
    report_lines.append(f"Current Market Average:    ${current_avg:,.2f}")
    report_lines.append("")
    
    # Price Forecast
    report_lines.append("PRICE FORECAST (5-Year Outlook)")
    report_lines.append("-" * 80)
    predictions = analysis_data.get("prediction", [])
    if predictions:
        for pred in predictions[:5]:  # Show next 5 years
            year_val = pred.get("year", "")
            price = pred.get("predicted_price", 0)
            lower = pred.get("lower_bound", 0)
            upper = pred.get("upper_bound", 0)
            report_lines.append(
                f"{year_val}: ${price:,.2f} (Range: ${lower:,.2f} - ${upper:,.2f})"
            )
    report_lines.append("")
    
    # Volatility Assessment
    report_lines.append("MARKET VOLATILITY")
    report_lines.append("-" * 80)
    volatility = analysis_data.get("volatility_metrics", {})
    if volatility:
        volatility_score = volatility.get("volatility_score", "N/A")
        assessment = volatility.get("stability_assessment", "N/A")
        report_lines.append(f"Volatility Score:  {volatility_score}/10")
        report_lines.append(f"Assessment:        {assessment}")
    report_lines.append("")
    
    # Comparable Sales
    report_lines.append("COMPARABLE RECENT SALES")
    report_lines.append("-" * 80)
    comparables = analysis_data.get("market_comparables", {}).get("comparables", [])
    if comparables:
        for i, comp in enumerate(comparables[:5], 1):  # Show top 5
            price = comp.get("price", 0)
            days_ago = comp.get("days_ago", 0)
            condition = comp.get("condition", "N/A")
            source = comp.get("source", "N/A")
            report_lines.append(
                f"{i}. ${price:,.2f} ({days_ago} days ago) - Condition: {condition}/5 - {source}"
            )
    report_lines.append("")
    
    # Data Quality
    report_lines.append("DATA QUALITY & CONFIDENCE")
    report_lines.append("-" * 80)
    data_quality = analysis_data.get("data_quality", {})
    if data_quality:
        hist_points = data_quality.get("historical_data_points", "N/A")
        listings = data_quality.get("current_listings_count", "N/A")
        confidence = data_quality.get("confidence_level", "N/A")
        report_lines.append(f"Historical Data Points:    {hist_points}")
        report_lines.append(f"Current Listings Analyzed: {listings}")
        report_lines.append(f"Confidence Level:          {confidence}")
    report_lines.append("")
    
    # Methodology
    report_lines.append("METHODOLOGY")
    report_lines.append("-" * 80)
    methodology = analysis_data.get("methodology", {})
    for key, value in methodology.items():
        key_formatted = key.replace("_", " ").title()
        report_lines.append(f"{key_formatted}: {value}")
    report_lines.append("")
    
    # Footer
    report_lines.append("=" * 80)
    report_lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("This report is for informational purposes and should not be considered")
    report_lines.append("as professional financial or investment advice.")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)
