from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.models import User
from app.schemas.schemas import UserUpdate, UserSettings
from app.core.security import get_password_hash
from app.api.users.repository import UserRepository


class UserService:
    """Service layer for user operations."""
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def get_user_by_id(self, user_id: int, current_user: User) -> User:
        """Get user by ID."""
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    def update_user(self, user_update: UserUpdate, current_user: User) -> User:
        """Update current user information."""
        update_data = {}
        
        # Validate and prepare username update
        if user_update.username is not None:
            existing_user = self.repository.get_user_by_username(user_update.username)
            if existing_user and existing_user.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            update_data["username"] = user_update.username
        
        # Validate and prepare email update
        if user_update.email is not None:
            existing_user = self.repository.get_user_by_email(user_update.email)
            if existing_user and existing_user.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            update_data["email"] = user_update.email
        
        # Prepare password update
        if user_update.password is not None:
            update_data["password_hash"] = get_password_hash(user_update.password)
        
        # Prepare other field updates
        if user_update.avatar_url is not None:
            update_data["avatar_url"] = user_update.avatar_url
        
        if user_update.voice_speed_setting is not None:
            update_data["voice_speed_setting"] = user_update.voice_speed_setting
        
        if user_update.contrast_setting is not None:
            update_data["contrast_setting"] = user_update.contrast_setting
        
        if user_update.confirmation_nudges_setting is not None:
            update_data["confirmation_nudges_setting"] = user_update.confirmation_nudges_setting
        
        return self.repository.update_user(current_user, update_data)
    
    def get_user_settings(self, current_user: User) -> Dict[str, Any]:
        """Get user settings."""
        return {
            "voice_speed_setting": current_user.voice_speed_setting,
            "contrast_setting": current_user.contrast_setting,
            "confirmation_nudges_setting": current_user.confirmation_nudges_setting
        }
    
    def update_user_settings(self, settings: UserSettings, current_user: User) -> Dict[str, Any]:
        """Update user settings."""
        settings_data = {
            "voice_speed_setting": settings.voice_speed_setting,
            "contrast_setting": settings.contrast_setting,
            "confirmation_nudges_setting": settings.confirmation_nudges_setting
        }
        
        updated_user = self.repository.update_user_settings(current_user, settings_data)
        
        return {
            "voice_speed_setting": updated_user.voice_speed_setting,
            "contrast_setting": updated_user.contrast_setting,
            "confirmation_nudges_setting": updated_user.confirmation_nudges_setting
        }
