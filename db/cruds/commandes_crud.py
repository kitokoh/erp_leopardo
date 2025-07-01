import sqlite3
import uuid
from datetime import datetime, timezone
import logging
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

# --- Commandes (Orders) CRUD ---

@_manage_conn
def add_commande(data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Adds a new commande (order) to the Commandes table.
    Expected data keys: client_id, commande_reference, status_commande_id, created_by_user_id.
    Optional keys: project_id, description_commande, total_ht, total_ttc, currency, shipping_address, billing_address, commande_date.
    """
    cursor = conn.cursor()
    new_commande_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()
    commande_date = data.get('commande_date', now_utc)

    required_fields = ['client_id', 'commande_reference', 'status_commande_id', 'created_by_user_id']
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.error(f"Field '{field}' is required to add a commande.")
            return None

    sql = """
        INSERT INTO Commandes (
            commande_id, client_id, project_id, commande_reference, commande_date,
            status_commande_id, description_commande, notes, is_default,
            total_ht, total_ttc, currency,
            shipping_address, billing_address,
            created_at, updated_at, created_by_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_commande_id,
        data['client_id'],
        data.get('project_id'),
        data['commande_reference'],
        commande_date,
        data['status_commande_id'],
        data.get('description_commande'),
        data.get('notes'), # Added notes
        data.get('is_default', False), # Added is_default
        data.get('total_ht'),
        data.get('total_ttc'),
        data.get('currency', 'EUR'),
        data.get('shipping_address'),
        data.get('billing_address'),
        now_utc,
        now_utc,
        data['created_by_user_id']
    )
    try:
        cursor.execute(sql, params)
        logger.info(f"Commande '{data['commande_reference']}' added with ID: {new_commande_id} for client {data['client_id']}.")
        return new_commande_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add commande with data {data}. Error: {type(e).__name__} - {e}", exc_info=True)
        if "UNIQUE constraint failed: Commandes.commande_reference" in str(e):
             logger.error(f"Unique constraint failed for commande_reference: {data['commande_reference']}")
        return None

@_manage_conn
def get_commande_by_id(commande_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a commande by its ID, joining with Clients, Projects, and StatusSettings for more details."""
    cursor = conn.cursor()
    # Adjust JOINs and selected fields as necessary
    sql = """
        SELECT
            cmd.*,
            c.client_name,
            p.project_name,
            s.status_name AS status_commande_name,
            s.color_hex AS status_commande_color,
            u.username AS created_by_username
        FROM Commandes cmd
        JOIN Clients c ON cmd.client_id = c.client_id
        LEFT JOIN Projects p ON cmd.project_id = p.project_id
        JOIN StatusSettings s ON cmd.status_commande_id = s.status_id
        LEFT JOIN Users u ON cmd.created_by_user_id = u.user_id
        WHERE cmd.commande_id = ?
    """
    cursor.execute(sql, (commande_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_commandes_for_client(client_id: str, filters: dict = None, conn: sqlite3.Connection = None, limit: int = None, offset: int = 0) -> list[dict]:
    """Retrieves all commandes for a given client_id, with optional filtering and pagination."""
    cursor = conn.cursor()
    base_sql = """
        SELECT
            cmd.*,
            p.project_name,
            s.status_name AS status_commande_name,
            s.color_hex AS status_commande_color,
            u.username AS created_by_username
        FROM Commandes cmd
        LEFT JOIN Projects p ON cmd.project_id = p.project_id
        JOIN StatusSettings s ON cmd.status_commande_id = s.status_id
        LEFT JOIN Users u ON cmd.created_by_user_id = u.user_id
        WHERE cmd.client_id = ?
    """
    q_params = [client_id]

    conditions = []
    if filters:
        if 'status_commande_id' in filters and filters['status_commande_id'] is not None:
            conditions.append("cmd.status_commande_id = ?")
            q_params.append(filters['status_commande_id'])
        if 'commande_reference' in filters and filters['commande_reference']:
            conditions.append("cmd.commande_reference LIKE ?")
            q_params.append(f"%{filters['commande_reference']}%")
        # Add more filters as needed (e.g., date range)

    if conditions:
        base_sql += " AND " + " AND ".join(conditions)

    base_sql += " ORDER BY cmd.commande_date DESC"

    if limit is not None:
        base_sql += " LIMIT ? OFFSET ?"
        q_params.extend([limit, offset])

    cursor.execute(base_sql, q_params)
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_commande(commande_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    """Updates an existing commande."""
    cursor = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()

    valid_fields = [
        'project_id', 'commande_reference', 'commande_date', 'status_commande_id',
        'description_commande', 'notes', 'is_default',
        'total_ht', 'total_ttc', 'currency',
        'shipping_address', 'billing_address'
    ]

    fields_to_update = {k: v for k, v in data.items() if k in valid_fields}
    if not fields_to_update:
        logger.info(f"No valid fields provided for updating commande {commande_id}.")
        return False

    fields_to_update['updated_at'] = now_utc

    set_clauses = [f"{field} = ?" for field in fields_to_update.keys()]
    params = list(fields_to_update.values())
    params.append(commande_id)

    sql = f"UPDATE Commandes SET {', '.join(set_clauses)} WHERE commande_id = ?"

    try:
        cursor.execute(sql, tuple(params))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error updating commande {commande_id}: {e}", exc_info=True)
        if "UNIQUE constraint failed: Commandes.commande_reference" in str(e):
             logger.error(f"Unique constraint failed for commande_reference during update: {data.get('commande_reference')}")
        return False

@_manage_conn
def delete_commande(commande_id: str, conn: sqlite3.Connection = None) -> bool:
    """Deletes a commande by its ID (hard delete for now). Also deletes associated CommandeItems."""
    cursor = conn.cursor()
    try:
        # First delete associated items
        cursor.execute("DELETE FROM CommandeItems WHERE commande_id = ?", (commande_id,))
        logger.info(f"Deleted items for commande_id {commande_id}")

        # Then delete the commande itself
        cursor.execute("DELETE FROM Commandes WHERE commande_id = ?", (commande_id,))
        if cursor.rowcount > 0:
            logger.info(f"Commande {commande_id} deleted successfully.")
            return True
        logger.warning(f"No commande found with ID {commande_id} to delete.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error deleting commande {commande_id}: {e}", exc_info=True)
        return False

# --- CommandeItems (Order Items) CRUD ---

@_manage_conn
def add_commande_item(data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Adds a new item to a commande.
    Expected data keys: commande_id, product_id, description_item, quantity, unit_price_ht.
    Optional keys: vat_rate.
    Calculates total_item_ht and total_item_ttc.
    """
    cursor = conn.cursor()
    new_item_id = str(uuid.uuid4())

    required_fields = ['commande_id', 'product_id', 'description_item', 'quantity', 'unit_price_ht']
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.error(f"Field '{field}' is required to add a commande item.")
            return None

    quantity = float(data['quantity'])
    unit_price_ht = float(data['unit_price_ht'])
    vat_rate = float(data.get('vat_rate', 0.0))

    total_item_ht = quantity * unit_price_ht
    total_item_ttc = total_item_ht * (1 + vat_rate)

    sql = """
        INSERT INTO CommandeItems (
            item_id, commande_id, product_id, description_item, quantity,
            unit_price_ht, vat_rate, total_item_ht, total_item_ttc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_item_id,
        data['commande_id'],
        data['product_id'],
        data['description_item'],
        quantity,
        unit_price_ht,
        vat_rate,
        total_item_ht,
        total_item_ttc
    )
    try:
        cursor.execute(sql, params)
        logger.info(f"CommandeItem added with ID: {new_item_id} for commande {data['commande_id']}.")
        return new_item_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add commande item with data {data}. Error: {e}", exc_info=True)
        return None

@_manage_conn
def get_items_for_commande(commande_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """Retrieves all items for a given commande_id, joining with Products for product_name."""
    cursor = conn.cursor()
    sql = """
        SELECT ci.*, p.product_name, p.product_code
        FROM CommandeItems ci
        JOIN Products p ON ci.product_id = p.product_id
        WHERE ci.commande_id = ?
        ORDER BY ci.item_id -- Or some other ordering if items have a sequence
    """
    cursor.execute(sql, (commande_id,))
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_commande_item(item_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    """Updates an existing commande item."""
    cursor = conn.cursor()

    valid_fields = ['product_id', 'description_item', 'quantity', 'unit_price_ht', 'vat_rate']
    fields_to_update = {k: v for k, v in data.items() if k in valid_fields}

    if not fields_to_update:
        logger.info(f"No valid fields provided for updating commande item {item_id}.")
        return False

    # Recalculate totals if quantity, price, or vat_rate changes
    recalculate_totals = False
    if 'quantity' in fields_to_update or 'unit_price_ht' in fields_to_update or 'vat_rate' in fields_to_update:
        recalculate_totals = True
        # Fetch current values if not all are being updated, to ensure correct calculation
        if not all(k in fields_to_update for k in ['quantity', 'unit_price_ht']):
            current_item_sql = "SELECT quantity, unit_price_ht, vat_rate FROM CommandeItems WHERE item_id = ?"
            current_item_row = cursor.execute(current_item_sql, (item_id,)).fetchone()
            if not current_item_row:
                logger.error(f"Cannot find item {item_id} to update for recalculating totals.")
                return False
            current_item = dict(current_item_row)
        else:
            current_item = {} # All needed fields are in fields_to_update

        quantity = float(fields_to_update.get('quantity', current_item.get('quantity')))
        unit_price_ht = float(fields_to_update.get('unit_price_ht', current_item.get('unit_price_ht')))
        vat_rate = float(fields_to_update.get('vat_rate', current_item.get('vat_rate', 0.0)))

        fields_to_update['total_item_ht'] = quantity * unit_price_ht
        fields_to_update['total_item_ttc'] = fields_to_update['total_item_ht'] * (1 + vat_rate)

    set_clauses = [f"{field} = ?" for field in fields_to_update.keys()]
    params = list(fields_to_update.values())
    params.append(item_id)

    sql = f"UPDATE CommandeItems SET {', '.join(set_clauses)} WHERE item_id = ?"

    try:
        cursor.execute(sql, tuple(params))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error updating commande item {item_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_commande_item(item_id: str, conn: sqlite3.Connection = None) -> bool:
    """Deletes a commande item by its ID."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM CommandeItems WHERE item_id = ?", (item_id,))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error deleting commande item {item_id}: {e}", exc_info=True)
        return False

@_manage_conn
def get_next_commande_reference(conn: sqlite3.Connection = None, prefix="CMD") -> str:
    """
    Generates the next available commande_reference based on a prefix and the current year.
    Example: CMD-2023-0001, CMD-2023-0002.
    """
    cursor = conn.cursor()
    current_year = datetime.now().year
    year_prefix = f"{prefix}-{current_year}-"

    sql = "SELECT commande_reference FROM Commandes WHERE commande_reference LIKE ? ORDER BY commande_reference DESC LIMIT 1"
    cursor.execute(sql, (f"{year_prefix}%",))
    last_ref_row = cursor.fetchone()

    if last_ref_row:
        last_ref = last_ref_row['commande_reference']
        try:
            last_num_str = last_ref.split('-')[-1]
            next_num = int(last_num_str) + 1
        except (IndexError, ValueError):
            # Fallback if parsing fails (e.g., unexpected format)
            next_num = 1
    else:
        next_num = 1

    return f"{year_prefix}{next_num:04d}"

__all__ = [
    "add_commande",
    "get_commande_by_id",
    "get_commandes_for_client",
    "update_commande",
    "delete_commande",
    "add_commande_item",
    "get_items_for_commande",
    "update_commande_item",
    "delete_commande_item",
    "get_next_commande_reference",
    "get_all_commandes_with_details",
    "get_all_commandes_count"
]

@_manage_conn
def get_all_commandes_with_details(filters: dict = None, limit: int = None, offset: int = 0, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all commandes with details from joined tables (Clients, Projects, StatusSettings, Users).
    Supports filtering and pagination.
    """
    cursor = conn.cursor()
    # Ensure row_factory is set for this cursor if not globally for the connection
    # conn.row_factory = sqlite3.Row # Already set at connection level in _manage_conn likely

    base_sql = """
        SELECT
            cmd.commande_id, cmd.commande_reference, cmd.commande_date, cmd.description_commande,
            cmd.notes, cmd.is_default, -- Added notes and is_default
            cmd.total_ht, cmd.total_ttc, cmd.currency, cmd.created_at, cmd.project_id,
            c.client_id, c.client_name,
            p.project_name,
            s.status_name AS status_commande_name, s.color_hex AS status_commande_color,
            u.username AS created_by_username
        FROM Commandes cmd
        JOIN Clients c ON cmd.client_id = c.client_id
        LEFT JOIN Projects p ON cmd.project_id = p.project_id
        JOIN StatusSettings s ON cmd.status_commande_id = s.status_id AND s.status_type = 'Commande'
        LEFT JOIN Users u ON cmd.created_by_user_id = u.user_id
    """
    q_params = []
    conditions = []

    if filters:
        if filters.get('status_commande_id'):
            conditions.append("cmd.status_commande_id = ?")
            q_params.append(filters['status_commande_id'])

        if filters.get('search_term'):
            term = f"%{filters['search_term']}%"
            # Adjusted to search in commande_reference, client_name, or project_name
            conditions.append("(cmd.commande_reference LIKE ? OR c.client_name LIKE ? OR IFNULL(p.project_name, '') LIKE ?)")
            q_params.extend([term, term, term])

        if filters.get('date_from'):
            # Ensure date format matches 'YYYY-MM-DD' as stored or used by date() function
            conditions.append("date(cmd.commande_date) >= date(?)")
            q_params.append(filters['date_from']) # Should be 'YYYY-MM-DD'

        if filters.get('date_to'):
            conditions.append("date(cmd.commande_date) <= date(?)")
            q_params.append(filters['date_to']) # Should be 'YYYY-MM-DD'

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += " ORDER BY cmd.commande_date DESC"

    if limit is not None: # Ensure offset is used with limit
        base_sql += " LIMIT ? OFFSET ?"
        q_params.extend([limit, offset if offset is not None else 0])

    try:
        cursor.execute(base_sql, tuple(q_params)) # Ensure q_params is a tuple
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get all commandes with details. Filters: {filters}. SQL: {base_sql} Params: {q_params} Error: {e}", exc_info=True)
        return []

@_manage_conn
def get_all_commandes_count(filters: dict = None, conn: sqlite3.Connection = None) -> int:
    """Counts all commandes based on filters."""
    cursor = conn.cursor()
    base_sql = "SELECT COUNT(DISTINCT cmd.commande_id) FROM Commandes cmd" # Use DISTINCT if joins might create duplicates
    q_params = []
    conditions = []

    joins = " JOIN Clients c ON cmd.client_id = c.client_id LEFT JOIN Projects p ON cmd.project_id = p.project_id JOIN StatusSettings s ON cmd.status_commande_id = s.status_id AND s.status_type = 'Commande' LEFT JOIN Users u ON cmd.created_by_user_id = u.user_id"

    if filters:
        if filters.get('status_commande_id'):
            conditions.append("cmd.status_commande_id = ?")
            q_params.append(filters['status_commande_id'])

        if filters.get('search_term'):
            term = f"%{filters['search_term']}%"
            conditions.append("(cmd.commande_reference LIKE ? OR c.client_name LIKE ? OR IFNULL(p.project_name, '') LIKE ?)")
            q_params.extend([term, term, term])

        if filters.get('date_from'):
            conditions.append("date(cmd.commande_date) >= date(?)")
            q_params.append(filters['date_from'])

        if filters.get('date_to'):
            conditions.append("date(cmd.commande_date) <= date(?)")
            q_params.append(filters['date_to'])

    full_sql = base_sql + joins
    if conditions:
        full_sql += " WHERE " + " AND ".join(conditions)

    try:
        cursor.execute(full_sql, tuple(q_params)) # Ensure q_params is a tuple
        count_result = cursor.fetchone()
        return count_result[0] if count_result is not None else 0
    except sqlite3.Error as e:
        logger.error(f"Failed to count commandes. Filters: {filters}. SQL: {full_sql} Params: {q_params} Error: {e}", exc_info=True)
        return 0

