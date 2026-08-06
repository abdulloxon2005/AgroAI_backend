"""
AgroAI — Dependency Tests
Tests for token validation and user resolution in deps.py.
"""
import uuid

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestSecurity:
    """Test security module functions."""

    def test_password_hash_and_verify(self):
        password = "SecurePass123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPass", hashed)

    def test_create_access_token(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        user_id = str(uuid.uuid4())
        token = create_refresh_token(data={"sub": user_id})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        result = decode_token("invalid.token.here")
        assert result is None

    def test_decode_empty_token(self):
        result = decode_token("")
        assert result is None

    def test_token_type_distinction(self):
        """Access and refresh tokens must have different type claims."""
        user_id = str(uuid.uuid4())
        access = decode_token(create_access_token(data={"sub": user_id}))
        refresh = decode_token(create_refresh_token(data={"sub": user_id}))
        assert access["type"] == "access"
        assert refresh["type"] == "refresh"

    def test_uuid_in_token_subject(self):
        """Token subject must be a valid UUID string."""
        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id})
        payload = decode_token(token)
        # Verify it can be parsed back to UUID
        parsed = uuid.UUID(payload["sub"])
        assert str(parsed) == user_id
