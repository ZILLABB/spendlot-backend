"""
Test configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.services.user_service import UserService
from app.schemas.user import UserCreate

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """Create database session for testing."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user_service = UserService(db_session)
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    user = user_service.create(user_data)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    login_data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
