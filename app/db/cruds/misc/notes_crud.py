from sqlalchemy.orm import Session
from app.models.db.documents.defaultdocumentnotes import Defaultdocumentnotes
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DefaultDocumentNotesCRUD:
    def get_default_document_note(self, db: Session, document_type: str, language_code: str) -> Defaultdocumentnotes | None:
        return db.query(Defaultdocumentnotes).filter_by(document_type=document_type, language_code=language_code).first()

    def add_default_document_note(self, db: Session, document_type: str, language_code: str, note_content: str) -> Defaultdocumentnotes:
        new_note = Defaultdocumentnotes(
            document_type=document_type,
            language_code=language_code,
            note_content=note_content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return new_note

default_document_notes_crud = DefaultDocumentNotesCRUD()

# The rest of the file is kept as is for now, to avoid breaking other parts of the app
# that might still be using the old functions. I will refactor them later if needed.

import sqlite3
from ..generic_crud import _manage_conn


# --- CommandeDocumentNotes CRUD ---

@_manage_conn
def add_commande_document_note(commande_document_id: str, note_content: str, language_code: str, conn: sqlite3.Connection = None) -> int | None:
    """Adds a new commande-specific document note."""
    sql = """
        INSERT INTO CommandeDocumentNotes (commande_document_id, note_content, language_code, updated_at)
        VALUES (?, ?, ?, ?)
    """
    try:
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        cursor.execute(sql, (commande_document_id, note_content, language_code, current_time))
        # conn.commit() # Handled by _manage_conn
        last_id = cursor.lastrowid
        logging.info(f"Commande document note added with ID: {last_id} for commande_document_id '{commande_document_id}'.")
        return last_id
    except sqlite3.IntegrityError:
        logging.warning(
            f"Failed to add commande document note due to UNIQUE constraint violation "
            f"(commande_document_id: {commande_document_id})."
        )
        return None
    except sqlite3.Error as e:
        logging.error(f"Database error adding commande document note for commande_document_id '{commande_document_id}': {e}", exc_info=True)
        return None

@_manage_conn
def get_commande_document_note(commande_document_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a specific commande document note by commande_document_id."""
    sql = "SELECT * FROM CommandeDocumentNotes WHERE commande_document_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (commande_document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logging.error(f"Database error getting commande document note for commande_document_id '{commande_document_id}': {e}", exc_info=True)
        return None

@_manage_conn
def update_commande_document_note(note_id: int = None, commande_document_id: str = None, note_content: str = None, language_code: str = None, conn: sqlite3.Connection = None) -> bool:
    """
    Updates an existing commande document note.
    Can be identified by `note_id` (primary key) or `commande_document_id` (unique).
    If using `commande_document_id`, ensure it's for updating an existing note, not creating.
    """
    fields_to_update = []
    params = []
    identifier_field = None
    identifier_value = None

    if note_id is not None:
        identifier_field = "id"
        identifier_value = note_id
    elif commande_document_id is not None:
        identifier_field = "commande_document_id"
        identifier_value = commande_document_id
    else:
        logging.error("Either note_id or commande_document_id must be provided to update commande document note.")
        return False

    if note_content is not None:
        fields_to_update.append("note_content = ?")
        params.append(note_content)
    if language_code is not None: # Allow updating language if needed, though typically tied to document
        fields_to_update.append("language_code = ?")
        params.append(language_code)

    if not fields_to_update:
        logging.warning("No fields provided to update for commande document note.")
        return False

    fields_to_update.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(identifier_value)

    sql = f"UPDATE CommandeDocumentNotes SET {', '.join(fields_to_update)} WHERE {identifier_field} = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        # conn.commit() # Handled by _manage_conn
        updated_rows = cursor.rowcount
        if updated_rows > 0:
            logging.info(f"Commande document note identified by {identifier_field}='{identifier_value}' updated successfully.")
        else:
            logging.warning(f"No commande document note found with {identifier_field}='{identifier_value}' to update.")
        return updated_rows > 0
    except sqlite3.IntegrityError:
        # This could happen if trying to update commande_document_id to one that already exists and has a note.
        logging.warning(
            f"Failed to update commande document note ({identifier_field}='{identifier_value}') due to UNIQUE constraint violation."
        )
        return False
    except sqlite3.Error as e:
        logging.error(f"Database error updating commande document note ({identifier_field}='{identifier_value}'): {e}", exc_info=True)
        return False

@_manage_conn
def upsert_commande_document_note(commande_document_id: str, note_content: str, language_code: str, conn: sqlite3.Connection = None) -> int | None:
    """
    Inserts a new commande document note or updates it if it already exists for the given commande_document_id.
    Returns the ID of the inserted or updated note.
    """
    # Check if a note already exists for this commande_document_id
    existing_note = get_commande_document_note(commande_document_id, conn=conn)

    if existing_note:
        # Update existing note
        sql_update = """
            UPDATE CommandeDocumentNotes
            SET note_content = ?, language_code = ?, updated_at = ?
            WHERE commande_document_id = ?
        """
        try:
            cursor = conn.cursor()
            current_time = datetime.utcnow().isoformat()
            cursor.execute(sql_update, (note_content, language_code, current_time, commande_document_id))
            logging.info(f"Commande document note updated for commande_document_id '{commande_document_id}'.")
            return existing_note['id'] # Return existing ID
        except sqlite3.Error as e:
            logging.error(f"Database error updating commande document note for commande_document_id '{commande_document_id}': {e}", exc_info=True)
            return None
    else:
        # Insert new note
        return add_commande_document_note(commande_document_id, note_content, language_code, conn=conn)


@_manage_conn
def delete_commande_document_note(note_id: int = None, commande_document_id: str = None, conn: sqlite3.Connection = None) -> bool:
    """
    Deletes a commande document note by its ID or by commande_document_id.
    """
    if note_id is None and commande_document_id is None:
        logging.error("Either note_id or commande_document_id must be provided to delete commande document note.")
        return False

    identifier_field = "id" if note_id is not None else "commande_document_id"
    identifier_value = note_id if note_id is not None else commande_document_id

    sql = f"DELETE FROM CommandeDocumentNotes WHERE {identifier_field} = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (identifier_value,))
        # conn.commit() # Handled by _manage_conn
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logging.info(f"Commande document note with {identifier_field}='{identifier_value}' deleted successfully.")
        else:
            logging.warning(f"No commande document note found with {identifier_field}='{identifier_value}' to delete.")
        return deleted_rows > 0
    except sqlite3.Error as e:
        logging.error(f"Database error deleting commande document note ({identifier_field}='{identifier_value}'): {e}", exc_info=True)
        return False

@_manage_conn
def list_commande_document_notes_for_commande(commande_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Lists all custom notes for documents associated with a specific commande.
    This requires joining with ClientDocuments table if commande_id is not directly in CommandeDocumentNotes.
    For now, assuming commande_document_id in CommandeDocumentNotes refers to ClientDocuments.document_id,
    and ClientDocuments has a commande_id field.
    """
    # This function might be complex if commande_document_id is not directly linkable to a main commande_id without joins.
    # The current CommandeDocumentNotes table links via 'commande_document_id' which is assumed to be ClientDocuments.document_id.
    # We need to find ClientDocuments that belong to the given 'commande_id'.
    sql = """
        SELECT cdn.*
        FROM CommandeDocumentNotes cdn
        JOIN ClientDocuments cd ON cdn.commande_document_id = cd.document_id
        WHERE cd.commande_id = ?
        ORDER BY cdn.created_at DESC
    """
    # If ClientDocuments.commande_id is not reliable or doesn't exist, this query needs adjustment.
    # Alternative: If `order_identifier` in ClientDocuments is the commande_id/reference:
    # sql = """
    #     SELECT cdn.*
    #     FROM CommandeDocumentNotes cdn
    #     JOIN ClientDocuments cd ON cdn.commande_document_id = cd.document_id
    #     WHERE cd.order_identifier = ?  -- Assuming order_identifier is the link to the commande
    #     ORDER BY cdn.created_at DESC
    # """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (commande_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logging.error(f"Database error listing commande document notes for commande_id '{commande_id}': {e}", exc_info=True)
        return []

@_manage_conn
def get_effective_document_note(commande_document_id: str, document_type: str, language_code: str, conn: sqlite3.Connection = None) -> str | None:
    """
    Retrieves the effective note for a given document instance.
    It first checks for a custom note in CommandeDocumentNotes.
    If not found, it falls back to the DefaultDocumentNotes.
    """
    custom_note = get_commande_document_note(commande_document_id, conn=conn)
    if custom_note and custom_note.get('note_content'):
        return custom_note['note_content']

    default_note = default_document_notes_crud.get_default_document_note(db=conn, document_type=document_type, language_code=language_code)
    if default_note and default_note.note_content:
        return default_note.note_content

    return None
