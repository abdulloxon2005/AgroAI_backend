"""
AgroAI — Config Tests
Tests for configuration singleton and settings.
"""
import pytest

from app.core.config import Settings, get_settings, settings


class TestConfig:
    """Test configuration module."""

    def test_settings_singleton(self):
        """get_settings() must return the same instance (lru_cache)."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_module_level_settings(self):
        """Module-level `settings` should be the same as get_settings()."""
        assert settings is get_settings()

    def test_default_values(self):
        """Verify critical defaults exist."""
        assert settings.APP_NAME == "AgroAI"
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30
        assert settings.MAX_FILE_SIZE == 10 * 1024 * 1024
        assert settings.GEMINI_MODEL == "gemini-2.0-flash"

    def test_rate_limit_defaults(self):
        """Rate limit settings must be present."""
        assert settings.RATE_LIMIT_LOGIN
        assert settings.RATE_LIMIT_REGISTER
        assert settings.RATE_LIMIT_SCAN

    def test_ai_timeout_defaults(self):
        """AI timeout settings must be present."""
        assert settings.AI_REQUEST_TIMEOUT > 0
        assert settings.AI_MAX_RETRIES >= 0

    def test_weather_cache_ttl(self):
        """Weather cache TTL must be positive."""
        assert settings.WEATHER_CACHE_TTL > 0
