from requests import get
from fastapi import HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.models import User, Item, Section, Connection, SectionAccess
from app.schemas.schemas import ItemCreate, ItemUpdate
from app.api.items.repository import ItemRepository
from app.api.ai.service import get_ai_service
from app.services.vector_service import create_embedding


class ItemService:
    """Service layer for item operations."""
    
    def __init__(self, db: Session):
        self.repository = ItemRepository(db)
    
    async def create_item(self, item: ItemCreate, current_user: User):
        """Create a new item in a section."""
        # Check if section exists
        section = self.repository.get_section_by_id(item.section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user has access to create items in this section
        if section.owner_user_id != current_user.user_id:
            # Check if user has edit access through connections
            connections = self.repository.get_connections_between_users(
                section.owner_user_id, current_user.user_id
            )
            
            has_edit_access = False
            for conn in connections:
                # Get the connection type
                conn_type = conn.connection_type
                
                # Check if there's an access rule for this connection type
                access_rule = self.repository.get_section_access_rule(
                    item.section_id, conn_type
                )
                
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
        item_data = {
            "section_id": item.section_id,
            "creator_user_id": current_user.user_id,
            "content_text": item.content_text,
            "is_task": item.is_task,
            "due_date": item.due_date,
            "priority": item.priority,
            "vector_embedding": vector_embedding,
            "last_modified_by_user_id": current_user.user_id,
            "last_modified_at": datetime.utcnow()
        }
        
        return self.repository.create_item(item_data)
    
    async def create_voice_item(
        self, 
        audio_file: UploadFile, 
        current_user: User
    ):
        """Create a new item from voice input.
        
        This method transcribes the audio file to text and creates a new item.
        The system automatically determines the appropriate section for the item.
        """
        from app.services.audio_service import transcribe_audio
        
        # Read the audio file content
        audio_content = await audio_file.read()
        
        # Transcribe the audio to text
        try:
            content_text = transcribe_audio(audio_content)
        except Exception as e:
            # If transcription fails, use a placeholder
            content_text = f"Voice note: {audio_file.filename} (Transcription failed: {str(e)})"
        
        # Store in vector database with metadata
        metadata = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "item_type": "voice_note"
        }

        try:
            ai_service = get_ai_service()
            vector_embedding = ai_service.vectorize_and_store(content_text, metadata)
        except Exception as e:
            print("Error vectorizing voice note:", e)
            vector_embedding = None

        # Find the user's default section or create one if it doesn't exist
        # default_sections = self.repository.db.query(Section).filter(
        #     Section.owner_user_id == current_user.user_id,
        #     Section.section_name == "Voice Notes"
        # ).all()
        
        # if not default_sections:
        #     # Create a default section for voice notes
        #     default_section = Section(
        #         owner_user_id=current_user.user_id,
        #         section_name="Voice Notes",
        #         display_color="#4A90E2",  # Blue color
        #         is_template=False
        #     )
        #     self.repository.db.add(default_section)
        #     self.repository.db.commit()
        #     self.repository.db.refresh(default_section)
        #     section_id = default_section.section_id
        # else:
        #     section_id = default_sections[0].section_id
        item_data = {
            "section_id": vector_embedding['classification']['section_id'] or 1,
            "creator_user_id": current_user.user_id,
            "content_text": content_text,
            "is_task": False,
            "due_date": None,
            "priority": "Medium",
            "vector_embedding": vector_embedding,
            "last_modified_by_user_id": current_user.user_id,
            "last_modified_at": datetime.utcnow()
        }
        return self.repository.create_item(item_data)
        
    
    def get_items_by_section(self, section_id: int, current_user: User):
        """Get all items in a section."""
        # Check if section exists
        section = self.repository.get_section_by_id(section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user has access to view items in this section
        if section.owner_user_id != current_user.user_id:
            # Check if user has view access through connections
            connections = self.repository.get_connections_between_users(
                section.owner_user_id, current_user.user_id
            )
            
            has_view_access = False
            for conn in connections:
                # Get the connection type
                conn_type = conn.connection_type
                
                # Check if there's an access rule for this connection type
                access_rule = self.repository.get_section_access_rule(
                    section_id, conn_type
                )
                
                if access_rule and access_rule.can_view:
                    has_view_access = True
                    break
            
            if not has_view_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view items in this section"
                )
        
        return self.repository.get_items_by_section_id(section_id)
    
    def get_item(self, item_id: int, current_user: User):
        """Get a specific item by ID."""
        # Get the item
        item = self.repository.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Get the section for this item
        section = self.repository.get_section_by_id(item.section_id)
        
        # Check if user has access to view this item
        if section.owner_user_id != current_user.user_id:
            # Check if user has view access through connections
            connections = self.repository.get_connections_between_users(
                section.owner_user_id, current_user.user_id
            )
            
            has_view_access = False
            for conn in connections:
                # Get the connection type
                conn_type = conn.connection_type
                
                # Check if there's an access rule for this connection type
                access_rule = self.repository.get_section_access_rule(
                    item.section_id, conn_type
                )
                
                if access_rule and access_rule.can_view:
                    has_view_access = True
                    break
            
            if not has_view_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this item"
                )
        
        return item
    
    async def update_item(self, item_id: int, item_update: ItemUpdate, current_user: User):
        """Update an item."""
        # Get the item
        item = self.repository.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Get the section for this item
        section = self.repository.get_section_by_id(item.section_id)
        
        # Check if user has access to edit this item
        if section.owner_user_id != current_user.user_id and item.creator_user_id != current_user.user_id:
            # Check if user has edit access through connections
            connections = self.repository.get_connections_between_users(
                section.owner_user_id, current_user.user_id
            )
            
            has_edit_access = False
            for conn in connections:
                # Get the connection type
                conn_type = conn.connection_type
                
                # Check if there's an access rule for this connection type
                access_rule = self.repository.get_section_access_rule(
                    item.section_id, conn_type
                )
                
                if access_rule and access_rule.can_edit:
                    has_edit_access = True
                    break
            
            if not has_edit_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to edit this item"
                )
        
        # Prepare update data
        update_data = {
            "content_text": item_update.content_text,
            "is_task": item_update.is_task,
            "due_date": item_update.due_date,
            "is_completed": item_update.is_completed,
            "priority": item_update.priority,
            "last_modified_by_user_id": current_user.user_id,
            "last_modified_at": datetime.utcnow()
        }
        
        # Update vector embedding if content changed
        if item_update.content_text is not None:
            update_data["vector_embedding"] = await create_embedding(item_update.content_text)
        
        return self.repository.update_item(item, update_data)
    
    def delete_item(self, item_id: int, current_user: User):
        """Delete an item."""
        # Get the item
        item = self.repository.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Get the section for this item
        section = self.repository.get_section_by_id(item.section_id)
        
        # Check if user has access to delete this item
        if section.owner_user_id != current_user.user_id and item.creator_user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this item"
            )
        
        self.repository.delete_item(item)
