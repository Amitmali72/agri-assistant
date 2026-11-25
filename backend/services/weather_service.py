"""
Weather Service (Module 8).
Provides LIVE real-time weather + 3-day agricultural forecast + localized advisories.
Uses:
1. OpenWeatherMap API (when OPENWEATHER_API_KEY is configured)
2. Open-Meteo API (100% free, live, no API key required) as automatic live provider!
Includes in-memory TTL caching (15 min), rate limiting, and explicit is_live/cached metadata.
"""

from __future__ import annotations

import os
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from backend.config import settings

logger = logging.getLogger(__name__)

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"
OPEN_METEO_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_WEATHER_CODES = {
    0: {"en": "Clear sky", "hi": "साफ आसमान", "mr": "निरभ्र आकाश"},
    1: {"en": "Mainly clear", "hi": "मुख्यतः साफ", "mr": "मुख्यतः स्वच्छ हवामान"},
    2: {"en": "Partly cloudy", "hi": "आंशिक बादल", "mr": "अंशतः ढगाळ"},
    3: {"en": "Overcast", "hi": "घने बादल", "mr": "दाट ढगाळ हवामान"},
    45: {"en": "Foggy", "hi": "कोहरा", "mr": "धुके"},
    48: {"en": "Dense fog", "hi": "घना कोहरा", "mr": "दाट धुके"},
    51: {"en": "Light drizzle", "hi": "हल्की बूंदाबांदी", "mr": "हलकी रिमझिम"},
    61: {"en": "Light rain", "hi": "हल्की बारिश", "mr": "हलका पाऊस"},
    63: {"en": "Moderate rain", "hi": "मध्यम बारिश", "mr": "मध्यम पाऊस"},
    65: {"en": "Heavy rain", "hi": "भारी बारिश", "mr": "जोरदार पाऊस"},
    80: {"en": "Rain showers", "hi": "बारिश की बौछारें", "mr": "पावसाच्या सरी"},
    95: {"en": "Thunderstorm", "hi": "आंधी-तूफान", "mr": "वादळी पाऊस व विजा"},
}

_ADVISORIES = {
    "high_temp": {
        "en": "High temperature alert (>35°C) — irrigate crops early morning or evening and apply mulch.",
        "hi": "उच्च तापमान चेतावनी (>35°C) — फसलों की सिंचाई सुबह या शाम को करें और मल्चिंग अपनाएं।",
        "mr": "उच्च तापमान सूचना (>35°C) — पिकांना सकाळी किंवा संध्याकाळी पाणी द्या आणि आच्छादनाचा वापर करा.",
    },
    "heavy_rain": {
        "en": "Rain/heavy rainfall expected — postpone spraying of pesticides/fertilizers and ensure field drainage.",
        "hi": "बारिश की संभावना — कीटनाशक या खाद का छिड़काव टालें और खेत में जल निकासी की व्यवस्था रखें।",
        "mr": "पावसाची शक्यता — कीटकनाशक किंवा खत फवारणी पुढे ढकला आणि शेतातील पाण्याचा निचरा करा.",
    },
    "high_humidity": {
        "en": "High humidity (>80%) — monitor crops closely for fungal diseases like blight and rust.",
        "hi": "उच्च आर्द्रता (>80%) — झुलसा और गेरुआ जैसे फफूंद जनित रोगों की निगरानी करें।",
        "mr": "उच्च आर्द्रता (>80%) — करपा आणि तांबेरा यांसारख्या बुरशीजन्य रोगांवर लक्ष ठेवा.",
    },
    "low_temp": {
        "en": "Low temperature alert (<10°C) — protect sensitive crops from cold stress with light evening irrigation.",
        "hi": "कम तापमान चेतावनी (<10°C) — पाले से बचाव के लिए शाम को हल्की सिंचाई करें।",
        "mr": "कमी तापमान सूचना (<10°C) — थंडीपासून पिकांच्या संरक्षणासाठी संध्याकाळी हलके पाणी द्या.",
    },
    "normal": {
        "en": "Weather conditions are favorable for routine sowing, weeding, and field operations.",
        "hi": "मौसम बुवाई, निराई-गुड़ाई और सामान्य कृषि कार्यों के लिए अनुकूल है।",
        "mr": "हवामान पेरणी, आंतरमशागत आणि इतर शेती कामांसाठी अनुकूल आहे.",
    },
}

WeatherResult = Dict[str, Any]


class WeatherService:
    """Live weather & agronomic advisory service with TTL caching and rate limiting."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("OPENWEATHER_API_KEY", settings.OPENWEATHER_API_KEY)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_ts: float = 0.0

    def get_weather(
        self,
        location: str,
        state: str = "Maharashtra",
        language: str = "mr",
    ) -> WeatherResult:
        loc_clean = (location or "Pune").strip()
        lang_code = language if language in ("hi", "mr", "en") else "en"
        cache_key = f"{loc_clean.lower()}_{state.lower()}_{lang_code}"

        # Check fresh TTL cache (never serve stale cache as live)
        cached_entry = self._cache.get(cache_key)
        if cached_entry and (time.time() - cached_entry["stored_at"] < settings.WEATHER_CACHE_TTL_SECONDS):
            result = dict(cached_entry["data"])
            result["cached"] = True
            return result

        # Simple rate limiter (min 150ms gap between outbound live API calls)
        elapsed = time.time() - self._last_request_ts
        if elapsed < 0.15:
            time.sleep(0.15 - elapsed)
        self._last_request_ts = time.time()

        # 1. Try OpenWeatherMap if API key is configured
        if self.api_key:
            try:
                result = self._fetch_from_owm(loc_clean, state, lang_code)
                self._cache[cache_key] = {"stored_at": time.time(), "data": result}
                return result
            except Exception as exc:
                logger.warning(f"OpenWeatherMap failed, falling back to Open-Meteo: {exc}")

        # 2. Live Open-Meteo (no API key required)
        try:
            result = self._fetch_from_open_meteo(loc_clean, state, lang_code)
            self._cache[cache_key] = {"stored_at": time.time(), "data": result}
            return result
        except Exception as exc:
            logger.error(f"Live weather retrieval failed: {exc}")
            return {
                "success": False,
                "is_live": False,
                "cached": False,
                "location": loc_clean,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Live weather API temporarily unavailable: {exc}",
            }

    def _fetch_from_open_meteo(self, location: str, state: str, language: str) -> WeatherResult:
        geo_resp = requests.get(
            OPEN_METEO_GEO_URL,
            params={"name": location, "count": 5, "language": "en", "format": "json"},
            timeout=8,
        )
        geo_resp.raise_for_status()
        geo_results = geo_resp.json().get("results", [])

        # Prefer Indian match
        chosen = None
        for g in geo_results:
            if g.get("country_code") == "IN":
                chosen = g
                break
        if not chosen and geo_results:
            chosen = geo_results[0]
        if not chosen:
            raise ValueError(f"Location '{location}' not found in Open-Meteo geocoding")

        lat, lon = chosen["latitude"], chosen["longitude"]
        resolved_name = chosen.get("name", location)

        fc_resp = requests.get(
            OPEN_METEO_FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": 3,
                "timezone": "Asia/Kolkata",
            },
            timeout=8,
        )
        fc_resp.raise_for_status()
        fc_data = fc_resp.json()

        current = fc_data.get("current", {})
        daily = fc_data.get("daily", {})

        temp = float(current.get("temperature_2m", 0.0))
        feels_like = float(current.get("apparent_temperature", temp))
        humidity = int(current.get("relative_humidity_2m", 0))
        rainfall = float(current.get("precipitation", current.get("rain", 0.0)))
        wind_speed = float(current.get("wind_speed_10m", 0.0))
        wcode = int(current.get("weather_code", 0))

        desc_map = WMO_WEATHER_CODES.get(wcode, WMO_WEATHER_CODES[0])
        description = desc_map.get(language, desc_map["en"])

        # Build 3-day forecast
        forecast_days: List[Dict[str, Any]] = []
        dates = daily.get("time", [])
        tmaxs = daily.get("temperature_2m_max", [])
        tmins = daily.get("temperature_2m_min", [])
        prcp_sums = daily.get("precipitation_sum", [])
        wcodes = daily.get("weather_code", [])

        for i in range(min(3, len(dates))):
            dc = int(wcodes[i]) if i < len(wcodes) else 0
            d_desc = WMO_WEATHER_CODES.get(dc, WMO_WEATHER_CODES[0]).get(language, "Clear")
            forecast_days.append({
                "date": dates[i],
                "temp_max_c": tmaxs[i] if i < len(tmaxs) else None,
                "temp_min_c": tmins[i] if i < len(tmins) else None,
                "rainfall_mm": prcp_sums[i] if i < len(prcp_sums) else 0.0,
                "description": d_desc,
            })

        upcoming_rain = sum(d.get("rainfall_mm") or 0.0 for d in forecast_days)
        advisory_key = self._advisory_key(temp, max(rainfall, upcoming_rain), humidity)
        advisory = _ADVISORIES[advisory_key][language]

        forecast_summary = "; ".join(
            f"{d['date']}: {d['temp_min_c']}–{d['temp_max_c']}°C, {d['description']} ({d['rainfall_mm']}mm)"
            for d in forecast_days
        )

        return {
            "success": True,
            "is_live": True,
            "cached": False,
            "location": resolved_name,
            "temperature": round(temp, 1),
            "feels_like": round(feels_like, 1),
            "humidity": humidity,
            "description": description,
            "rainfall": round(rainfall, 1),
            "wind_speed": round(wind_speed, 1),
            "forecast_summary": forecast_summary,
            "forecast_days": forecast_days,
            "advisory": advisory,
            "source": "Open-Meteo Live Meteorological API",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _fetch_from_owm(self, location: str, state: str, language: str) -> WeatherResult:
        query = f"{location},{state},IN"
        params: Dict[str, Any] = {
            "q": query,
            "appid": self.api_key,
            "units": "metric",
            "lang": "hi" if language in ("hi", "mr") else "en",
        }
        response = requests.get(OPENWEATHERMAP_URL, params=params, timeout=8)
        if response.status_code == 404:
            params["q"] = f"{location},IN"
            response = requests.get(OPENWEATHERMAP_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        temp = float(data.get("main", {}).get("temp", 0.0))
        feels_like = float(data.get("main", {}).get("feels_like", temp))
        humidity = int(data.get("main", {}).get("humidity", 0))
        description = data.get("weather", [{}])[0].get("description", "")
        wind_speed = float(data.get("wind", {}).get("speed", 0.0)) * 3.6
        rain_data = data.get("rain", {})
        rainfall = float(rain_data.get("1h", rain_data.get("3h", 0.0)))

        advisory_key = self._advisory_key(temp, rainfall, humidity)
        advisory = _ADVISORIES[advisory_key][language]

        return {
            "success": True,
            "is_live": True,
            "cached": False,
            "location": data.get("name", location),
            "temperature": round(temp, 1),
            "feels_like": round(feels_like, 1),
            "humidity": humidity,
            "description": description,
            "rainfall": round(rainfall, 1),
            "wind_speed": round(wind_speed, 1),
            "forecast_summary": description,
            "forecast_days": [],
            "advisory": advisory,
            "source": "OpenWeatherMap Live API",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _advisory_key(temp: float, rainfall: float, humidity: int) -> str:
        if temp > 35:
            return "high_temp"
        if rainfall > 5:
            return "heavy_rain"
        if humidity > 80:
            return "high_humidity"
        if temp < 10:
            return "low_temp"
        return "normal"
