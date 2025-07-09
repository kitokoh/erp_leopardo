import sqlite3
import uuid
import logging
from .generic_crud import _manage_conn
# It's good practice to also import any specific models if complex queries are built,
# but for simple CRUD on this table, it might not be strictly necessary yet.
# from ..models import User, SmtpConfig # Example if using SQLAlchemy models

logger = logging.getLogger(__name__)

@_manage_conn
def assign_smtp_to_user(user_id: str, smtp_config_id: int, is_default_for_user: bool = False, conn=None) -> str | None:
    """
    Assigns an SMTP configuration to a user.
    If is_default_for_user is True, this will also set it as the user's default.
    Returns the assignment_id if successful, else None.
    """
    assignment_id = str(uuid.uuid4())
    try:
        cursor = conn.cursor()

        if is_default_for_user:
            # Ensure no other config is default for this user
            cursor.execute("""
                UPDATE UserSmtpAssignments
                SET is_default_for_user = FALSE
                WHERE user_id = ? AND is_default_for_user = TRUE
            """, (user_id,))

        sql = """
            INSERT INTO UserSmtpAssignments (
                assignment_id, user_id, smtp_config_id, is_default_for_user
            ) VALUES (?, ?, ?, ?)
        """
        params = (assignment_id, user_id, smtp_config_id, is_default_for_user)
        cursor.execute(sql, params)
        # conn.commit() handled by _manage_conn
        logger.info(f"SMTP config ID {smtp_config_id} assigned to user ID {user_id} with assignment ID {assignment_id}. Default for user: {is_default_for_user}")
        return assignment_id
    except sqlite3.IntegrityError: # Handles UNIQUE constraint violation
        logger.warning(f"SMTP config ID {smtp_config_id} is already assigned to user ID {user_id}. Assignment failed.")
        # conn.rollback() handled by _manage_conn
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error assigning SMTP config {smtp_config_id} to user {user_id}: {e}", exc_info=True)
        # conn.rollback() handled by _manage_conn
        return None

@_manage_conn
def unassign_smtp_from_user(assignment_id: str, conn=None) -> bool:
    """Unassigns an SMTP configuration from a user using the assignment_id."""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM UserSmtpAssignments WHERE assignment_id = ?", (assignment_id,))
        # conn.commit() handled by _manage_conn
        deleted_rows = cursor.rowcount
        if deleted_rows > 0:
            logger.info(f"SMTP assignment ID {assignment_id} successfully unassigned.")
            return True
        else:
            logger.warning(f"No SMTP assignment found with ID {assignment_id} to unassign.")
            return False
    except sqlite3.Error as e:
        logger.error(f"Database error unassigning SMTP assignment ID {assignment_id}: {e}", exc_info=True)
        # conn.rollback() handled by _manage_conn
        return False

@_manage_conn
def get_user_smtp_assignments(user_id: str, conn=None) -> list[dict]:
    """
    Retrieves all SMTP configurations assigned to a user, along with their details.
    Returns a list of dictionaries, where each dict includes assignment details
    and SMTP configuration details.
    """
    assignments = []
    try:
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        # Joins UserSmtpAssignments with SmtpConfigs to get full details
        sql = """
            SELECT
                usa.assignment_id,
                usa.user_id,
                usa.smtp_config_id,
                usa.is_default_for_user,
                usa.created_at AS assignment_created_at,
                sc.config_name,
                sc.smtp_server,
                sc.smtp_port,
                sc.username,
                sc.password_encrypted, -- For service layer to decrypt if needed
                sc.use_tls,
                sc.sender_email_address,
                sc.sender_display_name,
                sc.is_default AS is_global_default
            FROM UserSmtpAssignments usa
            JOIN SmtpConfigs sc ON usa.smtp_config_id = sc.smtp_config_id
            WHERE usa.user_id = ?
            ORDER BY sc.config_name
        """
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        for row in rows:
            assignments.append(dict(row))
        return assignments
    except sqlite3.Error as e:
        logger.error(f"Database error fetching SMTP assignments for user ID {user_id}: {e}", exc_info=True)
        return []

@_manage_conn
def get_default_smtp_for_user(user_id: str, conn=None) -> dict | None:
    """
    Retrieves the default SMTP configuration for a specific user.
    Returns a dictionary with combined assignment and SmtpConfig details, or None.
    """
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = """
            SELECT
                usa.assignment_id,
                usa.user_id,
                usa.smtp_config_id,
                usa.is_default_for_user,
                usa.created_at AS assignment_created_at,
                sc.config_name,
                sc.smtp_server,
                sc.smtp_port,
                sc.username,
                sc.password_encrypted,
                sc.use_tls,
                sc.sender_email_address,
                sc.sender_display_name,
                sc.is_default AS is_global_default
            FROM UserSmtpAssignments usa
            JOIN SmtpConfigs sc ON usa.smtp_config_id = sc.smtp_config_id
            WHERE usa.user_id = ? AND usa.is_default_for_user = TRUE
            LIMIT 1
        """
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching default SMTP for user {user_id}: {e}", exc_info=True)
        return None

@_manage_conn
def set_default_smtp_for_user(user_id: str, assignment_id: str, conn=None) -> bool:
    """
    Sets a specific SMTP assignment as the default for the user,
    unsetting any other default for that user.
    """
    try:
        cursor = conn.cursor()
        # Unset current default for the user
        cursor.execute("""
            UPDATE UserSmtpAssignments
            SET is_default_for_user = FALSE
            WHERE user_id = ? AND is_default_for_user = TRUE
        """, (user_id,))

        # Set new default for the user
        cursor.execute("""
            UPDATE UserSmtpAssignments
            SET is_default_for_user = TRUE
            WHERE user_id = ? AND assignment_id = ?
        """, (user_id, assignment_id))

        # conn.commit() handled by _manage_conn
        if cursor.rowcount > 0:
            logger.info(f"SMTP assignment ID {assignment_id} set as default for user ID {user_id}.")
            return True
        else:
            logger.warning(f"Failed to set assignment {assignment_id} as default for user {user_id} (assignment not found or already set).")
            return False
    except sqlite3.Error as e:
        logger.error(f"Database error setting default SMTP for user {user_id}, assignment {assignment_id}: {e}", exc_info=True)
        # conn.rollback() handled by _manage_conn
        return False

@_manage_conn
def update_user_smtp_assignment_default_status(assignment_id: str, is_default: bool, user_id: str, conn=None) -> bool:
    """
    Updates the 'is_default_for_user' status of a specific assignment.
    If setting to True, it ensures other assignments for the same user are set to False.
    """
    try:
        cursor = conn.cursor()
        if is_default:
            # First, unset any other default for this user
            cursor.execute("""
                UPDATE UserSmtpAssignments
                SET is_default_for_user = FALSE
                WHERE user_id = ? AND assignment_id != ? AND is_default_for_user = TRUE
            """, (user_id, assignment_id))

        # Update the target assignment
        cursor.execute("""
            UPDATE UserSmtpAssignments
            SET is_default_for_user = ?
            WHERE assignment_id = ? AND user_id = ?
        """, (is_default, assignment_id, user_id))

        # conn.commit() handled by _manage_conn
        if cursor.rowcount > 0:
            logger.info(f"Default status for assignment ID {assignment_id} (user {user_id}) updated to {is_default}.")
            return True
        else:
            # This might happen if the assignment_id doesn't belong to the user_id,
            # or if the value was already the same.
            logger.warning(f"No change or assignment ID {assignment_id} not found for user {user_id} when updating default status.")
            return False # Or True if no change is not an error
    except sqlite3.Error as e:
        logger.error(f"Database error updating default status for assignment {assignment_id}: {e}", exc_info=True)
        # conn.rollback() handled by _manage_conn
        return False

@_manage_conn
def get_assignment_by_user_and_config(user_id: str, smtp_config_id: int, conn=None) -> dict | None:
    """Retrieves a specific assignment by user_id and smtp_config_id."""
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT * FROM UserSmtpAssignments WHERE user_id = ? AND smtp_config_id = ?"
        cursor.execute(sql, (user_id, smtp_config_id))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"DB error fetching assignment for user {user_id}, config {smtp_config_id}: {e}", exc_info=True)
        return None

# Example usage (for testing if run directly)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # This test requires SmtpConfigs and Users tables to exist and have some data.
    # It also needs a way to manage DB connections for testing, similar to smtp_configs_crud.py.
    print("User SMTP Assignments CRUD - Standalone Test (requires DB setup with Users and SmtpConfigs)")

    import os
    import functools
    from db.cruds.smtp_configs_crud import add_smtp_config as add_global_smtp_config # To add some configs
    from db.cruds.users_crud import add_user as add_test_user, get_user_by_username # To add some users

    DB_PATH_USA_TEST = 'test_user_smtp_assignments_crud.db'

    if os.path.exists(DB_PATH_USA_TEST):
        os.remove(DB_PATH_USA_TEST)

    def standalone_usa_manage_conn(func):
        @functools.wraps(func)
        def wrapper_manage_conn(*args, **kwargs):
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH_USA_TEST)
                # Create tables if not exists for the test
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, hashed_password TEXT NOT NULL,
                    role_id INTEGER NOT NULL, full_name TEXT, email TEXT, is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP, updated_at TIMESTAMP, last_login_at TIMESTAMP,
                    is_fingerprint_auth_enabled BOOLEAN DEFAULT FALSE, fingerprint_template_id TEXT,
                    is_face_auth_enabled BOOLEAN DEFAULT FALSE, face_template_id TEXT,
                    is_voice_auth_enabled BOOLEAN DEFAULT FALSE, voice_profile_id TEXT,
                    is_deleted INTEGER DEFAULT 0, deleted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS SmtpConfigs (
                    smtp_config_id INTEGER PRIMARY KEY AUTOINCREMENT, config_name TEXT NOT NULL UNIQUE,
                    smtp_server TEXT NOT NULL, smtp_port INTEGER NOT NULL, username TEXT,
                    password_encrypted TEXT, use_tls BOOLEAN DEFAULT TRUE, is_default BOOLEAN DEFAULT FALSE,
                    sender_email_address TEXT NOT NULL, sender_display_name TEXT
                );
                CREATE TABLE IF NOT EXISTS UserSmtpAssignments (
                    assignment_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, smtp_config_id INTEGER NOT NULL,
                    is_default_for_user BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (smtp_config_id) REFERENCES SmtpConfigs (smtp_config_id) ON DELETE CASCADE,
                    UNIQUE (user_id, smtp_config_id)
                );
                """)
                conn.commit()
                kwargs['conn'] = conn
                result = func(*args, **kwargs)
                conn.commit()
                return result
            except sqlite3.Error as e:
                if conn: conn.rollback()
                logger.error(f"Standalone DB error in {func.__name__}: {e}", exc_info=True)
                raise
            finally:
                if conn: conn.close()
        return wrapper_manage_conn

    _manage_conn = standalone_usa_manage_conn # Override decorator for this test block

    # Setup some test data
    # Note: add_test_user and add_global_smtp_config will use the overridden _manage_conn
    test_user_id = add_test_user(username='testuser_usa', password='password', role_id=1, full_name='Test User USA')
    test_smtp_id1 = add_global_smtp_config({'config_name': 'USA Test SMTP1', 'smtp_server': 's1.com', 'smtp_port': 587, 'sender_email_address': 'usa1@test.com'})
    test_smtp_id2 = add_global_smtp_config({'config_name': 'USA Test SMTP2', 'smtp_server': 's2.com', 'smtp_port': 587, 'sender_email_address': 'usa2@test.com'})

    if not test_user_id or not test_smtp_id1 or not test_smtp_id2:
        print("Failed to setup initial user or SMTP configs for test. Aborting.")
    else:
        print(f"Setup: UserID: {test_user_id}, SMTP1_ID: {test_smtp_id1}, SMTP2_ID: {test_smtp_id2}")

        # Assign SMTP1 to user, not as default
        assign_id1 = assign_smtp_to_user(test_user_id, test_smtp_id1, is_default_for_user=False)
        print(f"Assigned SMTP1 to user: {assign_id1}")
        assert assign_id1 is not None

        # Assign SMTP2 to user, as default
        assign_id2 = assign_smtp_to_user(test_user_id, test_smtp_id2, is_default_for_user=True)
        print(f"Assigned SMTP2 to user as default: {assign_id2}")
        assert assign_id2 is not None

        # Get assignments for user
        assignments = get_user_smtp_assignments(test_user_id)
        print(f"\nAssignments for user {test_user_id} ({len(assignments)}):")
        for a in assignments:
            print(f"  AssignID: {a['assignment_id']}, ConfigName: {a['config_name']}, UserDefault: {a['is_default_for_user']}")
        assert len(assignments) == 2

        # Get default for user
        user_default = get_default_smtp_for_user(test_user_id)
        print(f"\nUser's default SMTP config: {user_default['config_name'] if user_default else 'None'}")
        assert user_default and user_default['smtp_config_id'] == test_smtp_id2

        # Change default to SMTP1 (using assignment_id1)
        print(f"\nSetting assignment {assign_id1} (SMTP1) as user's default...")
        set_success = set_default_smtp_for_user(test_user_id, assign_id1)
        print(f"Set default success: {set_success}")
        assert set_success

        user_default_new = get_default_smtp_for_user(test_user_id)
        print(f"New user's default SMTP config: {user_default_new['config_name'] if user_default_new else 'None'}")
        assert user_default_new and user_default_new['smtp_config_id'] == test_smtp_id1

        assignments_after_change = get_user_smtp_assignments(test_user_id)
        for a in assignments_after_change:
            if a['assignment_id'] == assign_id1: assert a['is_default_for_user'] == True
            if a['assignment_id'] == assign_id2: assert a['is_default_for_user'] == False

        # Test get_assignment_by_user_and_config
        specific_assign = get_assignment_by_user_and_config(test_user_id, test_smtp_id2)
        print(f"\nRetrieved specific assignment for user {test_user_id}, config {test_smtp_id2}: {specific_assign['assignment_id'] if specific_assign else 'Not found'}")
        assert specific_assign and specific_assign['assignment_id'] == assign_id2

        # Unassign SMTP1
        unassign_success = unassign_smtp_from_user(assign_id1)
        print(f"\nUnassigned SMTP1 (assignment {assign_id1}): {unassign_success}")
        assert unassign_success

        assignments_after_unassign = get_user_smtp_assignments(test_user_id)
        print(f"Assignments for user after unassign ({len(assignments_after_unassign)}):")
        assert len(assignments_after_unassign) == 1
        assert assignments_after_unassign[0]['smtp_config_id'] == test_smtp_id2

    if os.path.exists(DB_PATH_USA_TEST):
        os.remove(DB_PATH_USA_TEST)
        print(f"\nCleaned up test database: {DB_PATH_USA_TEST}")

    print("User SMTP Assignments CRUD standalone test completed.")
