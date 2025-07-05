# db/cruds/password_reset_tokens_crud.py
import sqlite3
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

def create_reset_token(conn: sqlite3.Connection, user_id: str, token_hash: str, expires_at: datetime) -> bool:
    """
    Stores a new password reset token hash for a user.
    Deletes any previous, unused tokens for the same user to ensure only one is active.
    """
    # First, delete any existing non-used tokens for this user
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PasswordResetTokens WHERE user_id = ? AND used_at IS NULL", (user_id,))
        logger.info(f"Deleted {cursor.rowcount} existing unused reset token(s) for user {user_id}.")
    except sqlite3.Error as e_delete:
        logger.error(f"Error deleting old reset tokens for user {user_id}: {e_delete}", exc_info=True)
        # Don't necessarily rollback here, try to proceed with adding the new one.
        # If this fails, the main insert's rollback will handle it.

    sql = """
        INSERT INTO PasswordResetTokens (user_id, token_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    """
    created_at_iso = datetime.now(timezone.utc).isoformat()
    expires_at_iso = expires_at.isoformat()
    params = (user_id, token_hash, expires_at_iso, created_at_iso)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        logger.info(f"Password reset token created for user {user_id}.")
        return True
    except sqlite3.IntegrityError as e: # Should ideally not happen if old tokens are deleted
        logger.error(f"Integrity error creating password reset token for user {user_id} (token_hash might exist): {e}", exc_info=True)
        conn.rollback()
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error creating password reset token for user {user_id}: {e}", exc_info=True)
        conn.rollback()
        return False

def get_reset_token_by_hash(conn: sqlite3.Connection, token_hash: str) -> dict | None:
    """
    Retrieves a password reset token by its hash.
    Only returns if not expired and not already used.
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql = """
        SELECT * FROM PasswordResetTokens
        WHERE token_hash = ? AND expires_at > ? AND used_at IS NULL
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (token_hash, now_utc_iso))
        row = cursor.fetchone()
        if row:
            logger.debug(f"Valid password reset token found for hash {token_hash[:10]}...")
            return dict(row)
        else:
            logger.debug(f"No valid (active, non-expired, unused) password reset token found for hash {token_hash[:10]}...")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving reset token by hash {token_hash[:10]}...: {e}", exc_info=True)
        return None

def mark_token_as_used(conn: sqlite3.Connection, token_hash: str) -> bool:
    """Marks a password reset token as used by setting the used_at timestamp."""
    used_at_iso = datetime.now(timezone.utc).isoformat()
    sql = "UPDATE PasswordResetTokens SET used_at = ? WHERE token_hash = ? AND used_at IS NULL"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (used_at_iso, token_hash))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Password reset token with hash {token_hash[:10]}... marked as used.")
            return True
        logger.warning(f"Attempted to mark token {token_hash[:10]}... as used, but not found or already used.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error marking reset token {token_hash[:10]}... as used: {e}", exc_info=True)
        conn.rollback()
        return False

def delete_all_tokens_for_user(conn: sqlite3.Connection, user_id: str) -> int:
    """
    Deletes all password reset tokens for a given user, regardless of status.
    Useful if user changes email or is deleted. Returns number of tokens deleted.
    """
    sql = "DELETE FROM PasswordResetTokens WHERE user_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} password reset token(s) for user {user_id}.")
        return deleted_count
    except sqlite3.Error as e:
        logger.error(f"Error deleting all reset tokens for user {user_id}: {e}", exc_info=True)
        conn.rollback()
        return 0

def cleanup_expired_or_used_tokens(conn: sqlite3.Connection) -> int:
    """
    Deletes all expired or already used password reset tokens from the database.
    Returns the number of tokens deleted.
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    sql = "DELETE FROM PasswordResetTokens WHERE expires_at <= ? OR used_at IS NOT NULL"
    logger.info("Cleaning up expired or used password reset tokens...")
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (now_utc_iso,))
        deleted_count = cursor.rowcount
        conn.commit()
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired/used password reset token(s).")
        else:
            logger.info("No expired/used password reset tokens found to clean up.")
        return deleted_count
    except sqlite3.Error as e:
        logger.error(f"Error cleaning up expired/used reset tokens: {e}", exc_info=True)
        conn.rollback()
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

