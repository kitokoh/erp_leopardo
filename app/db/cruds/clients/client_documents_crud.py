import logging
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.db.generic_crud import _manage_conn, _convert_to_dict

logger = logging.getLogger(__name__)

@_manage_conn
def add_client_document(data: dict, conn: Session = None) -> str | None:
    """Adds a new client document entry to the ClientDocuments table."""
    new_document_id = str(uuid.uuid4())
    data.pop('is_deleted', None)
    data.pop('deleted_at', None)

    sql = text("""
        INSERT INTO ClientDocuments (
            document_id, client_id, project_id, order_identifier,
            document_name, file_name_on_disk, file_path_relative,
            document_type_generated, source_template_id,
            version_tag, notes, footer_notes, created_by_user_id,
            parent_document_id, is_latest_version
        ) VALUES (:doc_id, :client_id, :proj_id, :ord_id, :doc_name, :disk_name, :rel_path,
                  :doc_type, :template_id, :version, :notes, :footer, :user_id, :parent_id, :latest)
    """)
    params = {
        "doc_id": new_document_id,
        "client_id": data.get('client_id'),
        "proj_id": data.get('project_id'),
        "ord_id": data.get('order_identifier'),
        "doc_name": data.get('document_name'),
        "disk_name": data.get('file_name_on_disk'),
        "rel_path": data.get('file_path_relative'),
        "doc_type": data.get('document_type_generated'),
        "template_id": data.get('source_template_id'),
        "version": data.get('version_tag', "1.0"),
        "notes": data.get('notes'),
        "footer": data.get('footer_notes'),
        "user_id": data.get('user_id'),
        "parent_id": data.get('parent_document_id'),
        "latest": data.get('is_latest_version', 1)
    }

    try:
        logger.debug(f"Attempting to add client document. Params: {params}")
        conn.execute(sql, params)
        conn.commit()
        logger.info(f"Successfully added client document with ID: {new_document_id} for client: {data.get('client_id')}")
        return new_document_id
    except Exception as e:
        logger.error(f"Error adding client document for client {data.get('client_id')}: {e}", exc_info=True)
        conn.rollback()
        return None

@_manage_conn
def get_documents_for_client(client_id: str, filters: dict = None, include_deleted: bool = False, fetch_only_latest_versions: bool = True, conn: Session = None) -> list[dict]:
    if not client_id:
        logger.error("get_documents_for_client: client_id cannot be empty.")
        return []

    try:
        conditions = ["client_id = :client_id"]
        params = {"client_id": client_id}

        if not include_deleted:
            conditions.append("(is_deleted = 0 OR is_deleted IS NULL)")

        if fetch_only_latest_versions:
            conditions.append("(is_latest_version = 1 OR is_latest_version IS NULL)")

        if filters:
            order_identifier_filter = filters.get('order_identifier')
            if order_identifier_filter == 'NONE':
                conditions.append("order_identifier IS NULL")
            elif order_identifier_filter and order_identifier_filter != 'ALL':
                conditions.append("order_identifier = :order_id")
                params["order_id"] = order_identifier_filter

        sql_str = f"SELECT * FROM ClientDocuments WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
        sql = text(sql_str)
        result = conn.execute(sql, params)
        return [_convert_to_dict(row) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error retrieving documents for client {client_id} with filters {filters}: {e}", exc_info=True)
        return []
