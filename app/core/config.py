from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "AgroAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = "sqlite+aiosqlite:///./agroai.db"

    GEMINI_API_KEY: str = ""
    OPENWEATHERMAP_API_KEY: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    UPLOAD_DIR: str = "uploads"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    GEMINI_MODEL: str = "gemini-2.0-flash"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_SCAN: str = "10/minute"

    # AI timeouts
    AI_REQUEST_TIMEOUT: int = 30  # seconds
    AI_MAX_RETRIES: int = 1

    # Weather cache
    WEATHER_CACHE_TTL: int = 600  # 10 minutes


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
