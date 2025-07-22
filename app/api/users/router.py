from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse, UserUpdate, UserSettings
from app.core.security import get_current_active_user
from app.api.users.service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information."""
    service = UserService(db)
    return service.update_user(user_update, current_user)

@router.get("/settings", response_model=UserSettings)
def get_user_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user settings."""
    service = UserService(db)
    return service.get_user_settings(current_user)

@router.put("/settings", response_model=UserSettings)
def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user settings."""
    service = UserService(db)
    return service.update_user_settings(settings, current_user)

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID."""
    service = UserService(db)
    return service.get_user_by_id(user_id, current_user)
