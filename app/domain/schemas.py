"""
AgroAI — Pydantic V2 Schemas
All request/response schemas for the API.
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


# ──────────────────────────────────────────────
# Generic Responses
# ──────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    pages: int


# ──────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────

class Token(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request to refresh or revoke a token."""
    refresh_token: str


# ──────────────────────────────────────────────
# User Schemas
# ──────────────────────────────────────────────

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    password: str
    region: Optional[str] = None
    district: Optional[str] = None
    farm_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Parol kamida 8 ta belgidan iborat bo'lishi kerak")
        if not any(c.isupper() for c in v):
            raise ValueError("Parolda kamida 1 ta katta harf bo'lishi kerak")
        if not any(c.isdigit() for c in v):
            raise ValueError("Parolda kamida 1 ta raqam bo'lishi kerak")
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    farm_name: Optional[str] = None
    land_area: Optional[float] = None


class SettingsUpdate(BaseModel):
    language: Optional[str] = None
    dark_mode: Optional[bool] = None
    notifications: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    phone: str
    region: Optional[str] = None
    district: Optional[str] = None
    farm_name: Optional[str] = None
    land_area: Optional[float] = None
    language: str
    dark_mode: bool
    notifications: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SettingsResponse(BaseModel):
    language: str
    dark_mode: bool
    notifications: bool
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=20)
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ──────────────────────────────────────────────
# Scan Schemas
# ──────────────────────────────────────────────

class ScanCreate(BaseModel):
    crop_name: str
    tflite_result: Optional[Dict[str, Any]] = None


class ScanResponse(BaseModel):
    id: uuid.UUID
    image_url: Optional[str] = None
    crop_name: str
    disease_name: Optional[str] = None
    confidence: Optional[float] = None
    is_healthy: Optional[bool] = None
    ai_description: Optional[str] = None
    recommendations: Optional[Any] = None
    medicine_info: Optional[Any] = None
    scanned_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScanListResponse(BaseModel):
    items: List[ScanResponse]
    total: int
    page: int
    limit: int


class ScanAnalysisResponse(BaseModel):
    scan: ScanResponse
    weather_tip: Optional[str] = None


# ──────────────────────────────────────────────
# Chat Schemas
# ──────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: str = "Yangi suhbat"


class ChatMessageCreate(BaseModel):
    content: str = Field(..., max_length=2000)
    image_url: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionResponse]
    total: int = 0
    page: int = 1
    limit: int = 20


class ChatMessageListResponse(BaseModel):
    items: List[ChatMessageResponse]


# ──────────────────────────────────────────────
# Weather Schemas
# ──────────────────────────────────────────────

class WeatherResponse(BaseModel):
    temperature: float
    humidity: float
    description: str
    location: str
    model_config = ConfigDict(from_attributes=True)


class WeatherRecommendationResponse(BaseModel):
    location: str
    crop: str
    temperature: float
    recommendation: str


# ──────────────────────────────────────────────
# Dashboard Schemas
# ──────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_scans: int
    diseases_found: int
    healthy_count: int
    last_scan_date: Optional[datetime] = None


class DashboardStatsResponse(BaseModel):
    total_scans: int
    diseases_found: int
    healthy_count: int
    last_scan_date: Optional[datetime] = None


class ChartDataPoint(BaseModel):
    month: Optional[str] = None
    date: Optional[str] = None
    disease: Optional[str] = None
    count: Optional[int] = None
    healthy: Optional[int] = None
    diseased: Optional[int] = None


class DashboardChartsResponse(BaseModel):
    monthly_scans: List[Dict[str, Any]]
    disease_distribution: List[Dict[str, Any]]
    health_trend: List[Dict[str, Any]]
