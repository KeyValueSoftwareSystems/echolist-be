from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import User, Connection, ConnectionStatus, ConnectionType
from app.schemas.schemas import ConnectionCreate, ConnectionResponse, ConnectionUpdate
from app.core.security import get_current_active_user

router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ConnectionResponse)
def create_connection(
    connection: ConnectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new connection with another user."""
    # Check if target user exists
    target_user = db.query(User).filter(User.user_id == connection.user_b_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found"
        )
    
    # Check if connection already exists
    existing_connection = db.query(Connection).filter(
        ((Connection.user_a_id == current_user.user_id) & 
         (Connection.user_b_id == connection.user_b_id)) |
        ((Connection.user_a_id == connection.user_b_id) & 
         (Connection.user_b_id == current_user.user_id))
    ).first()
    
    if existing_connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection already exists"
        )
    
    # Create new connection
    db_connection = Connection(
        user_a_id=current_user.user_id,
        user_b_id=connection.user_b_id,
        connection_type=connection.connection_type,
        status=ConnectionStatus.PENDING
    )
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    
    return db_connection

@router.get("/", response_model=List[ConnectionResponse])
def get_connections(
    connection_type: ConnectionType = None,
    status: ConnectionStatus = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all connections for the current user."""
    query = db.query(Connection).filter(
        (Connection.user_a_id == current_user.user_id) | 
        (Connection.user_b_id == current_user.user_id)
    )
    
    # Apply filters if provided
    if connection_type:
        query = query.filter(Connection.connection_type == connection_type)
    
    if status:
        query = query.filter(Connection.status == status)
    
    return query.all()

@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(
    connection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific connection by ID."""
    connection = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Check if user is part of the connection
    if connection.user_a_id != current_user.user_id and connection.user_b_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this connection"
        )
    
    return connection

@router.put("/{connection_id}", response_model=ConnectionResponse)
def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a connection."""
    connection = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Check if user is part of the connection
    if connection.user_a_id != current_user.user_id and connection.user_b_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this connection"
        )
    
    # Only the initiator can change the connection type
    if connection_update.connection_type is not None:
        if connection.user_a_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the connection initiator can change the connection type"
            )
        connection.connection_type = connection_update.connection_type
    
    # Status can be updated by either user
    if connection_update.status is not None:
        # If accepting a connection, only the recipient can do it
        if connection_update.status == ConnectionStatus.ACCEPTED and connection.user_b_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the connection recipient can accept the connection"
            )
        connection.status = connection_update.status
    
    db.commit()
    db.refresh(connection)
    return connection

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a connection."""
    connection = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Check if user is part of the connection
    if connection.user_a_id != current_user.user_id and connection.user_b_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this connection"
        )
    
    db.delete(connection)
    db.commit()
    return None
