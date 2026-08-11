import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# Create in-memory SQLite engine for isolated testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Create clean database tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# -------------------------------------------------------------
# 1. Health Check Test
# -------------------------------------------------------------
def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Welcome" in data["message"]
    assert "documentation" in data["data"]


# -------------------------------------------------------------
# 2. Authentication & User Registration Tests
# -------------------------------------------------------------
def test_user_registration_and_login():
    # Register standard user
    reg_resp = client.post("/auth/register", json={
        "username": "testuser",
        "password": "userpass123",
        "role": "user"
    })
    assert reg_resp.status_code == 201
    assert reg_resp.json()["status"] == "success"
    assert reg_resp.json()["data"]["username"] == "testuser"
    assert reg_resp.json()["data"]["role"] == "user"

    # Duplicate registration should fail
    dup_resp = client.post("/auth/register", json={
        "username": "testuser",
        "password": "userpass123",
        "role": "user"
    })
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["message"]

    # Login with wrong password
    wrong_login = client.post("/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert wrong_login.status_code == 401
    assert wrong_login.json()["status"] == "error"

    # Login with correct password
    login_resp = client.post("/auth/login", json={
        "username": "testuser",
        "password": "userpass123"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()["data"]
    assert "access_token" in login_data
    assert login_data["role"] == "user"

    # Access /auth/me with token
    headers = {"Authorization": f"Bearer {login_data['access_token']}"}
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["username"] == "testuser"


# -------------------------------------------------------------
# 3. Product CRUD & Validation Tests
# -------------------------------------------------------------
def test_product_crud_and_validation():
    # Setup Admin user
    client.post("/auth/register", json={
        "username": "adminuser",
        "password": "adminpassword",
        "role": "admin"
    })
    admin_login = client.post("/auth/login", json={
        "username": "adminuser",
        "password": "adminpassword"
    }).json()["data"]
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

    # Setup Standard user
    client.post("/auth/register", json={
        "username": "stduser",
        "password": "stdpassword",
        "role": "user"
    })
    std_login = client.post("/auth/login", json={
        "username": "stduser",
        "password": "stdpassword"
    }).json()["data"]
    std_headers = {"Authorization": f"Bearer {std_login['access_token']}"}

    # 1. Unauthenticated creation attempt -> 401
    unauth_resp = client.post("/products", json={
        "product_id": 1,
        "product_name": "Laptop",
        "price": 999.99,
        "quantity": 10,
        "category": "Electronics"
    })
    assert unauth_resp.status_code == 401

    # 2. Invalid JWT token attempt -> 401
    invalid_tok_resp = client.post("/products", headers={"Authorization": "Bearer badtoken123"}, json={
        "product_id": 1,
        "product_name": "Laptop",
        "price": 999.99,
        "quantity": 10,
        "category": "Electronics"
    })
    assert invalid_tok_resp.status_code == 401

    # 3. Negative price validation -> 400
    neg_price_resp = client.post("/products", headers=std_headers, json={
        "product_id": 1,
        "product_name": "Laptop",
        "price": -50.0,
        "quantity": 10,
        "category": "Electronics"
    })
    assert neg_price_resp.status_code == 400
    assert neg_price_resp.json()["status"] == "error"

    # 4. Negative quantity validation -> 400
    neg_qty_resp = client.post("/products", headers=std_headers, json={
        "product_id": 1,
        "product_name": "Laptop",
        "price": 999.99,
        "quantity": -5,
        "category": "Electronics"
    })
    assert neg_qty_resp.status_code == 400

    # 5. Invalid Product ID (<= 0) -> 400
    invalid_id_resp = client.post("/products", headers=std_headers, json={
        "product_id": 0,
        "product_name": "Laptop",
        "price": 999.99,
        "quantity": 5,
        "category": "Electronics"
    })
    assert invalid_id_resp.status_code == 400

    # 6. Create Product 1 (Laptop)
    prod1_resp = client.post("/products", headers=std_headers, json={
        "product_id": 101,
        "product_name": "Pro Gaming Laptop",
        "description": "High performance gaming laptop",
        "price": 1499.99,
        "quantity": 15,
        "category": "Electronics"
    })
    assert prod1_resp.status_code == 201
    assert prod1_resp.json()["status"] == "success"
    assert prod1_resp.json()["data"]["product_name"] == "Pro Gaming Laptop"

    # 7. Create Product 2 (Office Chair)
    prod2_resp = client.post("/products", headers=std_headers, json={
        "product_id": 102,
        "product_name": "Ergonomic Office Chair",
        "description": "Adjustable mesh chair",
        "price": 199.50,
        "quantity": 30,
        "category": "Furniture"
    })
    assert prod2_resp.status_code == 201

    # 8. Duplicate Product ID check -> 400
    dup_id_resp = client.post("/products", headers=std_headers, json={
        "product_id": 101,
        "product_name": "Another Laptop",
        "price": 500.0,
        "quantity": 2,
        "category": "Electronics"
    })
    assert dup_id_resp.status_code == 400

    # 9. Get all products
    all_prod_resp = client.get("/products")
    assert all_prod_resp.status_code == 200
    assert len(all_prod_resp.json()["data"]) == 2

    # 10. Filter products by category
    cat_filter_resp = client.get("/products?category=Furniture")
    assert cat_filter_resp.status_code == 200
    assert len(cat_filter_resp.json()["data"]) == 1
    assert cat_filter_resp.json()["data"][0]["category"] == "Furniture"

    # 11. Search products by keyword
    search_resp = client.get("/products?search=Gaming")
    assert search_resp.status_code == 200
    assert len(search_resp.json()["data"]) == 1
    assert search_resp.json()["data"][0]["product_id"] == 101

    # 12. Update Product
    update_resp = client.put("/products/101", headers=std_headers, json={
        "price": 1399.99,
        "quantity": 12
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["price"] == 1399.99
    assert update_resp.json()["data"]["quantity"] == 12

    # 13. Update non-existent product -> 404
    upd_404_resp = client.put("/products/999", headers=std_headers, json={
        "price": 10.0
    })
    assert upd_404_resp.status_code == 404

    # 14. Delete Product as Standard User -> 403 Forbidden
    del_std_resp = client.delete("/products/101", headers=std_headers)
    assert del_std_resp.status_code == 403
    assert "Admin role required" in del_std_resp.json()["message"]

    # 15. Delete Product as Admin User -> 200 OK
    del_admin_resp = client.delete("/products/101", headers=admin_headers)
    assert del_admin_resp.status_code == 200
    assert del_admin_resp.json()["status"] == "success"

    # 16. Verify product deletion -> 404
    get_deleted = client.get("/products/101")
    assert get_deleted.status_code == 404

    # 17. Verify Transaction History logs (CREATE, UPDATE, DELETE)
    tx_resp = client.get("/transactions", headers=admin_headers)
    assert tx_resp.status_code == 200
    tx_logs = tx_resp.json()["data"]
    assert len(tx_logs) >= 3  # CREATE (x2), UPDATE (x1), DELETE (x1)
    actions = [t["action"] for t in tx_logs]
    assert "CREATE" in actions
    assert "UPDATE" in actions
    assert "DELETE" in actions
