import sqlite3 # Keep for type hint reference if _manage_conn can provide both
from sqlalchemy.sql import text # Import text
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from datetime import datetime
import logging
from .generic_crud import _manage_conn

# --- ApplicationSettings CRUD ---
@_manage_conn
def get_setting(key: str, default: any = None, conn = None) -> any: # conn type can be Session or Connection
    value_to_return = default
    try:
        # Check if conn is SQLAlchemy Session, Engine, or Connection
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            # SQLAlchemy execution
            stmt = text("SELECT setting_value FROM ApplicationSettings WHERE setting_key = :key")
            result = conn.execute(stmt, {"key": key})
            row = result.fetchone()
            if row:
                # Access by index (e.g., row[0])
                value_to_return = row[0]
        elif hasattr(conn, 'cursor'): # Fallback to sqlite3.Connection interface
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM ApplicationSettings WHERE setting_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                # sqlite3 rows can be accessed by index or by name if row_factory is set
                # Assuming row is a tuple or a row object that supports indexed access like a tuple
                value_to_return = row[0] if isinstance(row, tuple) else row['setting_value']
        else:
            logging.error(f"Unsupported connection type for get_setting: {type(conn)}")
            return default

        logging.info(f"Retrieved setting: {key} = {value_to_return}")
        return value_to_return
    except Exception as e: # Catch generic Exception as it could be SQLAlchemy or sqlite3
        logging.error(f"Failed to get setting for key {key}: {e}", exc_info=True)
        logging.info(f"Returning default value for key {key} due to error: {default}")
        return default

@_manage_conn
def set_setting(key: str, value: str, conn = None, **kwargs) -> bool: # conn type can be Session or Connection
    try:
        logging.info(f"Setting value for key {key} = {value}")
        # Check if conn is an SQLAlchemy Session, Engine, or Connection
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            stmt = text("INSERT OR REPLACE INTO ApplicationSettings (setting_key, setting_value) VALUES (:key, :value)")
            result = conn.execute(stmt, {"key": key, "value": value})
            # For SQLAlchemy, commit is often handled by the session's context manager or explicitly outside.
            # _manage_conn is assumed to handle commit for session if it provided one.
            # result.rowcount might not be available/reliable for all drivers/statements with SQLAlchemy,
            # but for INSERT/REPLACE it usually is.
            return result.rowcount > 0 if hasattr(result, 'rowcount') else True
        elif hasattr(conn, 'cursor'): # Fallback to sqlite3.Connection interface (DBAPI)
            # This branch handles raw sqlite3 connections
            cursor = conn.cursor()
            sql = "INSERT OR REPLACE INTO ApplicationSettings (setting_key, setting_value) VALUES (?, ?)"
            cursor.execute(sql, (key, value))
            # conn.commit() is handled by _manage_conn for sqlite3
            return cursor.rowcount > 0
        else:
            logging.error(f"Unsupported connection type for set_setting: {type(conn)}")
            return False
    except Exception as e: # Catch generic Exception
        logging.error(f"Failed to set setting for key {key}, value {value}: {e}", exc_info=True)
        return False

@_manage_conn
def get_next_invoice_number(conn = None) -> str: # conn type can be Session or Connection
    """
    Generates the next invoice number in the sequence for the current year.
    Format: INV-YYYY-NNNNN (e.g., INV-2024-00001)
    """
    current_year = datetime.now().year
    setting_key = f"last_invoice_sequence_{current_year}"
    prefix = f"INV-{current_year}-"

    last_sequence_str = get_setting(setting_key, conn=conn)

    last_sequence = 0
    if last_sequence_str:
        try:
            last_sequence = int(last_sequence_str)
        except ValueError:
            # Invalid value in DB, log an error or handle as first invoice
            # For now, treat as first invoice of the year if conversion fails
            print(f"Warning: Invalid invoice sequence number '{last_sequence_str}' in settings for key '{setting_key}'. Resetting to 0.")
            last_sequence = 0
            # Optionally, one might want to repair the setting here or raise a more critical error.

    next_sequence = last_sequence + 1

    # Store the new sequence number
    # The set_setting function is also decorated with _manage_conn,
    # it will use the connection provided by this function's decorator.
    success = set_setting(setting_key, str(next_sequence), conn=conn)

    if not success:
        # This would indicate a problem saving the new sequence, which is critical.
        # Depending on desired robustness, could raise an exception here.
        # For now, we'll proceed to format the number, but the next call might reuse it.
        print(f"CRITICAL: Failed to update invoice sequence number for key '{setting_key}' to '{next_sequence}'.")
        # Consider raising an exception: raise sqlite3.Error("Failed to update invoice sequence number.")

    invoice_number = f"{prefix}{next_sequence:05d}" # Zero-pads to 5 digits
    return invoice_number
