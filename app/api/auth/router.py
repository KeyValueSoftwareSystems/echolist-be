from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import Token, UserCreate, UserResponse
from app.api.auth.service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)
    return auth_service.register_user(user.username, user.email, user.password)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token."""
    auth_service = AuthService(db)
    return auth_service.authenticate_user(form_data.username, form_data.password)
