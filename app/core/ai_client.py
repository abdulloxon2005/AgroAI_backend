"""
AgroAI — Centralized AI Client
Single initialization point for Google Gemini API.
"""
import asyncio
from typing import Any

import google.generativeai as genai
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Configure Gemini API once
genai.configure(api_key=settings.GEMINI_API_KEY)

# Pre-built models for different use cases
_scan_model = genai.GenerativeModel(settings.GEMINI_MODEL)

_chat_model = genai.GenerativeModel(
    settings.GEMINI_MODEL,
    system_instruction=(
        "Sen AgroAI — yetakchi sun'iy intellekt agronom maslahatchisisan. "
        "Fermerlarning savollariga qishloq xo'jaligi, ekinlar parvarishi, "
        "tuproq va unumdorlik bo'yicha professional, ilmiy va amaliy javob berasan. "
        "O'zingni har doim AgroAI deb tanishtir va javoblarni o'zbek tilida ber."
    ),
)

_weather_model = genai.GenerativeModel(settings.GEMINI_MODEL)


def get_scan_model() -> genai.GenerativeModel:
    """Get the Gemini model configured for plant scan analysis."""
    return _scan_model


def get_chat_model() -> genai.GenerativeModel:
    """Get the Gemini model configured for agricultural chat."""
    return _chat_model


def get_weather_model() -> genai.GenerativeModel:
    """Get the Gemini model configured for weather recommendations."""
    return _weather_model


async def generate_with_timeout(
    model: genai.GenerativeModel,
    content: Any,
    timeout: int | None = None,
    retries: int | None = None,
) -> str:
    """Generate content with timeout and retry support.

    Args:
        model: Gemini model instance.
        content: Prompt string or list of content parts.
        timeout: Timeout in seconds (defaults to settings.AI_REQUEST_TIMEOUT).
        retries: Number of retries on failure (defaults to settings.AI_MAX_RETRIES).

    Returns:
        Generated text response.

    Raises:
        asyncio.TimeoutError: If all attempts time out.
        Exception: If all retry attempts fail.
    """
    timeout = timeout or settings.AI_REQUEST_TIMEOUT
    retries = retries if retries is not None else settings.AI_MAX_RETRIES
    last_error: Exception | None = None

    for attempt in range(1 + retries):
        try:
            response = await asyncio.wait_for(
                model.generate_content_async(content),
                timeout=timeout,
            )
            return response.text if response.text else ""
        except asyncio.TimeoutError:
            last_error = asyncio.TimeoutError(
                f"AI javob berish vaqti tugadi ({timeout}s)"
            )
            logger.warning(
                "ai_timeout",
                attempt=attempt + 1,
                max_attempts=1 + retries,
                timeout=timeout,
            )
        except Exception as e:
            last_error = e
            logger.warning(
                "ai_error",
                attempt=attempt + 1,
                max_attempts=1 + retries,
                error=str(e),
            )

        if attempt < retries:
            await asyncio.sleep(1)  # Brief pause before retry

    raise last_error  # type: ignore[misc]
