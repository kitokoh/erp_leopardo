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


def get_auth_token(username: str = TEST_USERNAME, password: str = TEST_PASSWORD) -> str:
    """
    Helper function to get an authentication token for a given user.
    """
    response = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]

def test_login_for_access_token_invalid_password():
    response = client.post(
        "/api/auth/token",
        data={"username": TEST_USERNAME, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"
