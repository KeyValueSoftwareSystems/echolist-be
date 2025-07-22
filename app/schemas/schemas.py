from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum

# Enums
class ConnectionType(str, Enum):
    FAMILY = "Family"
    FRIEND = "Friend"
    COLLEAGUE = "Colleague"

class ConnectionStatus(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"

class Priority(str, Enum):
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    voice_speed_setting: Optional[int] = None
    contrast_setting: Optional[str] = None
    confirmation_nudges_setting: Optional[bool] = None

class UserSettings(BaseModel):
    voice_speed_setting: int = 100
    contrast_setting: str = "normal"
    confirmation_nudges_setting: bool = True

class UserResponse(UserBase):
    user_id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    daily_streak_count: int
    
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserAuthResponse(BaseModel):
    id: str
    name: str
    email: str
    token: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None

# Connection Schemas
class ConnectionBase(BaseModel):
    user_b_id: int
    connection_type: ConnectionType

class ConnectionCreate(ConnectionBase):
    pass

class ConnectionUpdate(BaseModel):
    connection_type: Optional[ConnectionType] = None
    status: Optional[ConnectionStatus] = None

class ConnectionResponse(ConnectionBase):
    connection_id: int
    user_a_id: int
    status: ConnectionStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

# Section Schemas
class SectionBase(BaseModel):
    section_name: str
    display_color: Optional[str] = "#808080"
    is_template: bool = False
    template_description: Optional[str] = None

class SectionCreate(SectionBase):
    pass

class SectionUpdate(BaseModel):
    section_name: Optional[str] = None
    display_color: Optional[str] = None
    template_description: Optional[str] = None

class SectionResponse(SectionBase):
    section_id: int
    owner_user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Section Access Schemas
class SectionAccessBase(BaseModel):
    allowed_connection_type: ConnectionType
    can_view: bool = False
    can_edit: bool = False

class SectionAccessCreate(SectionAccessBase):
    section_id: int

class SectionAccessUpdate(BaseModel):
    can_view: Optional[bool] = None
    can_edit: Optional[bool] = None

class SectionAccessResponse(SectionAccessBase):
    section_access_id: int
    section_id: int
    
    class Config:
        from_attributes = True

# Item Schemas
class ItemBase(BaseModel):
    content_text: str
    is_task: bool = False
    due_date: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM

class ItemCreate(ItemBase):
    section_id: int

class ItemUpdate(BaseModel):
    content_text: Optional[str] = None
    is_task: Optional[bool] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    priority: Optional[Priority] = None

class ItemResponse(ItemBase):
    item_id: int
    section_id: int
    creator_user_id: int
    timestamp: datetime
    is_completed: bool
    original_audio_url: Optional[str] = None
    last_modified_by_user_id: Optional[int] = None
    last_modified_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Home Screen Schemas
class HomeItemResponse(ItemResponse):
    section_name: str
    section_color: str

class HomeResponse(BaseModel):
    urgent_items: List[HomeItemResponse]
    today_items: List[HomeItemResponse]
    completed_items: List[HomeItemResponse]
    
    class Config:
        orm_mode = True

# AI Schemas
class TextPayload(BaseModel):
    text: str
    metadata: dict = {}

class VectorizeResponse(BaseModel):
    message: str
    chunks_count: int
    hash_id: str
    classification: Optional[dict] = None

class QueryResult(BaseModel):
    text: str
    metadata: dict
    score: Optional[float] = None

class QueryResponse(BaseModel):
    results: List[QueryResult]
    query: str
    summary: Optional[str] = None

# Text Classification Schemas
class TextClassificationRequest(BaseModel):
    text_to_classify: str

class TextClassificationResponse(BaseModel):
    predicted_section_name: Optional[str]
    confidence_score: Optional[float] = None
    section_id: Optional[int] = None
