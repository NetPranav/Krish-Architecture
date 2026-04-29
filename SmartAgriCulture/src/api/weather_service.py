"""
Weather service using OpenWeatherMap API.
Free tier: 1000 calls/day, 60 calls/min.
Get key at: https://home.openweathermap.org/api_keys

.env: OPENWEATHER_API_KEY=your_key_here
"""

import os, httpx, logging, math
from datetime import datetime, timedelta
from functools import lru_cache

log = logging.getLogger(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE = "https://api.openweathermap.org/data/2.5"
GEO = "https://api.openweathermap.org/geo/1.0"

# Cache weather for 10 min to save API calls
_cache = {}
_cache_ttl = 600  # seconds


def _get_cached(key: str):
    if key in _cache:
        data, ts = _cache[key]
        if (datetime.now() - ts).seconds < _cache_ttl:
            return data
    return None


def _set_cache(key: str, data):
    _cache[key] = (data, datetime.now())


def get_current(lat: float = 20.0063, lon: float = 73.7895) -> dict:
    """Get current weather. Falls back to mock data if no API key."""
    if not API_KEY:
        return _mock_current()

    cache_key = f"current_{lat}_{lon}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        r = httpx.get(f"{BASE}/weather", params={
            "lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"
        }, timeout=10)
        r.raise_for_status()
        d = r.json()
        result = {
            "status": "success", "source": "openweathermap",
            "temperature": round(d["main"]["temp"]),
            "feels_like": round(d["main"]["feels_like"]),
            "humidity": d["main"]["humidity"],
            "description": d["weather"][0]["description"].title(),
            "icon": d["weather"][0]["icon"],
            "wind_speed": round(d["wind"]["speed"] * 3.6),  # m/s to km/h
            "wind_dir": _deg_to_dir(d["wind"].get("deg", 0)),
            "rain_probability": d.get("rain", {}).get("1h", 0),
            "frost_safe": d["main"]["temp"] > 5,
            "soil_moisture_status": "Optimal" if d["main"]["humidity"] > 50 else "Low",
        }
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        log.warning("Weather API failed: %s — using mock", e)
        return _mock_current()


def get_forecast(lat: float = 20.0063, lon: float = 73.7895) -> dict:
    """5-day/3-hour forecast. Free tier supports this."""
    if not API_KEY:
        return _mock_forecast()

    cache_key = f"forecast_{lat}_{lon}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        r = httpx.get(f"{BASE}/forecast", params={
            "lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"
        }, timeout=10)
        r.raise_for_status()
        d = r.json()

        # Build hourly (next 30 hours = 10 entries)
        hourly = []
        for item in d["list"][:10]:
            dt = datetime.fromtimestamp(item["dt"])
            hourly.append({
                "time": dt.strftime("%H:%M") if len(hourly) > 0 else "Now",
                "temp": round(item["main"]["temp"]),
                "icon": item["weather"][0]["main"].lower(),
                "rain_pct": round(item.get("pop", 0) * 100),
            })

        # Build weekly (group by day, take 5 days)
        days_seen = {}
        for item in d["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            day_key = dt.strftime("%a")
            if day_key not in days_seen:
                days_seen[day_key] = {"temps": [], "rain": [], "icon": item["weather"][0]["main"]}
            days_seen[day_key]["temps"].append(item["main"]["temp"])
            days_seen[day_key]["rain"].append(item.get("pop", 0))

        weekly = []
        for i, (day, info) in enumerate(days_seen.items()):
            weekly.append({
                "day": "Today" if i == 0 else day,
                "low": round(min(info["temps"])),
                "high": round(max(info["temps"])),
                "rain": f"{round(max(info['rain']) * 100)}%",
                "icon": info["icon"].lower(),
                "highlight": max(info["rain"]) > 0.8,
            })
            if len(weekly) >= 5:
                break

        result = {"status": "success", "source": "openweathermap",
                  "hourly": hourly, "weekly": weekly}
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        log.warning("Forecast API failed: %s — using mock", e)
        return _mock_forecast()


def _deg_to_dir(deg):
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[round(deg / 45) % 8]


def _mock_current():
    return {
        "status": "success", "source": "mock",
        "temperature": 32, "feels_like": 35, "humidity": 65,
        "description": "Partly Cloudy", "icon": "02d",
        "wind_speed": 12, "wind_dir": "NE",
        "rain_probability": 0, "frost_safe": True,
        "soil_moisture_status": "Optimal",
    }


def _mock_forecast():
    return {
        "status": "success", "source": "mock",
        "hourly": [
            {"time": "Now", "icon": "clouds", "temp": 32, "rain_pct": 0},
            {"time": "14:00", "icon": "clear", "temp": 34, "rain_pct": 0},
            {"time": "17:00", "icon": "clear", "temp": 35, "rain_pct": 0},
            {"time": "20:00", "icon": "clouds", "temp": 31, "rain_pct": 5},
            {"time": "23:00", "icon": "clouds", "temp": 28, "rain_pct": 10},
            {"time": "02:00", "icon": "rain", "temp": 25, "rain_pct": 40},
            {"time": "05:00", "icon": "rain", "temp": 24, "rain_pct": 60},
            {"time": "08:00", "icon": "clouds", "temp": 26, "rain_pct": 20},
        ],
        "weekly": [
            {"day": "Today", "rain": "10%", "low": 22, "high": 35, "icon": "clear", "highlight": False},
            {"day": "Thu", "rain": "20%", "low": 23, "high": 33, "icon": "clouds", "highlight": False},
            {"day": "Fri", "rain": "90%", "low": 20, "high": 28, "icon": "rain", "highlight": True},
            {"day": "Sat", "rain": "60%", "low": 21, "high": 29, "icon": "rain", "highlight": False},
            {"day": "Sun", "rain": "0%", "low": 22, "high": 32, "icon": "clear", "highlight": False},
        ],
    }
