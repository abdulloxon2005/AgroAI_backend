"""
AgroAI — Auth Endpoints
Registration, login, token refresh, and logout.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import User, RefreshToken
from app.domain.schemas import (
    Token, UserCreate, RefreshTokenRequest,
    LoginRequest, LoginResponse, UserResponse, MessageResponse
)
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


import re


def _normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    if not cleaned.startswith('+'):
        if cleaned.startswith('998'):
            cleaned = '+' + cleaned
        else:
            cleaned = '+998' + cleaned
    return cleaned


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and return tokens + user info."""
    clean_phone = _normalize_phone(user_in.phone)

    # Check if phone already exists
    result = await db.execute(
        select(User).filter(
            (User.phone == user_in.phone) | (User.phone == clean_phone)
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Bu telefon raqami allaqachon ro'yxatdan o'tgan")

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        phone=clean_phone,
        password_hash=hashed_pw,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        region=user_in.region,
        district=user_in.district,
        farm_name=user_in.farm_name,
    )
    db.add(new_user)
    await db.flush()

    # Create token pair
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    # Save refresh token to DB
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(token=refresh_token, user_id=new_user.id, expires_at=expires_at)
    db.add(db_token)
    await db.commit()
    await db.refresh(new_user)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify phone and password, return tokens + user info."""
    raw_phone = login_in.phone.strip()
    clean_phone = _normalize_phone(raw_phone)
    digits_only = re.sub(r'\D', '', raw_phone)

    # Search user matching raw, clean, or digits
    result = await db.execute(
        select(User).filter(
            (User.phone == raw_phone) |
            (User.phone == clean_phone) |
            (User.phone.like(f"%{digits_only[-9:]}%") if len(digits_only) >= 9 else User.phone == raw_phone)
        )
    )
    user = result.scalars().first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telefon raqami yoki parol noto'g'ri",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=expires_at)
    db.add(db_token)
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=Token)
async def refresh(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token (with rotation)."""
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.token == body.refresh_token)
    )
    db_token = result.scalars().first()

    if not db_token or db_token.is_revoked:
        raise HTTPException(status_code=401, detail="Yaroqsiz refresh token")

    if db_token.expires_at and db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token muddati tugagan")

    # Revoke old refresh token (token rotation)
    db_token.is_revoked = True

    # Create new token pair
    access_token = create_access_token(data={"sub": str(db_token.user_id)})
    new_refresh_token = create_refresh_token(data={"sub": str(db_token.user_id)})

    # Save new refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_db_token = RefreshToken(
        token=new_refresh_token, user_id=db_token.user_id, expires_at=expires_at
    )
    db.add(new_db_token)
    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revoke refresh token on the server side."""
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.token == body.refresh_token,
            RefreshToken.user_id == user.id,
        )
    )
    db_token = result.scalars().first()
    if db_token:
        db_token.is_revoked = True
        await db.commit()

    return MessageResponse(message="Muvaffaqiyatli chiqildi")
