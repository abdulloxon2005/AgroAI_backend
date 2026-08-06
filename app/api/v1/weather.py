"""
AgroAI — Weather Endpoints
Current weather data with in-memory caching and AI recommendations.
"""
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.core.ai_client import generate_with_timeout, get_weather_model
from app.core.config import settings
from app.db.models import User
from app.domain.schemas import WeatherRecommendationResponse, WeatherResponse

router = APIRouter(prefix="/weather", tags=["Weather"])

# ---- In-memory cache ----
_weather_cache: dict[str, tuple[float, dict]] = {}

# Shared HTTP client (connection pooling)
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=10.0)
    return _http_client


async def _fetch_weather(location: str | None = None, lat: float | None = None, lon: float | None = None) -> dict:
    """Fetch weather from OpenWeatherMap or Open-Meteo fallback with caching using location name or lat/lon GPS."""
    if lat is not None and lon is not None:
        cache_key = f"{lat:.2f}:{lon:.2f}"
    else:
        cache_key = (location or "tashkent").lower().strip()

    # Return cached data if fresh
    if cache_key in _weather_cache:
        cached_time, cached_data = _weather_cache[cache_key]
        if time.time() - cached_time < settings.WEATHER_CACHE_TTL:
            return cached_data

    client = _get_http_client()

    # 1. Try OpenWeatherMap if key exists
    if settings.OPENWEATHERMAP_API_KEY:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "appid": settings.OPENWEATHERMAP_API_KEY,
            "units": "metric",
            "lang": "uz",
        }
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        else:
            params["q"] = location or "Tashkent"

        try:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                _weather_cache[cache_key] = (time.time(), data)
                return data
        except Exception:
            pass  # Fallback to Open-Meteo below

    # 2. Fallback to Open-Meteo (Free, No API key required)
    target_lat = lat if lat is not None else 41.2995  # Default Tashkent lat
    target_lon = lon if lon is not None else 69.2401  # Default Tashkent lon
    city_name = location or "Toshkent"

    if (lat is None or lon is None) and location:
        try:
            geo_res = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "uz"},
            )
            if geo_res.status_code == 200:
                geo_data = geo_res.json()
                if geo_data.get("results"):
                    target_lat = geo_data["results"][0]["latitude"]
                    target_lon = geo_data["results"][0]["longitude"]
                    city_name = geo_data["results"][0].get("name", location)
        except Exception:
            pass

    try:
        om_res = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": target_lat,
                "longitude": target_lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
            },
        )
        if om_res.status_code == 200:
            om_data = om_res.json()
            current = om_data.get("current", {})
            temp = current.get("temperature_2m", 25.0)
            humidity = current.get("relative_humidity_2m", 50)
            code = current.get("weather_code", 0)

            # Weather code interpretation
            desc = "Ochiq va quyoshli ob-havo"
            if code in [1, 2, 3]:
                desc = "Biroz bulutli ob-havo"
            elif code in [45, 48]:
                desc = "Tumanli ob-havo"
            elif code in [51, 53, 55, 61, 63, 65]:
                desc = "Yomg'irli ob-havo"
            elif code in [71, 73, 75, 77, 85, 86]:
                desc = "Qorli ob-havo"
            elif code in [95, 96, 99]:
                desc = "Moyachilik, momaqaldiroqli ob-havo"

            formatted_data = {
                "name": city_name if city_name != "Tashkent" else "Toshkent",
                "main": {"temp": temp, "humidity": humidity},
                "weather": [{"description": desc}],
            }
            _weather_cache[cache_key] = (time.time(), formatted_data)
            return formatted_data
    except Exception:
        pass

    # Standard fallback
    fallback_data = {
        "name": city_name or "Toshkent",
        "main": {"temp": 25.0, "humidity": 50},
        "weather": [{"description": "Ochiq ob-havo"}],
    }
    _weather_cache[cache_key] = (time.time(), fallback_data)
    return fallback_data


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    location: str | None = Query(None, description="City name"),
    lat: float | None = Query(None, description="Latitude"),
    lon: float | None = Query(None, description="Longitude"),
    current_user: User = Depends(get_current_user),
):
    """Get current weather from OpenWeatherMap using city name or lat/lon GPS."""
    data = await _fetch_weather(location=location, lat=lat, lon=lon)
    city_name = data.get("name") or location or "Tashkent"
    return {
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "location": city_name,
    }


@router.get("/recommendation", response_model=WeatherRecommendationResponse)
async def get_weather_recommendation(
    location: str | None = Query(None, description="City name"),
    lat: float | None = Query(None, description="Latitude"),
    lon: float | None = Query(None, description="Longitude"),
    crop: str = Query("Ekin", description="Crop name"),
    current_user: User = Depends(get_current_user),
):
    """AI irrigation recommendation using AgroAI + weather data."""
    data = await _fetch_weather(location=location, lat=lat, lon=lon)

    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    desc = data["weather"][0]["description"]
    city_name = data.get("name") or location or "Tashkent"

    prompt = (
        f"Sen AgroAI agronomisiz. Hozirgi ob-havo {city_name} da: {desc}, {temp}°C, namlik {humidity}%. "
        f"Fermer {crop} etishtirmoqda. Qisqa, amaliy va ilmiy sug'orish va parvarish tavsiyasi ber. "
        f"O'zbek tilida javob ber."
    )

    try:
        recommendation = await generate_with_timeout(get_weather_model(), prompt)
    except Exception:
        recommendation = "Muntazam sug'orish jadvalini saqlang va tuproq namligini kuzating."

    return {
        "location": city_name,
        "crop": crop,
        "temperature": temp,
        "recommendation": recommendation,
    }
