import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.auth import UserCreate, LoginResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.exceptions import AppException
from fastapi import status
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)

async def _create_token_pair(user_id: int) -> Token:
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

async def register_user(db: AsyncSession, user_data: UserCreate) -> LoginResponse:
    logger.info("Registering new user", phone=user_data.phone)
    
    # Check if user exists
    stmt = select(User).where(User.phone == user_data.phone)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        logger.warning("Registration failed, phone already exists", phone=user_data.phone)
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        phone=user_data.phone,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role="user",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    tokens = await _create_token_pair(user.id)
    logger.info("User registered successfully", user_id=user.id)
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user=user
    )

async def login_user(db: AsyncSession, phone: str, password: str) -> LoginResponse:
    logger.info("Attempting login", phone=phone)
    
    stmt = select(User).where(User.phone == phone)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Login failed, invalid credentials", phone=phone)
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password"
        )
    
    if not user.is_active:
        logger.warning("Login failed, inactive user", phone=phone)
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    tokens = await _create_token_pair(user.id)
    logger.info("User logged in successfully", user_id=user.id)
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user=user
    )

async def refresh_tokens(db: AsyncSession, refresh_token: str) -> Token:
    from app.core.security import decode_token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise AppException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user_id = int(payload.get("sub"))
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AppException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        
    return await _create_token_pair(user_id)

async def logout_user(db: AsyncSession, refresh_token: str) -> bool:
    logger.info("User logged out")
    return True
