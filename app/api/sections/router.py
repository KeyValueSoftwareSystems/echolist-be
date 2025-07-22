from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import User, Section, SectionAccess, Connection, ConnectionType
from app.schemas.schemas import SectionCreate, SectionResponse, SectionUpdate, SectionAccessCreate, SectionAccessResponse
from app.core.security import get_current_active_user

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
    # Create new section
    db_section = Section(
        owner_user_id=current_user.user_id,
        section_name=section.section_name,
        display_color=section.display_color,
        is_template=section.is_template,
        template_description=section.template_description
    )
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    
    return db_section

@router.get("/", response_model=List[SectionResponse])
def get_sections(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all sections owned by the current user."""
    return db.query(Section).filter(Section.owner_user_id == current_user.user_id).all()

@router.get("/{section_id}", response_model=SectionResponse)
def get_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific section by ID."""
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Check if user is the owner or has access
    if section.owner_user_id != current_user.user_id:
        # Check if user has access through connections
        connections = db.query(Connection).filter(
            ((Connection.user_a_id == section.owner_user_id) & 
             (Connection.user_b_id == current_user.user_id)) |
            ((Connection.user_a_id == current_user.user_id) & 
             (Connection.user_b_id == section.owner_user_id))
        ).all()
        
        has_access = False
        for conn in connections:
            # Get the connection type
            conn_type = conn.connection_type
            
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == section_id,
                SectionAccess.allowed_connection_type == conn_type
            ).first()
            
            if access_rule and access_rule.can_view:
                has_access = True
                break
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this section"
            )
    
    return section

@router.put("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int,
    section_update: SectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a section."""
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Check if user is the owner
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
                detail="Not authorized to edit this section"
            )
    
    # Update section fields if provided
    if section_update.section_name is not None:
        section.section_name = section_update.section_name
    
    if section_update.display_color is not None:
        section.display_color = section_update.display_color
    
    if section_update.template_description is not None:
        section.template_description = section_update.template_description
    
    db.commit()
    db.refresh(section)
    return section

@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a section."""
    section = db.query(Section).filter(Section.section_id == section_id).first()
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
    
    db.delete(section)
    db.commit()
    return None

@router.post("/access", response_model=SectionAccessResponse)
def create_section_access(
    access: SectionAccessCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create or update access rules for a section."""
    section = db.query(Section).filter(Section.section_id == access.section_id).first()
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
    existing_rule = db.query(SectionAccess).filter(
        SectionAccess.section_id == access.section_id,
        SectionAccess.allowed_connection_type == access.allowed_connection_type
    ).first()
    
    if existing_rule:
        # Update existing rule
        existing_rule.can_view = access.can_view
        existing_rule.can_edit = access.can_edit
        db.commit()
        db.refresh(existing_rule)
        return existing_rule
    else:
        # Create new access rule
        db_access = SectionAccess(
            section_id=access.section_id,
            allowed_connection_type=access.allowed_connection_type,
            can_view=access.can_view,
            can_edit=access.can_edit
        )
        db.add(db_access)
        db.commit()
        db.refresh(db_access)
        return db_access

@router.get("/{section_id}/access", response_model=List[SectionAccessResponse])
def get_section_access(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get access rules for a section."""
    section = db.query(Section).filter(Section.section_id == section_id).first()
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
    
    return db.query(SectionAccess).filter(SectionAccess.section_id == section_id).all()
