import sqlite3
from ..generic_crud import _manage_conn
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from sqlalchemy.sql import text as sqlalchemy_text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__) # Use module-level logger

# Helper functions (copied from other CRUD modules)
# Ideally, these should be in a shared db.crud_utils module
def _get_cursor_and_dialect(conn):
    if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
        return conn, "sqlalchemy"
    elif hasattr(conn, 'cursor'):
        return conn.cursor(), "sqlite"
    logger.warning(f"Unsupported connection type: {type(conn)} in _get_cursor_and_dialect (activity_logs_crud).")
    return None, None

def _execute_query(db_obj, sql_query, params, dialect, logger_to_use=None):
    current_logger = logger_to_use if logger_to_use else logger
    try:
        if dialect == "sqlalchemy":
            return db_obj.execute(sql_query, params)
        elif dialect == "sqlite":
            return db_obj.execute(sql_query, params)
        else:
            current_logger.error(f"Unsupported dialect '{dialect}' in _execute_query.")
            return None
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _execute_query (dialect: {dialect}): {e}", exc_info=True)
        raise

def _fetch_one_as_dict(db_obj, sql_query, params, dialect, logger_to_use=None):
    current_logger = logger_to_use if logger_to_use else logger
    try:
        row_data = None
        if dialect == "sqlalchemy":
            result = db_obj.execute(sql_query, params)
            row = result.fetchone()
            if row: row_data = dict(row._mapping)
        elif dialect == "sqlite":
            db_obj.execute(sql_query, params)
            row = db_obj.fetchone()
            if row:
                # Assuming conn.row_factory = sqlite3.Row was set by _manage_conn or get_db_connection for sqlite
                # If not, manual conversion:
                column_names = [desc[0] for desc in db_obj.description]
                row_data = dict(zip(column_names, row))
        return row_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _fetch_one_as_dict (dialect: {dialect}): {e}", exc_info=True)
        return None

def _fetch_all_as_dict_list(db_obj, sql_query, params, dialect, logger_to_use=None):
    current_logger = logger_to_use if logger_to_use else logger
    try:
        rows_data = []
        if dialect == "sqlalchemy":
            result = db_obj.execute(sql_query, params)
            for row in result.fetchall():
                rows_data.append(dict(row._mapping))
        elif dialect == "sqlite":
            db_obj.execute(sql_query, params)
            rows = db_obj.fetchall()
            if rows:
                # Assuming conn.row_factory = sqlite3.Row for sqlite
                for row_item in rows:
                    rows_data.append(dict(row_item))
        return rows_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _fetch_all_as_dict_list (dialect: {dialect}): {e}", exc_info=True)
        return []

@_manage_conn
def add_activity_log(data: dict, conn=None) -> int | None:
    now = datetime.utcnow().isoformat() + "Z"

    sql_cols = "(user_id, action_type, details, related_entity_type, related_entity_id, related_client_id, created_at)"
    sql_sqlite_placeholders = "(?, ?, ?, ?, ?, ?, ?)"
    sql_sa_placeholders = "(:user_id, :action_type, :details, :related_entity_type, :related_entity_id, :related_client_id, :created_at)"

    sql_sqlite = f"INSERT INTO activity_log {sql_cols} VALUES {sql_sqlite_placeholders}"
    sql_sa = sqlalchemy_text(f"INSERT INTO activity_log {sql_cols} VALUES {sql_sa_placeholders}")

    params_sa = {
        "user_id": data.get('user_id'),
        "action_type": data.get('action_type'),
        "details": data.get('details'),
        "related_entity_type": data.get('related_entity_type'),
        "related_entity_id": data.get('related_entity_id'),
        "related_client_id": data.get('related_client_id'),
        "created_at": now
    }
    params_sqlite = (
        data.get('user_id'), data.get('action_type'), data.get('details'),
        data.get('related_entity_type'), data.get('related_entity_id'),
        data.get('related_client_id'), now
    )

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in add_activity_log: {type(conn)}")
        return None

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                params_sa if dialect == "sqlalchemy" else params_sqlite, dialect, logger)

        last_id = None
        if dialect == "sqlalchemy":
            if result and hasattr(result, 'lastrowid'): last_id = result.lastrowid
        elif dialect == "sqlite": # db_obj is cursor
            if result and hasattr(result, 'lastrowid'): last_id = result.lastrowid

        if last_id is not None:
            return last_id
        # If lastrowid is not supported/returned (e.g. some DBs with SA without RETURNING clause)
        # we can't return the ID, but the operation might have succeeded.
        # For INSERTs, usually want the ID. If it's critical, might need specific handling.
        logger.warning("add_activity_log: lastrowid not retrieved after insert.")
        return None # Or True if success is just "no error"
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Failed to add activity log: {e} with params: {params_sa if dialect == 'sqlalchemy' else params_sqlite}", exc_info=True)
        return None

@_manage_conn
def get_activity_logs(limit: int = 100, offset: int = 0, user_id_filter: str = None, conn=None) -> list[dict]:
    base_sql = "SELECT * FROM activity_log"
    conditions_sqlite = []
    params_sqlite_list = []

    conditions_sa_str = []
    params_sa_dict = {}

    if user_id_filter:
        conditions_sqlite.append("user_id = ?")
        params_sqlite_list.append(user_id_filter)
        conditions_sa_str.append("user_id = :user_id_filter")
        params_sa_dict["user_id_filter"] = user_id_filter

    where_clause_sqlite = (" WHERE " + " AND ".join(conditions_sqlite)) if conditions_sqlite else ""
    where_clause_sa = (" WHERE " + " AND ".join(conditions_sa_str)) if conditions_sa_str else ""

    # Append ORDER BY, LIMIT, OFFSET carefully for each dialect
    # SQLite: ORDER BY ... LIMIT limit_val OFFSET offset_val
    # SA (generic SQL): ORDER BY ... LIMIT :limit_val OFFSET :offset_val (syntax varies by DB)
    # For simplicity with text(), we often embed limit/offset directly for SQLite,
    # or rely on SA features if building SA Core expressions.
    # Here, we'll construct SQL string, so care is needed for SA if not SQLite.
    # Assuming SQLite-like syntax for LIMIT/OFFSET for now.

    final_sql_sqlite = f"{base_sql}{where_clause_sqlite} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params_sqlite_list.extend([limit, offset])

    # For SA, if using named params for limit/offset:
    params_sa_dict["limit_val"] = limit
    params_sa_dict["offset_val"] = offset
    final_sql_sa_str = f"{base_sql}{where_clause_sa} ORDER BY created_at DESC LIMIT :limit_val OFFSET :offset_val"
    final_sql_sa = sqlalchemy_text(final_sql_sa_str)


    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in get_activity_logs: {type(conn)}")
        return []

    try:
        return _fetch_all_as_dict_list(db_obj,
                                       final_sql_sa if dialect == "sqlalchemy" else final_sql_sqlite,
                                       params_sa_dict if dialect == "sqlalchemy" else tuple(params_sqlite_list),
                                       dialect, logger)
    except (sqlite3.Error, SQLAlchemyError) as e: # Should be caught by helper, but as safeguard
        logger.error(f"Failed to get activity logs: {e}", exc_info=True)
        return []

@_manage_conn
def get_activity_log_by_id(log_id: int, conn=None) -> dict | None:
    sql_sqlite = "SELECT * FROM activity_log WHERE log_id = ?"
    sql_sa = sqlalchemy_text("SELECT * FROM activity_log WHERE log_id = :log_id")

    params_sqlite = (log_id,)
    params_sa = {"log_id": log_id}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in get_activity_log_by_id: {type(conn)}")
        return None

    try:
        return _fetch_one_as_dict(db_obj,
                                  sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                  params_sa if dialect == "sqlalchemy" else params_sqlite,
                                  dialect, logger)
    except (sqlite3.Error, SQLAlchemyError) as e: # Should be caught by helper
        logger.error(f"Failed to get activity log by ID {log_id}: {e}", exc_info=True)
        return None

__all__ = [
    "add_activity_log",
    "get_activity_logs",
    "get_activity_log_by_id",
]
