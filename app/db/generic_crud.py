import sqlite3
import functools
import logging
from sqlalchemy.engine.row import Row as RowProxy
from app.db.connection import get_db_connection
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection


logger = logging.getLogger(__name__)

def _is_sqlalchemy_obj(conn):
    """Checks if the object is a SQLAlchemy Session, Engine, or Connection."""
    return isinstance(conn, (Session, Engine, SQLAlchemyConnection))

def _convert_to_dict(row):
    """
    Converts a SQLAlchemy RowProxy or sqlite3.Row object to a dictionary.
    """
    if isinstance(row, RowProxy):
        return dict(row._mapping)
    elif isinstance(row, sqlite3.Row):
        return dict(row)
    return row

def _manage_conn(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = kwargs.get('conn')
        if conn:
            # If a connection is already provided, use it without managing it.
            # This allows for transactions across multiple CRUD calls.
            return func(*args, **kwargs)

        # If no connection is provided, create and manage one.
        conn = None
        try:
            conn = get_db_connection()
            kwargs['conn'] = conn
            result = func(*args, **kwargs)
            conn.commit()
            return result
        except sqlite3.Error as e:
            logger.error(f"Database error in function '{func.__name__}': {e}", exc_info=True)
            if conn:
                conn.rollback()
            # Depending on desired behavior, you might want to return None, False, or re-raise.
            # Returning None is a common pattern for "failure".
            return None
        finally:
            if conn and not kwargs.get('conn'): # Only close if this wrapper created it
                conn.close()
    return wrapper

class GenericCRUD:
    def __init__(self, table_name, primary_key, db_path=None):
        self.table_name = table_name
        self.primary_key = primary_key
        self.db_path = db_path

    def create(self, data: dict, conn: sqlite3.Connection = None):
        if conn is None:
            with get_db_connection(self.db_path) as conn:
                return self._execute_create(conn, data)
        else:
            return self._execute_create(conn, data)

    def _execute_create(self, conn: sqlite3.Connection, data: dict):
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' for _ in data)
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        try:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(data.values()))
            # No commit here if conn is passed in, assuming caller manages transaction
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating record in {self.table_name}: {e}")
            return False

    def read(self, pk_value, conn: sqlite3.Connection = None):
        if conn is None:
            with get_db_connection(self.db_path) as conn:
                return self._execute_read(conn, pk_value)
        else:
            return self._execute_read(conn, pk_value)

    def _execute_read(self, conn: sqlite3.Connection, pk_value):
        sql = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = ?"
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (pk_value,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error reading record from {self.table_name}: {e}")
            return None

    def update(self, pk_value, data: dict, conn: sqlite3.Connection = None):
        if conn is None:
            with get_db_connection(self.db_path) as conn:
                return self._execute_update(conn, pk_value, data)
        else:
            return self._execute_update(conn, pk_value, data)

    def _execute_update(self, conn: sqlite3.Connection, pk_value, data: dict):
        if not data:
            return False
        columns = ', '.join(f"{key} = ?" for key in data)
        sql = f"UPDATE {self.table_name} SET {columns} WHERE {self.primary_key} = ?"
        params = list(data.values())
        params.append(pk_value)
        try:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating record in {self.table_name}: {e}")
            return False

    def delete(self, pk_value, conn: sqlite3.Connection = None):
        if conn is None:
            with get_db_connection(self.db_path) as conn:
                return self._execute_delete(conn, pk_value)
        else:
            return self._execute_delete(conn, pk_value)

    def _execute_delete(self, conn: sqlite3.Connection, pk_value):
        sql = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?"
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (pk_value,))
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting record from {self.table_name}: {e}")
            return False
