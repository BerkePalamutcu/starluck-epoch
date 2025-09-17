"""Forecast service for transit calculations."""

from datetime import datetime
from typing import Dict, List
from app.models.schemas import ForecastRequest, ForecastResponse, TransitHit
from app.services.astrology_core import forecast_transits


class ForecastService:
    """Service for transit forecasts."""
    
    def generate_forecast(self, request: ForecastRequest) -> ForecastResponse:
        """Generate transit forecast."""
        # Parse start date
        start_local = datetime.fromisoformat(request.start_date)
        
        # Generate forecast
        hits = forecast_transits(
            request.natal_chart,
            start_local,
            request.timezone,
            days=request.days,
            step_hours=request.step_hours
        )
        
        # Convert to response format
        transits = [
            TransitHit(
                when_utc=hit["when_utc"],
                transit=hit["transit"],
                natal=hit["natal"],
                aspect=hit["aspect"],
                orb_diff=hit["orb_diff"]
            )
            for hit in hits
        ]
        
        return ForecastResponse(transits=transits)
