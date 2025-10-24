"""SVG chart generation service."""

import math
from typing import Dict, List, Tuple
from app.services.astrology_core import (
     ZODIAC, P_GLYPH,
    synastry_aspects, find_aspects
)


class SVGService:
    """
    Service for generating SVG charts optimized for mobile and desktop viewing.
    
    Mobile Optimization (React Native):
    - Larger base font sizes (18px for zodiac signs, 20px for house numbers)
    - Thicker stroke widths (2-3px for better visibility)
    - Larger planet circles (12-14px radius) and angle markers (6-7px)
    - Bold font weights (800-900) for critical text elements
    - Increased letter spacing for improved readability
    - Enhanced text shadows and visual contrast
    
    All elements are proportionally sized to scale well across:
    - Mobile phones (320px - 480px width)
    - Tablets (768px - 1024px width)  
    - Desktop screens (1200px+ width)
    
    Note: This is optimized for React Native SVG rendering where CSS media queries
    are not supported. All sizing is done at the base level to ensure clarity on
    small screens while remaining visually balanced on larger displays.
    """
    
    def generate_wheel(self, request) -> Dict:
        """Generate single chart wheel."""
        chart = request.chart_data
        size = request.size
        show_aspects = request.show_aspects
        show_planet_degrees = getattr(request, 'show_planet_degrees', False)
        show_houses = getattr(request, 'show_houses', True)
        
        svg_content = self._svg_wheel(chart, size, show_aspects, show_planet_degrees, show_houses)
        return {"svg_content": svg_content, "size": size}
    
    def generate_biwheel(self, request) -> Dict:
        """Generate synastry biwheel."""
        inner = request.inner_chart
        outer = request.outer_chart
        size = request.size
        lab_in = request.label_inner
        lab_out = request.label_outer
        show_aspects = request.show_aspects
        show_planet_degrees = getattr(request, 'show_planet_degrees', False)
        show_houses = getattr(request, 'show_houses', True)
        
        svg_content = self._svg_biwheel(inner, outer, size, lab_in, lab_out, show_aspects, show_planet_degrees, show_houses)
        return {"svg_content": svg_content}
    
    def _pol_oriented(self, lon: float, r: float, cx: float, cy: float, asc: float) -> Tuple[float, float]:
        """
        Convert polar coordinates with ASC orientation.
        We place ASC at the LEFT (9 o'clock), like the reference image.
        """
        rad = math.radians(asc - lon + 180.0)
        return cx + r * math.cos(rad), cy - r * math.sin(rad)
    
    def _aspect_style(self, label: str) -> Tuple[str, str, str]:
            """Returns color, dash pattern, and opacity for aspect lines - black and white version"""
            L = label.lower()
            if L == "conjunction":                  return "#000000", "", "0.9"
            if L in ("square","opposition"):        return "#000000", "", "0.85"
            if L == "trine":                        return "#000000", "5,5", "0.85"
            if L == "sextile":                      return "#000000", "3,3", "0.8"
            if L == "quincunx":                     return "#000000", "8,8", "0.7"
            if L in ("semisquare","sesquiquadrate"):return "#000000", "5,5", "0.65"
            if L in ("semisextile","quintile","biquintile","decile","tredecile"):
                                                return "#000000", "3,3", "0.6"
            return "#000000", "2,2", "0.5"

    
    def _create_gradient_defs(self, cx: float, cy: float, r_sign_inner: float, r_sign_outer: float) -> str:
        """Create filter/gradient definitions"""
        defs = ['<defs>']
        
        defs.append('''
            <filter id="planet-shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15"/>
            </filter>
        ''')
        
        defs.append('''
            <filter id="glyph-glow">
                <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
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

    def _svg_wheel(self, chart: Dict, size: int = 1000, show_aspects: bool = True, 
                   show_planet_degrees: bool = True, show_houses: bool = True) -> str:
        """Generate mobile-optimized single wheel with modern design."""
        asc = chart["angles"]["ASC"]
        cx = cy = size // 2

        # Radii - houses now between zodiac and planets
        r_outer = size * 0.48
        r_sign_outer  = size * 0.44
        r_sign_inner  = size * 0.37
        r_house_out   = size * 0.35
        r_house_in    = size * 0.28
        r_planet      = size * 0.24
        r_label       = size * 0.20
        r_house_num   = size * 0.315
        r_inner_circle = size * 0.20

        # CSS - optimized for mobile viewing in React Native (scales well on desktop too)
        css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=Cinzel:wght@400;500;600;700;800;900&amp;display=swap');

        /* Background */
        .chart-bg { fill: #FAFBFC; }
        .outer-ring { fill: none; stroke: #E1E4E8; stroke-width: 3; }
        .inner-bg { fill: #FFFFFF; }
        .center-circle { fill: #F6F8FA; stroke: #E1E4E8; stroke-width: 2; }

        /* Zodiac band - larger text and thicker lines for mobile */
        .zodiac-band   { fill: #000000; }
        .zodiac-cutout { fill: #FFFFFF; }
        .zodiac-divider { stroke: #FFFFFF; stroke-width: 2; }

        .sign-text { 
            font: 800 18px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle; 
            letter-spacing: 1px; 
            text-transform: uppercase;
            text-shadow: 0 2px 4px rgba(0,0,0,0.6);
        }
        
        /* Houses - more visible */
        .house-circle { fill: none; stroke: #D0D7DE; stroke-width: 2.5; }
        .house-line { stroke: #D0D7DE; stroke-width: 2; opacity: 0.7; }
        .house-num { 
            font: 700 22px 'Cinzel', serif; 
            fill: #1A1A1A; 
            text-anchor: middle; 
            dominant-baseline: middle;
            letter-spacing: 0.5px;
        }
        
        /* Angles - larger and more prominent */
        .angle-tick { stroke: #4A5568; stroke-width: 1.5; stroke-linecap: round; }
        .angle-marker-outer { fill: #2C3E50; }
        .angle-marker-inner { fill: #FFD700; }
        .angle-text-bg { fill: #2C3E50; rx: 4; }
        .angle-text { 
            font: 900 16px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle;
            text-transform: uppercase;
            letter-spacing: 1.2px;
        }
        
        /* Planets - VERY LARGE black glyphs with NO background */
        .planet-glyph { 
            font: 400 44px serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #1A1A1A;
            filter: url(#glyph-glow);
        }
        .planet-degree { 
            font: 600 13px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #2C3E50;
            font-weight: 600;
        }
        
        /* Aspects - thicker lines */
        .aspect { fill: none; stroke-linecap: round; }
        """

        def line_at(lon: float, r1: float, r2: float, cls: str) -> str:
            x1,y1 = self._pol_oriented(lon, r1, cx, cy, asc)
            x2,y2 = self._pol_oriented(lon, r2, cx, cy, asc)
            return f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'

        def text_at(lon: float, r: float, text: str, cls: str, rotate: bool = False) -> str:
            x, y = self._pol_oriented(lon, r, cx, cy, asc)
            if rotate:
                # Calculate rotation angle to align text radially (pointing outward from center)
                angle = asc - lon + 180.0
                # Normalize angle to -180 to 180
                while angle > 180:
                    angle -= 360
                while angle < -180:
                    angle += 360
                
                # Subtract 90 to align radially (perpendicular to circle)
                angle -= 90
                
                # Flip text if it would be upside down (on the left side of circle)
                # Text should always read left-to-right
                if angle < -90 or angle > 90:
                    angle += 180
                
                return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" transform="rotate({-angle:.1f} {x:.1f} {y:.1f})">{text}</text>'
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

        # Sign labels (full names) with rotation
        r_text = (r_sign_outer + r_sign_inner) / 2
        for s in range(12):
            start = s*30
            sign_name = ZODIAC[s]
            svg.append(text_at(start + 15, r_text, sign_name.upper(), "sign-text", rotate=True))

        # House circles (conditional)
        if show_houses:
            svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_out}"/>')
            svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_in}"/>')

            # House lines and numbers
            for i, house_cusp in enumerate(chart["houses"]):
                svg.append(line_at(house_cusp, r_house_in, r_house_out, "house-line"))
                
                # Calculate center of house (midpoint between this cusp and next)
                next_cusp = chart["houses"][(i + 1) % 12]
                if next_cusp < house_cusp:
                    next_cusp += 360
                house_center = (house_cusp + next_cusp) / 2
                if house_center >= 360:
                    house_center -= 360
                
                # House number at center
                x, y = self._pol_oriented(house_center, r_house_num, cx, cy, asc)
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
                        f'style="font-weight:700; font-size:14px; fill:#445; opacity:0.9;">{label}</text>'
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
            # marker + compact label hugging the band (larger for mobile)
            x, y = self._pol_oriented(lon, r_sign_inner - 12, cx, cy, asc)
            svg.append(f'<circle class="angle-marker-outer" cx="{x:.1f}" cy="{y:.1f}" r="7" filter="url(#angle-glow)"/>')
            svg.append(f'<circle class="angle-marker-inner" cx="{x:.1f}" cy="{y:.1f}" r="3.5"/>')
            text_x, text_y = self._pol_oriented(lon, r_sign_inner - 28, cx, cy, asc)
            svg.append(f'<rect class="angle-text-bg" x="{text_x-20:.1f}" y="{text_y-9:.1f}" width="40" height="18"/>')
            svg.append(f'<text class="angle-text" x="{text_x:.1f}" y="{text_y:.1f}">{abbr}</text>')

        # Calculate aspects if not provided
        if show_aspects:
            if not chart.get("aspects"):
                planet_lons = {k: v["lon"] for k, v in chart["planets"].items() if k != "PartOfFortune"}
                chart["aspects"] = find_aspects(planet_lons)

        # Planets with improved anti-collision
        placed: List[Tuple[float,float]] = []
        planet_elements = []
        r_planet_center = r_inner_circle + (r_house_in - r_inner_circle) * 0.3
        
        for name, p in sorted(chart["planets"].items(), key=lambda kv: kv[1]["lon"]):
            if name == "PartOfFortune":
                continue
                
            lon = p["lon"]
            r_use = r_planet_center
            
            # Improved anti-collision - check for nearby planets and adjust radius
            collision_detected = False
            for (plon, pr) in placed[-10:]:
                angle_diff = min(abs(lon-plon), 360-abs(lon-plon))
                if angle_diff <= 12:
                    collision_detected = True
                    if len(placed) % 2 == 0:
                        r_use -= 30
                    else:
                        r_use += 30
                    break
            
            x, y = self._pol_oriented(lon, r_use, cx, cy, asc)
            
            planet_group = [f'<g transform="translate({x:.1f},{y:.1f})">']
            font_size = "62" if name == "Sun" else "44"
            planet_group.append(f'<text class="planet-glyph" style="font-size:{font_size}px;" x="0" y="2">{P_GLYPH.get(name, name[0])}</text>')
            planet_group.append('</g>')
            planet_elements.extend(planet_group)
            
            if show_planet_degrees:
                d = int(p["deg"])
                m = int(round((p["deg"]-d)*60))
                retro = "℞" if p.get("retro") else ""
                degree_label = f'{d}°{m:02d}′{retro}'
                label_r = r_use + 25 if collision_detected else r_use + 20
                label_x, label_y = self._pol_oriented(lon, label_r, cx, cy, asc)
                planet_elements.append(f'<text class="planet-degree" x="{label_x:.1f}" y="{label_y:.1f}">{degree_label}</text>')
            
            placed.append((lon, r_use))
        
        svg.extend(planet_elements)

        # Aspects
        if show_aspects and chart.get("aspects"):
            aspect_group = ['<g opacity="0.8">']
            pts = {k: self._pol_oriented(v["lon"], r_inner_circle * 0.9, cx, cy, asc) for k,v in chart["planets"].items() if k!="PartOfFortune"}
            
            for a in chart["aspects"]:
                p1, p2 = a["p1"], a["p2"]
                if p1 not in pts or p2 not in pts: 
                    continue
                
                col, dash, opacity = self._aspect_style(a["aspect"])
                x1, y1 = pts[p1]
                x2, y2 = pts[p2]
                
                dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
                stroke_width = "1.5" if a["aspect"] in ["conjunction", "opposition", "square", "trine"] else "1"
                
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
                    show_aspects: bool = True, show_planet_degrees: bool = True, 
                    show_houses: bool = True) -> str:
        """Generate synastry biwheel SVG with proper planet rings."""
        asc = inner["angles"]["ASC"]
        cx = cy = size // 2

        # Adjusted radii for proper biwheel layout - houses between zodiac and planets
        r_outer = size * 0.48
        r_sign_outer  = size * 0.44
        r_sign_inner  = size * 0.37
        
        # Houses (between zodiac and planets)
        r_house_out = size * 0.35
        r_house_in = size * 0.30
        r_house_num = size * 0.325
        
        # Outer planets ring
        r_outer_planets_outer = size * 0.285
        r_outer_planets_inner = size * 0.25
        r_outer_planets_mid = size * 0.2675  # Center of outer planets ring
        
        # Inner planets ring
        r_inner_planets_outer = size * 0.24
        r_inner_planets_inner = size * 0.21
        r_inner_planets_mid = size * 0.225  # Center of inner planets ring
        
        r_inner_circle = size * 0.16

        css = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=Cinzel:wght@400;500;600;700;800;900&amp;display=swap');
        
        .chart-bg { fill: #FAFBFC; }
        .outer-ring { fill: none; stroke: #E1E4E8; stroke-width: 3; }
        .center-circle { fill: #F6F8FA; stroke: #E1E4E8; stroke-width: 2; }
        
        /* Zodiac band - larger for mobile */
        .zodiac-band   { fill: #000000; }
        .zodiac-cutout { fill: #FFFFFF; }
        .zodiac-divider { stroke: #FFFFFF; stroke-width: 2; }
        .sign-text { 
            font: 800 18px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle; 
            letter-spacing: 1px; 
            text-transform: uppercase;
            text-shadow: 0 2px 4px rgba(0,0,0,0.6);
        }
        
        /* Planet rings - thicker lines */
        .planet-ring { fill: #F8F9FA; stroke: #D0D7DE; stroke-width: 2; }
        .planet-ring-divider { stroke: #E1E4E8; stroke-width: 1; opacity: 0.5; }
        
        /* Houses - more visible */
        .house-circle { fill: none; stroke: #D0D7DE; stroke-width: 2.5; }
        .house-line { stroke: #D0D7DE; stroke-width: 2; opacity: 0.7; }
        .house-num { 
            font: 700 20px 'Cinzel', serif; 
            fill: #1A1A1A; 
            text-anchor: middle; 
            dominant-baseline: middle;
            letter-spacing: 0.5px;
        }
        
        /* Angles - larger */
        .angle-tick { stroke: #4A5568; stroke-width: 1.5; stroke-linecap: round; }
        .angle-marker { fill: #FFD700; stroke: #2C3E50; stroke-width: 2; }
        .angle-text-bg { fill: #2C3E50; rx: 4; }
        .angle-text { 
            font: 900 14px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            fill: #FFFFFF; 
            text-anchor: middle; 
            dominant-baseline: middle;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Planets - VERY LARGE black glyphs with NO background */
        .planet-inner { }
        .planet-outer { opacity: 0.9; }
        .planet-glyph { 
            font: 400 42px serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #1A1A1A;
            filter: url(#glyph-glow);
        }
        .planet-degree { 
            font: 600 12px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            text-anchor: middle; 
            dominant-baseline: middle;
            fill: #2C3E50;
        }
        
        /* Aspects - thicker */
        .aspect { fill: none; stroke-linecap: round; }
        
        /* Labels - more readable */
        .chart-label {
            font: 800 15px 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            fill: #2C3E50;
            text-anchor: middle;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        """

        def line_at(lon, r1, r2, cls):
            x1,y1 = self._pol_oriented(lon, r1, cx, cy, asc)
            x2,y2 = self._pol_oriented(lon, r2, cx, cy, asc)
            return f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'

        def text_at(lon, r, t, cls, rotate=False):
            x, y = self._pol_oriented(lon, r, cx, cy, asc)
            if rotate:
                # Calculate rotation angle to align text radially (pointing outward from center)
                angle = asc - lon + 180.0
                # Normalize angle
                while angle > 180:
                    angle -= 360
                while angle < -180:
                    angle += 360
                
                # Subtract 90 to align radially (perpendicular to circle)
                angle -= 90
                
                # Flip text if it would be upside down (on the left side of circle)
                # Text should always read left-to-right
                if angle < -90 or angle > 90:
                    angle += 180
                
                return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" transform="rotate({-angle:.1f} {x:.1f} {y:.1f})">{t}</text>'
            return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}">{t}</text>'

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
            f"<style>{css}</style>",
            self._create_gradient_defs(cx, cy, r_sign_inner, r_sign_outer)
        ]

        svg.append(f'<rect class="chart-bg" width="{size}" height="{size}"/>')
        svg.append(f'<circle class="outer-ring" cx="{cx}" cy="{cy}" r="{r_outer}"/>')

        # Zodiac band
        svg.append(f'<circle class="zodiac-band" cx="{cx}" cy="{cy}" r="{r_sign_outer}"/>')
        svg.append(f'<circle class="zodiac-cutout" cx="{cx}" cy="{cy}" r="{r_sign_inner}"/>')
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_sign_inner}" fill="none" stroke="#FFFFFF" stroke-width="2"/>')

        # Zodiac dividers
        for s in range(12):
            start = s * 30
            x1, y1 = self._pol_oriented(start, r_sign_inner, cx, cy, asc)
            x2, y2 = self._pol_oriented(start, r_sign_outer, cx, cy, asc)
            svg.append(f'<line class="zodiac-divider" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')

        # Sign labels with rotation
        r_text = (r_sign_outer + r_sign_inner) / 2
        for s in range(12):
            start = s*30
            sign_name = ZODIAC[s]
            svg.append(text_at(start + 15, r_text, sign_name.upper(), "sign-text", rotate=True))

        # Outer planets ring (with light background)
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer_planets_outer}" fill="#F8F9FA" stroke="#D0D7DE" stroke-width="1"/>')
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer_planets_inner}" fill="#FFFFFF" stroke="#D0D7DE" stroke-width="1"/>')
        
        # Inner planets ring (with light background)
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner_planets_outer}" fill="#F0F1F3" stroke="#D0D7DE" stroke-width="1"/>')
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner_planets_inner}" fill="#FFFFFF" stroke="#D0D7DE" stroke-width="1"/>')

        # Houses (conditional)
        if show_houses:
            svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_out}"/>')
            svg.append(f'<circle class="house-circle" cx="{cx}" cy="{cy}" r="{r_house_in}"/>')

            # House lines and numbers
            for i, house_cusp in enumerate(inner["houses"]):
                svg.append(line_at(house_cusp, r_house_in, r_house_out, "house-line"))
                
                # Calculate center of house (midpoint between this cusp and next)
                next_cusp = inner["houses"][(i + 1) % 12]
                if next_cusp < house_cusp:
                    next_cusp += 360
                house_center = (house_cusp + next_cusp) / 2
                if house_center >= 360:
                    house_center -= 360
                
                # House number at center
                x, y = self._pol_oriented(house_center, r_house_num, cx, cy, asc)
                svg.append(f'<text class="house-num" x="{x:.1f}" y="{y:.1f}">{i+1}</text>')

        # Center circle
        svg.append(f'<circle class="center-circle" cx="{cx}" cy="{cy}" r="{r_inner_circle}"/>')

        # Angles - extend through planet rings
        angle_data = [
            (inner["angles"]["ASC"], "ASC"),
            (inner["angles"]["DS"],  "DS"),
            (inner["angles"]["MC"],  "MC"),
            (inner["angles"]["IC"],  "IC")
        ]
        for lon, abbr in angle_data:
            # Draw tick from houses to just before zodiac
            svg.append(line_at(lon, r_house_out, r_sign_inner - 2, "angle-tick"))
            
            # Add angle marker and label (larger for mobile)
            x, y = self._pol_oriented(lon, r_sign_inner - 12, cx, cy, asc)
            svg.append(f'<circle class="angle-marker" cx="{x:.1f}" cy="{y:.1f}" r="6"/>')
            
            text_x, text_y = self._pol_oriented(lon, r_sign_inner - 26, cx, cy, asc)
            svg.append(f'<rect class="angle-text-bg" x="{text_x-18:.1f}" y="{text_y-8:.1f}" width="36" height="16"/>')
            svg.append(f'<text class="angle-text" x="{text_x:.1f}" y="{text_y:.1f}">{abbr}</text>')

        # Chart labels removed

        # Inner planets (in the inner planet ring) with improved anti-collision
        placed_inner = []
        for name, p in sorted(inner["planets"].items(), key=lambda kv: kv[1]["lon"]):
            if name == "PartOfFortune":
                continue
                
            lon = p["lon"]
            r_use = r_inner_planets_mid
            
            # Improved anti-collision for inner planets
            shift_count = 0
            for (plon, pr) in placed_inner:
                angle_diff = min(abs(lon-plon), 360-abs(lon-plon))
                if angle_diff <= 8:
                    shift_count += 1
                    if shift_count % 4 == 1:
                        r_use -= 40
                    elif shift_count % 4 == 2:
                        r_use += 40
                    elif shift_count % 4 == 3:
                        r_use -= 20
                    else:
                        r_use += 20
            
            x, y = self._pol_oriented(lon, r_use, cx, cy, asc)
            
            # Just the glyph, NO background circle
            svg.append(f'<text class="planet-glyph" x="{x:.1f}" y="{y+2:.1f}">{P_GLYPH.get(name, name[0])}</text>')
            
            placed_inner.append((lon, r_use))
            
            # Degree label (conditional)
            if show_planet_degrees:
                d = int(p["deg"])
                m = int(round((p["deg"]-d)*60))
                retro = "℞" if p.get("retro") else ""
                degree_label = f'{d}°{m:02d}′{retro}'
                
                # Adjust label position based on shift
                if shift_count > 0:
                    deg_x, deg_y = self._pol_oriented(lon, r_use - 20, cx, cy, asc)
                else:
                    deg_x, deg_y = self._pol_oriented(lon, r_use - 15, cx, cy, asc)
                svg.append(f'<text class="planet-degree" x="{deg_x:.1f}" y="{deg_y:.1f}">{degree_label}</text>')

        # Outer planets (in the outer planet ring) with improved anti-collision
        placed_outer = []
        for name, p in sorted(outer["planets"].items(), key=lambda kv: kv[1]["lon"]):
            if name == "PartOfFortune":
                continue
                
            lon = p["lon"]
            r_use = r_outer_planets_mid
            
            # Improved anti-collision for outer planets
            shift_count = 0
            for (plon, pr) in placed_outer:
                angle_diff = min(abs(lon-plon), 360-abs(lon-plon))
                if angle_diff <= 8:
                    shift_count += 1
                    if shift_count % 4 == 1:
                        r_use -= 40
                    elif shift_count % 4 == 2:
                        r_use += 40
                    elif shift_count % 4 == 3:
                        r_use -= 20
                    else:
                        r_use += 20
            
            x, y = self._pol_oriented(lon, r_use, cx, cy, asc)
            
            # Just the glyph, NO background circle
            svg.append(f'<text class="planet-glyph" x="{x:.1f}" y="{y+2:.1f}">{P_GLYPH.get(name, name[0])}</text>')
            
            placed_outer.append((lon, r_use))
            
            # Degree label (conditional)
            if show_planet_degrees:
                d = int(p["deg"])
                m = int(round((p["deg"]-d)*60))
                retro = "℞" if p.get("retro") else ""
                degree_label = f'{d}°{m:02d}′{retro}'
                
                # Adjust label position based on shift
                if shift_count > 0:
                    deg_x, deg_y = self._pol_oriented(lon, r_use + 20, cx, cy, asc)
                else:
                    deg_x, deg_y = self._pol_oriented(lon, r_use + 15, cx, cy, asc)
                svg.append(f'<text class="planet-degree" x="{deg_x:.1f}" y="{deg_y:.1f}">{degree_label}</text>')

        # Synastry aspects - draw inside inner circle
        if show_aspects:
            aspects = synastry_aspects(inner, outer)
            aspect_group = ['<g opacity="0.6">']
            
            # Map planet positions to inner circle for aspect lines
            pts_inner = {k: self._pol_oriented(v["lon"], r_inner_circle * 0.9, cx, cy, asc) for k,v in inner["planets"].items() if k!="PartOfFortune"}
            pts_outer = {k: self._pol_oriented(v["lon"], r_inner_circle * 0.9, cx, cy, asc) for k,v in outer["planets"].items() if k!="PartOfFortune"}
            
            for a in aspects:
                if a["p1"] in pts_inner and a["p2"] in pts_outer:
                    x1, y1 = pts_inner[a["p1"]]
                    x2, y2 = pts_outer[a["p2"]]
                    col, dash, opacity = self._aspect_style(a["aspect"])
                    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
                    stroke_width = "2" if a["aspect"] in ["conjunction", "opposition", "square", "trine"] else "1.5"
                    
                    aspect_group.append(
                        f'<line class="aspect" stroke="{col}" stroke-width="{stroke_width}" '
                        f'opacity="{opacity}"{dash_attr} '
                        f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
                    )
            
            aspect_group.append('</g>')
            svg.extend(aspect_group)

        svg.append("</svg>")
        return "\n".join(svg)