# auth/authentication.py
import logging
from db.cruds import users_crud # Assuming users_crud.py is in db/cruds/

logger = logging.getLogger(__name__)

# Module-level variable to store the current user's data
_current_user_data = None

def login(username: str, password: str) -> tuple[bool, str | None, dict | None]:
    """
    Attempts to log in a user.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        tuple[bool, str | None, dict | None]: (success_status, error_message_or_None, user_data_or_None)
                                              user_data includes user_id, username, full_name, role_name, role_id, email.
    """
    global _current_user_data
    try:
        user = users_crud.get_user_by_username(username)
        if not user:
            logger.warning(f"Login attempt failed: User '{username}' not found.")
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None

        if not user.get('is_active'):
            logger.warning(f"Login attempt failed: User '{username}' is inactive.")
            return False, "Ce compte utilisateur est désactivé.", None

        if users_crud.verify_password(user['hashed_password'], password):
            logger.info(f"User '{username}' logged in successfully.")
            users_crud.record_login_time(user['user_id'])

            # Prepare user data to store (excluding sensitive info like hashed_password)
            _current_user_data = {
                'user_id': user['user_id'],
                'username': user['username'],
                'full_name': user.get('full_name'),
                'email': user.get('email'),
                'role_id': user['role_id'],
                'role_name': user.get('role_name') # role_name is joined in get_user_by_username
            }
            return True, None, _current_user_data
        else:
            logger.warning(f"Login attempt failed: Invalid password for user '{username}'.")
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None
    except Exception as e:
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        return False, "Une erreur est survenue lors de la connexion.", None

def logout():
    """Logs out the current user."""
    global _current_user_data
    if _current_user_data:
        logger.info(f"User '{_current_user_data.get('username')}' logged out.")
        _current_user_data = None
    else:
        logger.info("Logout called but no user was logged in.")

def get_current_user() -> dict | None:
    """
    Retrieves the currently logged-in user's data.

    Returns:
        dict | None: User data if a user is logged in, otherwise None.
    """
    return _current_user_data

def set_current_user(user_data: dict | None):
    """
    Sets the current user. Primarily for session loading or testing.
    Direct use in application flow after login should be via login().
    """
    global _current_user_data
    _current_user_data = user_data
    if user_data:
        logger.info(f"Current user set to: {user_data.get('username')}")
    else:
        logger.info("Current user cleared (set to None).")

def get_current_user_id() -> str | None:
    """Helper to quickly get the current user's ID."""
    if _current_user_data:
        return _current_user_data.get('user_id')
    return None

def get_current_user_role() -> str | None:
    """Helper to quickly get the current user's role name."""
    if _current_user_data:
        return _current_user_data.get('role_name')
    return None
