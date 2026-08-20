def test_user_registration_and_login(client):
    reg_response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "testuser@enterprise.com",
        "password": "Password123!",
        "role": "Manager",
        "department": "Finance"
    })
    assert reg_response.status_code == 201, reg_response.text
    data = reg_response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "Manager"

    login_response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "Password123!"
    })
    assert login_response.status_code == 200, login_response.text
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testuser"
