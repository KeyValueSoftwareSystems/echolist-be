from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.models import User, Connection, ConnectionStatus, ConnectionType
from app.schemas.schemas import ConnectionCreate, ConnectionUpdate
from app.api.connections.repository import ConnectionRepository


class ConnectionService:
    """Service layer for connection operations."""
    
    def __init__(self, db: Session):
        self.repository = ConnectionRepository(db)
    
    def create_connection(self, connection: ConnectionCreate, current_user: User) -> Connection:
        """Create a new connection with another user using email."""
        # Check if target user exists by email
        target_user = self.repository.get_user_by_email(connection.email)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{connection.email}' not found"
            )
        
        # Check if user is trying to connect with themselves
        if target_user.user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create connection with yourself"
            )
        
        # Check if connection already exists
        existing_connection = self.repository.get_existing_connection(
            current_user.user_id, target_user.user_id
        )
        if existing_connection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection already exists with status: {existing_connection.status}"
            )
        
        # Create new connection
        connection_data = {
            "user_a_id": current_user.user_id,
            "user_b_id": target_user.user_id,
            "connection_type": connection.connection_type,
            "status": ConnectionStatus.PENDING
        }
        
        return self.repository.create_connection(connection_data)
    
    def get_connections(
        self, 
        current_user: User,
        connection_type: Optional[ConnectionType] = None,
        status: Optional[ConnectionStatus] = None
    ) -> List[Connection]:
        """Get all connections for the current user."""
        return self.repository.get_user_connections(
            current_user.user_id, connection_type, status
        )
    
    def get_connection(self, connection_id: int, current_user: User) -> Connection:
        """Get a specific connection by ID."""
        connection = self.repository.get_connection_by_id(connection_id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Check if user is part of the connection
        if not self._user_has_connection_access(connection, current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this connection"
            )
        
        return connection
    
    def update_connection(
        self, 
        connection_id: int, 
        connection_update: ConnectionUpdate, 
        current_user: User
    ) -> Connection:
        """Update a connection."""
        connection = self.repository.get_connection_by_id(connection_id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Check if user is part of the connection
        if not self._user_has_connection_access(connection, current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this connection"
            )
        
        update_data = {}
        
        # Only the initiator can change the connection type
        if connection_update.connection_type is not None:
            if connection.user_a_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the connection initiator can change the connection type"
                )
            update_data["connection_type"] = connection_update.connection_type
        
        # Status can be updated by either user with specific rules
        if connection_update.status is not None:
            # If accepting a connection, only the recipient can do it
            if (connection_update.status == ConnectionStatus.ACCEPTED and 
                connection.user_b_id != current_user.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the connection recipient can accept the connection"
                )
            update_data["status"] = connection_update.status
        
        return self.repository.update_connection(connection, update_data)
    
    def delete_connection(self, connection_id: int, current_user: User) -> None:
        """Delete a connection."""
        connection = self.repository.get_connection_by_id(connection_id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Check if user is part of the connection
        if not self._user_has_connection_access(connection, current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this connection"
            )
        
        self.repository.delete_connection(connection)
    
    def _user_has_connection_access(self, connection: Connection, user_id: int) -> bool:
        """Check if user has access to a connection."""
        return connection.user_a_id == user_id or connection.user_b_id == user_id
