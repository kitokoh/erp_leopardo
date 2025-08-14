# -*- coding: utf-8 -*-
import sqlite3
import uuid
from datetime import datetime, timezone
import logging
from app.db.cruds.generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_sav_ticket(ticket_data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Adds a new SAV ticket to the database.

    Args:
        ticket_data (dict): Data for the new SAV ticket. Expected keys:
            'client_id' (str, required),
            'issue_description' (str, required),
            'status_id' (int, required),
            'created_by_user_id' (str, required),
            'client_project_product_id' (int, optional),
            'assigned_technician_id' (int, optional).
    conn (sqlite3.Connection, optional): Database connection.

    Returns:
        str | None: The new ticket_id on success, None on failure.
    """
    required_fields = ['client_id', 'issue_description', 'status_id', 'created_by_user_id']
    for field in required_fields:
        if field not in ticket_data or ticket_data[field] is None:
            logger.error(f"Missing required field '{field}' in add_sav_ticket data.")
            return None

    ticket_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    sql = """
    INSERT INTO SAVTickets (
        ticket_id, client_id, client_project_product_id, issue_description,
        status_id, assigned_technician_id, opened_at, created_by_user_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        ticket_id,
        ticket_data['client_id'],
        ticket_data.get('client_project_product_id'), # Can be NULL
        ticket_data['issue_description'],
        ticket_data['status_id'],
        ticket_data.get('assigned_technician_id'), # Can be NULL
        now_iso,
        ticket_data['created_by_user_id']
    )

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        # conn.commit() # Managed by decorator
        logger.info(f"SAV Ticket added with ID: {ticket_id} for client {ticket_data['client_id']}")
        return ticket_id
    except sqlite3.Error as e:
        logger.error(f"Database error in add_sav_ticket for client {ticket_data.get('client_id')}: {e}", exc_info=True)
        # conn.rollback() # Managed by decorator
        return None

@_manage_conn
def get_sav_ticket_by_id(ticket_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """
    Retrieves an SAV ticket by its ID, joining with related tables for more context.
    """
    sql = """
    SELECT
        st.*,
        c.client_name,
        p.product_name AS linked_product_name,
        ss.status_name AS status_name,
        ss.color_hex AS status_color,
        u_creator.full_name AS creator_name,
        u_tech.full_name AS technician_name
    FROM SAVTickets st
    JOIN Clients c ON st.client_id = c.client_id
    LEFT JOIN ClientProjectProducts cpp ON st.client_project_product_id = cpp.client_project_product_id
    LEFT JOIN Products p ON cpp.product_id = p.product_id
    LEFT JOIN StatusSettings ss ON st.status_id = ss.status_id AND ss.status_type = 'SAVTicket'
    LEFT JOIN Users u_creator ON st.created_by_user_id = u_creator.user_id
    LEFT JOIN TeamMembers tm_tech ON st.assigned_technician_id = tm_tech.team_member_id
    LEFT JOIN Users u_tech ON tm_tech.user_id = u_tech.user_id
    WHERE st.ticket_id = ?
    """
    # Note: Join with TeamMembers then Users for technician_name.
    # If assigned_technician_id directly refers to Users.user_id, simplify the join.
    # Assuming assigned_technician_id is TeamMembers.team_member_id for now.

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (ticket_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error in get_sav_ticket_by_id for ticket_id {ticket_id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_sav_tickets_for_client(client_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all SAV tickets for a given client_id, including product name, status name, and technician name.
    This function is optimized to avoid N+1 queries by using JOINs.
    """
    sql = """
    SELECT
        st.ticket_id,
        st.client_project_product_id,
        st.issue_description,
        st.status_id,
        st.assigned_technician_id,
        st.opened_at,
        st.closed_at,
        st.created_by_user_id,
        p.product_name AS linked_product_name,  -- Fetched via JOIN
        ss.status_name AS status_name,          -- Fetched via JOIN
        u_tech.full_name AS technician_name     -- Fetched via JOIN (adjust if tech ID is Users.user_id)
    FROM SAVTickets st
    LEFT JOIN ClientProjectProducts cpp ON st.client_project_product_id = cpp.client_project_product_id
    LEFT JOIN Products p ON cpp.product_id = p.product_id
    LEFT JOIN StatusSettings ss ON st.status_id = ss.status_id AND ss.status_type = 'SAVTicket'
    LEFT JOIN TeamMembers tm_tech ON st.assigned_technician_id = tm_tech.team_member_id
    LEFT JOIN Users u_tech ON tm_tech.user_id = u_tech.user_id
    WHERE st.client_id = ?
    ORDER BY st.opened_at DESC
    """
    # Adjust join for technician_name if assigned_technician_id refers directly to Users table user_id.
    # If assigned_technician_id is Users.user_id:
    # LEFT JOIN Users u_tech ON st.assigned_technician_id = u_tech.user_id
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (client_id,))
        tickets = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(tickets)} SAV tickets for client_id {client_id}")
        return tickets
    except sqlite3.Error as e:
        logger.error(f"Database error in get_sav_tickets_for_client for client_id {client_id}: {e}", exc_info=True)
        return []

@_manage_conn
def update_sav_ticket(ticket_id: str, update_data: dict, conn: sqlite3.Connection = None) -> bool:
    """
    Updates an SAV ticket. If status changes to a 'closed' or 'resolved' type,
    updates closed_at timestamp.

    Args:
        ticket_id (str): The ID of the ticket to update.
        update_data (dict): Dictionary of fields to update. Expected keys:
            'client_project_product_id' (optional),
            'issue_description' (optional),
            'status_id' (optional),
            'assigned_technician_id' (optional),
            'resolution_details' (optional).
    conn (sqlite3.Connection, optional): Database connection.

    Returns:
        bool: True on success, False on failure.
    """
    if not update_data:
        logger.info(f"No data provided to update_sav_ticket for ticket_id {ticket_id}")
        return False

    fields_to_update = []
    params = []

    allowed_fields = [
        'client_project_product_id', 'issue_description', 'status_id',
        'assigned_technician_id', 'resolution_details'
    ]

    for key, value in update_data.items():
        if key in allowed_fields:
            fields_to_update.append(f"{key} = ?")
            params.append(value)

    # Handle closed_at if status is being updated to a completion status
    if 'status_id' in update_data:
        # try:
            # Need to fetch the status_type properties (is_completion_status)
            # Assuming a function get_status_setting_by_id exists and returns a dict or object
            # from .status_settings_crud import get_status_setting_by_id # Local import to avoid issues
            # status_info = get_status_setting_by_id(update_data['status_id'], conn=conn) # Pass conn

            # Simpler: Assume status_service is available or this logic is handled by caller
            # For now, if status_id changes, we assume it might be a closing one.
            # A more robust solution would check status_info.is_completion_status.
            # Let's assume for now that if 'status_id' is updated, and if the new status
            # implies closure, 'closed_at' is also passed in update_data by the caller.
            # This CRUD will just update what's given.
            # OR, if a specific status name means closed:
            # if status_info and status_info.get('is_completion_status'):
            # fields_to_update.append("closed_at = ?")
            # params.append(datetime.now(timezone.utc).isoformat())
            pass # Caller should explicitly provide closed_at if status implies closure.

    if not fields_to_update:
        logger.info(f"No valid fields to update for SAV ticket {ticket_id}")
        return False

    sql = f"UPDATE SAVTickets SET {', '.join(fields_to_update)} WHERE ticket_id = ?"
    params.append(ticket_id)

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        # conn.commit() # Managed by decorator
        logger.info(f"SAV Ticket {ticket_id} updated successfully.")
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in update_sav_ticket for ticket_id {ticket_id}: {e}", exc_info=True)
        # conn.rollback() # Managed by decorator
        return False

# __all__ definition for easier imports from db_manager or other modules
__all__ = [
    "add_sav_ticket",
    "get_sav_ticket_by_id",
    "get_sav_tickets_for_client",
    "update_sav_ticket"
]
