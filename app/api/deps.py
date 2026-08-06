"""
AgroAI — API Dependencies
Database session and authentication dependencies.
"""
import uuid as uuid_mod

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db as get_session
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException
from app.db.models import User

security_scheme = HTTPBearer()


async def get_db(session: AsyncSession = Depends(get_session)):
    return session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise UnauthorizedException("Token yaroqsiz yoki muddati o'tgan")

    if payload.get("type") != "access":
        raise UnauthorizedException("Access token talab qilinadi")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Token yaroqsiz")

    # User.id is UUID, so parse the subject as UUID (not int)
    try:
        user_uuid = uuid_mod.UUID(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedException("Token yaroqsiz")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("Foydalanuvchi topilmadi")

    return user
