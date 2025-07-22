from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List
from datetime import datetime, date

from app.db.database import get_db
from app.models.models import User, Item, Section, SectionAccess, Connection
from app.schemas.schemas import HomeResponse, HomeItemResponse
from app.core.security import get_current_active_user

router = APIRouter(
    prefix="/home",
    tags=["home"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=HomeResponse)
def get_home_screen(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the home screen with today's important tasks and reminders."""
    today = date.today()
    
    # Get all sections the user owns
    owned_sections = db.query(Section).filter(Section.owner_user_id == current_user.user_id).all()
    owned_section_ids = [section.section_id for section in owned_sections]
    
    # Get all sections the user has access to through connections
    accessible_section_ids = []
    
    # Get all connections where the user is involved
    connections = db.query(Connection).filter(
        or_(
            Connection.user_a_id == current_user.user_id,
            Connection.user_b_id == current_user.user_id
        )
    ).all()
    
    for connection in connections:
        # Determine the other user in the connection
        other_user_id = connection.user_b_id if connection.user_a_id == current_user.user_id else connection.user_a_id
        
        # Get sections owned by the other user
        other_user_sections = db.query(Section).filter(Section.owner_user_id == other_user_id).all()
        
        for section in other_user_sections:
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == section.section_id,
                SectionAccess.allowed_connection_type == connection.connection_type,
                SectionAccess.can_view == True
            ).first()
            
            if access_rule:
                accessible_section_ids.append(section.section_id)
    
    # Combine owned and accessible section IDs
    all_accessible_section_ids = owned_section_ids + accessible_section_ids
    
    # Query for urgent items (due today or overdue, not completed)
    urgent_items_query = db.query(
        Item, Section.section_name, Section.display_color
    ).join(
        Section, Item.section_id == Section.section_id
    ).filter(
        Item.section_id.in_(all_accessible_section_ids),
        Item.is_task == True,
        Item.is_completed == False,
        Item.due_date <= datetime.combine(today, datetime.min.time()),
        Item.priority.in_(["Urgent", "High"])
    ).order_by(
        Item.due_date, Item.priority
    )
    
    # Query for today's items (due today, not completed, not urgent)
    today_items_query = db.query(
        Item, Section.section_name, Section.display_color
    ).join(
        Section, Item.section_id == Section.section_id
    ).filter(
        Item.section_id.in_(all_accessible_section_ids),
        Item.is_task == True,
        Item.is_completed == False,
        func.date(Item.due_date) == today,
        Item.priority.in_(["Medium", "Low"])
    ).order_by(
        Item.priority
    )
    
    # Query for recently completed items
    completed_items_query = db.query(
        Item, Section.section_name, Section.display_color
    ).join(
        Section, Item.section_id == Section.section_id
    ).filter(
        Item.section_id.in_(all_accessible_section_ids),
        Item.is_task == True,
        Item.is_completed == True,
        func.date(Item.last_modified_at) == today
    ).order_by(
        Item.last_modified_at.desc()
    ).limit(5)
    
    # Convert query results to HomeItemResponse objects
    urgent_items = []
    for item, section_name, display_color in urgent_items_query.all():
        urgent_items.append(HomeItemResponse(
            **item.__dict__,
            section_name=section_name,
            section_color=display_color
        ))
    
    today_items = []
    for item, section_name, display_color in today_items_query.all():
        today_items.append(HomeItemResponse(
            **item.__dict__,
            section_name=section_name,
            section_color=display_color
        ))
    
    completed_items = []
    for item, section_name, display_color in completed_items_query.all():
        completed_items.append(HomeItemResponse(
            **item.__dict__,
            section_name=section_name,
            section_color=display_color
        ))
    
    return HomeResponse(
        urgent_items=urgent_items,
        today_items=today_items,
        completed_items=completed_items
    )

@router.get("/search", response_model=List[HomeItemResponse])
async def search_items(
    query: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for items using natural language."""
    from app.services.vector_service import create_embedding, get_embedding_from_bytes, calculate_similarity
    
    # Create embedding for the search query
    query_embedding = await create_embedding(query)
    query_embedding_np = await get_embedding_from_bytes(query_embedding)
    
    # Get all sections the user owns
    owned_sections = db.query(Section).filter(Section.owner_user_id == current_user.user_id).all()
    owned_section_ids = [section.section_id for section in owned_sections]
    
    # Get all sections the user has access to through connections
    accessible_section_ids = []
    
    # Get all connections where the user is involved
    connections = db.query(Connection).filter(
        or_(
            Connection.user_a_id == current_user.user_id,
            Connection.user_b_id == current_user.user_id
        )
    ).all()
    
    for connection in connections:
        # Determine the other user in the connection
        other_user_id = connection.user_b_id if connection.user_a_id == current_user.user_id else connection.user_a_id
        
        # Get sections owned by the other user
        other_user_sections = db.query(Section).filter(Section.owner_user_id == other_user_id).all()
        
        for section in other_user_sections:
            # Check if there's an access rule for this connection type
            access_rule = db.query(SectionAccess).filter(
                SectionAccess.section_id == section.section_id,
                SectionAccess.allowed_connection_type == connection.connection_type,
                SectionAccess.can_view == True
            ).first()
            
            if access_rule:
                accessible_section_ids.append(section.section_id)
    
    # Combine owned and accessible section IDs
    all_accessible_section_ids = owned_section_ids + accessible_section_ids
    
    # Get all items from accessible sections
    items_with_sections = db.query(
        Item, Section.section_name, Section.display_color
    ).join(
        Section, Item.section_id == Section.section_id
    ).filter(
        Item.section_id.in_(all_accessible_section_ids)
    ).all()
    
    # Calculate similarity scores
    results = []
    for item, section_name, display_color in items_with_sections:
        if item.vector_embedding:
            item_embedding = await get_embedding_from_bytes(item.vector_embedding)
            similarity = await calculate_similarity(query_embedding_np, item_embedding)
            
            if similarity > 0.5:  # Threshold for relevance
                results.append((
                    HomeItemResponse(
                        **item.__dict__,
                        section_name=section_name,
                        section_color=display_color
                    ),
                    similarity
                ))
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Return top 10 results
    return [item for item, _ in results[:10]]
