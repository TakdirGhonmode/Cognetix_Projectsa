from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models.user import User
from models.organization import Organization, OrganizationMember
from models.subscription import TenantSubscription, SubscriptionPlan
from models.usage import UsageLog
from auth.security import decode_token

http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    token_oauth: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to extract and validate current user from Bearer JWT token."""
    token = None
    if credentials:
        token = credentials.credentials
    elif token_oauth:
        token = token_oauth

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception
    
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency ensuring user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")
    return current_user

def get_current_superadmin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency enforcing Superadmin role."""
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation allowed only for system Superadmin"
        )
    return current_user

def get_organization_context(
    organization_id: Optional[int] = Header(None, alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Optional[OrganizationMember]:
    """
    Dependency to resolve user membership and role for requested organization.
    Uses 'X-Organization-ID' header.
    """
    if not organization_id:
        return None
    
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not member and not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the specified organization"
        )
    return member

def require_role(allowed_roles: List[str]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Allowed roles example: ["ADMIN", "ORG_OWNER", "MANAGER"]
    """
    def role_checker(
        organization_id: int = Header(..., alias="X-Organization-ID"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        if current_user.is_superadmin:
            return True
            
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Not a member of this organization"
            )

        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{member.role}' does not have sufficient permissions. Required roles: {allowed_roles}"
            )
        return member

    return role_checker

def require_plan_feature(feature_name: str):
    """
    Dependency enforcing subscription feature flags (e.g. 'has_analytics', 'has_export').
    """
    def feature_checker(
        organization_id: int = Header(..., alias="X-Organization-ID"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == organization_id,
            TenantSubscription.status == "active"
        ).first()

        if not sub or not sub.plan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription plan found for this organization"
            )

        has_access = getattr(sub.plan, feature_name, False)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Feature '{feature_name}' is locked on current subscription tier ('{sub.plan.name}'). Upgrade required."
            )
        return sub.plan

    return feature_checker
