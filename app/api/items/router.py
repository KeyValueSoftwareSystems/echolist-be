from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.models import User, Item, Section, SectionAccess, Connection
from app.schemas.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.core.security import get_current_active_user
from app.services.vector_service import create_embedding

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
    # Check if section exists
    section = db.query(Section).filter(Section.section_id == item.section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Check if user has access to create items in this section
    if section.owner_user_id != current_user.user_id:
        # Check if user has edit access through connections
        connections = db.query(Connection).filter(
            ((Connection.user_a_id == section.owner_user_id) & 
             (Connection.user_b_id == current_user.user_id)) |
            ((Connection.user_a_id == current_user.user_id) & 
             (Connection.user_b_id == section.owner_user_id))
        ).all()
        
        has_edit_access = False
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == item.section_id,
                SectionAccess.allowed_connection_type == conn_type
            ).first()
            
            if access_rule and access_rule.can_edit:
                has_edit_access = True
                break
        
        if not has_edit_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create items in this section"
            )
    
    # Create vector embedding for the content
    vector_embedding = await create_embedding(item.content_text)
    
    # Create new item
    db_item = Item(
        section_id=item.section_id,
        creator_user_id=current_user.user_id,
        content_text=item.content_text,
        is_task=item.is_task,
        due_date=item.due_date,
        priority=item.priority,
        vector_embedding=vector_embedding,
        last_modified_by_user_id=current_user.user_id,
        last_modified_at=datetime.utcnow()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item

@router.post("/voice", response_model=ItemResponse)
async def create_voice_item(
    section_id: int = Form(...),
    is_task: bool = Form(False),
    due_date: Optional[datetime] = Form(None),
    priority: str = Form("Medium"),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new item from voice input."""
    # Check if section exists
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Check if user has access to create items in this section
    if section.owner_user_id != current_user.user_id:
        # Check if user has edit access through connections
        connections = db.query(Connection).filter(
            ((Connection.user_a_id == section.owner_user_id) & 
             (Connection.user_b_id == current_user.user_id)) |
            ((Connection.user_a_id == current_user.user_id) & 
             (Connection.user_b_id == section.owner_user_id))
        ).all()
        
        has_edit_access = False
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == section_id,
                SectionAccess.allowed_connection_type == conn_type
            ).first()
            
            if access_rule and access_rule.can_edit:
                has_edit_access = True
                break
        
        if not has_edit_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create items in this section"
            )
    
    # Save audio file
    audio_content = await audio_file.read()
    audio_filename = f"user_{current_user.user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.wav"
    audio_path = f"uploads/audio/{audio_filename}"
    
    # In a real implementation, you would save the file to storage
    # and then use a speech-to-text service to transcribe it
    # For now, we'll simulate this with a placeholder
    
    # Placeholder for speech-to-text transcription
    transcribed_text = "This is a placeholder for transcribed text from voice input"
    
    # Create vector embedding for the content
    vector_embedding = await create_embedding(transcribed_text)
    
    # Create new item
    db_item = Item(
        section_id=section_id,
        creator_user_id=current_user.user_id,
        content_text=transcribed_text,
        is_task=is_task,
        due_date=due_date,
        priority=priority,
        vector_embedding=vector_embedding,
        original_audio_url=audio_path,
        last_modified_by_user_id=current_user.user_id,
        last_modified_at=datetime.utcnow()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item

@router.get("/section/{section_id}", response_model=List[ItemResponse])
def get_items_by_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all items in a section."""
    # Check if section exists
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Check if user has access to view items in this section
    if section.owner_user_id != current_user.user_id:
        # Check if user has view access through connections
        connections = db.query(Connection).filter(
            ((Connection.user_a_id == section.owner_user_id) & 
             (Connection.user_b_id == current_user.user_id)) |
            ((Connection.user_a_id == current_user.user_id) & 
             (Connection.user_b_id == section.owner_user_id))
        ).all()
        
        has_view_access = False
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == section_id,
                SectionAccess.allowed_connection_type == conn_type
            ).first()
            
            if access_rule and access_rule.can_view:
                has_view_access = True
                break
        
        if not has_view_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view items in this section"
            )
    
    return db.query(Item).filter(Item.section_id == section_id).all()

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific item by ID."""
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Get the section for this item
    section = db.query(Section).filter(Section.section_id == item.section_id).first()
    
    # Check if user has access to view this item
    if section.owner_user_id != current_user.user_id:
        # Check if user has view access through connections
        connections = db.query(Connection).filter(
            ((Connection.user_a_id == section.owner_user_id) & 
             (Connection.user_b_id == current_user.user_id)) |
            ((Connection.user_a_id == current_user.user_id) & 
             (Connection.user_b_id == section.owner_user_id))
        ).all()
        
        has_view_access = False
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == item.section_id,
                SectionAccess.allowed_connection_type == conn_type
            ).first()
            
            if access_rule and access_rule.can_view:
                has_view_access = True
                break
        
        if not has_view_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this item"
            )
    
    return item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an item."""
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Get the section for this item
    section = db.query(Section).filter(Section.section_id == item.section_id).first()
    
    # Check if user has access to edit this item
    if section.owner_user_id != current_user.user_id and item.creator_user_id != current_user.user_id:
        # Check if user has edit access through connections
        connections = db.query(Connection).filter(
            ((Connection.user_a_id == section.owner_user_id) & 
             (Connection.user_b_id == current_user.user_id)) |
            ((Connection.user_a_id == current_user.user_id) & 
             (Connection.user_b_id == section.owner_user_id))
        ).all()
        
        has_edit_access = False
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == item.section_id,
                SectionAccess.allowed_connection_type == conn_type
            ).first()
            
            if access_rule and access_rule.can_edit:
                has_edit_access = True
                break
        
        if not has_edit_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this item"
            )
    
    # Update item fields if provided
    if item_update.content_text is not None:
        item.content_text = item_update.content_text
        # Update vector embedding
        item.vector_embedding = await create_embedding(item_update.content_text)
    
    if item_update.is_task is not None:
        item.is_task = item_update.is_task
    
    if item_update.due_date is not None:
        item.due_date = item_update.due_date
    
    if item_update.is_completed is not None:
        item.is_completed = item_update.is_completed
    
    if item_update.priority is not None:
        item.priority = item_update.priority
    
    # Update modification metadata
    item.last_modified_by_user_id = current_user.user_id
    item.last_modified_at = datetime.utcnow()
    
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an item."""
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Get the section for this item
    section = db.query(Section).filter(Section.section_id == item.section_id).first()
    
    # Check if user has access to delete this item
    if section.owner_user_id != current_user.user_id and item.creator_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this item"
        )
    
    db.delete(item)
    db.commit()
    return None
