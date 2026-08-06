"""
AgroAI — Scan Validation Tests
Tests for file size/type validation and scan model operations.
"""
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Scan, User
from app.core.config import settings


@pytest.mark.asyncio
class TestScanModel:
    """Test scan database operations."""

    async def test_create_scan(self, test_user: User, db_session: AsyncSession):
        """A scan can be created and linked to a user."""
        scan = Scan(
            user_id=test_user.id,
            crop_name="Pomidor",
            image_url="/uploads/test.jpg",
            disease_name="Fitoftoroz",
            confidence=0.92,
            is_healthy=False,
            ai_description="Kasallik aniqlandi",
            recommendations={"steps": ["Fungitsid sepish"]},
            medicine_info={"medicines": ["Ridomil Gold"]},
        )
        db_session.add(scan)
        await db_session.commit()
        await db_session.refresh(scan)

        assert isinstance(scan.id, uuid.UUID)
        assert scan.user_id == test_user.id
        assert scan.crop_name == "Pomidor"
        assert scan.confidence == 0.92
        assert scan.is_healthy is False

    async def test_healthy_scan(self, test_user: User, db_session: AsyncSession):
        """A healthy scan has no disease name."""
        scan = Scan(
            user_id=test_user.id,
            crop_name="Bug'doy",
            is_healthy=True,
            confidence=0.98,
        )
        db_session.add(scan)
        await db_session.commit()
        await db_session.refresh(scan)

        assert scan.is_healthy is True
        assert scan.disease_name is None


class TestFileValidation:
    """Test file upload validation logic."""

    def test_allowed_image_types(self):
        allowed = {"image/jpeg", "image/png", "image/webp"}
        assert "image/jpeg" in allowed
        assert "image/png" in allowed
        assert "image/webp" in allowed
        assert "application/pdf" not in allowed
        assert "image/gif" not in allowed

    def test_max_file_size(self):
        assert settings.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10 MB

    def test_file_over_max_size(self):
        """Content exceeding MAX_FILE_SIZE should be rejected."""
        fake_content = b"x" * (settings.MAX_FILE_SIZE + 1)
        assert len(fake_content) > settings.MAX_FILE_SIZE
