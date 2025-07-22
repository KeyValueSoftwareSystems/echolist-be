from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import User, ConnectionStatus, ConnectionType
from app.schemas.schemas import ConnectionCreate, ConnectionResponse, ConnectionUpdate
from app.core.security import get_current_active_user
from app.api.connections.service import ConnectionService

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
    service = ConnectionService(db)
    return service.create_connection(connection, current_user)

@router.get("/", response_model=List[ConnectionResponse])
def get_connections(
    connection_type: ConnectionType = None,
    status: ConnectionStatus = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all connections for the current user."""
    service = ConnectionService(db)
    return service.get_connections(current_user, connection_type, status)

@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(
    connection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific connection by ID."""
    service = ConnectionService(db)
    return service.get_connection(connection_id, current_user)

@router.put("/{connection_id}", response_model=ConnectionResponse)
def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a connection."""
    service = ConnectionService(db)
    return service.update_connection(connection_id, connection_update, current_user)

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a connection."""
    service = ConnectionService(db)
    service.delete_connection(connection_id, current_user)
    return None
