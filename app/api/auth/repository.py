from sqlalchemy.orm import Session
from app.models.models import User

class AuthRepository:
    """Repository layer for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_username(self, username: str):
        """Find a user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str):
        """Find a user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, username: str, email: str, password_hash: str):
        """Create a new user."""
        db_user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
