import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import get_db
from app.core.security import create_access_token
from app.db.models import User

@pytest.mark.asyncio
async def test_get_current_weather(db_session, test_user):
    """Test getting current weather data with location query."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/weather/current?location=Tashkent",
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "temperature" in data
        assert "humidity" in data
        assert "description" in data
        assert "location" in data
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_weather_recommendation(db_session, test_user):
    """Test getting weather irrigation recommendations."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/weather/recommendation?location=Samarkand&crop=Pomidor",
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        assert "temperature" in data
        assert data["crop"] == "Pomidor"
    finally:
        app.dependency_overrides.clear()
