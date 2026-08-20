from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from schemas.auth import UserRegister, UserLogin, Token
from auth.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered"
            )
        
        hashed_pwd = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_pwd,
            full_name=user_data.full_name,
            is_active=True,
            is_superadmin=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> Token:
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is deactivated")

        access_token = create_access_token(subject=user.id, extra_claims={"email": user.email})
        refresh_token = create_refresh_token(subject=user.id)
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

        new_access = create_access_token(subject=user.id, extra_claims={"email": user.email})
        new_refresh = create_refresh_token(subject=user.id)
        return Token(access_token=new_access, refresh_token=new_refresh, token_type="bearer")
