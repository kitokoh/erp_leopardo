import sqlite3
import uuid
from datetime import datetime, timezone # Added timezone
import logging # Added logging
from sqlalchemy.sql import text as sqlalchemy_text
from sqlalchemy.exc import SQLAlchemyError
from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

def _is_sa_obj(conn_obj):
    return not hasattr(conn_obj, 'cursor')

# --- Companies CRUD ---
@_manage_conn
def add_company(company_data: dict, conn = None) -> str | None:
    new_id = str(uuid.uuid4())
    # Ensure timezone-aware UTC datetime
    now = datetime.now(timezone.utc).isoformat()

    base_sql_cols = "company_id, company_name, address, payment_info, logo_path, other_info, is_default, created_at, updated_at"

    params_dict = {
        "company_id": new_id,
        "company_name": company_data['company_name'],
        "address": company_data.get('address'),
        "payment_info": company_data.get('payment_info'),
        "logo_path": company_data.get('logo_path'),
        "other_info": company_data.get('other_info'),
        "is_default": company_data.get('is_default', False),
        "created_at": now,
        "updated_at": now
    }

    try:
        if _is_sa_obj(conn):
            sa_placeholders = ", ".join([f":{col}" for col in params_dict.keys() if col in base_sql_cols.split(", ")]) # Ensure order matches columns
            # Need to ensure the columns in SQL match the keys in params_dict used for placeholders
            # For simplicity, let's assume params_dict keys are exactly the column names
            sql_sa = f"INSERT INTO companies ({base_sql_cols}) VALUES ({sa_placeholders})"
            conn.execute(sqlalchemy_text(sql_sa), params_dict)
        else:
            # For sqlite3, order matters for '?'
            sql_sqlite = f"INSERT INTO companies ({base_sql_cols}) VALUES (?,?,?,?,?,?,?,?,?)"
            # Ensure params_tuple matches the order of base_sql_cols
            params_tuple = (
                new_id, company_data['company_name'], company_data.get('address'),
                company_data.get('payment_info'), company_data.get('logo_path'),
                company_data.get('other_info'), company_data.get('is_default', False),
                now, now
            )
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, params_tuple)

        logger.info(f"Company '{company_data['company_name']}' added with ID {new_id}.")
        return new_id
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Failed to add company '{company_data.get('company_name', 'N/A')}': {e}", exc_info=True)
        return None

@_manage_conn
def get_company_by_id(company_id: str, conn = None) -> dict | None:
    sql = "SELECT * FROM companies WHERE company_id = :company_id"
    try:
        if _is_sa_obj(conn):
            result = conn.execute(sqlalchemy_text(sql), {"company_id": company_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
        else:
            sql_sqlite = "SELECT * FROM companies WHERE company_id = ?"
            original_factory = conn.row_factory
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, (company_id,))
            row = cursor.fetchone()
            conn.row_factory = original_factory
            return dict(row) if row else None
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error fetching company ID {company_id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_all_companies(conn = None) -> list[dict]:
    sql = "SELECT * FROM companies ORDER BY company_name"
    try:
        if _is_sa_obj(conn):
            result = conn.execute(sqlalchemy_text(sql))
            return [dict(row._mapping) for row in result.fetchall()]
        else:
            original_factory = conn.row_factory
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql) # Error was here: conn.cursor(); cursor.execute(...)
            rows = cursor.fetchall()
            conn.row_factory = original_factory
            return [dict(row) for row in rows]
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error fetching all companies: {e}", exc_info=True)
        return []

@_manage_conn
def update_company(company_id: str, data: dict, conn = None) -> bool:
    now = datetime.now(timezone.utc).isoformat()

    valid_cols = ['company_name', 'address', 'payment_info', 'logo_path', 'other_info', 'is_default']
    fields_to_update = {k: v for k, v in data.items() if k in valid_cols}
    if not fields_to_update:
        logger.warning(f"No valid fields to update for company ID {company_id}.")
        return False

    fields_to_update['updated_at'] = now # Always update 'updated_at'

    try:
        if _is_sa_obj(conn):
            set_clause_parts = [f"{key} = :{key}" for key in fields_to_update.keys()]
            sql_sa = f"UPDATE companies SET {', '.join(set_clause_parts)} WHERE company_id = :company_id"
            params_sa = {**fields_to_update, "company_id": company_id}
            result = conn.execute(sqlalchemy_text(sql_sa), params_sa)
            rowcount = result.rowcount
        else:
            set_clause_sqlite = [f"{key} = ?" for key in fields_to_update.keys()]
            sql_sqlite = f"UPDATE companies SET {', '.join(set_clause_sqlite)} WHERE company_id = ?"
            params_sqlite = list(fields_to_update.values())
            params_sqlite.append(company_id)
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, params_sqlite)
            rowcount = cursor.rowcount

        if rowcount > 0:
            logger.info(f"Company ID {company_id} updated.")
            return True
        logger.warning(f"Company ID {company_id} not found or no changes made during update.")
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Failed to update company {company_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_company(company_id: str, conn = None) -> bool:
    sql = "DELETE FROM companies WHERE company_id = :company_id"
    try:
        if _is_sa_obj(conn):
            result = conn.execute(sqlalchemy_text(sql), {"company_id": company_id})
            rowcount = result.rowcount
        else:
            sql_sqlite = "DELETE FROM companies WHERE company_id = ?"
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, (company_id,))
            rowcount = cursor.rowcount

        if rowcount > 0:
            logger.info(f"Company ID {company_id} deleted.")
            return True
        logger.warning(f"Company ID {company_id} not found for deletion.")
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Failed to delete company {company_id}: {e}", exc_info=True)
        return False

@_manage_conn
def set_default_company(company_id: str, conn = None) -> bool:
    try:
        if _is_sa_obj(conn):
            # Reset existing default(s)
            sql_reset = "UPDATE companies SET is_default = :false_val WHERE is_default = :true_val AND company_id != :company_id"
            conn.execute(sqlalchemy_text(sql_reset), {"false_val": False, "true_val": True, "company_id": company_id})
            # Set new default
            sql_set = "UPDATE companies SET is_default = :true_val WHERE company_id = :company_id"
            conn.execute(sqlalchemy_text(sql_set), {"true_val": True, "company_id": company_id})
        else:
            cursor = conn.cursor()
            cursor.execute("UPDATE companies SET is_default = FALSE WHERE is_default = TRUE AND company_id != ?", (company_id,))
            cursor.execute("UPDATE companies SET is_default = TRUE WHERE company_id = ?", (company_id,))

        logger.info(f"Company ID {company_id} set as default.")
        return True
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Failed to set default company {company_id}: {e}", exc_info=True)
        return False

@_manage_conn
def get_default_company(conn = None) -> dict | None:
    sql = "SELECT * FROM companies WHERE is_default = :is_default_true"
    try:
        if _is_sa_obj(conn):
            result = conn.execute(sqlalchemy_text(sql), {"is_default_true": True})
            row = result.fetchone()
            return dict(row._mapping) if row else None
        else:
            sql_sqlite = "SELECT * FROM companies WHERE is_default = TRUE" # sqlite3 handles TRUE as 1
            original_factory = conn.row_factory
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql_sqlite)
            row = cursor.fetchone()
            conn.row_factory = original_factory
            return dict(row) if row else None
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Failed to get default company: {e}", exc_info=True)
        return None

__all__ = [
    "add_company",
    "get_company_by_id",
    "get_all_companies",
    "update_company",
    "delete_company",
    "set_default_company",
    "get_default_company",
]
