from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse, UserUpdate, UserSettings
from app.core.security import get_current_active_user, get_password_hash

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
    # Update user fields if provided
    if user_update.username is not None:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user and existing_user.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
    
    if user_update.email is not None:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    if user_update.password is not None:
        current_user.password_hash = get_password_hash(user_update.password)
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    if user_update.voice_speed_setting is not None:
        current_user.voice_speed_setting = user_update.voice_speed_setting
    
    if user_update.contrast_setting is not None:
        current_user.contrast_setting = user_update.contrast_setting
    
    if user_update.confirmation_nudges_setting is not None:
        current_user.confirmation_nudges_setting = user_update.confirmation_nudges_setting
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/settings", response_model=UserSettings)
def get_user_settings(current_user: User = Depends(get_current_active_user)):
    """Get user settings."""
    return {
        "voice_speed_setting": current_user.voice_speed_setting,
        "contrast_setting": current_user.contrast_setting,
        "confirmation_nudges_setting": current_user.confirmation_nudges_setting
    }

@router.put("/settings", response_model=UserSettings)
def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user settings."""
    current_user.voice_speed_setting = settings.voice_speed_setting
    current_user.contrast_setting = settings.contrast_setting
    current_user.confirmation_nudges_setting = settings.confirmation_nudges_setting
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "voice_speed_setting": current_user.voice_speed_setting,
        "contrast_setting": current_user.contrast_setting,
        "confirmation_nudges_setting": current_user.confirmation_nudges_setting
    }

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
