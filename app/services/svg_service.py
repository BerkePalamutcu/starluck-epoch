"""SVG chart generation service."""

import math
from typing import Dict, List, Tuple
from app.services.astrology_core import (
    SIGN_NAMES, ZODIAC, SIGN_SYMBOLS, SIGN_COLORS, P_GLYPH, PLANET_COLORS,
    synastry_aspects, find_aspects
)


class SVGService:
    """Service for generating SVG charts."""
    
    def generate_wheel(self, request) -> Dict:
        """Generate single chart wheel."""
        chart = request.chart_data
        size = request.size
        show_aspects = request.show_aspects
        
        svg_content = self._svg_wheel(chart, size, show_aspects)
        return {"svg_content": svg_content, "size": size}
    
    def generate_biwheel(self, request) -> Dict:
        """Generate synastry biwheel."""
        inner = request.inner_chart
        outer = request.outer_chart
        size = request.size
        lab_in = request.label_inner
        lab_out = request.label_outer
        show_aspects = request.show_aspects
        
        svg_content = self._svg_biwheel(inner, outer, size, lab_in, lab_out, show_aspects)
        return {"svg_content": svg_content}
    
    def _pol_oriented(self, lon: float, r: float, cx: float, cy: float, asc: float) -> Tuple[float, float]:
        """
        Convert polar coordinates with ASC orientation.
        We place ASC at the LEFT (9 o'clock), like the reference image.
        """
        rad = math.radians(asc - lon + 180.0)
        return cx + r * math.cos(rad), cy - r * math.sin(rad)
    
    def _aspect_style(self, label: str) -> Tuple[str, str, str]:
        """Returns color, dash pattern, and opacity for aspect lines"""
        L = label.lower()
        if L == "conjunction":                  return "#FFD700", "", "0.9"
        if L in ("square","opposition"):        return "#FF4444", "", "0.85"
        if L == "trine":                        return "#4CAF50", "", "0.85"
        if L == "sextile":                      return "#00BCD4", "", "0.8"
        if L == "quincunx":                     return "#9C27B0", "5,5", "0.7"
        if L in ("semisquare","sesquiquadrate"):return "#FF9800", "5,5", "0.65"
        if L in ("semisextile","quintile","biquintile","decile","tredecile"):
                                              return "#607D8B", "3,3", "0.6"
        return "#757575", "2,2", "0.5"
    
    def _create_gradient_defs(self, cx: float, cy: float, r_sign_inner: float, r_sign_outer: float) -> str:
        """Create filter/gradient definitions"""
        defs = ['<defs>']
        
        defs.append('''
            <filter id="planet-shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15"/>
            </filter>
        ''')
        
        defs.append('''
            <filter id="angle-glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        ''')
        
        defs.append('''
            <radialGradient id="center-gradient">
                <stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#F6F8FA;stop-opacity:1" />
            </radialGradient>
        ''')
        
        defs.append('</defs>')
        return '\n'.join(defs)

    def _svg_wheel(self, chart: Dict, size: int = 1000, show_aspects: bool = True) -> str:
        """Generate SVG wheel with a purple zodiac band and refined angles."""
        asc = chart["angles"]["ASC"]
        cx = cy = size // 2

        # Radii
        r_outer = size * 0.48
        r_sign_outer  = size * 0.44
        r_sign_inner  = size * 0.37
        r_house_out   = size * 0.35
        r_house_in    = size * 0.24
        r_planet      = size * 0.295
        r_label       = size * 0.33
        r_house_num   = size * 0.20
        r_inner_circle = size * 0.16

        # CSS (escape & as &amp; inside @import)
        css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');

        /* Background */
        .chart-bg { fill: #FAFBFC; }
        .outer-ring { fill: none; stroke: #E1E4E8; stroke-width: 2; }
        .inner-bg { fill: #FFFFFF; }
        .center-circle { fill: #F6F8FA; stroke: #E1E4E8; stroke-width: 1; }

        /* Zodiac band like the reference image */
        .zodiac-band   { fill: #6B46C1; }  /* dark purple */
        .zodiac-cutout { fill: #FFFFFF; }  /* interior of the band */
        .zodiac-divider { stroke: #FFFFFF; stroke-width: 1; }

        .sign-text { 
            font: 600 12px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle; 
            letter-spacing: 0.5px; 
            text-transform: uppercase;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        
        /* Houses */
        .house-circle { fill: none; stroke: #D0D7DE; stroke-width: 1.5; }
        .house-line { stroke: #D0D7DE; stroke-width: 1; opacity: 0.7; }
        .house-num { 
            font: 700 13px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #2C3E50; 
            text-anchor: middle; 
            dominant-baseline: middle;
        }
        
        /* Angles (subtle ticks only, no long thick lines) */
        .angle-tick { stroke: #4A5568; stroke-width: 1.2; stroke-linecap: round; }
        .angle-marker-outer { fill: #2C3E50; }
        .angle-marker-inner { fill: #FFD700; }
        .angle-text-bg { fill: #2C3E50; rx: 3; }
        .angle-text { 
            font: 800 12px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        
        /* Planets */
        .planet-dot { filter: url(#planet-shadow); }
        .planet-glyph { 
            font: 600 16px serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #FFFFFF;
        }
        .planet-degree { 
            font: 400 9px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #586069;
        }
        
        /* Aspects */
        .aspect { fill: none; stroke-linecap: round; }
        """

        def line_at(lon: float, r1: float, r2: float, cls: str) -> str:
            x1,y1 = self._pol_oriented(lon, r1, cx, cy, asc)
            x2,y2 = self._pol_oriented(lon, r2, cx, cy, asc)
            return f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'

        def text_at(lon: float, r: float, text: str, cls: str) -> str:
            x,y = self._pol_oriented(lon, r, cx, cy, asc)
            return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}">{text}</text>'

        # Start SVG
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
            f"<style>{css}</style>",
            self._create_gradient_defs(cx, cy, r_sign_inner, r_sign_outer)
        ]

        # Background
        svg.append(f'<rect class="chart-bg" width="{size}" height="{size}"/>')
        
        # Outer decorative ring
        svg.append(f'<circle class="outer-ring" cx="{cx}" cy="{cy}" r="{r_outer}"/>')

        # --- Zodiac band (purple annulus like the reference) ---
        svg.append(f'<circle class="zodiac-band"   cx="{cx}" cy="{cy}" r="{r_sign_outer}"/>')
        svg.append(f'<circle class="zodiac-cutout" cx="{cx}" cy="{cy}" r="{r_sign_inner}"/>')
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_sign_inner}" fill="none" stroke="#FFFFFF" stroke-width="2"/>')

        # Zodiac dividers
        for s in range(12):
            start = s * 30
            x1, y1 = self._pol_oriented(start, r_sign_inner, cx, cy, asc)
            x2, y2 = self._pol_oriented(start, r_sign_outer, cx, cy, asc)
            svg.append(f'<line class="zodiac-divider" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')

        # Sign labels (full names)
        r_text = (r_sign_outer + r_sign_inner) / 2
        for s in range(12):
            start = s*30
            sign_name = ZODIAC[s]
            svg.append(text_at(start + 15, r_text, sign_name.upper(), "sign-text"))

        # House circles
        svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_out}"/>')
        svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_in}"/>')

        # House lines and numbers
        for i, house_cusp in enumerate(chart["houses"]):
            svg.append(line_at(house_cusp, r_house_in, r_house_out, "house-line"))
            # House number
            x, y = self._pol_oriented(house_cusp, r_house_num, cx, cy, asc)
            svg.append(f'<text class="house-num" x="{x:.1f}" y="{y:.1f}">{i+1}</text>')
            
            label = ""
            # Optional: show sign split like "Ar 20% / Ta 80%"
            if chart.get("house_signs"):
                segs = chart["house_signs"][i]
                # take up to 2 largest segments for brevity
                segs_sorted = sorted(segs, key=lambda s: s["percent"], reverse=True)[:2]

                def abbr(sign: str) -> str:
                    return {
                        "Aries":"Ar","Taurus":"Ta","Gemini":"Ge","Cancer":"Cn","Leo":"Le","Virgo":"Vi",
                        "Libra":"Li","Scorpio":"Sc","Sagittarius":"Sg","Capricorn":"Cp","Aquarius":"Aq","Pisces":"Pi"
                    }.get(sign, sign[:2])

                label = " / ".join(f'{abbr(s["sign"])} {int(round(s["percent"]))}%'
                                for s in segs_sorted if s["percent"] >= 1)

            if label:
                x2, y2 = self._pol_oriented(house_cusp, r_house_num + 18, cx, cy, asc)
                svg.append(
                    f'<text class="house-num" x="{x2:.1f}" y="{y2:.1f}" '
                    f'style="font-weight:600; font-size:11px; fill:#445; opacity:0.85;">{label}</text>'
                )

        # Inner circle
        svg.append(f'<circle class="center-circle" cx="{cx}" cy="{cy}" r="{r_inner_circle}"/>')

        # Angles (ASC/DS/MC/IC) — short ticks near the band; no long lines
        tick_start = r_house_out + 2
        tick_end   = r_sign_inner - 2
        angle_data = [
            (chart["angles"]["ASC"], "ASC"),
            (chart["angles"]["DS"],  "DS"),
            (chart["angles"]["MC"],  "MC"),
            (chart["angles"]["IC"],  "IC")
        ]
        for lon, abbr in angle_data:
            svg.append(line_at(lon, tick_start, tick_end, "angle-tick"))
            # marker + compact label hugging the band
            x, y = self._pol_oriented(lon, r_sign_inner - 12, cx, cy, asc)
            svg.append(f'<circle class="angle-marker-outer" cx="{x:.1f}" cy="{y:.1f}" r="5" filter="url(#angle-glow)"/>')
            svg.append(f'<circle class="angle-marker-inner" cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>')
            text_x, text_y = self._pol_oriented(lon, r_sign_inner - 26, cx, cy, asc)
            svg.append(f'<rect class="angle-text-bg" x="{text_x-16:.1f}" y="{text_y-7:.1f}" width="32" height="14"/>')
            svg.append(f'<text class="angle-text" x="{text_x:.1f}" y="{text_y:.1f}">{abbr}</text>')

        # Calculate aspects if not provided
        if show_aspects:
            if not chart.get("aspects"):
                planet_lons = {k: v["lon"] for k, v in chart["planets"].items() if k != "PartOfFortune"}
                chart["aspects"] = find_aspects(planet_lons)

        # Planets
        placed: List[Tuple[float,float]] = []
        planet_elements = []
        
        for name, p in sorted(chart["planets"].items(), key=lambda kv: kv[1]["lon"]):
            lon = p["lon"]
            r_use = r_planet
            
            # Anti-collision
            for (plon, pr) in placed[-8:]:
                if min(abs(lon-plon), 360-abs(lon-plon)) <= 8:
                    r_use -= 15
            
            x, y = self._pol_oriented(lon, r_use, cx, cy, asc)
            color = PLANET_COLORS.get(name, "#000")
            
            planet_group = [f'<g transform="translate({x:.1f},{y:.1f})">']
            planet_group.append(f'<circle class="planet-dot" r="11" fill="{color}"/>')
            planet_group.append(f'<text class="planet-glyph" x="0" y="1">{P_GLYPH.get(name, name[0])}</text>')
            planet_group.append('</g>')
            planet_elements.extend(planet_group)
            
            d = int(p["deg"])
            m = int(round((p["deg"]-d)*60))
            retro = "℞" if p.get("retro") else ""
            degree_label = f'{d}°{m:02d}′{retro}'
            
            label_r = r_label if r_use == r_planet else r_use + 25
            label_x, label_y = self._pol_oriented(lon, label_r, cx, cy, asc)
            planet_elements.append(f'<text class="planet-degree" x="{label_x:.1f}" y="{label_y:.1f}">{degree_label}</text>')
            
            placed.append((lon, r_use))
        
        svg.extend(planet_elements)

        # Aspects
        if show_aspects and chart.get("aspects"):
            aspect_group = ['<g opacity="0.8">']
            pts = {k: self._pol_oriented(v["lon"], r_planet, cx, cy, asc) for k,v in chart["planets"].items() if k!="PartOfFortune"}
            
            for a in chart["aspects"]:
                p1, p2 = a["p1"], a["p2"]
                if p1 not in pts or p2 not in pts: 
                    continue
                
                col, dash, opacity = self._aspect_style(a["aspect"])
                x1, y1 = pts[p1]
                x2, y2 = pts[p2]
                
                dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
                stroke_width = "2.5" if a["aspect"] in ["conjunction", "opposition", "square", "trine"] else "2"
                
                aspect_group.append(
                    f'<line class="aspect" stroke="{col}" stroke-width="{stroke_width}" '
                    f'opacity="{opacity}"{dash_attr} '
                    f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
                )
            
            aspect_group.append('</g>')
            svg.extend(aspect_group)

        svg.append("</svg>")
        return "\n".join(svg)
    
    def _svg_biwheel(self, inner: Dict, outer: Dict, size: int = 1000,
                    lab_in: str = "Inner", lab_out: str = "Outer",
                    show_aspects: bool = True) -> str:
        """Generate synastry biwheel SVG with the same band + subtle angles."""
        asc = inner["angles"]["ASC"]
        cx = cy = size // 2

        r_outer = size * 0.48
        r_sign_outer  = size * 0.44
        r_sign_inner  = size * 0.37
        r_house_out   = size * 0.35
        r_house_in    = size * 0.24
        r_in_planet   = size * 0.295
        r_in_label    = size * 0.33
        r_out_planet  = size * 0.40
        r_out_label   = size * 0.44
        r_house_num   = size * 0.20
        r_inner_circle = size * 0.16

        css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
        
        .chart-bg { fill: #FAFBFC; }
        .outer-ring { fill: none; stroke: #E1E4E8; stroke-width: 2; }
        .inner-bg { fill: #FFFFFF; }
        .center-circle { fill: #F6F8FA; stroke: #E1E4E8; stroke-width: 1; }
        
        /* Purple zodiac band only */
        .zodiac-band   { fill: #6B46C1; }
        .zodiac-cutout { fill: #FFFFFF; }
        .zodiac-divider { stroke: #FFFFFF; stroke-width: 1; }
        .sign-text { 
            font: 600 12px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle; 
            letter-spacing: 0.5px; 
            text-transform: uppercase;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        
        .house-circle { fill: none; stroke: #D0D7DE; stroke-width: 1.5; }
        .house-line { stroke: #D0D7DE; stroke-width: 1; opacity: 0.7; }
        .house-num { 
            font: 700 13px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #2C3E50; 
            text-anchor: middle; 
            dominant-baseline: middle;
        }
        
        /* Angles: short ticks only */
        .angle-tick { stroke: #4A5568; stroke-width: 1.2; stroke-linecap: round; }
        .angle-marker-outer { fill: #2C3E50; }
        .angle-marker-inner { fill: #FFD700; }
        .angle-text-bg { fill: #2C3E50; rx: 3; }
        .angle-text { 
            font: 800 12px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        
        .pin { filter: url(#planet-shadow); }
        .pout { filter: url(#planet-shadow); opacity: 0.85; }
        .lbl { 
            font: 600 18px serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #FFFFFF;
        }
        .aspect { fill: none; stroke-linecap: round; }
        """

        def line_at(lon, r1, r2, cls):
            x1,y1 = self._pol_oriented(lon, r1, cx, cy, asc)
            x2,y2 = self._pol_oriented(lon, r2, cx, cy, asc)
            return f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'

        def text_at(lon, r, t, cls):
            x,y = self._pol_oriented(lon, r, cx, cy, asc)
            return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}">{t}</text>'

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
            f"<style>{css}</style>",
            self._create_gradient_defs(cx, cy, r_sign_inner, r_sign_outer)
        ]

        svg.append(f'<rect class="chart-bg" width="{size}" height="{size}"/>')
        svg.append(f'<circle class="outer-ring" cx="{cx}" cy="{cy}" r="{r_outer}"/>')

        # --- Zodiac band (purple annulus) ---
        svg.append(f'<circle class="zodiac-band"   cx="{cx}" cy="{cy}" r="{r_sign_outer}"/>')
        svg.append(f'<circle class="zodiac-cutout" cx="{cx}" cy="{cy}" r="{r_sign_inner}"/>')
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_sign_inner}" fill="none" stroke="#FFFFFF" stroke-width="2"/>')

        # Dividers
        for s in range(12):
            start = s * 30
            x1, y1 = self._pol_oriented(start, r_sign_inner, cx, cy, asc)
            x2, y2 = self._pol_oriented(start, r_sign_outer, cx, cy, asc)
            svg.append(f'<line class="zodiac-divider" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')

        # Sign labels
        r_text = (r_sign_outer + r_sign_inner) / 2
        for s in range(12):
            start = s*30
            sign_name = ZODIAC[s]
            svg.append(text_at(start + 15, r_text, sign_name.upper(), "sign-text"))

        # Houses
        svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_out}"/>')
        svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_in}"/>')

        for i, house_cusp in enumerate(inner["houses"]):
            svg.append(line_at(house_cusp, r_house_in, r_house_out, "house-line"))
            x, y = self._pol_oriented(house_cusp, r_house_num, cx, cy, asc)
            svg.append(f'<text class="house-num" x="{x:.1f}" y="{y:.1f}">{i+1}</text>')

        # Center
        svg.append(f'<circle class="center-circle" cx="{cx}" cy="{cy}" r="{r_inner_circle}"/>')

        # Angles: ticks only near band
        tick_start = r_house_out + 2
        tick_end   = r_sign_inner - 2
        angle_data = [
            (inner["angles"]["ASC"], "ASC"),
            (inner["angles"]["DS"],  "DS"),
            (inner["angles"]["MC"],  "MC"),
            (inner["angles"]["IC"],  "IC")
        ]
        for lon, abbr in angle_data:
            svg.append(line_at(lon, tick_start, tick_end, "angle-tick"))
            x, y = self._pol_oriented(lon, r_sign_inner - 12, cx, cy, asc)
            svg.append(f'<circle class="angle-marker-outer" cx="{x:.1f}" cy="{y:.1f}" r="5" filter="url(#angle-glow)"/>')
            svg.append(f'<circle class="angle-marker-inner" cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>')
            text_x, text_y = self._pol_oriented(lon, r_sign_inner - 26, cx, cy, asc)
            svg.append(f'<rect class="angle-text-bg" x="{text_x-16:.1f}" y="{text_y-7:.1f}" width="32" height="14"/>')
            svg.append(f'<text class="angle-text" x="{text_x:.1f}" y="{text_y:.1f}">{abbr}</text>')

        # Inner planets
        used=[]
        for name,p in sorted(inner["planets"].items(), key=lambda kv: kv[1]["lon"]):
            lon=p["lon"]; rr=r_in_planet
            for (pl,pr) in used[-8:]:
                if min(abs(lon-pl), 360-abs(lon-pl)) <= 8: rr -= 15
            x,y = self._pol_oriented(lon, rr, cx, cy, asc)
            color = PLANET_COLORS.get(name, "#000")
            svg.append(f'<circle class="pin" cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{color}"/>')
            svg.append(f'<text class="lbl" x="{x:.1f}" y="{y+1:.1f}">{P_GLYPH.get(name,name[0])}</text>')
            used.append((lon,rr))

        # Outer planets
        used=[]
        for name,p in sorted(outer["planets"].items(), key=lambda kv: kv[1]["lon"]):
            lon=p["lon"]; rr=r_out_planet
            for (pl,pr) in used[-8:]:
                if min(abs(lon-pl), 360-abs(lon-pl)) <= 8: rr += 15
            x,y = self._pol_oriented(lon, rr, cx, cy, asc)
            color = PLANET_COLORS.get(name, "#000")
            svg.append(f'<circle class="pout" cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}"/>')
            svg.append(f'<text class="lbl" x="{x:.1f}" y="{y+1:.1f}">{P_GLYPH.get(name,name[0])}</text>')
            used.append((lon,rr))

        # Synastry aspects
        if show_aspects:
            aspects = synastry_aspects(inner, outer)
            aspect_group = ['<g opacity="0.6">']
            pts_in = {k: self._pol_oriented(v["lon"], r_in_planet, cx, cy, asc) for k,v in inner["planets"].items()}
            pts_out = {k: self._pol_oriented(v["lon"], r_out_planet, cx, cy, asc) for k,v in outer["planets"].items()}
            
            for a in aspects:
                if a["p1"] in pts_in and a["p2"] in pts_out:
                    x1,y1 = pts_in[a["p1"]]; x2,y2 = pts_out[a["p2"]]
                    col, dash, opacity = self._aspect_style(a["aspect"])
                    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
                    aspect_group.append(
                        f'<line class="aspect" stroke="{col}" stroke-width="1.5" '
                        f'opacity="{opacity}"{dash_attr} '
                        f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
                    )
            
            aspect_group.append('</g>')
            svg.extend(aspect_group)

        svg.append("</svg>")
        return "\n".join(svg)
