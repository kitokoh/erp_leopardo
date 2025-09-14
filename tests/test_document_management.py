import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api.main import app
from app.services.auth.authentication import login
from app.db.cruds.clients import clients_crud
from app.db.cruds.projects import projects_crud
from app.db.cruds.misc import companies_crud
from app.document_generator.cover_page_generator import generate_cover_page_html
from app.core.config import CONFIG

client = TestClient(app)

def test_document_management_workflow(db_session: Session):
    # 1. Login
    success, _, user_data, _ = login(
        username=CONFIG['default_admin_username'],
        password=CONFIG['default_admin_password']
    )
    print(f"Login result: success={success}, message={_}")
    assert success
    assert user_data is not None

    # 2. Create a default company
    company_data = {
        "company_name": "Default Exporter Inc.",
        "is_default": True
    }
    company_id = companies_crud.add_company(company_data=company_data, conn=db_session)
    assert company_id is not None

    # 3. Create a client
    client_data = {
        "client_name": "Test Client for Doc Gen",
        "company_name": "Doc Gen Inc.",
        "project_identifier": "DOC-GEN-001",
        "created_by_user_id": user_data['user_id']
    }
    new_client = clients_crud.add_client(db_session, client_data)
    assert new_client['success']
    assert new_client['client_id'] is not None

    # 4. Create a project
    project_data = {
        "client_id": new_client['client_id'],
        "project_name": "Document Generation Project"
    }
    project_id = projects_crud.add_project(project_data=project_data, db=db_session)
    assert project_id is not None

    # 5. Generate a document
    doc_context = {
        "client_id": new_client['client_id'],
        "project_id": project_id,
        "document_title": "Test Document"
    }
    html_content = generate_cover_page_html(db_session, doc_context)
    assert html_content is not None
    assert "Default Exporter Inc." in html_content
    assert "Test Client for Doc Gen" in html_content
    assert "Document Generation Project" in html_content
