"""
AgroAI — Test Configuration
Shared fixtures for all tests using an in-memory SQLite database.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.database import Base
from app.db.models import User, RefreshToken
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings


# In-memory async engine for tests
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a fresh database session per test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a test user."""
    user = User(
        first_name="Test",
        last_name="User",
        phone="+998901234567",
        password_hash=get_password_hash("TestPass1"),
        region="Toshkent",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_access_token(test_user: User) -> str:
    """Create a valid access token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest_asyncio.fixture
async def test_refresh_token(test_user: User, db_session: AsyncSession) -> str:
    """Create and persist a valid refresh token."""
    token = create_refresh_token(data={"sub": str(test_user.id)})
    db_token = RefreshToken(
        token=token,
        user_id=test_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(db_token)
    await db_session.commit()
    return token
