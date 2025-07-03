import sqlite3
from datetime import datetime
import logging
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def link_contact_to_entity(entity_id: str, entity_type: str, contact_id: int,
                           role_in_entity: str = None, is_primary: bool = False,
                           can_receive_documents: bool = True, notes: str = None,
                           conn: sqlite3.Connection = None) -> int | None:
    """
    Links a contact from the central Contacts table to an entity (e.g., Transporter, FreightForwarder).
    Returns the ID of the new link (entity_contact_id) or None if an error occurs.
    """
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    sql = """
        INSERT INTO EntityContacts
            (entity_id, entity_type, contact_id, role_in_entity, is_primary, can_receive_documents, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (entity_id, entity_type, contact_id, role_in_entity,
              1 if is_primary else 0, 1 if can_receive_documents else 0,
              notes, now, now)
    try:
        cursor.execute(sql, params)
        new_link_id = cursor.lastrowid
        logger.info(f"Successfully linked contact_id {contact_id} to entity {entity_type}:{entity_id} with role '{role_in_entity}'. New link ID: {new_link_id}")
        return new_link_id
    except sqlite3.IntegrityError as e:
        logger.warning(f"Failed to link contact {contact_id} to entity {entity_type}:{entity_id}. Link might already exist or contact_id invalid. Error: {e}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error linking contact {contact_id} to entity {entity_type}:{entity_id}: {e}")
        return None

@_manage_conn
def unlink_contact_from_entity(entity_contact_id: int, conn: sqlite3.Connection = None) -> bool:
    """
    Deletes a specific link between an entity and a contact.
    Does NOT delete the contact from the central Contacts table.
    Returns True if the link was deleted, False otherwise.
    """
    cursor = conn.cursor()
    sql = "DELETE FROM EntityContacts WHERE entity_contact_id = ?"
    try:
        cursor.execute(sql, (entity_contact_id,))
        if cursor.rowcount > 0:
            logger.info(f"Successfully unlinked entity_contact_id {entity_contact_id}.")
            return True
        else:
            logger.warning(f"No link found to delete for entity_contact_id {entity_contact_id}.")
            return False
    except sqlite3.Error as e:
        logger.error(f"Database error unlinking entity_contact_id {entity_contact_id}: {e}")
        return False

@_manage_conn
def get_contacts_for_entity(entity_id: str, entity_type: str, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all contacts linked to a specific entity, fetching full
    contact details from the central Contacts table.
    """
    cursor = conn.cursor()
    sql = """
        SELECT c.*, ec.entity_contact_id, ec.role_in_entity,
               ec.is_primary, ec.can_receive_documents, ec.notes AS link_notes,
               ec.created_at AS link_created_at, ec.updated_at AS link_updated_at
        FROM Contacts c
        JOIN EntityContacts ec ON c.contact_id = ec.contact_id
        WHERE ec.entity_id = ? AND ec.entity_type = ?
        ORDER BY ec.is_primary DESC, c.name, c.displayName
    """
    try:
        cursor.execute(sql, (entity_id, entity_type))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_contacts_for_entity for {entity_type}:{entity_id}: {e}")
        return []

@_manage_conn
def update_entity_contact_link(entity_contact_id: int, details: dict, conn: sqlite3.Connection = None) -> bool:
    """
    Updates details of a specific entity-contact link.
    `details` can contain: 'role_in_entity', 'is_primary', 'can_receive_documents', 'notes'.
    """
    if not details:
        logger.warning(f"No details provided to update link entity_contact_id {entity_contact_id}.")
        return False

    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    fields_to_update_sql = []
    params_sql = []

    if 'role_in_entity' in details:
        fields_to_update_sql.append("role_in_entity = ?")
        params_sql.append(details['role_in_entity'])
    if 'is_primary' in details:
        fields_to_update_sql.append("is_primary = ?")
        params_sql.append(1 if details['is_primary'] else 0)
    if 'can_receive_documents' in details:
        fields_to_update_sql.append("can_receive_documents = ?")
        params_sql.append(1 if details['can_receive_documents'] else 0)
    if 'notes' in details:
        fields_to_update_sql.append("notes = ?")
        params_sql.append(details['notes'])

    if not fields_to_update_sql:
        logger.info(f"No valid fields to update for link entity_contact_id {entity_contact_id}.")
        return False # Or True, if no change means success

    fields_to_update_sql.append("updated_at = ?")
    params_sql.append(now)
    params_sql.append(entity_contact_id)

    sql_update_link = f"UPDATE EntityContacts SET {', '.join(fields_to_update_sql)} WHERE entity_contact_id = ?"

    try:
        cursor.execute(sql_update_link, tuple(params_sql))
        if cursor.rowcount > 0:
            logger.info(f"Successfully updated link details for entity_contact_id {entity_contact_id}.")
            return True
        else:
            # This could mean the link ID doesn't exist, or values are the same
            logger.warning(f"No rows updated for entity_contact_id {entity_contact_id}. Link may not exist or data unchanged.")
            # Check if exists to differentiate
            cursor.execute("SELECT 1 FROM EntityContacts WHERE entity_contact_id = ?", (entity_contact_id,))
            return cursor.fetchone() is not None # True if exists (even if data unchanged), False if not found
    except sqlite3.Error as e:
        logger.error(f"Database error updating link entity_contact_id {entity_contact_id}: {e}")
        return False

@_manage_conn
def get_entity_contact_link_details(entity_contact_id: int, conn: sqlite3.Connection = None) -> dict | None:
    """
    Retrieves details of a specific entity-contact link, joining with the central
    Contacts table to get full contact details.
    """
    cursor = conn.cursor()
    sql = """
        SELECT c.*, ec.entity_contact_id, ec.entity_id, ec.entity_type,
               ec.role_in_entity, ec.is_primary, ec.can_receive_documents, ec.notes AS link_notes,
               ec.created_at AS link_created_at, ec.updated_at AS link_updated_at
        FROM Contacts c
        JOIN EntityContacts ec ON c.contact_id = ec.contact_id
        WHERE ec.entity_contact_id = ?
    """
    try:
        cursor.execute(sql, (entity_contact_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error in get_entity_contact_link_details for ID {entity_contact_id}: {e}")
        return None

@_manage_conn
def get_entities_for_contact(contact_id: int, entity_type: str = None, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all entities (and their link details) associated with a specific contact.
    Can optionally filter by entity_type.
    """
    cursor = conn.cursor()
    sql = """
        SELECT ec.entity_id, ec.entity_type, ec.entity_contact_id, ec.role_in_entity,
               ec.is_primary, ec.can_receive_documents, ec.notes AS link_notes,
               ec.created_at AS link_created_at, ec.updated_at AS link_updated_at
        FROM EntityContacts ec
        WHERE ec.contact_id = ?
    """
    params = [contact_id]
    if entity_type:
        sql += " AND ec.entity_type = ?"
        params.append(entity_type)

    sql += " ORDER BY ec.entity_type, ec.entity_id"

    try:
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_entities_for_contact for contact_id {contact_id} (type: {entity_type}): {e}")
        return []

@_manage_conn
def delete_all_contact_links_for_entity(entity_id: str, entity_type: str, conn: sqlite3.Connection = None) -> bool:
    """
    Deletes all contact links for a specific entity from EntityContacts.
    Does NOT delete contacts from the central Contacts table.
    Returns True if the operation was successful (even if no rows were deleted).
    """
    cursor = conn.cursor()
    sql = "DELETE FROM EntityContacts WHERE entity_id = ? AND entity_type = ?"
    try:
        cursor.execute(sql, (entity_id, entity_type))
        logger.info(f"Attempted deletion of all contact links for entity {entity_type}:{entity_id}. Rows affected: {cursor.rowcount}")
        return True # Operation is successful even if no rows were affected (e.g., no links existed)
    except sqlite3.Error as e:
        logger.error(f"Database error deleting all contact links for entity {entity_type}:{entity_id}: {e}")
        return False

__all__ = [
    "link_contact_to_entity",
    "unlink_contact_from_entity",
    "get_contacts_for_entity",
    "update_entity_contact_link",
    "get_entity_contact_link_details",
    "get_entities_for_contact",
    "delete_all_contact_links_for_entity"
]
