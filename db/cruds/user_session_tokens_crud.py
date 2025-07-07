# db/cruds/user_session_tokens_crud.py
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
import uuid
from sqlalchemy.sql import text # Import text
from sqlalchemy.exc import SQLAlchemyError # For SQLAlchemy specific errors

logger = logging.getLogger(__name__)

def _is_sqlalchemy_session(conn_obj):
    """Checks if the connection object is likely a SQLAlchemy Session."""
    return hasattr(conn_obj, 'execute') and hasattr(conn_obj, 'commit') and hasattr(conn_obj, 'rollback') and not hasattr(conn_obj, 'cursor')


def add_session_token(conn, user_id: str, token_hash: str, expires_at: datetime, device_identifier: str | None = None) -> str | None:
    token_id = str(uuid.uuid4())
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    expires_at_iso = expires_at.isoformat()

    sql_stmt = """
        INSERT INTO UserSessionTokens (
            token_id, user_id, token_hash, device_identifier,
            expires_at, created_at, last_used_at
        ) VALUES (:token_id, :user_id, :token_hash, :device_identifier,
                  :expires_at, :created_at, :last_used_at)
    """
    params = {
        "token_id": token_id, "user_id": user_id, "token_hash": token_hash,
        "device_identifier": device_identifier, "expires_at": expires_at_iso,
        "created_at": now_utc_iso, "last_used_at": now_utc_iso
    }

    try:
        if _is_sqlalchemy_session(conn):
            conn.execute(text(sql_stmt), params)
            conn.commit()
        else: # sqlite3.Connection
            # Convert named params for sqlite3's qmark style if necessary, or use dict style if version supports
            # For simplicity, assuming sqlite3 version supports named placeholders or adapting sql_stmt
            # Adapting to qmark style for broader compatibility:
            sql_qmark = """
                INSERT INTO UserSessionTokens (
                    token_id, user_id, token_hash, device_identifier,
                    expires_at, created_at, last_used_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            qmark_params = (
                token_id, user_id, token_hash, device_identifier,
                expires_at_iso, now_utc_iso, now_utc_iso
            )
            cursor = conn.cursor()
            cursor.execute(sql_qmark, qmark_params)
            conn.commit()
        logger.info(f"Session token {token_id} added for user {user_id}.")
        return token_id
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Database error adding session token for user {user_id}: {e}", exc_info=True)
        if hasattr(conn, 'rollback'): conn.rollback()
        return None

def get_session_token_by_hash(conn, token_hash: str) -> dict | None:
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql_stmt = """
        SELECT * FROM UserSessionTokens
        WHERE token_hash = :token_hash AND expires_at > :now_utc_iso
    """
    params = {"token_hash": token_hash, "now_utc_iso": now_utc_iso}

    try:
        if _is_sqlalchemy_session(conn):
            result = conn.execute(text(sql_stmt), params)
            row = result.fetchone()
            if row:
                logger.debug(f"Active session token found for hash {token_hash[:10]}...")
                return dict(row._mapping) # SQLAlchemy Row to dict
        else: # sqlite3.Connection
            # Adapting to qmark style
            sql_qmark = "SELECT * FROM UserSessionTokens WHERE token_hash = ? AND expires_at > ?"
            qmark_params = (token_hash, now_utc_iso)
            cursor = conn.cursor()
            # Ensure row factory is set for dict results if needed, or adapt
            original_row_factory = conn.row_factory
            conn.row_factory = sqlite3.Row # To get dict-like rows
            cursor.execute(sql_qmark, qmark_params)
            row = cursor.fetchone()
            conn.row_factory = original_row_factory # Reset row factory
            if row:
                logger.debug(f"Active session token found for hash {token_hash[:10]}...")
                return dict(row)

        if not row: # Common path for both if row is None
            logger.debug(f"No active session token found for hash {token_hash[:10]}... (possibly expired or non-existent).")
        return None
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error retrieving session token by hash {token_hash[:10]}...: {e}", exc_info=True)
        return None


def update_token_last_used(conn, token_hash: str) -> bool:
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql_stmt = "UPDATE UserSessionTokens SET last_used_at = :now_utc_iso WHERE token_hash = :token_hash"
    params = {"now_utc_iso": now_utc_iso, "token_hash": token_hash}

    try:
        if _is_sqlalchemy_session(conn):
            result = conn.execute(text(sql_stmt), params)
            conn.commit()
            return result.rowcount > 0
        else: # sqlite3.Connection
            # Adapting to qmark style
            sql_qmark = "UPDATE UserSessionTokens SET last_used_at = ? WHERE token_hash = ?"
            qmark_params = (now_utc_iso, token_hash)
            cursor = conn.cursor()
            cursor.execute(sql_qmark, qmark_params)
            conn.commit()
            return cursor.rowcount > 0
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error updating last_used_at for token hash {token_hash[:10]}...: {e}", exc_info=True)
        if hasattr(conn, 'rollback'): conn.rollback()
        return False

def delete_session_token(conn, token_hash: str) -> bool:
    sql_stmt = "DELETE FROM UserSessionTokens WHERE token_hash = :token_hash"
    params = {"token_hash": token_hash}

    try:
        if _is_sqlalchemy_session(conn):
            result = conn.execute(text(sql_stmt), params)
            conn.commit()
            deleted_count = result.rowcount
        else: # sqlite3.Connection
            # Adapting to qmark style
            sql_qmark = "DELETE FROM UserSessionTokens WHERE token_hash = ?"
            qmark_params = (token_hash,)
            cursor = conn.cursor()
            cursor.execute(sql_qmark, qmark_params)
            conn.commit()
            deleted_count = cursor.rowcount

        if deleted_count > 0:
            logger.info(f"Session token with hash {token_hash[:10]}... deleted.")
            return True
        logger.info(f"No session token found to delete for hash {token_hash[:10]}...")
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error deleting session token with hash {token_hash[:10]}...: {e}", exc_info=True)
        if hasattr(conn, 'rollback'): conn.rollback()
        return False

def delete_all_user_session_tokens(conn, user_id: str) -> int:
    sql_stmt = "DELETE FROM UserSessionTokens WHERE user_id = :user_id"
    params = {"user_id": user_id}
    deleted_count = 0
    try:
        if _is_sqlalchemy_session(conn):
            result = conn.execute(text(sql_stmt), params)
            conn.commit()
            deleted_count = result.rowcount
        else: # sqlite3.Connection
            # Adapting to qmark style
            sql_qmark = "DELETE FROM UserSessionTokens WHERE user_id = ?"
            qmark_params = (user_id,)
            cursor = conn.cursor()
            cursor.execute(sql_qmark, qmark_params)
            conn.commit()
            deleted_count = cursor.rowcount

        logger.info(f"Deleted {deleted_count} session token(s) for user {user_id}.")
        return deleted_count
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error deleting session tokens for user {user_id}: {e}", exc_info=True)
        if hasattr(conn, 'rollback'): conn.rollback()
        return 0

def cleanup_expired_tokens(conn, specific_hash: str | None = None) -> int:
    """
    Deletes all expired session tokens from the database.
    If specific_hash is provided, only that token is checked and deleted if expired.
    Returns the number of tokens deleted.
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    if specific_hash:
        sql = "DELETE FROM UserSessionTokens WHERE token_hash = ? AND expires_at <= ?"
        params = (specific_hash, now_utc_iso)
        log_msg_start = f"Cleaning up specific expired token (if any) for hash {specific_hash[:10]}..."
    else:
        sql = "DELETE FROM UserSessionTokens WHERE expires_at <= ?"
        params = (now_utc_iso,)
        log_msg_start = "Cleaning up all expired session tokens..."

    logger.info(log_msg_start)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        deleted_count = cursor.rowcount
        conn.commit()
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired session token(s).")
        else:
            logger.info("No expired session tokens found to clean up matching criteria.")
        return deleted_count
    except sqlite3.Error as e:
        logger.error(f"Error cleaning up expired session tokens: {e}", exc_info=True)
        conn.rollback()
        return 0

# Example Usage (for testing or integration)
if __name__ == '__main__':
    # This is a placeholder for testing.
    # You'd need a valid DB connection and a user_id.
    # Ensure db/connection.py and its get_db_connection() are set up.
    # from db.connection import get_db_connection
    # conn_test = get_db_connection()
    # if conn_test:
    #     try:
    #         # Test add_session_token
    #         test_user_id = "some-user-uuid" # Replace with an actual user_id from your Users table
    #         test_token_hash = "hashed_super_secret_token_string_example" # Replace with a real hash
    #         expiry = datetime.now(timezone.utc) + timedelta(days=30)
    #         new_token_id = add_session_token(conn_test, test_user_id, test_token_hash, expiry, "test_device_123")
    #         if new_token_id:
    #             print(f"Added token with ID: {new_token_id}")
    #
    #             # Test get_session_token_by_hash
    #             retrieved_token = get_session_token_by_hash(conn_test, test_token_hash)
    #             if retrieved_token:
    #                 print(f"Retrieved token: {retrieved_token}")
    #                 assert retrieved_token['token_id'] == new_token_id
    #
    #                 # Test update_token_last_used
    #                 update_success = update_token_last_used(conn_test, test_token_hash)
    #                 print(f"Token last_used_at update success: {update_success}")
    #                 retrieved_again = get_session_token_by_hash(conn_test, test_token_hash)
    #                 if retrieved_again:
    #                       print(f"Token after update: {retrieved_again}")
    #
    #             # Test delete_session_token
    #             # delete_success = delete_session_token(conn_test, test_token_hash)
    #             # print(f"Token deletion success: {delete_success}")
    #             # assert get_session_token_by_hash(conn_test, test_token_hash) is None
    #
    #         # Test delete_all_user_session_tokens
    #         # count_deleted = delete_all_user_session_tokens(conn_test, test_user_id)
    #         # print(f"Deleted {count_deleted} tokens for user {test_user_id}")
    #
    #         # Test cleanup_expired_tokens
    #         # Create an expired token first
    #         # expired_token_hash = "hashed_expired_token_example"
    #         # expired_expiry = datetime.now(timezone.utc) - timedelta(days=1)
    #         # add_session_token(conn_test, test_user_id, expired_token_hash, expired_expiry)
    #         # cleaned_count = cleanup_expired_tokens(conn_test)
    #         # print(f"Cleaned up {cleaned_count} expired tokens globally.")
    #
    #     finally:
    #         conn_test.close()
    pass

