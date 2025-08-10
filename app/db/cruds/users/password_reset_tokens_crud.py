# db/cruds/password_reset_tokens_crud.py
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def create_reset_token(conn, user_id: str, token_hash: str, expires_at: datetime) -> bool:
    """
    Stores a new password reset token hash for a user.
    Deletes any previous, unused tokens for the same user to ensure only one is active.
    Conn can be SQLAlchemy Session/Engine/Connection or sqlite3.Connection.
    """
    delete_sql_sqlite = "DELETE FROM PasswordResetTokens WHERE user_id = ? AND used_at IS NULL"
    delete_sql_sa = text("DELETE FROM PasswordResetTokens WHERE user_id = :user_id AND used_at IS NULL")

    insert_sql_sqlite = """
        INSERT INTO PasswordResetTokens (user_id, token_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    """
    insert_sql_sa = text("""
        INSERT INTO PasswordResetTokens (user_id, token_hash, expires_at, created_at)
        VALUES (:user_id, :token_hash, :expires_at, :created_at)
    """)
    created_at_iso = datetime.now(timezone.utc).isoformat()
    expires_at_iso = expires_at.isoformat()

    params_insert = {
        "user_id": user_id, "token_hash": token_hash,
        "expires_at": expires_at_iso, "created_at": created_at_iso
    }
    params_insert_sqlite = (user_id, token_hash, expires_at_iso, created_at_iso)

    try:
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            conn.execute(delete_sql_sa, {"user_id": user_id})
            # logger.info - rowcount for delete might not be straightforward or always available
            conn.execute(insert_sql_sa, params_insert)
            if isinstance(conn, Session): conn.commit()
        elif hasattr(conn, 'cursor'): # sqlite3.Connection
            cursor = conn.cursor()
            cursor.execute(delete_sql_sqlite, (user_id,))
            logger.info(f"Deleted {cursor.rowcount} existing unused reset token(s) for user {user_id}.")
            cursor.execute(insert_sql_sqlite, params_insert_sqlite)
            conn.commit()
        else:
            logger.error(f"Unsupported connection type: {type(conn)}")
            return False

        logger.info(f"Password reset token created for user {user_id}.")
        return True

    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Database error creating password reset token for user {user_id}: {e}", exc_info=True)
        if isinstance(conn, Session): conn.rollback()
        elif hasattr(conn, 'rollback'): conn.rollback()
        return False

def get_reset_token_by_hash(conn, token_hash: str) -> dict | None:
    """
    Retrieves a password reset token by its hash.
    Only returns if not expired and not already used.
    Conn can be SQLAlchemy Session/Engine/Connection or sqlite3.Connection.
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql_sqlite = """
        SELECT * FROM PasswordResetTokens
        WHERE token_hash = ? AND expires_at > ? AND used_at IS NULL
    """
    sql_sa = text("""
        SELECT * FROM PasswordResetTokens
        WHERE token_hash = :token_hash AND expires_at > :now_utc_iso AND used_at IS NULL
    """)
    params = {"token_hash": token_hash, "now_utc_iso": now_utc_iso}
    params_sqlite = (token_hash, now_utc_iso)

    try:
        row_data = None
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            result = conn.execute(sql_sa, params)
            row = result.fetchone()
            if row: row_data = dict(row._mapping)
        elif hasattr(conn, 'cursor'): # sqlite3.Connection
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, params_sqlite)
            row = cursor.fetchone()
            if row:
                column_names = [desc[0] for desc in cursor.description]
                row_data = dict(zip(column_names, row))
        else:
            logger.error(f"Unsupported connection type: {type(conn)}")
            return None

        if row_data:
            logger.debug(f"Valid password reset token found for hash {token_hash[:10]}...")
            return row_data
        else:
            logger.debug(f"No valid (active, non-expired, unused) password reset token found for hash {token_hash[:10]}...")
            return None
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error retrieving reset token by hash {token_hash[:10]}...: {e}", exc_info=True)
        return None

def mark_token_as_used(conn, token_hash: str) -> bool:
    """
    Marks a password reset token as used by setting the used_at timestamp.
    Conn can be SQLAlchemy Session/Engine/Connection or sqlite3.Connection.
    """
    used_at_iso = datetime.now(timezone.utc).isoformat()
    sql_sqlite = "UPDATE PasswordResetTokens SET used_at = ? WHERE token_hash = ? AND used_at IS NULL"
    sql_sa = text("UPDATE PasswordResetTokens SET used_at = :used_at WHERE token_hash = :token_hash AND used_at IS NULL")

    params = {"used_at": used_at_iso, "token_hash": token_hash}
    params_sqlite = (used_at_iso, token_hash)
    rowcount = 0

    try:
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            result = conn.execute(sql_sa, params)
            rowcount = result.rowcount
            if isinstance(conn, Session): conn.commit()
        elif hasattr(conn, 'cursor'): # sqlite3.Connection
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, params_sqlite)
            rowcount = cursor.rowcount
            conn.commit()
        else:
            logger.error(f"Unsupported connection type: {type(conn)}")
            return False

        if rowcount > 0:
            logger.info(f"Password reset token with hash {token_hash[:10]}... marked as used.")
            return True
        logger.warning(f"Attempted to mark token {token_hash[:10]}... as used, but not found or already used.")
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error marking reset token {token_hash[:10]}... as used: {e}", exc_info=True)
        if isinstance(conn, Session): conn.rollback()
        elif hasattr(conn, 'rollback'): conn.rollback()
        return False

def delete_all_tokens_for_user(conn, user_id: str) -> int:
    """
    Deletes all password reset tokens for a given user.
    Conn can be SQLAlchemy Session/Engine/Connection or sqlite3.Connection.
    """
    sql_sqlite = "DELETE FROM PasswordResetTokens WHERE user_id = ?"
    sql_sa = text("DELETE FROM PasswordResetTokens WHERE user_id = :user_id")
    params = {"user_id": user_id}
    deleted_count = 0

    try:
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            result = conn.execute(sql_sa, params)
            deleted_count = result.rowcount
            if isinstance(conn, Session): conn.commit()
        elif hasattr(conn, 'cursor'): # sqlite3.Connection
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
        else:
            logger.error(f"Unsupported connection type: {type(conn)}")
            return 0

        logger.info(f"Deleted {deleted_count} password reset token(s) for user {user_id}.")
        return deleted_count
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error deleting all reset tokens for user {user_id}: {e}", exc_info=True)
        if isinstance(conn, Session): conn.rollback()
        elif hasattr(conn, 'rollback'): conn.rollback()
        return 0

def cleanup_expired_or_used_tokens(conn) -> int:
    """
    Deletes expired or used password reset tokens.
    Conn can be SQLAlchemy Session/Engine/Connection or sqlite3.Connection.
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql_sqlite = "DELETE FROM PasswordResetTokens WHERE expires_at <= ? OR used_at IS NOT NULL"
    sql_sa = text("DELETE FROM PasswordResetTokens WHERE expires_at <= :now OR used_at IS NOT NULL")
    params = {"now": now_utc_iso}
    deleted_count = 0

    logger.info("Cleaning up expired or used password reset tokens...")
    try:
        if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
            result = conn.execute(sql_sa, params)
            deleted_count = result.rowcount
            if isinstance(conn, Session): conn.commit()
        elif hasattr(conn, 'cursor'): # sqlite3.Connection
            cursor = conn.cursor()
            cursor.execute(sql_sqlite, (now_utc_iso,))
            deleted_count = cursor.rowcount
            conn.commit()
        else:
            logger.error(f"Unsupported connection type: {type(conn)}")
            return 0

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired/used password reset token(s).")
        else:
            logger.info("No expired/used password reset tokens found to clean up.")
        return deleted_count
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error cleaning up expired/used reset tokens: {e}", exc_info=True)
        if isinstance(conn, Session): conn.rollback()
        elif hasattr(conn, 'rollback'): conn.rollback()
        return 0

if __name__ == '__main__':
    # Placeholder for testing - requires a live DB connection and user data
    # from db.connection import get_db_connection
    # conn_test = get_db_connection()
    # if conn_test:
    #     try:
    #         # Example:
    #         # test_user_id = "user-uuid-for-reset" # Ensure this user exists
    #         # test_token = "supersecretresettoken"
    #         # test_token_hash = hashlib.sha256(test_token.encode()).hexdigest() # Example hash
    #         # expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    #
    #         # if create_reset_token(conn_test, test_user_id, test_token_hash, expiry):
    #         #     print("Test token created.")
    #         #     retrieved = get_reset_token_by_hash(conn_test, test_token_hash)
    #         #     print(f"Retrieved: {retrieved}")
    #         #     if retrieved:
    #         #         if mark_token_as_used(conn_test, test_token_hash):
    #         #             print("Token marked as used.")
    #         #             assert get_reset_token_by_hash(conn_test, test_token_hash) is None
    #
    #         # cleanup_expired_or_used_tokens(conn_test)
    #
    #     finally:
    #         conn_test.close()
    pass

