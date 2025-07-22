from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.models import Item, Section, SectionAccess, Connection


class ItemRepository:
    """Repository layer for item operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_section_by_id(self, section_id: int):
        """Get a section by its ID."""
        return self.db.query(Section).filter(Section.section_id == section_id).first()
    
    def get_connections_between_users(self, user_a_id: int, user_b_id: int):
        """Get connections between two users."""
        return self.db.query(Connection).filter(
            ((Connection.user_a_id == user_a_id) & 
             (Connection.user_b_id == user_b_id)) |
            ((Connection.user_a_id == user_b_id) & 
             (Connection.user_b_id == user_a_id))
        ).all()
    
    def get_section_access_rule(self, section_id: int, connection_type: str):
        """Get section access rule for a specific connection type."""
        return self.db.query(SectionAccess).filter(
            SectionAccess.section_id == section_id,
            SectionAccess.allowed_connection_type == connection_type
        ).first()
    
    def create_item(self, item_data: dict):
        """Create a new item."""
        db_item = Item(**item_data)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def get_items_by_section_id(self, section_id: int):
        """Get all items in a section."""
        return self.db.query(Item).filter(Item.section_id == section_id).all()
    
    def get_item_by_id(self, item_id: int):
        """Get an item by its ID."""
        return self.db.query(Item).filter(Item.item_id == item_id).first()
    
    def update_item(self, item: Item, update_data: dict):
        """Update an item with the provided data."""
        for key, value in update_data.items():
            if value is not None:  # Only update fields that are provided
                setattr(item, key, value)
        
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def delete_item(self, item: Item):
        """Delete an item."""
        self.db.delete(item)
        self.db.commit()
