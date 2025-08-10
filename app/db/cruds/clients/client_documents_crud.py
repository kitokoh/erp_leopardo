import sqlite3 # Keep for type hinting if conn is directly manipulated, though _manage_conn handles it.
import logging
import uuid # For generating document_id
from ..generic_crud import _manage_conn

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- ClientDocuments ---
@_manage_conn
def add_client_document(data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Adds a new client document entry to the ClientDocuments table.

    Args:
        data (dict): A dictionary containing the document metadata. Expected keys:
            'client_id': (str) ID of the client.
            'document_name': (str) Name of the document.
            'file_name_on_disk': (str) The actual name of the file stored on disk.
            'file_path_relative': (str) The path to the file, relative to a base client directory.
            'document_type_generated': (str) Type of document (e.g., 'invoice_pdf', 'report_pdf').
            'source_template_id': (int) ID of the template used to generate this document.
            'user_id': (str) ID of the user creating this document (maps to created_by_user_id).
            Optional keys:
            'project_id': (str, optional) ID of the associated project.
            'order_identifier': (str, optional) Specific order ID related to this document.
            'version_tag': (str, optional) A version tag or number for the document.
            'notes': (str, optional) Any notes related to the document.
        conn (sqlite3.Connection, optional): SQLite connection object. Provided by _manage_conn.

    Returns:
        str | None: The newly generated document_id if successful, otherwise None.
    """
    new_document_id = str(uuid.uuid4())
    # Ensure is_deleted and deleted_at are not part of initial add data, or set to defaults
    data.pop('is_deleted', None)
    data.pop('deleted_at', None)
    cursor = conn.cursor()

    # Note: is_deleted and deleted_at columns are added to the table schema.
    # They will take their DEFAULT values (0 and NULL respectively) on INSERT.
    sql = """
        INSERT INTO ClientDocuments (
            document_id, client_id, project_id, order_identifier,
            document_name, file_name_on_disk, file_path_relative,
            document_type_generated, source_template_id,
            version_tag, notes, footer_notes, created_by_user_id,
            parent_document_id, is_latest_version
            -- is_deleted, deleted_at will use defaults from schema (0 and NULL)
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_document_id,
        data.get('client_id'),
        data.get('project_id'),
        data.get('order_identifier'),
        data.get('document_name'),
        data.get('file_name_on_disk'),
        data.get('file_path_relative'),
        data.get('document_type_generated'),
        data.get('source_template_id'),
        data.get('version_tag', "1.0"), # Default version_tag
        data.get('notes'),
        data.get('footer_notes'), # Added footer_notes
        data.get('user_id'),
        data.get('parent_document_id'), # New field for versioning
        data.get('is_latest_version', 1) # Default to True (1) for new/latest version
    )

    try:
        logging.debug(f"Attempting to add client document. SQL: {sql}, Params: {params}")
        cursor.execute(sql, params)
        logging.info(f"Successfully added client document with ID: {new_document_id} for client: {data.get('client_id')}")
        return new_document_id
    except sqlite3.Error as e:
        logging.error(f"SQLite error adding client document for client {data.get('client_id')}: {e} - SQL: {sql} - Params: {params}", exc_info=True)
        return None

@_manage_conn
def create_new_document_version(old_document_id: str, new_document_data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Creates a new version of a document.
    1. Marks the old document as not the latest.
    2. Adds the new document data as a new record, linking it to the old one.
    """
    from datetime import datetime # Local import

    cursor = conn.cursor()
    now_utc_iso = datetime.utcnow().isoformat()

    # 1. Mark old document as not latest
    try:
        logging.info(f"Marking old document {old_document_id} as not latest.")
        sql_update_old = "UPDATE ClientDocuments SET is_latest_version = 0, updated_at = ? WHERE document_id = ?"
        cursor.execute(sql_update_old, (now_utc_iso, old_document_id))
        if cursor.rowcount == 0:
            logging.warning(f"Old document {old_document_id} not found or no change made while marking not latest.")
            # Depending on desired strictness, could return None here or proceed.
            # For now, proceed to allow creating the new version anyway if old one vanished.
    except sqlite3.Error as e:
        logging.error(f"Error marking old document {old_document_id} as not latest: {e}", exc_info=True)
        return None # Fail if we can't update the old version status

    # 2. Prepare and add the new document version
    # Fetch old version_tag to increment it
    old_doc_details = get_document_by_id(old_document_id, conn=conn, include_deleted=True) # Get even if it was marked deleted
    current_version_tag = "1.0" # Default if old doc not found or has no tag
    if old_doc_details and old_doc_details.get('version_tag'):
        current_version_tag = old_doc_details.get('version_tag')

    # Simple version increment: "1.0" -> "1.1", "1.9" -> "2.0", "2" -> "2.1"
    try:
        parts = current_version_tag.split('.')
        if len(parts) == 1 and parts[0].isdigit(): # e.g. "2"
            major = int(parts[0])
            new_version_tag = f"{major}.1"
        elif len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit(): # e.g. "1.0" or "1.9"
            major = int(parts[0])
            minor = int(parts[1])
            if minor >= 9: # Or some other threshold for major bump
                major += 1
                minor = 0
            else:
                minor += 1
            new_version_tag = f"{major}.{minor}"
        else: # Non-standard, append ".vX"
            existing_versions_count = 1 # Simplified: count how many children parent_document_id has
            # A more robust way would be to query count of versions for this parent.
            # For now, just append a generic increment.
            new_version_tag = f"{current_version_tag}.new"
            # This part needs more robust version increment logic if complex versions are used.
            # Fallback: append timestamp or simple counter if parsing fails.
            # For now, let's assume version_tag is like "1.0", "1.1", etc.
            logging.warning(f"Could not parse version_tag '{current_version_tag}', using simple append for new version.")
            # A simpler strategy for now:
            new_version_tag = f"{current_version_tag}+{datetime.now().strftime('%Y%m%d%H%M%S')}"


    except ValueError:
        logging.warning(f"Could not parse version_tag '{current_version_tag}' for incrementing. Appending '.next'.")
        new_version_tag = current_version_tag + ".next"


    versioned_data = new_document_data.copy()
    versioned_data['parent_document_id'] = old_document_id
    versioned_data['version_tag'] = new_version_tag
    versioned_data['is_latest_version'] = 1 # This new version is the latest

    logging.info(f"Adding new version for document {old_document_id}. New version tag: {new_version_tag}. Data: {versioned_data}")
    return add_client_document(versioned_data, conn=conn)


@_manage_conn
def delete_client_document(document_id: str, conn: sqlite3.Connection = None) -> bool:
    """
    Soft deletes a client document by its document_id.
    Sets is_deleted = 1 and deleted_at = current UTC time.
    """
    from datetime import datetime # Local import for current time

    cursor = conn.cursor()
    now_utc_iso = datetime.utcnow().isoformat()
    try:
        logging.info(f"Attempting to soft delete client document with ID: {document_id}")
        sql = "UPDATE ClientDocuments SET is_deleted = 1, deleted_at = ? WHERE document_id = ?"
        cursor.execute(sql, (now_utc_iso, document_id))

        if cursor.rowcount > 0:
            logging.info(f"Successfully soft-deleted client document with ID: {document_id}")
            return True
        else:
            logging.warning(f"No client document found with ID: {document_id} to soft delete, or it was already marked.")
            return False # No row was updated
    except sqlite3.Error as e:
        logging.error(f"SQLite error soft-deleting client document {document_id}: {e}", exc_info=True)
        return False

@_manage_conn
def get_document_by_id(document_id: str, conn: sqlite3.Connection = None, include_deleted: bool = False, fetch_only_latest_version: bool = False) -> dict | None:
    """
    Retrieves a client document by its document_id.
    Optionally includes soft-deleted documents.
    Optionally fetches only the latest version if the given document_id is part of a version history
    (this part is simplified, true latest version finding might need traversal or a conceptual ID).
    For now, it respects is_latest_version if fetch_only_latest_version is True.
    """
    cursor = conn.cursor()
    sql = "SELECT * FROM ClientDocuments WHERE document_id = ?"
    params = [document_id]

    if not include_deleted:
        sql += " AND (is_deleted = 0 OR is_deleted IS NULL)"

    if fetch_only_latest_version: # This flag might be redundant if get_document_by_id is always for a specific version.
                                  # Keeping it for now if there's a use case.
                                  # A better approach for "latest" might be a different function that resolves the latest.
        sql += " AND (is_latest_version = 1 OR is_latest_version IS NULL)" # Assuming 1 is true, NULL might mean older system data

    try:
        cursor.execute(sql, tuple(params))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except sqlite3.Error as e:
        logging.error(f"SQLite error getting document by ID {document_id}: {e}", exc_info=True)
        return None


@_manage_conn
def get_documents_for_client(client_id: str, filters: dict = None, include_deleted: bool = False, fetch_only_latest_versions: bool = True, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves documents for a specific client, with optional filtering, soft delete handling,
    and option to fetch only latest versions.

    Args:
        client_id (str): The ID of the client.
        filters (dict, optional): Filtering dictionary.
        include_deleted (bool, optional): If True, includes soft-deleted documents. Defaults to False.
        fetch_only_latest_versions (bool, optional): If True, only fetches documents marked as the latest version.
                                                    Defaults to True.
        conn (sqlite3.Connection, optional): SQLite connection object.

    Returns:
        list[dict]: List of document dictionaries.
    """
    if not client_id:
        logging.error("get_documents_for_client: client_id cannot be empty.")
        return []

    try:
        conditions = ["client_id = ?"]
        params = [client_id]

        if not include_deleted:
            conditions.append("(is_deleted = 0 OR is_deleted IS NULL)")

        if fetch_only_latest_versions:
            conditions.append("(is_latest_version = 1 OR is_latest_version IS NULL)") # is NULL for older data before field existed

        if filters:
            order_identifier_filter = filters.get('order_identifier')
            if order_identifier_filter == 'NONE':
                conditions.append("order_identifier IS NULL")
            elif order_identifier_filter and order_identifier_filter != 'ALL':
                conditions.append("order_identifier = ?")
                params.append(order_identifier_filter)

        sql = f"SELECT * FROM ClientDocuments WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"

        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        # Convert rows to dicts (assuming conn.row_factory = sqlite3.Row)
        return [dict(row) for row in rows]

    except sqlite3.Error as e:
        logging.error(f"Error retrieving documents for client {client_id} with filters {filters}: {e} - SQL: {sql} - Params: {params}")
        return []
    except Exception as e: # Catch any other unexpected errors
        logging.error(f"Unexpected error in get_documents_for_client for client {client_id}: {e}")
        return []

@_manage_conn
def get_documents_for_project(project_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all documents for a specific project.
    STUB FUNCTION - Full implementation pending.
    """
    logging.warning(f"Called stub function get_documents_for_project for project_id: {project_id}. Full implementation is missing.")
    return []

@_manage_conn
def update_client_document(document_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    """
    Updates a client document.
    STUB FUNCTION - Full implementation pending.
    """
    # Changed document_id type hint to str
    logging.warning(f"Called stub function update_client_document for document_id: {document_id} with data: {data}. Full implementation is missing.")
    return False

# --- ClientDocumentNotes CRUD ---
# (Keep existing ClientDocumentNotes functions as they are, assuming they are not part of this subtask)
@_manage_conn
def get_client_document_notes(client_id: str, document_type: str = None, language_code: str = None, is_active: bool = None, conn: sqlite3.Connection = None) -> list[dict]:
    cursor=conn.cursor(); sql="SELECT * FROM ClientDocumentNotes WHERE client_id = ?"; params=[client_id]
    if document_type: sql+=" AND document_type = ?"; params.append(document_type)
    if language_code: sql+=" AND language_code = ?"; params.append(language_code)
    if is_active is not None: sql+=" AND is_active = ?"; params.append(1 if is_active else 0)
    sql+=" ORDER BY created_at DESC";
    try:
        cursor.execute(sql,params)
        # Assuming conn.row_factory = sqlite3.Row is set globally for the connection
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Error getting client document notes for client {client_id}: {e}")
        return []

@_manage_conn
def add_client_document_note(data: dict, conn: sqlite3.Connection = None) -> int | None:
    """
    Adds a new client document note.
    Handles UNIQUE constraint (client_id, document_type, language_code).
    """
    cursor = conn.cursor()
    sql = """
        INSERT INTO ClientDocumentNotes (
            client_id, document_type, language_code, note_content, is_active
        ) VALUES (?, ?, ?, ?, ?)
    """
    params = (
        data.get('client_id'),
        data.get('document_type'),
        data.get('language_code'),
        data.get('note_content'),
        data.get('is_active', True) # Default to True if not provided
    )
    try:
        cursor.execute(sql, params)
        # conn.commit() # Handled by _manage_conn
        last_id = cursor.lastrowid
        logging.info(f"Client document note added with ID: {last_id} for client {data.get('client_id')}")
        return last_id
    except sqlite3.IntegrityError:
        logging.warning(
            f"Failed to add client document note due to UNIQUE constraint violation "
            f"(client_id: {data.get('client_id')}, "
            f"document_type: {data.get('document_type')}, "
            f"language_code: {data.get('language_code')})."
        )
        return None # Indicates failure, possibly due to duplicate
    except sqlite3.Error as e:
        logging.error(f"Database error adding client document note for client {data.get('client_id')}: {e}")
        return None

@_manage_conn
def update_client_document_note(note_id: int, data: dict, conn: sqlite3.Connection = None) -> bool:
    logging.warning(f"Called stub function update_client_document_note for note_id {note_id} with data {data}. Full implementation is missing.")
    return False

@_manage_conn
def delete_client_document_note(note_id: int, conn: sqlite3.Connection = None) -> bool:
    logging.warning(f"Called stub function delete_client_document_note for note_id {note_id}. Full implementation is missing.")
    return False

@_manage_conn
def get_client_document_note_by_id(note_id: int, conn: sqlite3.Connection = None) -> dict | None:
    logging.warning(f"Called stub function get_client_document_note_by_id for note_id {note_id}. Full implementation is missing.")
    return None

@_manage_conn
def get_pdf_documents_for_order(commande_id: str, conn: sqlite3.Connection = None, include_deleted: bool = False) -> list[dict]:
    """
    Retrieves PDF documents for a specific commande_id.
    Filters by document_type_generated ending with 'PDF' (case-insensitive).
    """
    if not commande_id:
        logging.error("get_pdf_documents_for_order: commande_id cannot be empty.")
        return []

    cursor = conn.cursor()
    # We need client_id as well for constructing full paths later, so join with Clients if necessary,
    # or ensure ClientDocuments has enough path info or client_id.
    # For now, assume ClientDocuments has client_id and file_path_relative.
    sql = """
        SELECT document_id, client_id, document_name, file_path_relative, document_type_generated, created_at
        FROM ClientDocuments
        WHERE order_identifier = ?
          AND (UPPER(document_type_generated) LIKE '%PDF' OR UPPER(file_name_on_disk) LIKE '%.PDF')
    """
    params = [commande_id]

    if not include_deleted:
        sql += " AND (is_deleted = 0 OR is_deleted IS NULL)"

    sql += " ORDER BY created_at DESC"

    try:
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"SQLite error getting PDF documents for order {commande_id}: {e}", exc_info=True)
        return []

# Ensure the new function is added to __all__ if the module uses it.
# Not strictly necessary for direct calls but good practice for module interface.
# This requires checking how __all__ is defined or if it's used.
# For now, assuming direct import/use is fine.
