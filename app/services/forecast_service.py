from app.models.schemas import ForecastRequest, ForecastResponse, TransitHit
from app.services.astrology_core import (
    _retrograde_swiss,
    forecast_transits,
    planet_longitudes,
    HAVE_SWE
)
from datetime import datetime

class ForecastService:
    def generate_forecast(self, request: ForecastRequest) -> ForecastResponse:
        start_local = datetime.fromisoformat(request.start_date)
        
        # Generate raw aspect hits
        hits = forecast_transits(
            request.natal_chart,
            start_local,
            request.timezone,
            days=request.days,
            step_hours=request.step_hours
        )
        
        # Build a map of unique UTC times to compute planetary conditions once
        unique_utc_times = set()
        hit_time_map = {}  # (transit, when_utc) -> hit index
        for i, hit in enumerate(hits):
            dt_utc = datetime.fromisoformat(hit["when_utc"].replace("Z", "+00:00"))
            unique_utc_times.add(dt_utc)
            key = (hit["transit"], dt_utc)
            hit_time_map[key] = i

        # Precompute planetary conditions per UTC time
        planet_conditions = {}
        for dt_utc in unique_utc_times:
            lons = planet_longitudes(dt_utc)  # all planet longitudes
            sun_lon = lons.get("Sun", 0.0)
            conditions = {}
            for planet in lons:
                # Retrograde
                is_retro = _retrograde_swiss(dt_utc, planet) if HAVE_SWE else False
                # Combust: within 8.5° of Sun
                sep = min(abs(lons[planet] - sun_lon), 360 - abs(lons[planet] - sun_lon))
                is_combust = sep <= 8.5 and planet != "Sun"
                conditions[planet] = {
                    "is_retrograde": is_retro,
                    "is_combust": is_combust
                }
            planet_conditions[dt_utc] = conditions

        # Enrich hits with conditions
        enriched_hits = []
        for hit in hits:
            dt_utc = datetime.fromisoformat(hit["when_utc"].replace("Z", "+00:00"))
            transit = hit["transit"]
            cond = planet_conditions[dt_utc].get(transit, {})
            
            # Get natal house for functional nature
            natal_planet = hit["natal"]
            natal_info = request.natal_chart.get("planets", {}).get(natal_planet, {})
            natal_house = natal_info.get("house")  # Whole Sign → 1–12

            # Add to hit
            enriched_hit = {
                **hit,
                "is_retrograde": cond.get("is_retrograde", False),
                "is_combust": cond.get("is_combust", False),
                "natal_house": natal_house,
            }
            enriched_hits.append(enriched_hit)

        # Convert to response
        transits = [
            TransitHit(
                when_utc=h["when_utc"],
                transit=h["transit"],
                natal=h["natal"],
                aspect=h["aspect"],
                orb_diff=h["orb_diff"],
                is_retrograde=h["is_retrograde"],
                is_combust=h["is_combust"],
                natal_house=h["natal_house"],
            )
            for h in enriched_hits
        ]
        
        return ForecastResponse(transits=transits)