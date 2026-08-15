from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.user import UserResponse, UserUpdate
from services.user_service import UserService
from auth.dependencies import get_current_active_user, get_current_superadmin
from models.user import User

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("", response_model=StandardResponse[List[UserResponse]])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_superadmin)
):
    """Superadmin only endpoint to list all users."""
    users = UserService.list_users(db, skip, limit)
    return StandardResponse(
        success=True,
        message="Users retrieved successfully",
        data=users
    )

@router.get("/{user_id}", response_model=StandardResponse[UserResponse])
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve user details by ID."""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return StandardResponse(
        success=True,
        message="User details retrieved successfully",
        data=user
    )

@router.put("/me", response_model=StandardResponse[UserResponse])
def update_current_user_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update profile information of current user."""
    updated = UserService.update_user(db, current_user, update_data)
    return StandardResponse(
        success=True,
        message="User profile updated successfully",
        data=updated
    )
