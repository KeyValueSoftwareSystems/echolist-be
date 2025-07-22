from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.models import Section, SectionAccess, Connection, ConnectionType


class SectionRepository:
    """Repository layer for section operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_section(self, section_data: dict):
        """Create a new section."""
        db_section = Section(**section_data)
        self.db.add(db_section)
        self.db.commit()
        self.db.refresh(db_section)
        return db_section
    
    def get_sections_by_owner(self, owner_user_id: int):
        """Get all sections owned by a user."""
        return self.db.query(Section).filter(Section.owner_user_id == owner_user_id).all()
    
    def get_section_by_id(self, section_id: int):
        """Get a section by its ID."""
        return self.db.query(Section).filter(Section.section_id == section_id).first()
    
    def update_section(self, section: Section, update_data: dict):
        """Update a section with the provided data."""
        for key, value in update_data.items():
            if value is not None:  # Only update fields that are provided
                setattr(section, key, value)
        
        self.db.commit()
        self.db.refresh(section)
        return section
    
    def delete_section(self, section: Section):
        """Delete a section."""
        self.db.delete(section)
        self.db.commit()
    
    def get_connections_between_users(self, user_a_id: int, user_b_id: int):
        """Get connections between two users."""
        return self.db.query(Connection).filter(
            ((Connection.user_a_id == user_a_id) & 
             (Connection.user_b_id == user_b_id)) |
            ((Connection.user_a_id == user_b_id) & 
             (Connection.user_b_id == user_a_id))
        ).all()
    
    def get_section_access_rule(self, section_id: int, connection_type: ConnectionType):
        """Get section access rule for a specific connection type."""
        return self.db.query(SectionAccess).filter(
            SectionAccess.section_id == section_id,
            SectionAccess.allowed_connection_type == connection_type
        ).first()
    
    def create_section_access(self, access_data: dict):
        """Create a new section access rule."""
        db_access = SectionAccess(**access_data)
        self.db.add(db_access)
        self.db.commit()
        self.db.refresh(db_access)
        return db_access
    
    def get_existing_section_access(self, section_id: int, connection_type: ConnectionType):
        """Get existing section access rule."""
        return self.db.query(SectionAccess).filter(
            SectionAccess.section_id == section_id,
            SectionAccess.allowed_connection_type == connection_type
        ).first()
    
    def update_section_access(self, access_rule: SectionAccess, update_data: dict):
        """Update a section access rule."""
        for key, value in update_data.items():
            if value is not None:
                setattr(access_rule, key, value)
        
        self.db.commit()
        self.db.refresh(access_rule)
        return access_rule
    
    def get_section_access_rules(self, section_id: int):
        """Get all access rules for a section."""
        return self.db.query(SectionAccess).filter(SectionAccess.section_id == section_id).all()
