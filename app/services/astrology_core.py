"""Core astrological calculations extracted from CLI."""

from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Swiss Ephemeris (primary engine)
try:
    import swisseph as swe
    HAVE_SWE = True
except Exception:
    swe = None
    HAVE_SWE = False

# PyEphem (used only for robust Sun altitude check for day/night sect)
import ephem
from dateutil import tz

# Constants
SIGN_NAMES = [
    "ARIES","TAURUS","GEMINI","CANCER","LEO","VIRGO",
    "LIBRA","SCORPIO","SAGITTARIUS","CAPRICORN","AQUARIUS","PISCES"
]
ZODIAC = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

SIGN_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

PLANETS_PYEPHEM = {
    "Sun": ephem.Sun, "Moon": ephem.Moon, "Mercury": ephem.Mercury,
    "Venus": ephem.Venus, "Mars": ephem.Mars, "Jupiter": ephem.Jupiter,
    "Saturn": ephem.Saturn, "Uranus": ephem.Uranus, "Neptune": ephem.Neptune,
    "Pluto": ephem.Pluto,
}

P_GLYPH = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "TrueNode":"☊","Chiron":"⚷","PartOfFortune":"⊕"
}

PLANET_COLORS = {
    "Sun": "#FF6B35", "Moon": "#C0C5CE", "Mercury": "#4ECDC4", "Venus": "#FF6B9D",
    "Mars": "#C44569", "Jupiter": "#6C5CE7", "Saturn": "#4A4E69", "Uranus": "#00BFA5",
    "Neptune": "#3F51B5", "Pluto": "#2C2E3E", "TrueNode":"#546E7A", "Chiron":"#8D6E63",
    "PartOfFortune": "#00E676"
}

SIGN_COLORS = {
    0: "#FF5252", 1: "#8D6E63", 2: "#81D4FA", 3: "#42A5F5",
    4: "#FF6E40", 5: "#6D4C41", 6: "#64B5F6", 7: "#1E88E5",
    8: "#FF7043", 9: "#5D4037", 10: "#4FC3F7", 11: "#1976D2"
}

ASPECTS_DEG = {
    0:   ("conjunction",     8,  "☌"),
    30:  ("semisextile",     2,  "⚺"),
    36:  ("decile",          1.5,"⯑"),
    45:  ("semisquare",      2,  "∠"),
    60:  ("sextile",         4,  "⚹"),
    72:  ("quintile",        2,  "⬠"),
    90:  ("square",          6,  "□"),
    108: ("tredecile",       1.5,"⯑"),
    120: ("trine",           6,  "△"),
    135: ("sesquiquadrate",  2,  "⚼"),
    144: ("biquintile",      1.5,"±"),
    150: ("quincunx",        3,  "⚻"),
    180: ("opposition",      8,  "☍"),
}

MOON_PHASE_NAMES = [
    (0, "New Moon 🌑"), (45, "Waxing Crescent 🌒"), (90, "First Quarter 🌓"),
    (135, "Waxing Gibbous 🌔"), (180, "Full Moon 🌕"), (225, "Waning Gibbous 🌖"),
    (270, "Last Quarter 🌗"), (315, "Waning Crescent 🌘"), (360, "New Moon 🌑")
]

# Global settings
HAVE_SWE_FILES = False
SWISS_FLAGS = (swe.FLG_MOSEPH | swe.FLG_SPEED) if HAVE_SWE else 0


@dataclass
class GeoLocation:
    lat: float
    lon: float   # EAST positive
    elevation_m: float = 0.0


def norm360(x: float) -> float: 
    return x % 360.0


def angdist(a: float, b: float) -> float:
    d = abs(norm360(a - b))
    return d if d <= 180 else 360 - d


def deg_to_signpos(lon: float):
    lon = norm360(lon); idx = int(lon // 30)
    return ZODIAC[idx], lon - idx*30, idx


def fmt_deg(d: float) -> str:
    d = norm360(d); deg = int(d); mins = int(round((d - deg)*60))
    if mins == 60: deg, mins = deg+1, 0
    return f"{deg}°{mins:02d}′"


def to_jd_ut(dt_utc: datetime) -> float:
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600.0,
                      swe.GREG_CAL)


def swiss_calc_lon(jd_ut: float, body: int) -> float:
    if not HAVE_SWE:
        raise RuntimeError("Swiss Ephemeris not available.")
    flags_to_try = [SWISS_FLAGS]
    if SWISS_FLAGS & swe.FLG_SWIEPH:
        flags_to_try.append(swe.FLG_MOSEPH | swe.FLG_SPEED)

    last_err = None
    for flags in flags_to_try:
        try:
            res = swe.calc_ut(jd_ut, body, flags)
            if isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], (tuple, list)):
                vals, _ = res
                lon = float(vals[0])
            else:
                lon = float(res[0])
            return lon % 360.0
        except swe.Error as e:
            last_err = e
            continue
    raise RuntimeError(f"Swiss Ephemeris calc failed for body: {last_err}")


def swiss_planet_longitudes(dt_utc: datetime) -> Dict[str, float]:
    jd = to_jd_ut(dt_utc)
    mapping = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO, "TrueNode": swe.TRUE_NODE
    }
    if HAVE_SWE_FILES:
        mapping["Chiron"] = swe.CHIRON

    out: Dict[str, float] = {}
    for name, code in mapping.items():
        try:
            out[name] = swiss_calc_lon(jd, code)
        except swe.Error:
            continue
    return out


def swiss_angles_and_houses(dt_utc: datetime, loc: GeoLocation, system_code: bytes | str) -> Tuple[float, float, List[float]]:
    jd = to_jd_ut(dt_utc)

    if isinstance(system_code, (bytes, bytearray)):
        hsys_b = bytes(system_code[:1])
        try:
            hsys_s = hsys_b.decode('ascii', errors='ignore') or 'P'
        except Exception:
            hsys_s = 'P'
    else:
        hsys_s = str(system_code)[0] if system_code else 'P'
        hsys_b = hsys_s.encode('ascii', errors='ignore') or b'P'

    def _try_parse(callable_):
        res = callable_()
        cusps, ascmc = res

        if isinstance(cusps, tuple) and len(cusps) == 2 and isinstance(cusps[0], (tuple, list)):
            cusps = cusps[0]
        if isinstance(ascmc, tuple) and len(ascmc) == 2 and isinstance(ascmc[0], (tuple, list)):
            ascmc = ascmc[0]

        asc = float(ascmc[0]) % 360.0
        mc  = float(ascmc[1]) % 360.0

        cl = list(cusps)
        n = len(cl)
        if n >= 13:
            houses = [float(cl[i]) % 360.0 for i in range(1, 13)]
        elif n == 12:
            houses = [float(cl[i]) % 360.0 for i in range(12)]
        else:
            raise ValueError(f"Unexpected cusps length {n}")

        return asc, mc, houses

    attempts = [
        lambda: swe.houses_ex(jd, 0,           loc.lat, loc.lon, hsys_b),
        lambda: swe.houses_ex(jd, 0,           loc.lat, loc.lon, hsys_s),
        lambda: swe.houses_ex(jd, SWISS_FLAGS, loc.lat, loc.lon, hsys_b),
        lambda: swe.houses_ex(jd, SWISS_FLAGS, loc.lat, loc.lon, hsys_s),
        lambda: swe.houses_ex(jd, 0,           loc.lat, hsys_b,  loc.lon),
        lambda: swe.houses_ex(jd, 0,           loc.lat, hsys_s,  loc.lon),
        lambda: swe.houses_ex(jd, SWISS_FLAGS, loc.lat, hsys_b,  loc.lon),
        lambda: swe.houses_ex(jd, SWISS_FLAGS, loc.lat, hsys_s,  loc.lon),
        lambda: swe.houses(jd,                 loc.lat, loc.lon, hsys_s),
        lambda: swe.houses(jd,                 loc.lat, loc.lon, hsys_b),
    ]

    last_err = None
    for call in attempts:
        try:
            return _try_parse(call)
        except (TypeError, AttributeError, ValueError, swe.Error) as e:
            last_err = e
            continue

    raise RuntimeError(f"Swiss houses computation failed: {last_err}")


def to_ephem_date(dt_utc: datetime) -> ephem.Date:
    if dt_utc.tzinfo is None:
        raise ValueError("UTC datetime required")
    return ephem.Date(dt_utc)


def body_ecliptic_lon_pyephem(body: ephem.Body, dt_utc: datetime) -> float:
    body.compute(dt_utc)
    return float(math.degrees(ephem.Ecliptic(body).lon)) % 360.0


def planet_longitudes_pyephem(dt_utc: datetime) -> Dict[str, float]:
    return {name: body_ecliptic_lon_pyephem(PL(), dt_utc) for name, PL in PLANETS_PYEPHEM.items()}


def make_observer(dt_utc: datetime, loc: GeoLocation) -> ephem.Observer:
    obs = ephem.Observer()
    obs.lat, obs.lon = str(loc.lat), str(loc.lon)
    obs.elevation = loc.elevation_m
    obs.date = to_ephem_date(dt_utc)
    return obs


def is_day_chart(dt_utc: datetime, loc: GeoLocation) -> bool:
    obs = make_observer(dt_utc, loc)
    sun = ephem.Sun(); sun.compute(obs)
    return float(sun.alt) > 0.0


def whole_sign_houses(asc_lon: float) -> List[float]:
    start = int(asc_lon // 30) * 30.0
    return [norm360(start + i*30.0) for i in range(12)]


def equal_houses(asc_lon: float) -> List[float]:
    return [norm360(asc_lon + i*30.0) for i in range(12)]


def placidus_houses_placeholder(asc_lon: float, mc_lon: float, loc: GeoLocation, dt_utc: datetime) -> List[float]:
    return equal_houses(asc_lon)

def house_index_for_longitude(houses: List[float], lon: float) -> int:
    """
    Return 1..12. Rule: a planet exactly on a cusp belongs to the *following* house
    (except when it's exactly on the 12→1 wrap, which resolves to house 1).
    """
    lon = norm360(lon)
    for i in range(12):
        a = norm360(houses[i])
        b = norm360(houses[(i+1) % 12])

        if a == lon:
            return ((i + 1) % 12) + 1

        if a <= b:
            if a < lon < b:  # open interval on left cusp
                return i + 1
        else:
            # wraps 360
            if lon > a or lon < b:
                return i + 1
    return 12


def arc_len_forward(a: float, b: float) -> float:
    """Forward arc length from a to b along ecliptic [0..360)."""
    return (b - a) % 360.0

def arc_segments_by_sign(start: float, end: float) -> List[Tuple[int, float]]:
    """
    Split the forward arc [start → end) into chunks that lie inside each zodiac sign.
    Returns a list of (sign_index, span_deg).
    """
    start = norm360(start); end = norm360(end)
    total = arc_len_forward(start, end)
    if total == 0:  # full circle (rare for houses), treat as 360
        total = 360.0

    cur = start
    left = total
    out: List[Tuple[int, float]] = []

    while left > 1e-9:
        sign_idx = int(cur // 30)
        next_boundary = ((sign_idx + 1) * 30) % 360.0

        step_to_boundary = arc_len_forward(cur, next_boundary)
        # If exactly on boundary, allow a full 30° step
        if step_to_boundary == 0:
            step_to_boundary = 30.0

        take = min(step_to_boundary, left)
        out.append((sign_idx, take))
        cur = norm360(cur + take)
        left -= take

    return out

def house_sign_breakdown(houses: List[float]) -> List[List[Dict]]:
    """
    For each house, return a list of segments with the sign and percent:
    [
      [ {"sign":"Aries","deg":x,"percent":p}, {"sign":"Taurus","deg":y,"percent":q}, ... ],  # House 1
      ...
    ]
    """
    breakdown: List[List[Dict]] = []
    for i in range(12):
        start = houses[i]
        end   = houses[(i + 1) % 12]
        segs = arc_segments_by_sign(start, end)
        total = sum(d for _, d in segs) or 1.0
        parts = []
        for idx, span in segs:
            parts.append({
                "sign": ZODIAC[idx],
                "deg": round(span, 4),
                "percent": round(100.0 * span / total, 2),
            })
        breakdown.append(parts)
    return breakdown

def cusp_signs(houses: List[float]) -> List[str]:
    """Sign that each house cusp falls in."""
    return [ZODIAC[int(norm360(h)//30)] for h in houses]

def intercepted_signs(houses: List[float]) -> List[str]:
    """
    A sign is intercepted if no house cusp falls inside it.
    (Note: classic definitions vary by quadrant system; this is the standard cusp-based test.)
    """
    cusp_idxs = {int(norm360(h)//30) for h in houses}
    return [ZODIAC[i] for i in range(12) if i not in cusp_idxs]

def part_of_fortune(asc_lon: float, sun_lon: float, moon_lon: float, day_chart: bool) -> float:
    return norm360(asc_lon + (moon_lon - sun_lon if day_chart else sun_lon - moon_lon))


def moon_phase_info_from_lons(lon_sun: float, lon_moon: float):
    phase = norm360(lon_moon - lon_sun)
    name = None
    for bound, nm in MOON_PHASE_NAMES:
        if phase <= bound:
            name = nm; break
    return name or "New Moon 🌑", phase


def find_aspects(lons: Dict[str, float]) -> List[Dict]:
    hits = []
    names = list(lons.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = names[i], names[j]
            d = angdist(lons[a], lons[b])
            for deg, (label, orb, glyph) in ASPECTS_DEG.items():
                delta = min(abs(d - deg), abs(d - (360 - deg)))
                if delta <= orb:
                    hits.append({"p1": a, "p2": b, "aspect": label, "glyph": glyph, "orb": orb, "off": round(d - deg, 2)})
    order = {"conjunction":0,"opposition":1,"square":2,"trine":3,"sextile":4}
    hits.sort(key=lambda h: (order.get(h["aspect"], 5), abs(h["off"])))
    return hits


def planet_longitudes(dt_utc: datetime) -> Dict[str, float]:
    if HAVE_SWE:
        return swiss_planet_longitudes(dt_utc)
    return planet_longitudes_pyephem(dt_utc)


def _retrograde_swiss(dt_utc: datetime, name: str) -> bool:
    body_map = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO, "TrueNode": swe.TRUE_NODE, "Chiron": swe.CHIRON
    }
    if name not in body_map:
        return False
    jd_now  = to_jd_ut(dt_utc)
    jd_prev = jd_now - (10/1440.0)
    lon_now  = swiss_calc_lon(jd_now,  body_map[name])
    lon_prev = swiss_calc_lon(jd_prev, body_map[name])
    delta = (lon_now - lon_prev + 540) % 360 - 180
    return delta < 0


def _retrograde_pyephem(dt_utc: datetime, name: str) -> bool:
    if name not in PLANETS_PYEPHEM: return False
    now = planet_longitudes_pyephem(dt_utc)[name]
    then = planet_longitudes_pyephem(dt_utc - timedelta(minutes=10))[name]
    delta = (now - then + 540) % 360 - 180
    return delta < 0


def _local_sidereal_time(dt_utc: datetime, loc: GeoLocation) -> float:
    obs = make_observer(dt_utc, loc)
    return norm360(math.degrees(obs.sidereal_time()))


def _mc_from_lst_pyephem(dt_utc: datetime, loc: GeoLocation) -> float:
    OBLIQUITY_DEG = 23.4392911
    theta = math.radians(_local_sidereal_time(dt_utc, loc))
    eps = math.radians(OBLIQUITY_DEG)
    lam = math.degrees(math.atan2(math.sin(theta), math.cos(theta)*math.cos(eps)))
    return norm360(lam)


def _ascendant_precise_pyephem(dt_utc: datetime, loc: GeoLocation) -> float:
    obs = make_observer(dt_utc, loc)

    def alt_abs_for_eclip_lon(lon_deg: float) -> Tuple[float, float]:
        e = ephem.Ecliptic(math.radians(norm360(lon_deg)), 0.0)
        eq = ephem.Equatorial(e, epoch=to_ephem_date(dt_utc))
        star = ephem.FixedBody(); star._ra, star._dec = eq.ra, eq.dec
        star.compute(obs)
        return abs(float(star.alt)), float(star.az)

    best_lon, best_abs = 0.0, 1e9
    for lon in [i*5.0 for i in range(72)]:
        aabs, az = alt_abs_for_eclip_lon(lon)
        if (math.pi/4) < az < (3*math.pi/4) and aabs < best_abs:
            best_lon, best_abs = lon, aabs
    lo = best_lon - 5; hi = best_lon + 5
    for lon in [lo + i*0.1 for i in range(int((hi-lo)/0.1)+1)]:
        aabs, az = alt_abs_for_eclip_lon(lon)
        if (math.pi/4) < az < (3*math.pi/4) and aabs < best_abs:
            best_lon, best_abs = lon, aabs
    lo = best_lon - 0.5; hi = best_lon + 0.5
    for lon in [lo + i*0.01 for i in range(int((hi-lo)/0.01)+1)]:
        aabs, az = alt_abs_for_eclip_lon(lon)
        if (math.pi/4) < az < (3*math.pi/4) and aabs < best_abs:
            best_lon, best_abs = lon, aabs
    return norm360(best_lon)


def synastry_aspects(chart_a: Dict, chart_b: Dict) -> List[Dict]:
    lons_a = {k:v["lon"] for k,v in chart_a["planets"].items()}
    lons_b = {k:v["lon"] for k,v in chart_b["planets"].items()}
    hits=[]
    for a, la in lons_a.items():
        for b, lb in lons_b.items():
            d = angdist(la, lb)
            for deg,(label,orb,glyph) in ASPECTS_DEG.items():
                delta = min(abs(d-deg), abs(d-(360-deg)))
                if delta <= orb:
                    hits.append({"p1":a,"p2":b,"aspect":label,"glyph":glyph,"orb":orb,"off":round(d-deg,2)})
    order={"conjunction":0,"opposition":1,"square":2,"trine":3,"sextile":4}
    hits.sort(key=lambda h:(order.get(h["aspect"],5), abs(h["off"])))
    return hits


def composite_midpoints(chart_a: Dict, chart_b: Dict) -> Dict[str,float]:
    mids={}
    for k in set(chart_a["planets"]).intersection(chart_b["planets"]):
        a = chart_a["planets"][k]["lon"]
        b = chart_b["planets"][k]["lon"]
        mids[k] = norm360((a + ((b - a + 540) % 360) - 180)/2 + a)
    return mids


def forecast_transits(natal: Dict, start_local: datetime, tz_name: str, days: int=14, step_hours: int=24) -> List[Dict]:
    if start_local.tzinfo is None: start_local = start_local.replace(tzinfo=tz.gettz(tz_name))
    natal_lons = {k:v["lon"] for k,v in natal["planets"].items()}
    out=[]
    for t in range(0, days*24+1, step_hours):
        dt_utc = (start_local + timedelta(hours=t)).astimezone(tz.UTC)
        trans = planet_longitudes(dt_utc)
        for n_name,n_lon in natal_lons.items():
            for t_name,t_lon in trans.items():
                d = angdist(t_lon, n_lon)
                for deg,(label,orb,glyph) in ASPECTS_DEG.items():
                    delta = min(abs(d-deg), abs(d-(360-deg)))
                    tight_orb = 0.8 if t_name != "Moon" else 1.6
                    if delta <= tight_orb:
                        out.append({"when_utc":dt_utc.isoformat(),"transit":t_name,"natal":n_name,"aspect":label,"orb_diff":round(delta,2)})
    out.sort(key=lambda r:(r["when_utc"], r["orb_diff"]))
    return out
