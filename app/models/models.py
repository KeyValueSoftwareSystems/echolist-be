from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    Enum, Text, LargeBinary, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

from app.db.database import Base

class ConnectionType(str, enum.Enum):
    FAMILY = "Family"
    FRIEND = "Friend"
    COLLEAGUE = "Colleague"

class ConnectionStatus(str, enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"

class Priority(str, enum.Enum):
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    avatar_url = Column(String, nullable=True)
    voice_speed_setting = Column(Integer, default=100, nullable=False)  # percentage
    contrast_setting = Column(String, default="normal", nullable=False)
    confirmation_nudges_setting = Column(Boolean, default=True, nullable=False)
    daily_streak_count = Column(Integer, default=0, nullable=False)
    last_summary_date = Column(DateTime, nullable=True)

    # Relationships
    owned_sections = relationship("Section", back_populates="owner")
    created_items = relationship("Item", foreign_keys="Item.creator_user_id", back_populates="creator")
    modified_items = relationship("Item", foreign_keys="Item.last_modified_by_user_id", back_populates="last_modifier")
    
    # Self-referential many-to-many relationship for connections
    outgoing_connections = relationship(
        "Connection", 
        foreign_keys="Connection.user_a_id", 
        back_populates="user_a"
    )
    incoming_connections = relationship(
        "Connection", 
        foreign_keys="Connection.user_b_id", 
        back_populates="user_b"
    )

class Connection(Base):
    __tablename__ = "connections"

    connection_id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    connection_type = Column(Enum(ConnectionType), nullable=False)
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user_a = relationship("User", foreign_keys=[user_a_id], back_populates="outgoing_connections")
    user_b = relationship("User", foreign_keys=[user_b_id], back_populates="incoming_connections")

    # Ensure no duplicate connections
    __table_args__ = (
        UniqueConstraint('user_a_id', 'user_b_id', name='unique_connection'),
    )

class Section(Base):
    __tablename__ = "sections"

    section_id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    section_name = Column(String, nullable=False)
    display_color = Column(String, default="#808080", nullable=False)  # Default gray color
    is_template = Column(Boolean, default=False, nullable=False)
    template_description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="owned_sections")
    items = relationship("Item", back_populates="section", cascade="all, delete-orphan")
    access_rules = relationship("SectionAccess", back_populates="section", cascade="all, delete-orphan")

class SectionAccess(Base):
    __tablename__ = "section_access"

    section_access_id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.section_id"), nullable=False)
    allowed_connection_type = Column(Enum(ConnectionType), nullable=False)
    can_view = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)

    # Relationships
    section = relationship("Section", back_populates="access_rules")

    # Ensure no duplicate access rules for the same section and connection type
    __table_args__ = (
        UniqueConstraint('section_id', 'allowed_connection_type', name='unique_section_access'),
    )

class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.section_id"), nullable=False)
    creator_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    is_task = Column(Boolean, default=False, nullable=False)
    due_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)
    vector_embedding = Column(LargeBinary, nullable=True)  # Store as binary for flexibility
    original_audio_url = Column(String, nullable=True)
    last_modified_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    last_modified_at = Column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    section = relationship("Section", back_populates="items")
    creator = relationship("User", foreign_keys=[creator_user_id], back_populates="created_items")
    last_modifier = relationship("User", foreign_keys=[last_modified_by_user_id], back_populates="modified_items")
