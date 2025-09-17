#!/usr/bin/env python3
"""
Starluck Astro API — Full Endpoint Smoke Test
- Saves ALL outputs to repo root: ./debug_outputs/
- Exercises: /health, /natal (WHOLE & PLACIDUS), /svg (both),
             /biwheel, /synastry, /composite, /report, /forecast
- API key is OPTIONAL. If STARLUCK_ENABLE_API_KEY_AUTH=true and STARLUCK_API_KEY is set,
  it will be sent; otherwise no auth header is used.
"""

from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests

# ---------- Optional dotenv load ----------
def _load_dotenv_if_available():
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return False
    for p in (Path("../.env.test"), Path(".env.test"), Path("../.env"), Path(".env")):
        if p.exists():
            print(f"📁 Loading config from: {p.resolve()}")
            load_dotenv(p)
            return True
    return False

_loaded = _load_dotenv_if_available()
if not _loaded:
    print("ℹ️  No .env(.test) found (OK). Using env/defaults.")

# ---------- Project root & debug dir ----------
def _project_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here.parent] + list(here.parents):
        if (p / "app").exists() or (p / ".git").exists() or (p / "requirements.txt").exists():
            return p
    return Path.cwd()

ROOT = _project_root()
DEBUG_DIR = ROOT / "debug_outputs"
DEBUG_DIR.mkdir(exist_ok=True)

def _save_text(name: str, content: str):
    p = DEBUG_DIR / name
    p.write_text(content, encoding="utf-8")
    print(f"   💾 Saved: {p.relative_to(ROOT)}")

def _save_json(name: str, data: Any):
    _save_text(name, json.dumps(data, indent=2, ensure_ascii=False))

# ---------- Config ----------
API_BASE_URL = os.getenv("STARLUCK_API_BASE_URL", "http://localhost:8000/api/v1")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
TEST_TIMEZONE = os.getenv("TEST_TIMEZONE", "America/New_York")

API_KEY = os.getenv("STARLUCK_API_KEY", "")
API_KEY_AUTH_ENABLED = os.getenv("STARLUCK_ENABLE_API_KEY_AUTH", "false").lower() == "true"

headers = {"Content-Type": "application/json"}
if API_KEY_AUTH_ENABLED and API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"

# ---------- Test payloads ----------
sample_birth_data_whole = {
    "datetime_local": "1990-01-01 12:00",
    "timezone": TEST_TIMEZONE,
    "location": {"lat": 40.7128, "lon": -74.0060, "elevation_m": 0},
    "house_system": "WHOLE",
}

sample_birth_data_placidus = {
    "datetime_local": "1990-01-01 12:00",
    "timezone": TEST_TIMEZONE,
    "location": {"lat": 40.7128, "lon": -74.0060, "elevation_m": 0},
    "house_system": "PLACIDUS",
}


# ---------- HTTP helpers ----------
def _get(path: str) -> requests.Response:
    return requests.get(f"{API_BASE_URL}{path}", timeout=REQUEST_TIMEOUT)

def _post(path: str, payload: Dict[str, Any]) -> requests.Response:
    return requests.post(f"{API_BASE_URL}{path}", json=payload, headers=headers, timeout=REQUEST_TIMEOUT)

# ---------- Tests ----------
def test_health() -> bool:
    print("🔍 /health")
    try:
        r = _get("/health")
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        data = r.json()
        _save_json("health.json", data)
        print("   ✅ OK")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_natal(birth_data: Dict[str, Any], label: str) -> Optional[Dict[str, Any]]:
    print(f"🌟 /natal ({label})")
    try:
        r = _post("/natal", birth_data)
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return None
        data = r.json()
        sun = data["planets"]["Sun"]; moon = data["planets"]["Moon"]; asc = data["angles"]["ASC"]
        print(f"   ✅ Sun {sun['sign']} {sun['deg']:.1f}°, Moon {moon['sign']} {moon['deg']:.1f}°, ASC {asc:.1f}°")
        _save_json(f"natal_{label.lower()}.json", data)
        return data
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_svg(chart_data: Dict[str, Any], label: str, size: int = 900) -> bool:
    print(f"🎨 /svg (wheel – {label})")
    try:
        r = _post("/svg", {"chart_data": chart_data, "size": size, "show_aspects": True})
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        svg = r.json()["svg_content"]
        _save_text(f"wheel_{label.lower()}.svg", svg)
        print("   ✅ OK")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_biwheel(inner_chart: Dict[str, Any], outer_chart: Dict[str, Any]) -> bool:
    print("🎡 /biwheel")
    try:
        payload = {
            "inner_chart": inner_chart,
            "outer_chart": outer_chart,
            "size": 920,
            "label_inner": "Person A",
            "label_outer": "Person B",
            "show_aspects": True,
        }
        r = _post("/biwheel", payload)
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        svg = r.json()["svg_content"]
        _save_text("biwheel.svg", svg)
        print("   ✅ OK")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_synastry(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> bool:
    print("💕 /synastry")
    try:
        r = _post("/synastry", {"chart_a": chart_a, "chart_b": chart_b})
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        inter = r.json().get("interaspects", [])
        _save_json("synastry.json", inter)
        print(f"   ✅ {len(inter)} aspects")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_composite(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> bool:
    print("🤝 /composite")
    try:
        r = _post("/composite", {"chart_a": chart_a, "chart_b": chart_b})
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        mid = r.json().get("midpoints", {})
        _save_json("composite.json", mid)
        print(f"   ✅ {len(mid)} midpoints")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_report(chart_data: Dict[str, Any], title: str = "Comprehensive Test Birth Chart Analysis") -> bool:
    print("📄 /report")
    try:
        r = _post("/report", {"chart_data": chart_data, "title": title})
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        report = r.json().get("report_content", "")
        _save_text("report.md", report)
        print(f"   ✅ {len(report)} chars")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_forecast(natal_chart: Dict[str, Any], days: int = 7, step_hours: int = 12) -> bool:
    print("🔮 /forecast")
    try:
        start = datetime.now().strftime("%Y-%m-%d %H:%M")
        payload = {
            "natal_chart": natal_chart,
            "start_date": start,
            "timezone": TEST_TIMEZONE,
            "days": days,
            "step_hours": step_hours,
        }
        r = _post("/forecast", payload)
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   ❌ {r.text}")
            return False
        data = r.json()
        _save_json("forecast.json", data)
        hits = len(data.get("transits", []))
        print(f"   ✅ {hits} transit hits")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# ---------- Main ----------
def main():
    print("🌟 Starluck Astro API — Full Test Suite")
    print("=" * 60)
    print(f"🌐 Base URL: {API_BASE_URL}")
    print(f"🔐 Auth enabled? {'yes' if API_KEY_AUTH_ENABLED else 'no'}")
    print("=" * 60)

    results = {}

    # 1) Health
    results["health"] = test_health()
    if not results["health"]:
        print("\n❌ Health failed. Is the API running?")
        return

    # 2) Natal charts (WHOLE & PLACIDUS)
    natal_whole = test_natal(sample_birth_data_whole, "WHOLE")
    results["natal_whole"] = natal_whole is not None

    natal_placidus = test_natal(sample_birth_data_placidus, "PLACIDUS")
    results["natal_placidus"] = natal_placidus is not None

    # 3) SVG wheels for both charts
    results["svg_whole"] = test_svg(natal_whole, "WHOLE") if natal_whole else False
    results["svg_placidus"] = test_svg(natal_placidus, "PLACIDUS") if natal_placidus else False

    # 4) Biwheel (if both natal charts available)
    results["biwheel"] = test_biwheel(natal_whole, natal_placidus) if (natal_whole and natal_placidus) else False

    # 5) Synastry
    results["synastry"] = test_synastry(natal_whole, natal_placidus) if (natal_whole and natal_placidus) else False

    # 6) Composite
    results["composite"] = test_composite(natal_whole, natal_placidus) if (natal_whole and natal_placidus) else False

    # 7) Report (using WHOLE)
    results["report"] = test_report(natal_whole) if natal_whole else False

    # 8) Forecast (using WHOLE)
    results["forecast"] = test_forecast(natal_whole) if natal_whole else False

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    order = [
        ("health", "Health"),
        ("natal_whole", "Natal (WHOLE)"),
        ("natal_placidus", "Natal (PLACIDUS)"),
        ("svg_whole", "SVG (WHOLE)"),
        ("svg_placidus", "SVG (PLACIDUS)"),
        ("biwheel", "Biwheel"),
        ("synastry", "Synastry"),
        ("composite", "Composite"),
        ("report", "Report"),
        ("forecast", "Forecast"),
    ]
    passed = 0
    for key, label in order:
        ok = results.get(key, False)
        print(f"{label:<16} {'✅ PASS' if ok else '❌ FAIL'}")
        if ok:
            passed += 1
    total = len(order)
    print("-" * 60)
    pct = int(round((passed / total) * 100)) if total else 0
    print(f"Results: {passed}/{total} passed ({pct}%)")
    print(f"🗂  Files saved under: {DEBUG_DIR.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
