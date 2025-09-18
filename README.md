Starluck Epoch API

| **Whole Sign Chart** | **Placidus Chart** | **Synastry Biwheel** |
|---|---|---|
| <img src="docs/media/whole.png" alt="Whole Sign Chart" width="280" /> | <img src="docs/media/placidus.png" alt="Placidus Chart" width="280" /> | <img src="docs/media/biwheel.png" alt="Synastry Biwheel" width="280" /> |
FastAPI service for astrological charts & visuals — created by the Starluck team.
It computes natal data, renders SVG chart wheels (single & biwheel), runs synastry/composite math, and generates short reports & transit forecasts.

Natal chart (planets, houses, angles, aspects)

SVG chart wheels (single + biwheel)

Synastry & Composite calculations

Transit forecasts

Lightweight Markdown reports

Quick Setup

Requirements: Python 3.11+

git clone <your-repo>
cd starluck-epoch

python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt


Create a .env (API key is optional):

STARLUCK_DEBUG=false
STARLUCK_API_KEY=             # optional
STARLUCK_ALLOWED_HOSTS=127.0.0.1,localhost
STARLUCK_CORS_ORIGINS=http://localhost:8000
STARLUCK_SWE_PATH=            # optional; leave empty (no external SWE files required)


Run:

uvicorn app.main:app --host 0.0.0.0 --port 8000
# or
python -m app.main


Health check: GET /api/v1/health

Endpoints (brief)

All endpoints live under /api/v1. If you set an API key, send Authorization: Bearer <key>.

1) Natal — POST /natal

Compute a birth chart.

Request

{
  "datetime_local": "1990-01-01 12:00",
  "timezone": "America/New_York",
  "location": {"lat": 40.7128, "lon": -74.0060, "elevation_m": 10},
  "house_system": "PLACIDUS"  // or "WHOLE"
}


Response (trimmed)

{
  "angles": {"ASC": 23.4, "MC": 15.1, "DS": 203.4, "IC": 195.1},
  "houses": [23.4, 45.1, ...],
  "planets": {"Sun": {"lon": 280.1, "deg": 10.1, "retro": false}, "...": {}},
  "aspects": [{"p1":"Sun","p2":"Moon","aspect":"trine","orb":2.1}]
}

2) SVG Wheel — POST /svg

Turn a natal chart into a single-wheel SVG (purple band).

Request

{ "chart_data": { /* output from /natal */ }, "size": 900, "show_aspects": true }


Response

{ "svg_content": "<svg ...>...</svg>", "size": 900 }

3) Biwheel — POST /biwheel

Synastry double wheel: inner vs. outer chart.

Request

{
  "inner_chart": { /* /natal A */ },
  "outer_chart": { /* /natal B */ },
  "size": 920,
  "label_inner": "A",
  "label_outer": "B",
  "show_aspects": true
}


Response

{ "svg_content": "<svg ...>...</svg>", "size": 920 }

4) Synastry — POST /synastry

Inter-chart aspects only (no SVG).

Request

{ "chart_a": { /* /natal A */ }, "chart_b": { /* /natal B */ } }


Response (trimmed)

{ "interaspects": [{ "p1":"Sun", "p2":"Moon", "aspect":"trine", "orb": 1.9 }] }

5) Composite — POST /composite

Midpoint-composite data.

Request

{ "chart_a": { /* /natal A */ }, "chart_b": { /* /natal B */ } }


Response (trimmed)

{ "midpoints": { "Sun": { "lon": 123.4 }, "...": {} } }

6) Report — POST /report

Short Markdown report for a single chart.

Request

{ "chart_data": { /* /natal */ }, "title": "Birth Chart" }


Response

{ "report_content": "# Birth Chart\n..." }

7) Forecast — POST /forecast

Time-window transit aspects to natal.

Request

{
  "natal_chart": { /* /natal */ },
  "start_date": "2025-09-18",
  "timezone": "America/New_York",
  "days": 7,
  "step_hours": 12
}


Response (trimmed)

{
  "transits": [
    { "when_utc": "2025-09-18T06:40:00Z", "transit": "Sun",
      "natal": "Mercury", "aspect": "trine", "orb_diff": 0.01 }
  ]
}

Notes

Works out of the box without external Swiss Ephemeris files.

If you do provide STARLUCK_SWE_PATH, it will use it when available.

License

APGL license. Free to use; some dependencies are also APGL-licensed.

Contributing

Issues and PRs are welcome.
Open a ticket with a clear description (bug, enhancement, or design tweak) and, if possible, a minimal repro or a screenshot of the chart.

© Starluck Team