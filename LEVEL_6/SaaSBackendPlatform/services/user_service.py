from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from models.user import User
from schemas.user import UserUpdate

class UserService:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user: User, update_data: UserUpdate) -> User:
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.email is not None and update_data.email != user.email:
            existing = db.query(User).filter(User.email == update_data.email).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")
            user.email = update_data.email
        db.commit()
        db.refresh(user)
        return user
