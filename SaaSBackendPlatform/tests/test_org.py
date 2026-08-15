def test_create_organization(client, auth_headers):
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Test Org", "slug": "test-org"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Org"
    assert data["data"]["slug"] == "test-org"

def test_list_organizations(client, auth_headers):
    response = client.get("/api/v1/organizations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
