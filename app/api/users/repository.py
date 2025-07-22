from sqlalchemy.orm import Session
from typing import Optional

from app.models.models import User


class UserRepository:
    """Repository layer for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by their ID."""
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user: User, update_data: dict) -> User:
        """Update a user with the provided data."""
        for key, value in update_data.items():
            if value is not None:  # Only update fields that are provided
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user_settings(self, user: User, settings_data: dict) -> User:
        """Update user settings."""
        for key, value in settings_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
