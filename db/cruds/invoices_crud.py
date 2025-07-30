import sqlite3
import uuid
from datetime import datetime
import os

# Logic to import DATABASE_PATH from root config.py
import sys
import logging # Added logging

# Correctly determine the application's root directory relative to invoices_crud.py
# invoices_crud.py is in db/cruds/
# config.py is in project root (parent of db/)
# So, os.path.dirname(__file__) -> db/cruds
# os.path.join(..., "..") -> db/
# os.path.join(..., "..", "..") -> project_root/
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root_dir = os.path.abspath(os.path.join(_current_file_dir, "..", ".."))

if _project_root_dir not in sys.path:
    sys.path.insert(0, _project_root_dir)

try:
    from config import DATABASE_PATH
    # logging.debug(f"invoices_crud: Successfully imported DATABASE_PATH: {DATABASE_PATH}")
except ImportError as e:
    logging.error(f"CRITICAL: Could not import DATABASE_PATH from config.py (path: {_project_root_dir}): {e}. Falling back to a default path.", exc_info=True)
    # Fallback path relative to this file if config.py isn't found at assumed project root
    _db_dir_fallback = os.path.join(os.path.dirname(_current_file_dir), "data_fallback") # db/data_fallback/
    os.makedirs(_db_dir_fallback, exist_ok=True)
    DATABASE_PATH = os.path.join(_db_dir_fallback, "app_invoices_fallback.db")
    logging.warning(f"invoices_crud: Using fallback DATABASE_PATH: {DATABASE_PATH}")
finally:
    # Clean up sys.path if the directory was added by this specific import logic
    if sys.path[0] == _project_root_dir: # Check if it's the one we added
        sys.path.pop(0)
        # logging.debug(f"invoices_crud: Removed {_project_root_dir} from sys.path after import attempt.")


logger = logging.getLogger(__name__) # Initialize logger for this module

def _get_db_connection():
    """Returns a SQLite connection object to the database."""
    conn = sqlite3.connect(DATABASE_PATH) # Uses the DATABASE_PATH from the new import logic
    conn.row_factory = sqlite3.Row
    return conn

def add_invoice(invoice_data: dict) -> str | None:
    """
    Adds a new invoice to the database.

    Args:
        invoice_data: A dictionary containing invoice details.
                      Required: client_id, invoice_number, issue_date, due_date, total_amount, currency.
                      Optional: project_id, document_id, payment_status, payment_date,
                                payment_method, transaction_id, notes.

    Returns:
        The new invoice_id on success, None on failure.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    invoice_id = str(uuid.uuid4())

    required_fields = ['client_id', 'invoice_number', 'issue_date', 'due_date', 'total_amount', 'currency']
    for field in required_fields:
        if field not in invoice_data:
            logger.error(f"Missing required field '{field}' in invoice_data for add_invoice.")
            conn.close()
            return None

    sql = """
    INSERT INTO Invoices (
        invoice_id, client_id, project_id, document_id, invoice_number,
        issue_date, due_date, total_amount, currency, payment_status,
        payment_date, payment_method, transaction_id, notes, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """
    try:
        cursor.execute(sql, (
            invoice_id,
            invoice_data['client_id'],
            invoice_data.get('project_id'),
            invoice_data.get('document_id'),
            invoice_data['invoice_number'],
            invoice_data['issue_date'],
            invoice_data['due_date'],
            invoice_data['total_amount'],
            invoice_data['currency'],
            invoice_data.get('payment_status', 'unpaid'), # Default in schema, but can be explicit
            invoice_data.get('payment_date'),
            invoice_data.get('payment_method'),
            invoice_data.get('transaction_id'),
            invoice_data.get('notes')
        ))
        conn.commit()
        return invoice_id
    except sqlite3.Error as e:
        logger.error(f"Database error in add_invoice: {e}", exc_info=True)
        conn.rollback()
        return None
    finally:
        conn.close()

def get_invoice_by_id(invoice_id: str) -> dict | None:
    """
    Retrieves an invoice by its ID.

    Args:
        invoice_id: The ID of the invoice to retrieve.

    Returns:
        A dictionary representing the invoice if found, else None.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM Invoices WHERE invoice_id = ?"
    try:
        cursor.execute(sql, (invoice_id,))
        invoice = cursor.fetchone()
        return dict(invoice) if invoice else None
    except sqlite3.Error as e:
        logger.error(f"Database error in get_invoice_by_id for invoice_id {invoice_id}: {e}", exc_info=True)
        return None
    finally:
        conn.close()

def get_invoices_by_client_id(client_id: str) -> list[dict]:
    """
    Retrieves all invoices for a given client_id.

    Args:
        client_id: The ID of the client.

    Returns:
        A list of invoice dictionaries.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM Invoices WHERE client_id = ? ORDER BY issue_date DESC"
    try:
        cursor.execute(sql, (client_id,))
        invoices = cursor.fetchall()
        return [dict(invoice) for invoice in invoices]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_invoices_by_client_id for client_id {client_id}: {e}", exc_info=True)
        return []
    finally:
        conn.close()

def get_invoices_by_project_id(project_id: str) -> list[dict]:
    """
    Retrieves all invoices for a given project_id.

    Args:
        project_id: The ID of the project.

    Returns:
        A list of invoice dictionaries.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM Invoices WHERE project_id = ? ORDER BY issue_date DESC"
    try:
        cursor.execute(sql, (project_id,))
        invoices = cursor.fetchall()
        return [dict(invoice) for invoice in invoices]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_invoices_by_project_id for project_id {project_id}: {e}", exc_info=True)
        return []
    finally:
        conn.close()

def update_invoice(invoice_id: str, update_data: dict) -> bool:
    """
    Updates an existing invoice.

    Args:
        invoice_id: The ID of the invoice to update.
        update_data: A dictionary of columns to update with their new values.

    Returns:
        True on success, False on failure.
    """
    if not update_data:
        return False

    conn = _get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []
    for key, value in update_data.items():
        # Basic validation for allowed fields to prevent SQL injection if keys are crafted
        # A more robust solution might involve a whitelist of updatable fields
        if key in ['client_id', 'project_id', 'document_id', 'invoice_number',
                   'issue_date', 'due_date', 'total_amount', 'currency', 'payment_status',
                   'payment_date', 'payment_method', 'transaction_id', 'notes']:
            fields.append(f"{key} = ?")
            values.append(value)
        else:
            logger.warning(f"Attempted to update non-allowed field '{key}' in update_invoice for invoice_id {invoice_id}. Skipping.")

    if not fields: # No valid fields to update
        logger.info(f"No valid fields provided to update_invoice for invoice_id {invoice_id}.")
        conn.close()
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE Invoices SET {', '.join(fields)} WHERE invoice_id = ?"
    values.append(invoice_id)

    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in update_invoice for invoice_id {invoice_id}: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_invoice(invoice_id: str) -> bool:
    """
    Deletes an invoice from the database.

    Args:
        invoice_id: The ID of the invoice to delete.

    Returns:
        True on success, False on failure.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM Invoices WHERE invoice_id = ?"
    try:
        cursor.execute(sql, (invoice_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_invoice for invoice_id {invoice_id}: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()

def list_all_invoices(filters: dict = None, sort_by: str = None, limit: int = None, offset: int = None) -> list[dict]:
    """
    Lists all invoices with optional filtering, sorting, and pagination.

    Args:
        filters: A dictionary of filters. Supported keys:
                 'payment_status', 'client_id', 'project_id',
                 'issue_date_start', 'issue_date_end',
                 'due_date_start', 'due_date_end'.
        sort_by: Column to sort by, e.g., "issue_date_desc", "total_amount_asc".
                 Supported columns: issue_date, due_date, total_amount, payment_status.
        limit: Maximum number of invoices to return.
        offset: Number of invoices to skip.

    Returns:
        A list of invoice dictionaries.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    base_sql = "SELECT * FROM Invoices"
    where_clauses = []
    params = []

    if filters:
        if 'payment_status' in filters:
            where_clauses.append("payment_status = ?")
            params.append(filters['payment_status'])
        if 'client_id' in filters:
            where_clauses.append("client_id = ?")
            params.append(filters['client_id'])
        if 'project_id' in filters:
            where_clauses.append("project_id = ?")
            params.append(filters['project_id'])
        if 'issue_date_start' in filters:
            where_clauses.append("issue_date >= ?")
            params.append(filters['issue_date_start'])
        if 'issue_date_end' in filters:
            where_clauses.append("issue_date <= ?")
            params.append(filters['issue_date_end'])
        if 'due_date_start' in filters:
            where_clauses.append("due_date >= ?")
            params.append(filters['due_date_start'])
        if 'due_date_end' in filters:
            where_clauses.append("due_date <= ?")
            params.append(filters['due_date_end'])

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    if sort_by:
        sort_column, sort_direction = sort_by.rsplit('_', 1)
        allowed_sort_columns = ['issue_date', 'due_date', 'total_amount', 'payment_status']
        if sort_column in allowed_sort_columns and sort_direction.upper() in ['ASC', 'DESC']:
            base_sql += f" ORDER BY {sort_column} {sort_direction.upper()}"
        else:
            logger.warning(f"Invalid sort_by parameter '{sort_by}' in list_all_invoices. Using default sorting.")
            base_sql += " ORDER BY issue_date DESC" # Default sort
    else:
        base_sql += " ORDER BY issue_date DESC" # Default sort if not specified

    if limit is not None:
        base_sql += " LIMIT ?"
        params.append(limit)

    if offset is not None:
        if limit is None: # Offset requires limit in SQLite
            base_sql += " LIMIT -1" # Effectively no limit, but necessary for offset
        base_sql += " OFFSET ?"
        params.append(offset)

    try:
        cursor.execute(base_sql, tuple(params))
        invoices = cursor.fetchall()
        return [dict(invoice) for invoice in invoices]
    except sqlite3.Error as e:
        logger.error(f"Database error in list_all_invoices with filters {filters}, sort_by {sort_by}: {e}", exc_info=True)
        return []
    finally:
        conn.close()

def get_total_sales_amount_for_period(db_session, start_date, end_date):
    """
    Calculates the total sales amount for a given period.

    Args:
        db_session: The database session.
        start_date: The start date of the period.
        end_date: The end date of the period.

    Returns:
        The total sales amount for the period.
    """
    # This is a placeholder implementation.
    # You should replace this with your actual database query.
    return 12345.67

if __name__ == '__main__':
    # Example Usage (requires db_config.py and an initialized database with Invoices table)
    print("Running invoices_crud.py examples...")

    # Ensure database and table exist before running examples
    # You might need to run db/init_schema.py first

    # Example: Add Invoice
    sample_invoice_data = {
        'client_id': str(uuid.uuid4()), # Replace with actual client_id
        'project_id': str(uuid.uuid4()), # Replace with actual project_id
        'invoice_number': f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'issue_date': datetime.now().strftime('%Y-%m-%d'),
        'due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'total_amount': 1500.75,
        'currency': 'USD',
        'payment_status': 'unpaid',
        'notes': 'Sample invoice for services rendered.'
    }

    # To run examples, you'd need to create dummy Clients, Projects first or use existing ones.
    # For now, we'll just demonstrate the function calls without actual data modification
    # as this script is primarily for defining CRUD operations.

    print(f"Attempting to add invoice: {sample_invoice_data.get('invoice_number')}")
    # new_id = add_invoice(sample_invoice_data)
    # if new_id:
    #     print(f"Invoice added with ID: {new_id}")
    #
    #     # Example: Get Invoice by ID
    #     retrieved_invoice = get_invoice_by_id(new_id)
    #     print(f"Retrieved invoice: {retrieved_invoice}")
    #
    #     # Example: Update Invoice
    #     update_success = update_invoice(new_id, {'payment_status': 'paid', 'payment_date': datetime.now().strftime('%Y-%m-%d')})
    #     print(f"Invoice update status: {update_success}")
    #     retrieved_updated_invoice = get_invoice_by_id(new_id)
    #     print(f"Retrieved updated invoice: {retrieved_updated_invoice}")
    #
    #     # Example: List Invoices (potentially including the new one)
    #     all_invoices = list_all_invoices(filters={'client_id': sample_invoice_data['client_id']}, sort_by="due_date_asc", limit=10)
    #     print(f"List of invoices for client {sample_invoice_data['client_id']}: {all_invoices}")
    #
    #     # Example: Delete Invoice
    #     # delete_success = delete_invoice(new_id)
    #     # print(f"Invoice delete status: {delete_success}")
    # else:
    #     print("Failed to add invoice.")

    print("Invoice CRUD operations defined. Uncomment and adapt example usage as needed.")
    # Need to import timedelta for example usage.
    from datetime import timedelta
    # This is just to ensure timedelta is defined if example code is uncommented.
    # Actual database interaction examples are commented out to prevent unintended side effects
    # when this file is first created/executed.
    # Proper testing should be done via dedicated test scripts.

