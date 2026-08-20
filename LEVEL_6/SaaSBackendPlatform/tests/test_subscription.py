from seed import seed_database

def test_list_subscriptions(client, auth_headers):
    # Ensure plans seeded
    response = client.get("/api/v1/subscriptions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_change_subscription(client, auth_headers):
    # Create org first
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": "Sub Org", "slug": "sub-org"},
        headers=auth_headers
    )
    org_id = org_res.json()["data"]["id"]

    # Change to Basic plan
    headers = {**auth_headers, "X-Organization-ID": str(org_id)}
    res = client.post(
        "/api/v1/subscriptions/assign",
        json={"plan_name": "Basic"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
