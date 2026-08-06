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


async def _fetch_weather(location: str) -> dict:
    """Fetch weather from OpenWeatherMap with caching."""
    cache_key = location.lower().strip()

    # Return cached data if fresh
    if cache_key in _weather_cache:
        cached_time, cached_data = _weather_cache[cache_key]
        if time.time() - cached_time < settings.WEATHER_CACHE_TTL:
            return cached_data

    if not settings.OPENWEATHERMAP_API_KEY:
        raise HTTPException(status_code=503, detail="Ob-havo API kaliti sozlanmagan")

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric",
        "lang": "uz",
    }

    try:
        client = _get_http_client()
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Ob-havo ma'lumotlarini olishda xatolik",
            )
        data = response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Ob-havo xizmatiga ulanib bo'lmadi: {e}")

    # Update cache
    _weather_cache[cache_key] = (time.time(), data)
    return data


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    location: str = Query(..., description="City name"),
    current_user: User = Depends(get_current_user),
):
    """Get current weather from OpenWeatherMap (cached)."""
    data = await _fetch_weather(location)
    return {
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "location": location,
    }


@router.get("/recommendation", response_model=WeatherRecommendationResponse)
async def get_weather_recommendation(
    location: str = Query(..., description="City name"),
    crop: str = Query(..., description="Crop name"),
    current_user: User = Depends(get_current_user),
):
    """AI irrigation recommendation using AgroAI + weather data."""
    data = await _fetch_weather(location)

    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    desc = data["weather"][0]["description"]

    prompt = (
        f"Sen AgroAI agronomisiz. Hozirgi ob-havo {location} da: {desc}, {temp}°C, namlik {humidity}%. "
        f"Fermer {crop} etishtirmoqda. Qisqa, amaliy va ilmiy sug'orish va parvarish tavsiyasi ber. "
        f"O'zbek tilida javob ber."
    )

    try:
        recommendation = await generate_with_timeout(get_weather_model(), prompt)
    except Exception:
        recommendation = "Muntazam sug'orish jadvalini saqlang va tuproq namligini kuzating."

    return {
        "location": location,
        "crop": crop,
        "temperature": temp,
        "recommendation": recommendation,
    }
