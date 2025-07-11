import sqlite3 # Keep for type hints if necessary
import uuid
from datetime import datetime, timezone
import logging
from sqlalchemy.sql import text
from .generic_crud import _manage_conn
from . import clients_crud  # For updating client status
from . import status_settings_crud # For fetching status definitions

logger = logging.getLogger(__name__)

# --- Commandes (Orders) CRUD ---

@_manage_conn
def add_commande(data: dict, conn = None) -> str | None: # conn is Session
    """
    Adds a new commande (order) to the Commandes table.
    Expected data keys: client_id, commande_reference, status_commande_id, created_by_user_id.
    Optional keys: project_id, description_commande, total_ht, total_ttc, currency, shipping_address, billing_address, commande_date.
    """
    new_commande_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()
    commande_date_to_use = data.get('commande_date', now_utc)

    required_fields = ['client_id', 'commande_reference', 'status_commande_id', 'created_by_user_id']
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.error(f"Field '{field}' is required to add a commande.")
            return None

    sql_query = text("""
        INSERT INTO Commandes (
            commande_id, client_id, project_id, commande_reference, commande_date,
            status_commande_id, description_commande, notes, is_default,
            total_ht, total_ttc, currency,
            shipping_address, billing_address,
            created_at, updated_at, created_by_user_id
        )
        VALUES (:commande_id, :client_id, :project_id, :commande_reference, :commande_date,
                :status_commande_id, :description_commande, :notes, :is_default,
                :total_ht, :total_ttc, :currency,
                :shipping_address, :billing_address,
                :created_at, :updated_at, :created_by_user_id)
    """)
    params_dict = {
        "commande_id": new_commande_id,
        "client_id": data['client_id'],
        "project_id": data.get('project_id'),
        "commande_reference": data['commande_reference'],
        "commande_date": commande_date_to_use,
        "status_commande_id": data['status_commande_id'],
        "description_commande": data.get('description_commande'),
        "notes": data.get('notes'),
        "is_default": data.get('is_default', False),
        "total_ht": data.get('total_ht'),
        "total_ttc": data.get('total_ttc'),
        "currency": data.get('currency', 'EUR'),
        "shipping_address": data.get('shipping_address'),
        "billing_address": data.get('billing_address'),
        "created_at": now_utc,
        "updated_at": now_utc,
        "created_by_user_id": data['created_by_user_id']
    }
    try:
        conn.execute(sql_query, params_dict)
        # _manage_conn handles commit/rollback
        logger.info(f"Commande '{data['commande_reference']}' added with ID: {new_commande_id} for client {data['client_id']}.")
        return new_commande_id
    except Exception as e: # Changed to general Exception
        logger.error(f"Failed to add commande with data {data}. Error: {type(e).__name__} - {e}", exc_info=True)
        if "UNIQUE constraint failed: Commandes.commande_reference" in str(e).lower(): # Check lower for safety
             logger.error(f"Unique constraint failed for commande_reference: {data['commande_reference']}")
        return None

@_manage_conn
def get_commande_by_id(commande_id: str, conn = None) -> dict | None: # conn is Session
    """Retrieves a commande by its ID, joining with Clients, Projects, and StatusSettings for more details."""
    sql_query = text("""
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
        WHERE cmd.commande_id = :commande_id
    """)
    try:
        result = conn.execute(sql_query, {"commande_id": commande_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None
    except Exception as e:
        logger.error(f"Error getting commande by ID {commande_id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_commandes_for_client(client_id: str, filters: dict = None, conn = None, limit: int = None, offset: int = 0) -> list[dict]: # conn is Session
    """Retrieves all commandes for a given client_id, with optional filtering and pagination."""
    params_dict = {"client_id": client_id}

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
        WHERE cmd.client_id = :client_id
    """

    conditions = []
    if filters:
        if 'status_commande_id' in filters and filters['status_commande_id'] is not None:
            conditions.append("cmd.status_commande_id = :status_commande_id")
            params_dict["status_commande_id"] = filters['status_commande_id']
        if 'commande_reference' in filters and filters['commande_reference']:
            conditions.append("cmd.commande_reference LIKE :commande_reference")
            params_dict["commande_reference"] = f"%{filters['commande_reference']}%"
        # Add more filters as needed (e.g., date range)

    if conditions:
        base_sql += " AND " + " AND ".join(conditions)

    base_sql += " ORDER BY cmd.commande_date DESC"

    if limit is not None:
        base_sql += " LIMIT :limit OFFSET :offset"
        params_dict["limit"] = limit
        params_dict["offset"] = offset

    sql_query = text(base_sql)
    try:
        result = conn.execute(sql_query, params_dict)
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error getting commandes for client {client_id}: {e}", exc_info=True)
        return []

@_manage_conn
def update_commande(commande_id: str, data: dict, conn = None) -> bool: # conn is Session
    """Updates an existing commande."""
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
    # Add commande_id to params_dict for the WHERE clause
    fields_to_update['commande_id_where'] = commande_id

    set_clauses = [f"{field} = :{field}" for field in fields_to_update if field != 'commande_id_where']

    sql_query_str = f"UPDATE Commandes SET {', '.join(set_clauses)} WHERE commande_id = :commande_id_where"
    sql_query = text(sql_query_str)

    try:
        result = conn.execute(sql_query, fields_to_update)
        # _manage_conn handles commit/rollback
        return result.rowcount > 0
    except Exception as e: # Changed to general Exception
        logger.error(f"Database error updating commande {commande_id}: {e}", exc_info=True)
        if "UNIQUE constraint failed: Commandes.commande_reference" in str(e).lower():
             logger.error(f"Unique constraint failed for commande_reference during update: {data.get('commande_reference')}")
        return False

@_manage_conn
def delete_commande(commande_id: str, conn = None) -> bool: # conn is Session
    """
    Soft "deletes" a commande by its ID by setting the `deleted_at` timestamp.
    The `is_deleted` column does not exist in the `Commandes` table.
    Associated CommandeItems are NOT deleted.
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql_query = text("UPDATE Commandes SET deleted_at = :deleted_at WHERE commande_id = :commande_id")
    params_dict = {"deleted_at": now_utc_iso, "commande_id": commande_id}
    try:
        result = conn.execute(sql_query, params_dict)
        # _manage_conn handles commit/rollback
        if result.rowcount > 0:
            logger.info(f"Commande {commande_id} marked as deleted (deleted_at set).")
            return True
        logger.warning(f"No commande found with ID {commande_id} to mark as deleted, or already marked.")
        return False
    except Exception as e: # Changed to general Exception
        logger.error(f"Database error marking commande {commande_id} as deleted: {e}", exc_info=True)
        return False

# --- CommandeItems (Order Items) CRUD ---

@_manage_conn
def add_commande_item(data: dict, conn = None) -> str | None: # conn is Session
    """
    Adds a new item to a commande.
    Expected data keys: commande_id, product_id, description_item, quantity, unit_price_ht.
    Optional keys: vat_rate.
    Calculates total_item_ht and total_item_ttc.
    """
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

    sql_query = text("""
        INSERT INTO CommandeItems (
            item_id, commande_id, product_id, description_item, quantity,
            unit_price_ht, vat_rate, total_item_ht, total_item_ttc,
            weight, dimensions_text, product_language_code
        )
        VALUES (:item_id, :commande_id, :product_id, :description_item, :quantity,
                :unit_price_ht, :vat_rate, :total_item_ht, :total_item_ttc,
                :weight, :dimensions_text, :product_language_code)
    """)
    params_dict = {
        "item_id": new_item_id,
        "commande_id": data['commande_id'],
        "product_id": data['product_id'],
        "description_item": data['description_item'],
        "quantity": quantity,
        "unit_price_ht": unit_price_ht,
        "vat_rate": vat_rate,
        "total_item_ht": total_item_ht,
        "total_item_ttc": total_item_ttc,
        "weight": data.get('weight'),
        "dimensions_text": data.get('dimensions_text'),
        "product_language_code": data.get('product_language_code')
    }
    try:
        conn.execute(sql_query, params_dict)
        # _manage_conn handles commit/rollback
        logger.info(f"CommandeItem added with ID: {new_item_id} for commande {data['commande_id']}.")
        return new_item_id
    except Exception as e: # Changed to general Exception
        logger.error(f"Failed to add commande item with data {data}. Error: {e}", exc_info=True)
        return None

@_manage_conn
def get_items_for_commande(commande_id: str, conn = None) -> list[dict]: # conn is Session
    """Retrieves all items for a given commande_id, joining with Products for product_name."""
    sql_query = text("""
        SELECT ci.*, p.product_name, p.product_code,
               p.language_code AS global_product_language_code,
               p.weight AS global_product_weight,
               p.dimensions AS global_product_dimensions
        FROM CommandeItems ci
        JOIN Products p ON ci.product_id = p.product_id
        WHERE ci.commande_id = :commande_id
        ORDER BY ci.item_id -- Or some other ordering if items have a sequence
    """)
    try:
        result = conn.execute(sql_query, {"commande_id": commande_id})
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error getting items for commande {commande_id}: {e}", exc_info=True)
        return []

@_manage_conn
def update_commande_item(item_id: str, data: dict, conn = None) -> bool: # conn is Session
    """Updates an existing commande item."""
    # This method involves a preliminary SELECT if totals need recalculation,
    # then an UPDATE. Both need to use the session.

    valid_fields = ['product_id', 'description_item', 'quantity', 'unit_price_ht', 'vat_rate', 'weight', 'dimensions_text', 'product_language_code']
    fields_to_update = {k: v for k, v in data.items() if k in valid_fields}

    if not fields_to_update:
        logger.info(f"No valid fields provided for updating commande item {item_id}.")
        return False

    # Recalculate totals if quantity, price, or vat_rate changes
    recalculate_totals = False
    if 'quantity' in fields_to_update or 'unit_price_ht' in fields_to_update or 'vat_rate' in fields_to_update:
        recalculate_totals = True
        # Fetch current values if not all are being updated, to ensure correct calculation
        if not all(k in fields_to_update for k in ['quantity', 'unit_price_ht', 'vat_rate']): # vat_rate also needed if not in fields_to_update for calc
            current_item_sql = text("SELECT quantity, unit_price_ht, vat_rate FROM CommandeItems WHERE item_id = :item_id")
            current_item_result = conn.execute(current_item_sql, {"item_id": item_id})
            current_item_row = current_item_result.fetchone()
            if not current_item_row:
                logger.error(f"Cannot find item {item_id} to update for recalculating totals.")
                return False
            current_item = dict(current_item_row._mapping)
        else:
            current_item = {} # All needed fields are in fields_to_update or will default if not

        quantity = float(fields_to_update.get('quantity', current_item.get('quantity', 0)))
        unit_price_ht = float(fields_to_update.get('unit_price_ht', current_item.get('unit_price_ht', 0)))
        # Ensure vat_rate for calculation is sourced correctly
        # If 'vat_rate' is in fields_to_update, use it. Otherwise, use current_item's vat_rate, or default to 0.0.
        vat_rate_for_calc = float(fields_to_update.get('vat_rate', current_item.get('vat_rate', 0.0)))

        fields_to_update['total_item_ht'] = quantity * unit_price_ht
        fields_to_update['total_item_ttc'] = fields_to_update['total_item_ht'] * (1 + vat_rate_for_calc)

    # Prepare for UPDATE query
    # Add item_id to fields_to_update for the WHERE clause, ensuring it's not part of SET
    params_for_update = fields_to_update.copy()
    params_for_update['item_id_where'] = item_id

    set_clauses = [f"{field} = :{field}" for field in fields_to_update.keys()]

    sql_query_str = f"UPDATE CommandeItems SET {', '.join(set_clauses)} WHERE item_id = :item_id_where"
    sql_query = text(sql_query_str)

    try:
        result = conn.execute(sql_query, params_for_update)
        # _manage_conn handles commit/rollback
        return result.rowcount > 0
    except Exception as e: # Changed to general Exception
        logger.error(f"Database error updating commande item {item_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_commande_item(item_id: str, conn = None) -> bool: # conn is Session
    """Deletes a commande item by its ID."""
    sql_query = text("DELETE FROM CommandeItems WHERE item_id = :item_id")
    try:
        result = conn.execute(sql_query, {"item_id": item_id})
        # _manage_conn handles commit/rollback
        return result.rowcount > 0
    except Exception as e: # Changed to general Exception
        logger.error(f"Database error deleting commande item {item_id}: {e}", exc_info=True)
        return False

@_manage_conn
def get_next_commande_reference(conn = None, prefix="CMD") -> str: # conn is Session
    """
    Generates the next available commande_reference based on a prefix and the current year.
    Example: CMD-2023-0001, CMD-2023-0002.
    """
    current_year = datetime.now().year
    year_prefix_like = f"{prefix}-{current_year}-%"

    sql_query = text("SELECT commande_reference FROM Commandes WHERE commande_reference LIKE :year_prefix_like ORDER BY commande_reference DESC LIMIT 1")

    try:
        result = conn.execute(sql_query, {"year_prefix_like": year_prefix_like})
        last_ref_row = result.fetchone()

        next_num = 1
        if last_ref_row:
            last_ref = last_ref_row.commande_reference # Access by attribute
            try:
                last_num_str = last_ref.split('-')[-1]
                next_num = int(last_num_str) + 1
            except (IndexError, ValueError):
                logger.warning(f"Could not parse last commande reference number from '{last_ref}'. Defaulting to 1.")
                next_num = 1

        return f"{prefix}-{current_year}-{next_num:04d}"
    except Exception as e:
        logger.error(f"Database error generating next commande reference: {e}", exc_info=True)
        # Fallback reference in case of DB error
        timestamp_fallback = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}-ERR-{timestamp_fallback}"

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
def get_all_commandes_with_details(filters: dict = None, limit: int = None, offset: int = 0, conn = None) -> list[dict]: # conn is Session
    """
    Retrieves all commandes with details from joined tables (Clients, Projects, StatusSettings, Users).
    Supports filtering and pagination.
    """
    params_dict = {}
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
    conditions = []

    if filters:
        if filters.get('status_commande_id'):
            conditions.append("cmd.status_commande_id = :status_commande_id")
            params_dict["status_commande_id"] = filters['status_commande_id']

        if filters.get('search_term'):
            term = f"%{filters['search_term']}%"
            conditions.append("(cmd.commande_reference LIKE :search_term_ref OR c.client_name LIKE :search_term_client OR IFNULL(p.project_name, '') LIKE :search_term_project)")
            params_dict["search_term_ref"] = term
            params_dict["search_term_client"] = term
            params_dict["search_term_project"] = term

        if filters.get('date_from'):
            conditions.append("date(cmd.commande_date) >= date(:date_from)")
            params_dict["date_from"] = filters['date_from']

        if filters.get('date_to'):
            conditions.append("date(cmd.commande_date) <= date(:date_to)")
            params_dict["date_to"] = filters['date_to']

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += " ORDER BY cmd.commande_date DESC"

    if limit is not None:
        base_sql += " LIMIT :limit OFFSET :offset"
        params_dict["limit"] = limit
        params_dict["offset"] = offset if offset is not None else 0

    sql_query = text(base_sql)
    try:
        result = conn.execute(sql_query, params_dict)
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e: # Changed to general Exception
        logger.error(f"Failed to get all commandes with details. Filters: {filters}. SQL: {base_sql} Params: {params_dict} Error: {e}", exc_info=True)
        return []

@_manage_conn
def get_all_commandes_count(filters: dict = None, conn = None) -> int: # conn is Session
    """Counts all commandes based on filters."""
    params_dict = {}
    base_sql = "SELECT COUNT(DISTINCT cmd.commande_id) FROM Commandes cmd"
    joins = " JOIN Clients c ON cmd.client_id = c.client_id LEFT JOIN Projects p ON cmd.project_id = p.project_id JOIN StatusSettings s ON cmd.status_commande_id = s.status_id AND s.status_type = 'Commande' LEFT JOIN Users u ON cmd.created_by_user_id = u.user_id"
    conditions = []

    if filters:
        if filters.get('status_commande_id'):
            conditions.append("cmd.status_commande_id = :status_commande_id")
            params_dict["status_commande_id"] = filters['status_commande_id']

        if filters.get('search_term'):
            term = f"%{filters['search_term']}%"
            conditions.append("(cmd.commande_reference LIKE :search_term_ref OR c.client_name LIKE :search_term_client OR IFNULL(p.project_name, '') LIKE :search_term_project)")
            params_dict["search_term_ref"] = term
            params_dict["search_term_client"] = term
            params_dict["search_term_project"] = term

        if filters.get('date_from'):
            conditions.append("date(cmd.commande_date) >= date(:date_from)")
            params_dict["date_from"] = filters['date_from']

        if filters.get('date_to'):
            conditions.append("date(cmd.commande_date) <= date(:date_to)")
            params_dict["date_to"] = filters['date_to']

    full_sql_str = base_sql + joins
    if conditions:
        full_sql_str += " WHERE " + " AND ".join(conditions)

    sql_query = text(full_sql_str)
    try:
        result = conn.execute(sql_query, params_dict)
        count_result = result.scalar_one_or_none() # scalar_one_or_none() is good for single value results
        return count_result if count_result is not None else 0
    except Exception as e: # Changed to general Exception
        logger.error(f"Failed to count commandes. Filters: {filters}. SQL: {full_sql_str} Params: {params_dict} Error: {e}", exc_info=True)
        return 0

