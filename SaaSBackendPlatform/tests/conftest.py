import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from models import User, SubscriptionPlan
from auth.security import get_password_hash, create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_saas.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Seed subscription plans in test database
    db = TestingSessionLocal()
    try:
        plans = [
            {"name": "Free", "price_monthly": 0.0, "max_users": 3, "max_alerts": 10, "max_api_calls_per_day": 100, "has_analytics": False, "has_export": False},
            {"name": "Basic", "price_monthly": 29.99, "max_users": 10, "max_alerts": 100, "max_api_calls_per_day": 1000, "has_analytics": True, "has_export": False},
            {"name": "Premium", "price_monthly": 99.99, "max_users": 100, "max_alerts": 999999, "max_api_calls_per_day": 100000, "has_analytics": True, "has_export": True},
        ]
        for p in plans:
            existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == p["name"]).first()
            if not existing:
                db.add(SubscriptionPlan(**p))
        db.commit()
    finally:
        db.close()

    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        is_active=True,
        is_superadmin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(subject=test_user.id, extra_claims={"email": test_user.email})
    return {"Authorization": f"Bearer {token}"}
