from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.auth import UserRegister, UserLogin, Token, TokenRefreshRequest
from schemas.user import UserResponse
from services.auth_service import AuthService
from auth.dependencies import get_current_active_user
from models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """User Registration API endpoint."""
    user = AuthService.register_user(db, user_data)
    return StandardResponse(
        success=True,
        message="User registered successfully",
        data=user
    )

@router.post("/login", response_model=StandardResponse[Token])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """JSON-body login endpoint for JWT token generation."""
    tokens = AuthService.authenticate_user(db, login_data)
    return StandardResponse(
        success=True,
        message="Login successful",
        data=tokens
    )

@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 standard form-data login endpoint for FastAPI Swagger UI test convenience."""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    return AuthService.authenticate_user(db, login_data)

@router.post("/refresh", response_model=StandardResponse[Token])
def refresh_token(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh JWT access token using a valid refresh token."""
    tokens = AuthService.refresh_access_token(db, req.refresh_token)
    return StandardResponse(
        success=True,
        message="Access token refreshed successfully",
        data=tokens
    )

@router.get("/me", response_model=StandardResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_active_user)):
    """Retrieve profile of currently authenticated user."""
    return StandardResponse(
        success=True,
        message="User profile retrieved successfully",
        data=current_user
    )
