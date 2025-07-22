from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.models import User, Section, SectionAccess, ConnectionType
from app.schemas.schemas import SectionCreate, SectionUpdate, SectionAccessCreate
from app.api.sections.repository import SectionRepository


class SectionService:
    """Service layer for section operations."""
    
    def __init__(self, db: Session):
        self.repository = SectionRepository(db)
    
    def create_section(self, section: SectionCreate, current_user: User):
        """Create a new section."""
        section_data = {
            "owner_user_id": current_user.user_id,
            "section_name": section.section_name,
            "display_color": section.display_color,
            "is_template": section.is_template,
            "template_description": section.template_description
        }
        
        return self.repository.create_section(section_data)
    
    def get_sections(self, current_user: User):
        """Get all sections owned by the current user."""
        return self.repository.get_sections_by_owner(current_user.user_id)
    
    def get_section(self, section_id: int, current_user: User):
        """Get a specific section by ID."""
        section = self.repository.get_section_by_id(section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user is the owner or has access
        if section.owner_user_id != current_user.user_id:
            if not self._has_section_access(section_id, section.owner_user_id, current_user.user_id, "view"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this section"
                )
        
        return section
    
    def update_section(self, section_id: int, section_update: SectionUpdate, current_user: User):
        """Update a section."""
        section = self.repository.get_section_by_id(section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user is the owner or has edit access
        if section.owner_user_id != current_user.user_id:
            if not self._has_section_access(section_id, section.owner_user_id, current_user.user_id, "edit"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to edit this section"
                )
        
        # Prepare update data
        update_data = {
            "section_name": section_update.section_name,
            "display_color": section_update.display_color,
            "template_description": section_update.template_description
        }
        
        return self.repository.update_section(section, update_data)
    
    def delete_section(self, section_id: int, current_user: User):
        """Delete a section."""
        section = self.repository.get_section_by_id(section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user is the owner
        if section.owner_user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this section"
            )
        
        self.repository.delete_section(section)
    
    def create_section_access(self, access: SectionAccessCreate, current_user: User):
        """Create or update access rules for a section."""
        section = self.repository.get_section_by_id(access.section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user is the owner
        if section.owner_user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify access rules for this section"
            )
        
        # Check if access rule already exists
        existing_rule = self.repository.get_existing_section_access(
            access.section_id, access.allowed_connection_type
        )
        
        if existing_rule:
            # Update existing rule
            update_data = {
                "can_view": access.can_view,
                "can_edit": access.can_edit
            }
            return self.repository.update_section_access(existing_rule, update_data)
        else:
            # Create new access rule
            access_data = {
                "section_id": access.section_id,
                "allowed_connection_type": access.allowed_connection_type,
                "can_view": access.can_view,
                "can_edit": access.can_edit
            }
            return self.repository.create_section_access(access_data)
    
    def get_section_access(self, section_id: int, current_user: User):
        """Get access rules for a section."""
        section = self.repository.get_section_by_id(section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user is the owner
        if section.owner_user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view access rules for this section"
            )
        
        return self.repository.get_section_access_rules(section_id)
    
    def _has_section_access(self, section_id: int, owner_user_id: int, current_user_id: int, access_type: str) -> bool:
        """Check if user has access to a section through connections."""
        connections = self.repository.get_connections_between_users(owner_user_id, current_user_id)
        
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = self.repository.get_section_access_rule(section_id, conn_type)
            
            if access_rule:
                if access_type == "view" and access_rule.can_view:
                    return True
                elif access_type == "edit" and access_rule.can_edit:
                    return True
        
        return False
