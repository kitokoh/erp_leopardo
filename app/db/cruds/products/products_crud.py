import sqlite3
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ...generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_product(product_data: dict, conn: sqlite3.Connection = None) -> int | None:
    """Adds a new product to the database."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    sql = """
        INSERT INTO Products (product_name, product_code, description, base_unit_price, is_active, created_at, updated_at, language_code, weight, dimensions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        product_data.get('product_name'),
        product_data.get('product_code'),
        product_data.get('description'),
        product_data.get('base_unit_price'),
        product_data.get('is_active', True),
        now,
        now,
        product_data.get('language_code'),
        product_data.get('weight'),
        product_data.get('dimensions')
    )
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Error adding product: {e}")
        return None

@_manage_conn
def get_product_by_id(product_id: int, conn: sqlite3.Connection = None, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
    """Fetches a single product by its ID."""
    query = "SELECT * FROM Products WHERE product_id = ?"
    if not include_deleted:
        query += " AND is_deleted = 0"

    cursor = conn.cursor()
    cursor.execute(query, (product_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_product_by_name(product_name: str, conn: sqlite3.Connection = None, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
    """Fetches a single product by its name."""
    query = "SELECT * FROM Products WHERE product_name = ?"
    if not include_deleted:
        query += " AND is_deleted = 0"

    cursor = conn.cursor()
    cursor.execute(query, (product_name,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_all_products(conn: sqlite3.Connection = None, skip: int = 0, limit: int = 100, include_deleted: bool = False, filters: dict = None) -> List[Dict[str, Any]]:
    """Retrieves all products with pagination and optional filters."""
    query = "SELECT * FROM Products"
    conditions = []
    params = []

    if not include_deleted:
        conditions.append("is_deleted = 0")

    if filters:
        if 'is_active' in filters:
            conditions.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY product_name LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def get_products_by_name_pattern(name_pattern: str, conn: sqlite3.Connection = None, include_deleted: bool = False) -> List[Dict[str, Any]]:
    """Fetches products with names matching a pattern."""
    query = "SELECT * FROM Products WHERE product_name LIKE ?"
    if not include_deleted:
        query += " AND is_deleted = 0"

    cursor = conn.cursor()
    cursor.execute(query, (f"%{name_pattern}%",))
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_product(product_id: int, update_data: Dict[str, Any], conn: sqlite3.Connection = None) -> bool:
    """Updates a product's information."""
    if not update_data:
        return False

    update_data['updated_at'] = datetime.utcnow().isoformat()

    valid_columns = ['product_name', 'product_code', 'description', 'base_unit_price', 'is_active', 'updated_at', 'language_code', 'weight', 'dimensions']
    to_set = {k: v for k, v in update_data.items() if k in valid_columns}
    if not to_set: return False

    set_clauses = [f"{k} = ?" for k in to_set.keys()]
    params_list = list(to_set.values())
    params_list.append(product_id)
    sql = f"UPDATE Products SET {', '.join(set_clauses)} WHERE product_id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params_list))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return False

@_manage_conn
def delete_product(product_id: int, conn: sqlite3.Connection = None) -> bool:
    """Soft deletes a product."""
    update_data = {
        'is_deleted': True,
        'is_active': False,
        'deleted_at': datetime.utcnow().isoformat()
    }
    return update_product(product_id, update_data, conn=conn)

# Note: The following functions are not implemented as they depend on other tables that might also need refactoring.
# This is a placeholder for the functions that were in the original file.
def add_product_dimension(product_id: int, dimension_data: dict, conn: sqlite3.Connection = None):
    logger.warning("add_product_dimension is not implemented")
    return None

def get_product_dimension(product_id: int, conn: sqlite3.Connection = None):
    logger.warning("get_product_dimension is not implemented")
    return None

def add_product_equivalence(product_id_a: int, product_id_b: int, conn: sqlite3.Connection = None):
    logger.warning("add_product_equivalence is not implemented")
    return None

def get_equivalent_products(product_id: int, conn: sqlite3.Connection = None):
    logger.warning("get_equivalent_products is not implemented")
    return []

def get_total_products_count(conn: sqlite3.Connection = None, include_deleted: bool = False) -> int:
    logger.warning("get_total_products_count is not implemented")
    return 0

# This is a class instance that is not used anymore, but kept for compatibility with other files that might import it.
class ProductsCRUD:
    pass

products_crud_instance = ProductsCRUD()
