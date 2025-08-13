# db/cruds/clients/client_contacts_crud.py
import logging
from app.db.generic_crud import _manage_conn
from app.db.models.clients.clientcontacts import Clientcontacts
from app.db.models.clients.client import Client

logger = logging.getLogger(__name__)

@_manage_conn
def get_clients_for_contact(conn, contact_id: int) -> list[dict]:
    """
    Retrieves a list of clients associated with a given contact_id.
    Each item in the list is a dictionary containing client details
    and link information.
    """
    logger.info(f"Getting clients for contact_id: {contact_id}")
    query = """
    SELECT c.client_id, c.company_name, cc.is_primary_for_client
    FROM clients c
    JOIN client_contacts cc ON c.client_id = cc.client_id
    WHERE cc.contact_id = ?;
    """
    cursor = conn.cursor()
    cursor.execute(query, (contact_id,))
    clients_data = cursor.fetchall()
    result = [{'client_id': row[0], 'client_name': row[1], 'is_primary_for_client': bool(row[2])} for row in clients_data]
    logger.info(f"Found {len(result)} clients for contact_id {contact_id}")
    return result

@_manage_conn
def link_contact_to_client(conn, client_id: int, contact_id: int, is_primary: bool = False, can_receive_documents: bool = True, role_in_client: str = None, notes: str = None) -> int | None:
    """
    Links an existing contact to a client in the client_contacts table.
    Returns the ID of the new link, or None if linking failed.
    """
    logger.info(f"Linking contact_id {contact_id} to client_id {client_id}")
    query = """
    INSERT INTO client_contacts (client_id, contact_id, is_primary_for_client, can_receive_documents)
    VALUES (?, ?, ?, ?);
    """
    cursor = conn.cursor()
    cursor.execute(query, (client_id, contact_id, is_primary, can_receive_documents))
    conn.commit()
    link_id = cursor.lastrowid
    logger.info(f"Contact {contact_id} linked to client {client_id}. New link ID: {link_id}")
    return link_id

@_manage_conn
def unlink_contact_from_client(conn, client_contact_link_id: int) -> bool:
    """
    Removes a specific link between a client and a contact using the link's ID.
    """
    logger.info(f"Unlinking client_contact_link_id: {client_contact_link_id}")
    query = "DELETE FROM client_contacts WHERE client_contact_id = ?;"
    cursor = conn.cursor()
    cursor.execute(query, (client_contact_link_id,))
    conn.commit()
    return cursor.rowcount > 0

@_manage_conn
def get_specific_client_contact_link_details(conn, client_contact_link_id: int) -> dict | None:
    """
    Retrieves details for a specific client-contact link by its ID.
    """
    logger.info(f"Getting details for client_contact_link_id: {client_contact_link_id}")
    query = "SELECT client_id, contact_id, is_primary_for_client, can_receive_documents FROM client_contacts WHERE client_contact_id = ?;"
    cursor = conn.cursor()
    cursor.execute(query, (client_contact_link_id,))
    row = cursor.fetchone()
    if row:
        return {'client_id': row[0], 'contact_id': row[1], 'is_primary_for_client': bool(row[2]), 'can_receive_documents': bool(row[3])}
    return None

@_manage_conn
def update_client_contact_link(conn, client_contact_link_id: int, link_data: dict) -> bool:
    """
    Updates details of an existing client-contact link.
    """
    logger.info(f"Updating client_contact_link_id {client_contact_link_id} with data: {link_data}")
    fields_to_update = []
    params = []
    for key, value in link_data.items():
        if key in ['is_primary_for_client', 'can_receive_documents']: # Whitelist valid fields
            fields_to_update.append(f"{key} = ?")
            params.append(value)
    if not fields_to_update:
        logger.warning("No valid fields to update.")
        return False

    params.append(client_contact_link_id)
    query = f"UPDATE client_contacts SET {', '.join(fields_to_update)} WHERE client_contact_id = ?;"
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    conn.commit()
    return cursor.rowcount > 0

@_manage_conn
def check_if_contact_linked_to_client(conn, client_id: int, contact_id: int) -> bool:
    """
    Checks if a specific contact is already linked to a specific client.
    """
    logger.info(f"Checking if contact_id {contact_id} is linked to client_id {client_id}")
    query = "SELECT 1 FROM client_contacts WHERE client_id = ? AND contact_id = ? LIMIT 1;"
    cursor = conn.cursor()
    cursor.execute(query, (client_id, contact_id))
    return cursor.fetchone() is not None
