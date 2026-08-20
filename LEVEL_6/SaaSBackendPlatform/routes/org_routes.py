from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.organization import OrganizationCreate, OrganizationResponse, MemberAdd, MemberResponse
from services.org_service import OrgService
from auth.dependencies import get_current_active_user, require_role
from models.user import User

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations & Tenants"])

@router.post("", response_model=StandardResponse[OrganizationResponse], status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new tenant organization. Sets creator as ORG_OWNER & creates Free tier subscription."""
    org = OrgService.create_organization(db, org_data, current_user)
    return StandardResponse(
        success=True,
        message="Organization created successfully",
        data=org
    )

@router.get("", response_model=StandardResponse[List[OrganizationResponse]])
def get_my_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all tenant organizations that the current user belongs to."""
    orgs = OrgService.get_user_organizations(db, current_user.id)
    return StandardResponse(
        success=True,
        message="Organizations retrieved successfully",
        data=orgs
    )

@router.get("/{org_id}", response_model=StandardResponse[OrganizationResponse])
def get_organization_details(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get organization details by ID."""
    org = OrgService.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return StandardResponse(
        success=True,
        message="Organization details retrieved successfully",
        data=org
    )

@router.post("/{org_id}/members", response_model=StandardResponse[MemberResponse], status_code=status.HTTP_201_CREATED)
def add_organization_member(
    org_id: int,
    member_data: MemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER", "MANAGER"]))
):
    """
    Add a new member to an organization.
    Protected by RBAC: Requires ADMIN, ORG_OWNER, or MANAGER role.
    Validates subscription tier user limits before adding!
    """
    member = OrgService.add_member(db, org_id, member_data)
    return StandardResponse(
        success=True,
        message="Member added to organization successfully",
        data=member
    )

@router.get("/{org_id}/members", response_model=StandardResponse[List[MemberResponse]])
def list_organization_members(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all members belonging to an organization."""
    members = OrgService.get_members(db, org_id)
    return StandardResponse(
        success=True,
        message="Organization members retrieved successfully",
        data=members
    )

@router.delete("/{org_id}/members/{user_id}", response_model=StandardResponse[None])
def remove_organization_member(
    org_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER"]))
):
    """
    Remove a member from an organization.
    Protected by RBAC: Requires ADMIN or ORG_OWNER role.
    """
    OrgService.remove_member(db, org_id, user_id)
    return StandardResponse(
        success=True,
        message="Member removed from organization successfully",
        data=None
    )
