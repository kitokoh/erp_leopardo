import os
import sys
from pathlib import Path

# Set a dummy secret key for the tests to run before any other imports
os.environ['API_SECRET_KEY'] = 'test_secret_key_for_jules'
os.environ['ALGORITHM'] = 'HS256'
os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.session_manager import Base
from app.core.config import CONFIG
from app.models.db.settings.status_setting import StatusSetting

# Use a separate test database
TEST_SQLALCHEMY_DATABASE_URL = CONFIG["database_url"] + "_test"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.api.main import app
from app.db.session_manager import get_db as get_db_session

# Override the get_db_session dependency for testing
def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db_session

from app.db.session_manager import session_manager

from app.db.cruds.users import users_crud

@pytest.fixture(scope="session")
def db_session() -> Session:
    session_manager.initialize(TEST_SQLALCHEMY_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

from app.utils.auth import hash_password as util_hash_password

from app.db.cruds.users import roles_crud

@pytest.fixture(scope="session", autouse=True)
def setup_test_user(db_session: Session):
    role = roles_crud.get_role_by_name(db_session, "Administrator")
    if not role:
        role = roles_crud.add_role(db_session, "Administrator", "Administrator role")

    user = users_crud.get_user_by_username(db_session, CONFIG['default_admin_username'])
    if not user:
        hashed_password = util_hash_password(CONFIG['default_admin_password'])
        users_crud.add_user(
            db=db_session,
            username=CONFIG['default_admin_username'],
            password=CONFIG['default_admin_password'],
            role_id=role.role_id,
            full_name="Test Admin",
            email="admin@test.com"
        )

def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file
    after command line options have been parsed.
    """
    # The 'app' directory should be automatically added to the path by pytest
    # because of the `packages` configuration in pyproject.toml and the fact
    # that we run pytest from the root.
    pass
