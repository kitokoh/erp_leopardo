import logging
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import FileResponse
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid
import os
import datetime

from app.db.session_manager import get_db
from app.utils.html_to_pdf_util import render_html_template, convert_html_to_pdf, WeasyPrintError
from .models import DocumentGenerationRequest, DocumentGenerationResponse, UserInDB
from .auth import get_current_active_user
from .dependencies import PermissionRequired

from app.db.cruds.misc import templates_crud
from app.db.cruds.clients import client_documents_crud
from app.db.cruds.clients import clients_crud
from app.db.db_utils import get_document_context_data
from app.core.config import CONFIG

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
    responses={404: {"description": "Not found"}},
)

def _save_generated_pdf(client_id: str, project_id: Optional[str], file_name: str, pdf_bytes: bytes, db: Session) -> Optional[str]:
    try:
        client_info = clients_crud.get_client_by_id(db, client_id)
        if not client_info or not client_info.default_base_folder_path:
            return None

        target_dir_base = client_info.default_base_folder_path
        generated_docs_subfolder = "generated_documents"

        if project_id:
            specific_folder_name = str(project_id).replace('-', '')
            target_dir = os.path.join(target_dir_base, generated_docs_subfolder, specific_folder_name)
        else:
            target_dir = os.path.join(target_dir_base, generated_docs_subfolder, "general")

        os.makedirs(target_dir, exist_ok=True)
        file_path_on_disk = os.path.join(target_dir, file_name)

        with open(file_path_on_disk, "wb") as f:
            f.write(pdf_bytes)

        relative_to_client_base = os.path.join(generated_docs_subfolder,
                                               str(project_id).replace('-', '') if project_id else "general",
                                               file_name)
        return relative_to_client_base
    except Exception:
        return None

@router.post("/generate", response_model=DocumentGenerationResponse)
async def generate_document_api(
    request: DocumentGenerationRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(PermissionRequired("edit_documents"))
):
    template_data = templates_crud.get_template_by_id(db, request.template_id)
    if not template_data:
        raise HTTPException(status_code=404, detail=f"Template with ID {request.template_id} not found.")

    try:
        html_template_str = template_data.raw_template_file_data.decode('utf-8')
    except (UnicodeDecodeError, AttributeError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to decode template data for template ID {request.template_id}. Error: {e}")

    context_data = get_document_context_data(
        db=db,
        client_id=request.client_id,
        company_id=request.company_id,
        target_language_code=request.target_language_code,
        project_id=request.project_id,
        additional_context=request.additional_context
    )

    if request.document_title:
        context_data['doc']['document_title'] = request.document_title

    try:
        rendered_html = render_html_template(html_template_str, context_data)
        pdf_bytes = convert_html_to_pdf(rendered_html)
    except WeasyPrintError as wpe:
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(wpe)}")
    except Exception as e:
        # Catch other template rendering or PDF conversion errors
        raise HTTPException(status_code=500, detail=f"Failed to render or convert document: {e}")


    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation resulted in an empty file.")

    safe_template_name = "".join(c if c.isalnum() else "_" for c in template_data.template_name)
    client_name_for_file = context_data.get('client', {}).get('client_name', 'client')
    safe_client_name = "".join(c if c.isalnum() else "_" for c in client_name_for_file)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_file_name = f"{safe_template_name}_{safe_client_name}_{timestamp}.pdf"

    relative_file_path = _save_generated_pdf(
        client_id=request.client_id,
        project_id=request.project_id,
        file_name=generated_file_name,
        pdf_bytes=pdf_bytes,
        db=db
    )

    if not relative_file_path:
        raise HTTPException(status_code=500, detail="Failed to save generated PDF.")

    doc_metadata = {
        'client_id': request.client_id,
        'project_id': request.project_id,
        'document_name': request.document_title or template_data.template_name,
        'file_name_on_disk': generated_file_name,
        'file_path_relative': relative_file_path,
        'document_type_generated': template_data.template_type,
        'source_template_id': request.template_id,
        'created_by_user_id': current_user.user_id,
    }

    db_document_id = client_documents_crud.add_client_document(db, doc_metadata)
    if not db_document_id:
        # Consider cleanup: delete the saved PDF file if metadata fails to save
        raise HTTPException(status_code=500, detail="Failed to save document metadata.")

    download_url = f"/api/documents/{db_document_id}/download"

    return DocumentGenerationResponse(
        message="Document generated successfully.",
        document_id=db_document_id,
        client_id=request.client_id,
        file_name=generated_file_name,
        download_url=download_url
    )


@router.get("/{document_id}/download")
async def download_document_api(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(PermissionRequired("view_documents"))
):
    doc_meta = client_documents_crud.get_document_by_id(db, document_id)
    if not doc_meta:
        raise HTTPException(status_code=404, detail="Document not found.")

    client_info = clients_crud.get_client_by_id(db, doc_meta.client_id)
    if not client_info or not client_info.default_base_folder_path:
        raise HTTPException(status_code=404, detail="Client information or base folder path not found for the document.")

    logging.warning(f"client_info.default_base_folder_path: {client_info.default_base_folder_path}")
    logging.warning(f"doc_meta.file_path_relative: {doc_meta.file_path_relative}")
    absolute_file_path = os.path.join(client_info.default_base_folder_path, doc_meta.file_path_relative)

    if not os.path.exists(absolute_file_path):
        raise HTTPException(status_code=404, detail="File not found on server.")

    try:
        return FileResponse(path=absolute_file_path, filename=doc_meta.file_name_on_disk, media_type='application/pdf')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while trying to serve the file: {e}")
