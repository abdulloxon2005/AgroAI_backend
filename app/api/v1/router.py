"""
AgroAI — API V1 Router
Combines all v1 endpoint routers under /api/v1 prefix.
"""
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.scan import router as scan_router
from app.api.v1.chat import router as chat_router
from app.api.v1.weather import router as weather_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(scan_router)
api_router.include_router(chat_router)
api_router.include_router(weather_router)
api_router.include_router(dashboard_router)
