"""Report generation service for astrological charts."""

from typing import Dict, List
from app.models.schemas import ReportRequest, ReportResponse
from app.services.astrology_core import (
    SIGN_SYMBOLS, P_GLYPH, fmt_deg, deg_to_signpos
)


class ReportService:
    """Service for generating astrological reports."""
    
    def generate_report(self, request: ReportRequest) -> ReportResponse:
        """Generate a markdown report from chart data."""
        report_content = self._make_report(request.chart_data, request.title)
        return ReportResponse(report_content=report_content)
    
    def _chart_headline(self, chart: Dict) -> str:
        """Generate chart headline."""
        sun = chart["planets"]["Sun"]
        moon = chart["planets"]["Moon"]
        asc_sign, _d, _i = deg_to_signpos(chart["angles"]["ASC"])
        sun_symbol = SIGN_SYMBOLS[sun['sign']]
        moon_symbol = SIGN_SYMBOLS[moon['sign']]
        asc_symbol = SIGN_SYMBOLS[asc_sign]
        return f"✨ {sun['sign']} {sun_symbol} Sun • {moon['sign']} {moon_symbol} Moon • {asc_sign} {asc_symbol} Rising"
    
    def _planet_rows(self, chart: Dict) -> List[str]:
        """Generate planet position rows."""
        order = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","TrueNode","Chiron","PartOfFortune"]
        rows = []
        for name in order:
            if name not in chart["planets"]: 
                continue
            p = chart["planets"][name]
            sign_symbol = SIGN_SYMBOLS[p['sign']]
            retro_symbol = " ℞" if p["retro"] else ""
            rows.append(f"**{P_GLYPH[name]} {name}** — {fmt_deg(p['deg'])} {p['sign']} {sign_symbol} (House {p['house']}){retro_symbol}")
        return rows
    
    def _make_report(self, chart: Dict, person_label: str = "Birth Chart Analysis") -> str:
        """Generate markdown report - extracted from CLI logic."""
        from datetime import datetime
        
        phase_name = chart["moon_phase"]["name"]
        phase_angle = chart["moon_phase"]["angle"]
        
        lines = []
        lines.append(f"# 🌟 {person_label}")
        lines.append("")
        lines.append("## " + self._chart_headline(chart))
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Chart Data Section
        dt = datetime.fromisoformat(chart["datetime_utc"]).strftime("%B %d, %Y at %H:%M UTC")
        lat = chart["location"]["lat"]
        lon = chart["location"]["lon"]
        tzname = chart["location"]["tz"]
        
        lines.append("### 📍 Chart Information")
        lines.append("")
        lines.append(f"**Date & Time:** {dt}  ")
        lines.append(f"**Location:** {lat:.4f}°, {lon:.4f}°  ")
        lines.append(f"**House System:** {chart['house_system'].title()}  ")
        lines.append(f"**Chart Sect:** {'☀️ Day Chart' if chart['sect'] == 'DAY' else '🌙 Night Chart'}  ")
        lines.append("")
        
        # Planets Section
        lines.append("### 🪐 Planetary Positions")
        lines.append("")
        for row in self._planet_rows(chart):
            lines.append(row + "  ")
        lines.append("")
        
        # Angles Section
        lines.append("### 📐 Cardinal Points")
        lines.append("")
        for angle, label in [("ASC", "Ascendant"), ("MC", "Midheaven"), ("DS", "Descendant"), ("IC", "Imum Coeli")]:
            angle_deg = chart['angles'][angle]
            sign, deg, idx = deg_to_signpos(angle_deg)
            sign_symbol = SIGN_SYMBOLS[sign]
            lines.append(f"**{label}:** {fmt_deg(deg)} {sign} {sign_symbol}  ")
        lines.append("")
        
        # Moon Phase Section
        lines.append("### 🌙 Lunar Phase")
        lines.append("")
        lines.append(f"**{phase_name}** ({phase_angle:.1f}° separation)")
        lines.append("")
        
        # Aspects Section
        lines.append("### ⚡ Major Aspects")
        lines.append("")
        if chart["aspects"]:
            # Group aspects by type
            aspect_groups = {}
            for a in chart["aspects"]:
                aspect_type = a["aspect"]
                if aspect_type not in aspect_groups:
                    aspect_groups[aspect_type] = []
                aspect_groups[aspect_type].append(a)
            
            # Display aspects by importance
            aspect_order = ["conjunction", "opposition", "square", "trine", "sextile", 
                           "quincunx", "semisquare", "sesquiquadrate", "semisextile", 
                           "quintile", "biquintile", "decile", "tredecile"]
            
            for aspect_type in aspect_order:
                if aspect_type in aspect_groups:
                    for a in aspect_groups[aspect_type]:
                        orb_str = f"(orb: {abs(a['off']):.1f}°)"
                        lines.append(f"{P_GLYPH.get(a['p1'],a['p1'])} **{a['p1']}** {a['glyph']} **{a['p2']}** {P_GLYPH.get(a['p2'],a['p2'])} — *{a['aspect']}* {orb_str}  ")
        else:
            lines.append("*No major aspects found in this chart.*")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated with Starluck*")
        
        return "\n".join(lines)
