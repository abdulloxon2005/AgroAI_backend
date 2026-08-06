"""
AgroAI — User Endpoints
User profile and settings management.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.domain.schemas import UserResponse, UserUpdate, SettingsUpdate, SettingsResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user profile."""
    # Only allow fields that actually exist on the User model
    allowed_fields = {"first_name", "last_name", "region", "district", "farm_name", "land_area"}
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    settings_in: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user settings (language, dark_mode, notifications)."""
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
