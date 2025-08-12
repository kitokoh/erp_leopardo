import sqlite3
import uuid
from datetime import datetime, timezone
import logging
from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_asset(asset_data: dict, conn: sqlite3.Connection = None) -> str | None:
    """Adds a new asset to the CompanyAssets table."""
    required_fields = ['asset_name', 'asset_type', 'current_status']
    if not all(field in asset_data for field in required_fields):
        logger.error(f"Missing one or more required fields: {required_fields}")
        return None

    asset_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    asset = {
        'asset_id': asset_id,
        'asset_name': asset_data['asset_name'],
        'asset_type': asset_data['asset_type'],
        'serial_number': asset_data.get('serial_number'),
        'description': asset_data.get('description'),
        'purchase_date': asset_data.get('purchase_date'),
        'purchase_value': asset_data.get('purchase_value'),
        'current_status': asset_data['current_status'],
        'notes': asset_data.get('notes'),
        'created_at': now,
        'updated_at': now,
        'is_deleted': 0,
        'deleted_at': None
    }

    columns = ', '.join(asset.keys())
    placeholders = ', '.join('?' for _ in asset)
    sql = f"INSERT INTO CompanyAssets ({columns}) VALUES ({placeholders})"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(asset.values()))
        return asset_id
    except sqlite3.Error as e:
        logger.error(f"Error adding asset: {e}")
        return None

@_manage_conn
def get_asset_by_id(asset_id: str, include_deleted: bool = False, conn: sqlite3.Connection = None) -> dict | None:
    """Fetches an asset by its ID."""
    query = "SELECT * FROM CompanyAssets WHERE asset_id = ?"
    params = [asset_id]
    if not include_deleted:
        query += " AND is_deleted = 0"

    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_all_assets(filters: dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False, conn: sqlite3.Connection = None) -> list[dict]:
    """Fetches assets with optional filtering, pagination, and soft delete handling."""
    base_query = "SELECT * FROM CompanyAssets"
    conditions = []
    params = []

    if filters:
        # Simplified filtering for this example
        if 'asset_type' in filters:
            conditions.append("asset_type = ?")
            params.append(filters['asset_type'])
        if 'current_status' in filters:
            conditions.append("current_status = ?")
            params.append(filters['current_status'])

    if not include_deleted:
        conditions.append("is_deleted = 0")

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY created_at DESC"

    if limit is not None:
        base_query += " LIMIT ?"
        params.append(limit)
    if offset is not None and offset > 0:
        base_query += " OFFSET ?"
        params.append(offset)

    cursor = conn.cursor()
    cursor.execute(base_query, tuple(params))
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_asset(asset_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    """Updates an existing asset."""
    if not data:
        return False

    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    if 'is_deleted' in data:
        if data['is_deleted'] == 1 and 'deleted_at' not in data:
            data['deleted_at'] = data['updated_at']
        elif data['is_deleted'] == 0:
            data['deleted_at'] = None

    valid_columns = ['asset_name', 'asset_type', 'serial_number', 'description', 'purchase_date', 'purchase_value', 'current_status', 'notes', 'updated_at', 'is_deleted', 'deleted_at']
    to_set = {k: v for k, v in data.items() if k in valid_columns}
    if not to_set: return False

    set_clauses = [f"{k} = ?" for k in to_set.keys()]
    params_list = list(to_set.values())
    params_list.append(asset_id)
    sql = f"UPDATE CompanyAssets SET {', '.join(set_clauses)} WHERE asset_id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params_list))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error updating asset {asset_id}: {e}")
        return False

@_manage_conn
def delete_asset(asset_id: str, conn: sqlite3.Connection = None) -> bool:
    """Soft deletes an asset."""
    now_iso = datetime.now(timezone.utc).isoformat()
    data_to_update = {
        'is_deleted': 1,
        'deleted_at': now_iso,
    }
    return update_asset(asset_id, data_to_update, conn=conn)
