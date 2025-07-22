from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.models import Connection, User, ConnectionStatus, ConnectionType


class ConnectionRepository:
    """Repository layer for connection operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_connection(self, connection_data: dict) -> Connection:
        """Create a new connection."""
        db_connection = Connection(**connection_data)
        self.db.add(db_connection)
        self.db.commit()
        self.db.refresh(db_connection)
        return db_connection
    
    def get_connection_by_id(self, connection_id: int) -> Optional[Connection]:
        """Get a connection by its ID."""
        return self.db.query(Connection).filter(Connection.connection_id == connection_id).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by their ID."""
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_existing_connection(self, user_a_id: int, user_b_id: int) -> Optional[Connection]:
        """Check if a connection already exists between two users."""
        return self.db.query(Connection).filter(
            ((Connection.user_a_id == user_a_id) & 
             (Connection.user_b_id == user_b_id)) |
            ((Connection.user_a_id == user_b_id) & 
             (Connection.user_b_id == user_a_id))
        ).first()
    
    def get_user_connections(
        self, 
        user_id: int, 
        connection_type: Optional[ConnectionType] = None,
        status: Optional[ConnectionStatus] = None
    ) -> List[Connection]:
        """Get all connections for a user with optional filters."""
        query = self.db.query(Connection).filter(
            (Connection.user_a_id == user_id) | 
            (Connection.user_b_id == user_id)
        )
        
        if connection_type:
            query = query.filter(Connection.connection_type == connection_type)
        
        if status:
            query = query.filter(Connection.status == status)
        
        return query.all()
    
    def update_connection(self, connection: Connection, update_data: dict) -> Connection:
        """Update a connection with the provided data."""
        for key, value in update_data.items():
            if value is not None:
                setattr(connection, key, value)
        
        self.db.commit()
        self.db.refresh(connection)
        return connection
    
    def delete_connection(self, connection: Connection) -> None:
        """Delete a connection."""
        self.db.delete(connection)
        self.db.commit()
