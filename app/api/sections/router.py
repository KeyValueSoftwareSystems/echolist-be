from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import SectionCreate, SectionResponse, SectionUpdate, SectionAccessCreate, SectionAccessResponse
from app.core.security import get_current_active_user
from app.api.sections.service import SectionService

router = APIRouter(
    prefix="/sections",
    tags=["sections"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=SectionResponse)
def create_section(
    section: SectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new section."""
    service = SectionService(db)
    return service.create_section(section, current_user)

@router.get("/", response_model=List[SectionResponse])
def get_sections(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all sections owned by the current user."""
    service = SectionService(db)
    return service.get_sections(current_user)

@router.get("/{section_id}", response_model=SectionResponse)
def get_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific section by ID."""
    service = SectionService(db)
    return service.get_section(section_id, current_user)

@router.put("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int,
    section_update: SectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a section."""
    service = SectionService(db)
    return service.update_section(section_id, section_update, current_user)

@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a section."""
    service = SectionService(db)
    service.delete_section(section_id, current_user)
    return None

@router.post("/access", response_model=SectionAccessResponse)
def create_section_access(
    access: SectionAccessCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create or update access rules for a section."""
    service = SectionService(db)
    return service.create_section_access(access, current_user)

@router.get("/{section_id}/access", response_model=List[SectionAccessResponse])
def get_section_access(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get access rules for a section."""
    service = SectionService(db)
    return service.get_section_access(section_id, current_user)
