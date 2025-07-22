from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.core.security import get_current_active_user
from app.api.items.service import ItemService

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new item in a section."""
    item_service = ItemService(db)
    return await item_service.create_item(item, current_user)

@router.post("/voice", response_model=ItemResponse)
async def create_voice_item(
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new item from voice input."""
    item_service = ItemService(db)
    return await item_service.create_voice_item(
        audio_file, current_user
    )

@router.get("/section/{section_id}", response_model=List[ItemResponse])
def get_items_by_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all items in a section."""
    item_service = ItemService(db)
    return item_service.get_items_by_section(section_id, current_user)

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific item by ID."""
    item_service = ItemService(db)
    return item_service.get_item(item_id, current_user)

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an item."""
    item_service = ItemService(db)
    return await item_service.update_item(item_id, item_update, current_user)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an item."""
    item_service = ItemService(db)
    item_service.delete_item(item_id, current_user)
    return None
