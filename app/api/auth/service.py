from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth.repository import AuthRepository
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

class AuthService:
    """Service layer for authentication operations."""
    
    def __init__(self, db: Session):
        self.repository = AuthRepository(db)
    
    def register_user(self, username: str, email: str, password: str):
        """Register a new user."""
        # Check if username exists
        if self.repository.get_user_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        if self.repository.get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(password)
        return self.repository.create_user(username, email, hashed_password)
    
    def authenticate_user(self, username_or_email: str, password: str):
        """Authenticate a user and return an access token along with user details.
        
        Args:
            username_or_email: Can be either username or email
            password: User's password
        """
        # Try to find user by username first
        user = self.repository.get_user_by_username(username_or_email)
        
        # If not found by username, try email
        if not user and '@' in username_or_email:
            user = self.repository.get_user_by_email(username_or_email)
        
        # If still not found, raise error
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Return user details along with token
        return {
            "id": str(user.user_id),
            "name": user.username,
            "email": user.email,
            "token": access_token,
            "createdAt": user.created_at,
            "updatedAt": user.last_login
        }
