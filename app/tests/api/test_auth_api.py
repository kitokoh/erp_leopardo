import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.api.main import app
from app.db.cruds.users import users_crud as db_manager
from db.session_manager import Base
from app.core.config import CONFIG
from app.db.session_manager import get_db as get_db_session
import logging

# Use a separate test database
TEST_SQLALCHEMY_DATABASE_URL = CONFIG["database_url"] + "_test"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db_session dependency for testing
def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db_session

# Fixture for the database session
@pytest.fixture(scope="module")
def db_session() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

client = TestClient(app)

# Test user credentials
TEST_USERNAME = "testuser_api"
TEST_PASSWORD = "testpassword_api"
TEST_USER_ID = "test_user_api_uuid"

@pytest.fixture(scope="module", autouse=True)
def setup_test_user(db_session: Session):
    user = db_manager.get_user_by_username(db=db_session, username=TEST_USERNAME)
    if not user:
        role = db_session.query(db_manager.Role).filter_by(role_name="user").first()
        if not role:
            role = db_manager.Role(role_id=2, role_name="user", description="Standard user")
            db_session.add(role)
            db_session.commit()
            db_session.refresh(role)

        hashed_password = db_manager.util_hash_password(TEST_PASSWORD)
        new_user = db_manager.User(
            user_id=TEST_USER_ID,
            username=TEST_USERNAME,
            hashed_password=hashed_password,
            full_name='API Test User',
            email=f'{TEST_USERNAME}@example.com',
            role_id=role.role_id,
            is_active=True
        )
        db_session.add(new_user)
        db_session.commit()
    elif not user.is_active:
        user.is_active = True
        db_session.commit()

    yield

def test_login_for_access_token_success(db_session: Session):
    response = client.post(
        "/api/auth/token",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

def test_login_for_access_token_invalid_username():
    response = client.post(
        "/api/auth/token",
        data={"username": "wronguser", "password": TEST_PASSWORD}
    )
    assert response.status_code == 401
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"

def test_login_for_access_token_invalid_password():
    response = client.post(
        "/api/auth/token",
        data={"username": TEST_USERNAME, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"
