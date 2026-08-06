"""
AgroAI — Application Entry Point
FastAPI application factory with middleware, exception handlers, and routes.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import structlog
from pathlib import Path
import os
from sqlalchemy import text

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.database import init_db, async_session_maker
from app.api.v1.router import api_router
from app.api.v1.websocket import router as ws_router
from app.core.exceptions import AppException, app_exception_handler, generic_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ]
    )
    Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# --- Rate Limiter ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# --- Routes ---
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")

# --- Static Files & Web Landing Page ---
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

web_dir = Path(__file__).resolve().parents[2] / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


# --- Health Check ---
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok"}


@app.get("/health/db")
async def health_check_db():
    """Health check with database connectivity test."""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": f"error: {str(e)}"}
