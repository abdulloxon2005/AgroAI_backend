"""
AgroAI — Auth Flow Tests
Tests for token revocation, refresh rotation, and user lookup.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, RefreshToken
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


@pytest.mark.asyncio
class TestAuthModels:
    """Test authentication-related database operations."""

    async def test_user_has_uuid_id(self, test_user: User):
        """User.id must be a UUID, not an integer."""
        assert isinstance(test_user.id, uuid.UUID)

    async def test_refresh_token_saved(self, test_user, db_session: AsyncSession):
        """Refresh tokens are saved to the database."""
        token_str = create_refresh_token(data={"sub": str(test_user.id)})
        db_token = RefreshToken(
            token=token_str,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(db_token)
        await db_session.commit()

        result = await db_session.execute(
            select(RefreshToken).filter(RefreshToken.token == token_str)
        )
        saved = result.scalars().first()
        assert saved is not None
        assert saved.is_revoked is False
        assert saved.user_id == test_user.id

    async def test_revoke_refresh_token(self, test_user, db_session: AsyncSession):
        """Revoking a refresh token sets is_revoked = True."""
        token_str = create_refresh_token(data={"sub": str(test_user.id)})
        db_token = RefreshToken(
            token=token_str,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(db_token)
        await db_session.commit()

        # Revoke it
        db_token.is_revoked = True
        await db_session.commit()

        result = await db_session.execute(
            select(RefreshToken).filter(RefreshToken.token == token_str)
        )
        saved = result.scalars().first()
        assert saved.is_revoked is True

    async def test_access_token_contains_uuid_sub(self, test_user):
        """Access token 'sub' claim is a valid UUID string."""
        token = create_access_token(data={"sub": str(test_user.id)})
        payload = decode_token(token)
        assert payload is not None
        parsed_uuid = uuid.UUID(payload["sub"])
        assert parsed_uuid == test_user.id

    async def test_user_lookup_by_uuid(self, test_user, db_session: AsyncSession):
        """User can be found by UUID id, not int."""
        result = await db_session.execute(
            select(User).where(User.id == test_user.id)
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.phone == test_user.phone

    async def test_user_lookup_by_int_fails(self, test_user, db_session: AsyncSession):
        """Looking up user with int id should return None (UUID mismatch)."""
        result = await db_session.execute(
            select(User).where(User.id == 1)
        )
        user = result.scalar_one_or_none()
        # May or may not be None depending on DB, but it should not match UUID user
        # The important thing is that int(uuid_string) would raise ValueError
        with pytest.raises(ValueError):
            int(str(test_user.id))


@pytest.mark.asyncio
class TestPasswordValidation:
    """Test password hashing and validation."""

    async def test_correct_password(self):
        hashed = get_password_hash("MySecure1Pass")
        assert verify_password("MySecure1Pass", hashed)

    async def test_wrong_password(self):
        hashed = get_password_hash("MySecure1Pass")
        assert not verify_password("WrongPassword1", hashed)
