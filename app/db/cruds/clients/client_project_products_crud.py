import sqlite3
import uuid
from datetime import datetime
import json
import logging
from ..generic_crud import _manage_conn
from ..products.products_crud import products_crud_instance

logger = logging.getLogger(__name__)

@_manage_conn
def add_product_to_client_or_project(link_data: dict, conn: sqlite3.Connection = None) -> int | None:
    logging.info(f"cpp_crud.add_product_to_client_or_project: Attempting to link with data: {link_data}")
    cursor = conn.cursor()
    product_id = link_data.get('product_id')
    client_id = link_data.get('client_id')

    if not product_id or not client_id:
        logger.error("product_id and client_id are required to link a product.")
        return None

    prod_info = products_crud_instance.get_product_by_id(product_id, conn=conn) # Pass connection
    if not prod_info:
        logger.error(f"Product with ID {product_id} not found.")
        return None

    qty = link_data.get('quantity',1)
    override_price = link_data.get('unit_price_override')
    eff_price = override_price if override_price is not None else prod_info.get('base_unit_price')

    if eff_price is None: # Handle case where base_unit_price might also be None
        logger.warning(f"Effective price for product {product_id} is None. Defaulting to 0.0.")
        eff_price = 0.0

    total_price = qty * float(eff_price) # Ensure eff_price is float for calculation

    # Client-specific override fields
    client_specific_product_name = link_data.get('client_specific_product_name')
    line_description = link_data.get('line_description')
    line_weight = link_data.get('line_weight')
    line_dimensions_notes = link_data.get('line_dimensions_notes')

    sql="""INSERT INTO ClientProjectProducts
             (client_id, project_id, product_id, quantity, unit_price_override,
              total_price_calculated, serial_number, purchase_confirmed_at, added_at, added_by_user_id,
              client_specific_product_name, line_description, line_weight, line_dimensions_notes)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""" # Added 4 placeholders
    params=(client_id, link_data.get('project_id'), product_id, qty, override_price,
            total_price, link_data.get('serial_number'),
            link_data.get('purchase_confirmed_at'), datetime.utcnow().isoformat()+"Z",
            link_data.get('added_by_user_id'),
            client_specific_product_name, line_description, line_weight, line_dimensions_notes)


    # Enhanced logging for diagnostics
    logger.info(f"Executing SQL for add_product_to_client_or_project: {sql}")
    logger.info(f"With parameters: {params}")

    try:
        cursor.execute(sql,params)
        last_id = cursor.lastrowid
        logger.info(f"Product linked to client/project. New ClientProjectProducts ID: {last_id}")
        return last_id
    except sqlite3.Error as e:
        logger.error(f"cpp_crud.add_product_to_client_or_project: Failed to link with data {link_data}. Error: {type(e).__name__} - {e}", exc_info=True)
        return None

@_manage_conn
def update_client_project_product(link_id: int, data: dict, conn: sqlite3.Connection = None) -> bool:
    if not data: return False
    cursor = conn.cursor()

    # Fetch current link data to get product_id for fetching base_unit_price
    # and to use existing values if not provided in update data.
    current_link = get_client_project_product_by_id(link_id, conn=conn) # Pass connection
    if not current_link:
        logger.error(f"ClientProjectProduct link with ID {link_id} not found for update.")
        return False

    qty = data.get('quantity', current_link.get('quantity'))
    override_price = data.get('unit_price_override', current_link.get('unit_price_override'))

    # Need product's base_unit_price if override_price is being removed or was never set
    # current_link from get_client_project_product_by_id should already have base_unit_price
    base_price = current_link.get('base_unit_price')

    eff_price = override_price if override_price is not None else base_price
    if eff_price is None: # Handle case where base_unit_price might also be None
        logger.warning(f"Effective price for product in link {link_id} is None. Defaulting to 0.0 for total calculation.")
        eff_price = 0.0

    # S'assurer que data contient total_price_calculated s'il y a eu un changement pertinent
    if 'quantity' in data or 'unit_price_override' in data:
        data['total_price_calculated'] = qty * float(eff_price)
    elif 'total_price_calculated' not in data: # Si non fourni et pas de recalcul, utiliser la valeur actuelle
        data['total_price_calculated'] = current_link.get('total_price_calculated')


    # Mise à jour des colonnes valides
    valid_cols = ['quantity', 'unit_price_override', 'total_price_calculated', 'serial_number',
                  'purchase_confirmed_at',
                  'client_specific_product_name', 'line_description', 'line_weight', 'line_dimensions_notes']


    to_set = {k: v for k, v in data.items() if k in valid_cols}

    if not to_set:
        logger.info(f"No valid fields to update for ClientProjectProduct link ID {link_id}.")
        return False # Or True if no change is considered a success

    set_c = [f"{k}=?" for k in to_set.keys()]
    params_list = list(to_set.values())
    params_list.append(link_id)

    sql = f"UPDATE ClientProjectProducts SET {', '.join(set_c)} WHERE client_project_product_id = ?"
    try:
        cursor.execute(sql,tuple(params_list))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"DB error in update_client_project_product for link ID {link_id}: {e}")
        return False

@_manage_conn
def remove_product_from_client_or_project(link_id: int, conn: sqlite3.Connection = None) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ClientProjectProducts WHERE client_project_product_id = ?", (link_id,))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"DB error in remove_product_from_client_or_project for link ID {link_id}: {e}")
        return False

@_manage_conn
def get_client_project_product_by_id(link_id: int, conn: sqlite3.Connection = None) -> dict | None:
    cursor = conn.cursor()
    # Assurez-vous que les nouvelles colonnes sont sélectionnées ici
    sql="""SELECT cpp.*,
                  p.product_name, p.description as product_description, p.category as product_category,
                  p.base_unit_price, p.unit_of_measure, p.weight as global_product_weight,
                  p.dimensions as global_product_dimensions, p.language_code
           FROM ClientProjectProducts cpp
           JOIN Products p ON cpp.product_id = p.product_id
           WHERE cpp.client_project_product_id = ?"""
    # Note: cpp.* va chercher toutes les colonnes de ClientProjectProducts, y compris les nouvelles.
    # Les alias global_product_weight et global_product_dimensions sont pour distinguer des line_weight etc.
    try:
        cursor.execute(sql,(link_id,))
        row=cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"DB error in get_client_project_product_by_id for link ID {link_id}: {e}")
        return None

@_manage_conn
def get_products_for_client_or_project(client_id: str, project_id: str = None, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves products linked to a client, optionally filtered by a project.
    If project_id is None, retrieves all products for the client across all their projects (and those not linked to any project).
    If project_id is provided, retrieves products for that specific project.
    If project_id is '__NONE__', retrieves products for the client that are NOT linked to any project.
    """
    logging.info(f"cpp_crud.get_products_for_client_or_project: Fetching for client_id='{client_id}', project_id='{project_id}'")
    # ... (logique existante) ...
    cursor = conn.cursor()
    # Assurez-vous que les nouvelles colonnes sont sélectionnées ici
    sql = """SELECT cpp.*,
                    p.product_name, p.description as product_description, p.category as product_category,
                    p.base_unit_price, p.unit_of_measure, p.weight as global_product_weight,
                    p.dimensions as global_product_dimensions, p.language_code
             FROM ClientProjectProducts cpp
             JOIN Products p ON cpp.product_id = p.product_id
             WHERE cpp.client_id = ?"""
    # Note: cpp.* va chercher toutes les colonnes de ClientProjectProducts.
    params = [client_id]

    if project_id is not None:
        if project_id == '__NONE__': # Special value to filter for products not assigned to any project
            sql += " AND cpp.project_id IS NULL"
        else:
            sql += " AND cpp.project_id = ?"
            params.append(project_id)

    sql += " ORDER BY p.product_name"
    try:
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        logging.info(f"cpp_crud.get_products_for_client_or_project: Found {len(results)} items for client_id='{client_id}', project_id='{project_id}'.")
        return results
    except sqlite3.Error as e:
        logger.error(f"cpp_crud.get_products_for_client_or_project: DB error for client_id='{client_id}', project_id='{project_id}'. Error: {type(e).__name__} - {e}", exc_info=True)
        return []

@_manage_conn
def get_distinct_purchase_confirmed_at_for_client(client_id: str, conn: sqlite3.Connection = None) -> list[str]:
    """
    Retrieves distinct purchase_confirmed_at timestamps for a given client.
    Returns a list of strings (timestamps).
    """
    cursor = conn.cursor()
    sql = """
        SELECT DISTINCT purchase_confirmed_at
        FROM ClientProjectProducts
        WHERE client_id = ? AND purchase_confirmed_at IS NOT NULL
        ORDER BY purchase_confirmed_at DESC
    """
    try:
        cursor.execute(sql, (client_id,))
        # Fetches list of tuples, e.g., [('2023-01-01T10:00:00Z',), ('2023-01-15T12:00:00Z',)]
        # Convert to list of strings
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"DB error in get_distinct_purchase_confirmed_at_for_client for client ID {client_id}: {e}")
        return []

@_manage_conn
def get_product_usage_counts(conn: sqlite3.Connection = None) -> list[dict]:
    # logger is already defined at the module level: logger = logging.getLogger(__name__)
    cursor = conn.cursor()
    sql = """
        SELECT
            p.product_name,
            COUNT(cpp.client_project_product_id) as usage_count
        FROM ClientProjectProducts cpp
        JOIN Products p ON cpp.product_id = p.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY usage_count DESC
    """
    try:
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        logger.debug(f"Product usage counts retrieved successfully: {len(results)} products.")
        return results
    except sqlite3.Error as e:
        logger.error(f"DB error in get_product_usage_counts: {e}", exc_info=True)
        return []

@_manage_conn
def get_client_purchase_history(client_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves the purchase history for a given client.
    A purchase is defined as an entry in ClientProjectProducts with a non-null purchase_confirmed_at.
    """
    cursor = conn.cursor()
    sql = """
        SELECT
            cpp.client_project_product_id,
            p.product_name,
            cpp.quantity,
            cpp.serial_number, /* Assuming serial_number is on ClientProjectProducts */
            cpp.purchase_confirmed_at AS purchase_date,
            cpp.unit_price_override, /* For context if needed */
            p.base_unit_price /* For context if needed */
        FROM ClientProjectProducts cpp
        JOIN Products p ON cpp.product_id = p.product_id
        WHERE cpp.client_id = ? AND cpp.purchase_confirmed_at IS NOT NULL
        ORDER BY cpp.purchase_confirmed_at DESC
    """
    try:
        cursor.execute(sql, (client_id,))
        history = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(history)} purchase history items for client_id {client_id}")
        return history
    except sqlite3.Error as e:
        logger.error(f"DB error in get_client_purchase_history for client ID {client_id}: {e}", exc_info=True)
        return []
