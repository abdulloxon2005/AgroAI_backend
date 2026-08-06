"""
AgroAI — Centralized AI Client
Single initialization point for Google Gemini API with robust multi-model fallback.
"""
import asyncio
from typing import Any

import google.generativeai as genai
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Configure Gemini API once
genai.configure(api_key=settings.GEMINI_API_KEY)

FALLBACK_MODELS = [
    settings.GEMINI_MODEL,
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def get_scan_model(model_name: str | None = None) -> genai.GenerativeModel:
    """Get the Gemini model configured for plant scan analysis."""
    return genai.GenerativeModel(model_name or settings.GEMINI_MODEL)


def get_chat_model(model_name: str | None = None) -> genai.GenerativeModel:
    """Get the Gemini model configured for agricultural chat."""
    return genai.GenerativeModel(
        model_name or settings.GEMINI_MODEL,
        system_instruction=(
            "Sen AgroAI — yetakchi sun'iy intellekt agronom maslahatchisisan. "
            "Fermerlarning savollariga qishloq xo'jaligi, ekinlar parvarishi, "
            "tuproq va unumdorlik bo'yicha professional, ilmiy va amaliy javob berasan. "
            "O'zingni har doim AgroAI deb tanishtir va javoblarni o'zbek tilida ber."
        ),
    )


def get_weather_model(model_name: str | None = None) -> genai.GenerativeModel:
    """Get the Gemini model configured for weather recommendations."""
    return genai.GenerativeModel(model_name or settings.GEMINI_MODEL)


def _generate_agronomist_fallback(prompt: Any) -> str:
    """Generate smart agricultural expert advice when external Gemini API is unreachable."""
    prompt_str = str(prompt).lower()
    
    if any(w in prompt_str for w in ["sug'or", "suv", "namlik"]):
        return (
            "Assalomu alaykum! AgroAI Agronom maslahati:\n\n"
            "💧 **Sug'orish rejimi bo'yicha tavsiya:**\n"
            "- Ekinlarni ertalab barvaqt yoki kechqurun salqinda sug'orish maqsadga muvofiq.\n"
            "- Tuproqning 15-20 sm chuqurligi namligini tekshiring. Haddan tashqari ko'p suv ildiz chirishiga olib kelishi mumkin.\n"
            "- Tomchilatib sug'orish tizimi suvni 40% gacha tejaydi va hosildorlikni oshiradi."
        )
    elif any(w in prompt_str for w in ["o'g'it", "ogit", "oziqlantir", "azot", "fosfor", "kaliy"]):
        return (
            "Assalomu alaykum! AgroAI Agronom maslahati:\n\n"
            "🌿 **O'g'itlash va oziqlantirish:**\n"
            "- O'simlikning maysalash davrida Azotli (Ammiakli selitra/Karbamid) o'g'itlar bering.\n"
            "- G'unchalash va gullash davrida Fosfor va Kaliy o'g'itlari (NPK) ildiz tizimi va meva sifatini yaxshilaydi.\n"
            "- Bargdan oziqlantirish uchun mikroelementlar (Rux, Temir, Bor) eritmasini purkashingiz mumkin."
        )
    elif any(w in prompt_str for w in ["kasallik", "dori", "zararkunanda", "qurt", "shira", "zamburug'"]):
        return (
            "Assalomu alaykum! AgroAI Agronom maslahati:\n\n"
            "🛡️ **Zararkunanda va kasalliklarga qarshi kurash:**\n"
            "- Zamburug'li kasalliklar (fitoftora, un-shudring) uchun *Fitosporin-M* yoki *Ridomil Gold* fungitsidlarini qo'llang.\n"
            "- Zararkunandalar (shira, oq pashsha, qurtlar) uchun *Enjiyo* yoki *Emamektin* insektitsidlarini yo'riqnoma bo'yicha purkang.\n"
            "- Purkash ishlarini shamolsiz kuni, kechki vaqtda amalga oshiring."
        )
    else:
        return (
            "Assalomu alaykum! Men AgroAI — professional AI agronom maslahatchisiman.\n\n"
            "Qishloq xo'jaligi ekinlari parvarishi, sug'orish, mineral o'g'itlar va kasalliklar profilaktikasi bo'yicha istalgan savolingizga javob berishga tayyorman. "
            "Iltimos, ekin turi va muammoni batafsilroq yozing! 🌾"
        )


async def generate_with_timeout(
    model: genai.GenerativeModel,
    content: Any,
    timeout: int | None = None,
    retries: int | None = None,
) -> str:
    """Generate content with multi-model fallback and timeout support."""
    timeout = timeout or settings.AI_REQUEST_TIMEOUT
    retries = retries if retries is not None else settings.AI_MAX_RETRIES
    last_error: Exception | None = None

    # Collect candidate model names to try
    models_to_try = [model]
    for model_name in FALLBACK_MODELS:
        try:
            m = genai.GenerativeModel(model_name)
            models_to_try.append(m)
        except Exception:
            pass

    for candidate_model in models_to_try:
        for attempt in range(1 + retries):
            try:
                response = await asyncio.wait_for(
                    candidate_model.generate_content_async(content),
                    timeout=timeout,
                )
                if response and response.text and response.text.strip():
                    return response.text.strip()
            except asyncio.TimeoutError:
                last_error = asyncio.TimeoutError(f"AI javob vaqti tugadi ({timeout}s)")
            except Exception as e:
                last_error = e
                logger.warning("ai_model_attempt_failed", model=getattr(candidate_model, 'model_name', 'unknown'), error=str(e))
                break  # Switch to next model on API error/quota issue

    # If all models failed or rate limited, return intelligent fallback
    logger.error("all_ai_models_failed", last_error=str(last_error))
    return _generate_agronomist_fallback(content)

