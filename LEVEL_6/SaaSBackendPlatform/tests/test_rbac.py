from auth.security import create_access_token, get_password_hash
from models import User, OrganizationMember

def test_rbac_member_access(client, auth_headers, db_session):
    # 1. Create Org with owner
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": "RBAC Org", "slug": "rbac-org"},
        headers=auth_headers
    )
    org_id = org_res.json()["data"]["id"]

    # 2. Register regular user
    reg_user = User(
        email="regular@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Regular User"
    )
    db_session.add(reg_user)
    db_session.commit()
    db_session.refresh(reg_user)

    # 3. Add regular user to org with USER role
    mem = OrganizationMember(
        organization_id=org_id,
        user_id=reg_user.id,
        role="USER"
    )
    db_session.add(mem)
    db_session.commit()

    # 4. Token for regular user
    reg_token = create_access_token(subject=reg_user.id, extra_claims={"email": reg_user.email})
    reg_headers = {
        "Authorization": f"Bearer {reg_token}",
        "X-Organization-ID": str(org_id)
    }

    # 5. Regular USER attempts to change subscription (Requires ADMIN or ORG_OWNER) -> Forbidden 403
    forbidden_res = client.post(
        "/api/v1/subscriptions/assign",
        json={"plan_name": "Premium"},
        headers=reg_headers
    )
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["success"] is False
