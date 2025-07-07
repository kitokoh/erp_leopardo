import sqlite3
from typing import Union, List, Dict, Any
import uuid # Required by some CRUD functions, even if not directly in generic
import hashlib # Required by some CRUD functions, even if not directly in generic
from datetime import datetime # Required by some CRUD functions, even if not directly in generic
import json # Required by some CRUD functions, even if not directly in generic
import os # Keep os if used by other parts of the file, but not for path manipulation for config.
import logging

# Configuration and Utilities
# try:
#     # This is the primary and now should be the ONLY way it gets get_db_connection
#     from ..connection import get_db_connection ### MOVED INTO _manage_conn.wrapper
# except ImportError as e:
#     # If this import fails, it's a problem with db.connection or the package structure.
#     # generic_crud.py should not try to work around it with its own config loading.
#     logging.critical(f"CRITICAL: Failed to import get_db_connection from ..connection in generic_crud.py. Error: {e}")
#     # Re-raise the error as the CRUD operations cannot function without a db connection.
#     raise ImportError(f"Essential import get_db_connection from ..connection failed in generic_crud.py") from e

from sqlalchemy.sql import text as sqlalchemy_text # Import text
from sqlalchemy.exc import SQLAlchemyError # For SQLAlchemy specific errors

# Helper to check if conn is SQLAlchemy Session or similar
def _is_sqlalchemy_obj(conn_obj):
    return hasattr(conn_obj, 'execute') and not hasattr(conn_obj, 'cursor')

# Helper to manage connection lifecycle for CRUD functions
def _manage_conn(func):
    def wrapper(*args, **kwargs):
        from ..connection import get_db_connection # DEFERRED IMPORT
        conn_passed = kwargs.get('conn')
        conn_is_external = conn_passed is not None
        conn_to_use = conn_passed if conn_is_external else get_db_connection()

        try:
            kwargs_for_func = {**kwargs, 'conn': conn_to_use}
            result = func(*args, **kwargs_for_func)

            if not conn_is_external:
                write_ops_keywords = ['add', 'update', 'delete', 'set', 'link', 'unlink', 'assign', 'unassign', 'populate', 'insert', 'execute', 'remove', 'create', 'drop', 'alter']
                is_write_operation = any(op in func.__name__ for op in write_ops_keywords)

                # Check if the function returned a cursor and it performed a write operation
                # This is a heuristic and might need refinement based on actual function behaviors
                if hasattr(result, 'lastrowid') and result.lastrowid is not None: # e.g. INSERT
                    is_write_operation = True
                elif hasattr(result, 'rowcount') and result.rowcount > 0 and not func.__name__.startswith('get') and not func.__name__.startswith('fetch'): # e.g. UPDATE, DELETE
                    is_write_operation = True


                if is_write_operation:
                    conn_to_use.commit()
            return result
        except sqlite3.Error as e:
            # logging.error(f"Database error in {func.__name__}: {e}") # Consider logging
            if not conn_is_external and conn_to_use:
                conn_to_use.rollback()
            raise
        finally:
            if not conn_is_external and conn_to_use:
                conn_to_use.close()
    return wrapper


# Generic CRUD Base Class
class GenericCRUD:
    def __init__(self, table_name=None, primary_key=None, db_path=None):
        self.table_name = table_name
        self.primary_key = primary_key
        self.db_path = db_path
    """
    A base class providing generic CRUD (Create, Read, Update, Delete) operations
    that can be inherited by specific CRUD classes for different database tables.

    This class is designed to work with SQLite and uses a connection management
    decorator (`@_manage_conn`) for its methods. Child classes should typically
    define `table_name` and `id_column` attributes in their `__init__` method
    if they intend to use these generic methods directly without overriding or
    if they call super() to these methods.
    """

    # Helper function to convert sqlite3.Row objects to dictionaries
    # This is useful if not using conn.row_factory = sqlite3.Row globally,
    # or if needing to ensure dict conversion at a specific point.
    # However, with conn.row_factory = sqlite3.Row, direct dict(row) works.
    # Let's define it here for explicitness and potential complex object handling later.
    def _object_to_dict(self, db_row: sqlite3.Row) -> Union[Dict, None]:
        """Converts a sqlite3.Row object to a dictionary."""
        if db_row is None:
            return None
        return dict(db_row)

    @_manage_conn
    def get_by_id(self, table_name: str, id_column: str, item_id: Any, conn: sqlite3.Connection) -> Union[Dict, None]:
        """
        Fetches a single record from a specified table by its ID.

        Args:
            table_name (str): The name of the table to query.
            id_column (str): The name of the ID column in the table.
            item_id (any): The ID of the item to fetch.
            conn (sqlite3.Connection): The database connection object.

        Returns:
            dict | None: A dictionary representing the record if found, otherwise None.
        """
        query = f"SELECT * FROM {table_name} WHERE {id_column} = ?"

        if _is_sqlalchemy_obj(conn):
            # Query uses '?', so pass params as a tuple for SA text()
            result = conn.execute(sqlalchemy_text(query), (item_id,))
            row = result.fetchone()
        else:
            # Temporarily set row_factory for sqlite3 for dict-like access if not already default
            original_row_factory = None
            if hasattr(conn, 'row_factory') and conn.row_factory != sqlite3.Row:
                original_row_factory = conn.row_factory
                conn.row_factory = sqlite3.Row

            cursor = conn.execute(query, (item_id,))
            row = cursor.fetchone()

            if original_row_factory is not None: # Reset if changed
                conn.row_factory = original_row_factory

        return self._object_to_dict(row)

    @_manage_conn
    def delete_by_id(self, table_name: str, id_column: str, item_id: Any, conn: sqlite3.Connection) -> bool:
        query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
        if _is_sqlalchemy_obj(conn):
            # For SQLAlchemy, parameters for text() are typically passed as a dictionary
            # if the query string uses named parameters e.g. :id_param
            # If using '?', it depends on the DBAPI driver's paramstyle.
            # Pysqlite (sqlite3) uses qmark or numeric.
            # Let's assume qmark style for simplicity with text() for now.
            result = conn.execute(sqlalchemy_text(query), (item_id,))
            # conn.commit() # Handled by _manage_conn for SA if it's a session
        else:
            cursor = conn.execute(query, (item_id,))
            # conn.commit() # Handled by _manage_conn for sqlite3
            result = cursor
        return result.rowcount > 0

    @_manage_conn
    def exists_by_id(self, table_name: str, id_column: str, item_id: Any, conn: sqlite3.Connection) -> bool:
        query = f"SELECT 1 FROM {table_name} WHERE {id_column} = ?"
        row = None
        if _is_sqlalchemy_obj(conn):
            # Query uses '?', so pass params as a tuple for SA text()
            result = conn.execute(sqlalchemy_text(query), (item_id,))
            row = result.fetchone()
        else:
            cursor = conn.execute(query, (item_id,))
            row = cursor.fetchone()
        return row is not None

    @_manage_conn
    def get_all(self, table_name: str, conn: sqlite3.Connection, order_by: str = None) -> List[Dict]:
        query = f"SELECT * FROM {table_name}"
        if order_by:
            # Important: Ensure order_by is sanitized if it comes from user input
            # For now, assuming it's a safe, internally defined string.
            query += f" ORDER BY {order_by}"

        rows = []
        if _is_sqlalchemy_obj(conn):
            result = conn.execute(sqlalchemy_text(query))
            rows = result.fetchall()
        else:
            # Temporarily set row_factory for sqlite3 for dict-like access
            original_row_factory = None
            if hasattr(conn, 'row_factory') and conn.row_factory != sqlite3.Row:
                original_row_factory = conn.row_factory
                conn.row_factory = sqlite3.Row

            cursor = conn.execute(query)
            rows = cursor.fetchall()

            if original_row_factory is not None: # Reset if changed
                conn.row_factory = original_row_factory

        return [self._object_to_dict(row) for row in rows]

    @_manage_conn
    def create(self, data: Dict, conn: sqlite3.Connection, table_name: str = None) -> Union[Any, None]:
        _table_name = table_name if table_name else self.table_name
        if not _table_name:
            logging.error("Table name not specified for create operation.")
            return None

        columns = ', '.join(data.keys())

        if _is_sqlalchemy_obj(conn):
            # For SQLAlchemy, use named parameters for clarity with text()
            named_placeholders = ', '.join([f":{key}" for key in data.keys()])
            query = f"INSERT INTO {_table_name} ({columns}) VALUES ({named_placeholders})"
            params = data # Use the dict directly
        else:
            qmark_placeholders = ', '.join(['?'] * len(data))
            query = f"INSERT INTO {_table_name} ({columns}) VALUES ({qmark_placeholders})"
            params = list(data.values())

        try:
            if _is_sqlalchemy_obj(conn):
                result = conn.execute(sqlalchemy_text(query), params)
                # conn.commit() # Handled by _manage_conn for SA Session
                # lastrowid might not be available or reliable on all DBs/drivers with SA
                # For SQLite with SA, result.lastrowid should work after an INSERT.
                return result.lastrowid
            else:
                cursor = conn.execute(query, params)
                # conn.commit() # Handled by _manage_conn for sqlite3
                return cursor.lastrowid
        except (sqlite3.Error, SQLAlchemyError) as e:
            logging.error(f"Error creating record in {_table_name}: {e} with data {data}")
            raise

    @_manage_conn
    def get_by_attributes(self, attributes: Dict, conn: sqlite3.Connection, table_name: str = None, logical_operator: str = "AND", order_by: str = None) -> List[Dict]:
        """
        Fetches records from the specified table that match given attributes.

        Args:
            attributes (dict): A dictionary of column names and their desired values.
            conn (sqlite3.Connection): The database connection object.
            table_name (str, optional): The name of the table. If None, uses self.table_name.
            logical_operator (str): The logical operator to join conditions ("AND" or "OR").
                                    Defaults to "AND".
            order_by (str, optional): A string to use for the ORDER BY clause.

        Returns:
            list[dict]: A list of dictionaries representing the matching records.
                        Returns an empty list if no records match or table is not found.
                        Returns empty list if table_name is not set and not provided.
        """
        _table_name = table_name if table_name else self.table_name
        if not _table_name:
            logging.error("Table name not specified for get_by_attributes operation.")
            return []

        if not attributes:
            # If no attributes, effectively a get_all, but let's be explicit.
            # Or one might argue it should return an error or all items.
            # For now, let's return all items if attributes is empty, like a get_all.
            # This matches the behavior if the WHERE clause was empty.
            return self.get_all(table_name=_table_name, conn=conn, order_by=order_by)

        conditions = []
        values = []
        for key, value in attributes.items():
            if value is None:
                conditions.append(f"{key} IS NULL")
            else:
                conditions.append(f"{key} = ?")
                values.append(value)

        if not conditions: # Should not happen if attributes is not empty, but as a safe guard.
             return self.get_all(table_name=_table_name, conn=conn, order_by=order_by)

        where_clause = f" {logical_operator.upper()} ".join(conditions)
        # query will use '?' placeholders as constructed.
        query = f"SELECT * FROM {_table_name} WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}" # Assuming order_by is safe

        rows = []
        if _is_sqlalchemy_obj(conn):
            # For SA with '?' placeholders (qmark style), pass 'values' as a tuple.
            result = conn.execute(sqlalchemy_text(query), tuple(values))
            rows = result.fetchall()
        else:
            original_row_factory = None
            if hasattr(conn, 'row_factory') and conn.row_factory != sqlite3.Row:
                original_row_factory = conn.row_factory
                conn.row_factory = sqlite3.Row

            cursor = conn.execute(query, values)
            rows = cursor.fetchall()

            if original_row_factory is not None:
                conn.row_factory = original_row_factory

        return [self._object_to_dict(row) for row in rows]

    @_manage_conn
    def update(self, item_id: Any, data: Dict, conn: sqlite3.Connection, table_name: str = None, id_column: str = None) -> bool:
        _table_name = table_name if table_name else self.table_name
        _id_column = id_column if id_column else self.primary_key

        if not _table_name or not _id_column:
            logging.error("Table name or primary key not specified for update operation.")
            return False
        if not data:
            logging.warning(f"No data provided for update on table {_table_name}, ID {item_id}.")
            return False

        params_dict_for_sa = {} # For SQLAlchemy if using named parameters

        if _is_sqlalchemy_obj(conn):
            # Build SET clause with named parameters for SQLAlchemy
            set_clause_parts = []
            current_params = {}
            idx = 0
            for key, value in data.items():
                param_name = f"val_{idx}"
                set_clause_parts.append(f"{key} = :{param_name}")
                current_params[param_name] = value
                idx += 1
            set_clause = ", ".join(set_clause_parts)

            id_param_name = "id_val"
            current_params[id_param_name] = item_id
            query = f"UPDATE {_table_name} SET {set_clause} WHERE {_id_column} = :{id_param_name}"
            params_for_exec = current_params
        else:
            # Build SET clause with '?' for sqlite3
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            query = f"UPDATE {_table_name} SET {set_clause} WHERE {_id_column} = ?"
            params_for_exec = list(data.values())
            params_for_exec.append(item_id)

        try:
            if _is_sqlalchemy_obj(conn):
                result = conn.execute(sqlalchemy_text(query), params_for_exec)
                # conn.commit() # Handled by _manage_conn for SA Session
            else:
                cursor = conn.execute(query, params_for_exec)
                # conn.commit() # Handled by _manage_conn for sqlite3
                result = cursor # Use cursor for rowcount
            return result.rowcount > 0
        except (sqlite3.Error, SQLAlchemyError) as e:
            logging.error(f"Error updating record in {_table_name} with ID {item_id}: {e} using data {data}")
            raise

# Utility function, can be outside the class if preferred, or static.
# Making it a top-level function for easier import/use by other modules if needed.
def object_to_dict(db_row: sqlite3.Row) -> Union[Dict, None]:
    """Converts a sqlite3.Row object to a dictionary."""
    if db_row is None:
        return None
    return dict(db_row)