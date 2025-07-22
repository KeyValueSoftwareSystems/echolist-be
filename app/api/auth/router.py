from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import Token, UserCreate, UserResponse, LoginRequest
from app.api.auth.service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/signup", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)
    return auth_service.register_user(user.username, user.email, user.password)

@router.post("/signin", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token using email and password."""
    auth_service = AuthService(db)
    return auth_service.authenticate_user(login_data.email, login_data.password)
