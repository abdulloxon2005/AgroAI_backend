from app.core.config import settings
import httpx
import time
import structlog

logger = structlog.get_logger()

# Simple in-memory cache
_weather_cache: dict[str, tuple[float, WeatherResponse]] = {}
CACHE_TTL = 300  # 5 minutes


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    async def get_weather(self, lat: float, lon: float) -> dict:
        # Check cache
        cache_key = f"{lat:.2f}:{lon:.2f}"
        if cache_key in _weather_cache:
            cached_time, cached_data = _weather_cache[cache_key]
            if time.time() - cached_time < CACHE_TTL:
                return cached_data

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric",
                        "lang": "uz",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("weather_api_error", status=e.response.status_code)
            raise Exception(f"Ob-havo xizmati xatosi: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("weather_connection_error", error=str(e))
            raise Exception("Ob-havo xizmatiga ulanib bo'lmadi")

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        location = data.get("name", "")

        recommendation = self._get_recommendation(temp, humidity, description)

        weather_response = {
            "temperature": temp,
            "humidity": humidity,
            "description": description,
            "location": location,
            "wind_speed": data["wind"]["speed"],
            "recommendation": recommendation,
        }

        # Update cache
        _weather_cache[cache_key] = (time.time(), weather_response)

        return weather_response

    def _get_recommendation(self, temp: float, humidity: int, desc: str) -> str:
        tips = []

        if temp > 35:
            tips.append(
                "🌡️ Harorat juda yuqori. O'simliklarni ertalab yoki kechqurun sug'oring."
            )
        elif temp < 5:
            tips.append("❄️ Sovuq havo. O'simliklarni sovuqdan himoya qiling.")

        if humidity > 80:
            tips.append(
                "💧 Namlik yuqori. Zamburug' kasalliklariga e'tibor bering."
            )
        elif humidity < 30:
            tips.append("🏜️ Namlik past. Sug'orishni ko'paytiring.")

        if "yomg'ir" in desc.lower() or "rain" in desc.lower():
            tips.append("🌧️ Yomg'ir kutilmoqda. Sug'orishni kamaytiring.")

        return " | ".join(tips) if tips else "✅ Ob-havo qishloq xo'jaligi uchun qulay."
