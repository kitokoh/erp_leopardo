import pytest
from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch, MagicMock
import os
from .test_auth_api import get_auth_token, TEST_USERNAME, TEST_PASSWORD
import uuid # Added
from starlette.responses import FileResponse # Added


client = TestClient(app)

@pytest.fixture(scope="module")
def auth_headers():
    token = get_auth_token(client, TEST_USERNAME, TEST_PASSWORD)
    return {"Authorization": f"Bearer {token}"}

# TODO: Add more comprehensive tests for document generation and download

def test_generate_document_api_success(auth_headers):
    # This is a complex endpoint to test thoroughly due to dependencies.
    # Mock dependencies: db_manager calls, html_to_pdf_util calls, file system operations.

    request_payload = {
        "template_id": 1,
        "client_id": "client_uuid_test_doc_gen",
        "company_id": "company_uuid_test_doc_gen",
        "target_language_code": "en",
        "document_title": "Test Generated Document",
        "line_items": [{"product_id": 101, "quantity": 2}],
        "additional_context": {"some_custom_field": "custom_value"}
    }

    # Mock db_manager.get_template_by_id
    mock_template_data = {
        'template_id': 1, 'template_name': 'MockProforma', 'language_code': 'en',
        'base_file_name': 'proforma_template.html', # Assuming file based for this mock
        'raw_template_file_data': b"<html><body><h1>{{doc.title}}</h1><p>Client: {{client.name}}</p></body></html>"
    }
    # Mock db_manager.get_document_context_data
    mock_context_data = {
        "doc": {"title": "Test Generated Document"},
        "client": {"name": "Test Client for Doc Gen"},
        "seller": {"name": "Test Seller Co"},
        "products": [{"name": "Mock Product", "quantity": 2, "unit_price_formatted": "€10.00", "total_price_formatted": "€20.00"}]
    }
    # Mock db_manager.add_client_document
    mock_generated_doc_id = "generated_doc_uuid_123"

    # Mock html_to_pdf_util.render_html_template
    mock_rendered_html = "<html><body><h1>Test Generated Document</h1><p>Client: Test Client for Doc Gen</p></body></html>"
    # Mock html_to_pdf_util.convert_html_to_pdf
    mock_pdf_bytes = b"%PDF-1.4 mock pdf content"

    # Mock _save_generated_pdf (internal to api.documents)
    # The path here is relative to the client's base folder.
    mock_saved_relative_path = "generated_documents/general/MockProforma_TestClient_timestamp.pdf"

    # Mock client's default_base_folder_path for _save_generated_pdf path construction
    mock_client_info_for_save = {'default_base_folder_path': 'clients/TestClient_Country_ProjID'}


    with patch('api.documents.db_manager.get_template_by_id', MagicMock(return_value=mock_template_data)) as mock_get_tpl, \
         patch('api.documents.db_manager.get_document_context_data', MagicMock(return_value=mock_context_data)) as mock_get_ctx, \
         patch('api.documents.render_html_template', MagicMock(return_value=mock_rendered_html)) as mock_render, \
         patch('api.documents.convert_html_to_pdf', MagicMock(return_value=mock_pdf_bytes)) as mock_convert, \
         patch('api.documents._save_generated_pdf', MagicMock(return_value=mock_saved_relative_path)) as mock_save, \
         patch('api.documents.db_manager.add_client_document', MagicMock(return_value=mock_generated_doc_id)) as mock_add_meta, \
         patch('api.documents.db_manager.get_client_by_id', MagicMock(return_value=mock_client_info_for_save)): # For _save_generated_pdf needing client path

        response = client.post("/api/documents/generate", json=request_payload, headers=auth_headers)

        print(f"Generate Doc Response: {response.content}") # For debugging test failures
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["message"] == "Document generated successfully."
        assert json_response["document_id"] == mock_generated_doc_id
        assert json_response["client_id"] == request_payload["client_id"]
        assert "file_name" in json_response # Check if filename is part of response
        assert json_response["download_url"] == f"/api/documents/{mock_generated_doc_id}/download"

        mock_get_tpl.assert_called_once_with(request_payload["template_id"])
        # Add more assertions for other mock calls if needed

def test_generate_document_template_not_found(auth_headers):
    with patch('api.documents.db_manager.get_template_by_id', MagicMock(return_value=None)):
        response = client.post("/api/documents/generate", json={
            "template_id": 999, "client_id": "c1", "company_id": "comp1", "target_language_code": "en"
        }, headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Template with ID 999 not found."

def test_download_document_api_success(auth_headers):
    doc_id_to_download = "existing_doc_uuid_abc"
    mock_doc_meta = {
        'document_id': doc_id_to_download,
        'client_id': 'client_for_doc_dl',
        'file_path_relative': 'generated_documents/general/download_me.pdf', # Relative to client base
        'file_name_on_disk': 'download_me.pdf'
    }
    mock_client_meta = {
        'client_id': 'client_for_doc_dl',
        'default_base_folder_path': 'clients/TestClient_ForDownload_TestCountry_TestProjectID'
    }

    dummy_file_content = b"dummy pdf content for download test"
    temp_file_path = "temp_download_test_file.pdf"
    with open(temp_file_path, "wb") as f:
        f.write(dummy_file_content)

    # The problematic block starts here, ensuring indentation is correct.
    # All subsequent lines within this 'with' block must be indented further than this 'with'.
    with patch('api.documents.db_manager.get_document_by_id', MagicMock(return_value=mock_doc_meta)) as mock_get_doc, \
         patch('api.documents.db_manager.get_client_by_id', MagicMock(return_value=mock_client_meta)) as mock_get_client, \
         patch('os.path.exists', MagicMock(return_value=True)) as mock_os_exists, \
         patch('api.documents.FileResponse') as MockFileResponse: # Corrected patch target

        MockFileResponse.return_value = "Mocked FileResponse content"
        response = client.get(f"/api/documents/{doc_id_to_download}/download", headers=auth_headers)
        assert response.status_code == 200
        MockFileResponse.assert_called_once()
        args, kwargs = MockFileResponse.call_args
        assert kwargs.get('filename') == mock_doc_meta.get('file_name_on_disk')
        assert kwargs.get('media_type') == 'application/pdf'

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


def test_download_document_not_found(auth_headers):
    with patch('api.documents.db_manager.get_document_by_id', MagicMock(return_value=None)):
        response = client.get("/api/documents/non_existent_doc_id/download", headers=auth_headers)
        assert response.status_code == 404
        assert "Document with ID non_existent_doc_id not found" in response.json()["detail"]

def test_download_document_file_not_on_server(auth_headers):
    doc_id_file_missing = "doc_id_file_missing_xyz"
    mock_doc_meta = {
        'document_id': doc_id_file_missing, 'client_id': 'c1',
        'file_path_relative': 'path/to/missing_file.pdf', 'file_name_on_disk': 'missing_file.pdf'
    }
    mock_client_meta = {'client_id': 'c1', 'default_base_folder_path': 'clients/some_client'}

    with patch('api.documents.db_manager.get_document_by_id', MagicMock(return_value=mock_doc_meta)), \
         patch('api.documents.db_manager.get_client_by_id', MagicMock(return_value=mock_client_meta)), \
         patch('os.path.exists', MagicMock(return_value=False)): # Simulate file not existing
        response = client.get(f"/api/documents/{doc_id_file_missing}/download", headers=auth_headers)
        assert response.status_code == 404
        assert f"Generated document file not found on server for document ID {doc_id_file_missing}" in response.json()["detail"]
