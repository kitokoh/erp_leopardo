import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.api.main import app as fastapi_app
from app.db.cruds.users import users_crud, permissions_crud, role_permissions_crud
from db.session_manager import Base
from app.core.config import CONFIG
from app.db.session_manager import get_db as get_db_session
import app.db.import_all_models
from unittest.mock import patch, MagicMock
import os

# --- Test Database Setup ---
TEST_SQLALCHEMY_DATABASE_URL = CONFIG["database_url"] + "_test_docs"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Dependency Override ---
def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db_session] = override_get_db_session

# --- Test User Credentials ---
TEST_USERNAME = "testuser_docs_api"
TEST_PASSWORD = "password"
TEST_USER_ID = "test_user_docs_uuid"

client = TestClient(fastapi_app)

# --- Fixtures ---
@pytest.fixture(scope="module")
def db_session_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create test user for the entire module
        user = users_crud.get_user_by_username(db, username=TEST_USERNAME)
        if not user:
            role = db.query(users_crud.Role).filter_by(role_name="admin").first()
            if not role:
                role = users_crud.Role(role_id=1, role_name="admin", description="Admin user")
                db.add(role)
                db.commit()
                db.refresh(role)

            # Grant permissions to the role
            permissions = ["edit_documents", "view_documents"]
            for p_key in permissions:
                permission = permissions_crud.get_permission_by_key(db, p_key)
                if not permission:
                    permission = permissions_crud.add_permission(db, p_key, f"Permission to {p_key}")
                role_permissions_crud.add_permission_to_role(db, role.role_id, permission.permission_key)

            hashed_password = users_crud.util_hash_password(TEST_PASSWORD)
            new_user = users_crud.User(
                user_id=TEST_USER_ID,
                username=TEST_USERNAME,
                hashed_password=hashed_password,
                full_name='Docs API Test User',
                email=f'{TEST_USERNAME}@example.com',
                role_id=role.role_id,
                is_active=True
            )
            db.add(new_user)
            db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def auth_headers(db_session_module):
    """Fixture to get authentication headers for tests."""
    response = client.post("/api/auth/token", data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    if response.status_code != 200:
        pytest.fail(f"Failed to authenticate test user to get token. Status: {response.status_code}, Detail: {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Tests ---

def test_generate_document_api_success(auth_headers, db_session_module):
    request_payload = {
        "template_id": 1,
        "client_id": "client_uuid_test_doc_gen",
        "company_id": "company_uuid_test_doc_gen",
        "target_language_code": "en",
    }
    mock_template_data = MagicMock()
    mock_template_data.raw_template_file_data = b'Hello {{ name }}'
    mock_template_data.template_type = 'html'
    mock_template_data.template_name = 'Test Template'

    mock_context_data = {'name': 'World', 'client': {'client_name': 'Test Client'}, 'doc': {}}
    mock_generated_doc_id = "generated_doc_uuid_123"
    mock_saved_relative_path = "generated/document.pdf"

    with patch('app.api.documents.templates_crud.get_template_by_id', return_value=mock_template_data) as mock_get_tpl, \
         patch('app.api.documents.get_document_context_data', return_value=mock_context_data) as mock_get_ctx, \
         patch('app.api.documents.render_html_template', return_value="<html></html>") as mock_render, \
         patch('app.api.documents.convert_html_to_pdf', return_value=b'pdf_bytes') as mock_gen_pdf, \
         patch('app.api.documents.client_documents_crud.add_client_document', return_value=mock_generated_doc_id) as mock_add_doc, \
         patch('app.api.documents._save_generated_pdf', return_value=mock_saved_relative_path) as mock_save:

        response = client.post("/api/documents/generate", json=request_payload, headers=auth_headers)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["message"] == "Document generated successfully."
        assert json_response["document_id"] == mock_generated_doc_id

def test_generate_document_template_not_found(auth_headers):
    with patch('app.api.documents.templates_crud.get_template_by_id', return_value=None):
        response = client.post("/api/documents/generate", json={
            "template_id": 999, "client_id": "c1", "company_id": "comp1", "target_language_code": "en"
        }, headers=auth_headers)
        assert response.status_code == 404
        assert "Template with ID 999 not found" in response.json()["detail"]

def test_download_document_api_success(auth_headers):
    doc_id = "existing_doc_uuid_abc"
    mock_doc_meta = MagicMock()
    mock_doc_meta.document_id = doc_id
    mock_doc_meta.file_path_relative = 'some/path.pdf'
    mock_doc_meta.file_name_on_disk = 'document.pdf'
    mock_doc_meta.client_id = 'c1'

    mock_client_meta = MagicMock()
    mock_client_meta.default_base_folder_path = '/fake/client/folder'

    with patch('app.api.documents.client_documents_crud.get_document_by_id', return_value=mock_doc_meta), \
         patch('app.api.documents.clients_crud.get_client_by_id', return_value=mock_client_meta), \
         patch('os.path.exists', return_value=True), \
         patch('app.api.documents.FileResponse') as MockFileResponse:

        response = client.get(f"/api/documents/{doc_id}/download", headers=auth_headers)

        assert response.status_code == 200
        MockFileResponse.assert_called_once()
        _, kwargs = MockFileResponse.call_args
        assert kwargs.get('filename') == mock_doc_meta.file_name_on_disk

def test_download_document_not_found(auth_headers):
    with patch('app.api.documents.client_documents_crud.get_document_by_id', return_value=None):
        response = client.get("/api/documents/non_existent_doc_id/download", headers=auth_headers)
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

def test_download_document_file_not_on_server(auth_headers):
    doc_id = "doc_id_file_missing_xyz"
    mock_doc_meta = MagicMock()
    mock_doc_meta.document_id = doc_id
    mock_doc_meta.client_id = 'c1'
    mock_doc_meta.file_path_relative = 'path/to/missing.pdf'

    mock_client_meta = MagicMock()
    mock_client_meta.default_base_folder_path = '/fake/path'

    with patch('app.api.documents.client_documents_crud.get_document_by_id', return_value=mock_doc_meta), \
         patch('app.api.documents.clients_crud.get_client_by_id', return_value=mock_client_meta), \
         patch('os.path.exists', return_value=False):
        response = client.get(f"/api/documents/{doc_id}/download", headers=auth_headers)
        assert response.status_code == 404
        assert "File not found on server" in response.json()["detail"]
