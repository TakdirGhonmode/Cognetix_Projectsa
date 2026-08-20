from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
import auth
from dependencies import get_current_user
import models

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.APIResponse[schemas.UserResponse])
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user account (role can be 'user' or 'admin')."""
    existing_user = crud.get_user_by_username(db, username=user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' is already registered."
        )

    new_user = crud.create_user(db, user_data)
    user_resp = schemas.UserResponse.model_validate(new_user)

    return schemas.APIResponse(
        status="success",
        message="User registered successfully",
        data=user_resp
    )


@router.post("/login", response_model=schemas.APIResponse[schemas.TokenResponse])
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user credentials and generate a JWT access token."""
    user = crud.authenticate_user(db, username=login_data.username, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id}
    )

    token_data = schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username
    )

    return schemas.APIResponse(
        status="success",
        message="Login successful",
        data=token_data
    )


@router.get("/me", response_model=schemas.APIResponse[schemas.UserResponse])
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    """Retrieve profile details of the currently authenticated user."""
    user_resp = schemas.UserResponse.model_validate(current_user)
    return schemas.APIResponse(
        status="success",
        message="User profile retrieved successfully",
        data=user_resp
    )
