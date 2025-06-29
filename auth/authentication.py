# auth/authentication.py
import logging
from db.cruds import users_crud # Assuming users_crud.py is in db/cruds/

logger = logging.getLogger(__name__)

# Module-level variable to store the current user's data
_current_user_data = None

def login(username: str, password: str, remember_me: bool = False) -> tuple[bool, str | None, dict | None]:
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
    # The 'remember_me' flag will be passed from LoginDialog
    # For now, we define the function signature to accept it.
    # The actual call from LoginDialog needs to be updated to pass this.
    # This change means login() function signature needs to be updated everywhere it's called,
    # or provide a default value for remember_me. Let's use a default for now.
    # Defaulting to False to not break existing calls that don't pass it.
    # However, the LoginDialog will explicitly pass the checkbox state.
    # Actual signature change to include remember_me:
    # def login(username: str, password: str, remember_me: bool = False) -> tuple[bool, str | None, dict | None]:

    try:
        user = users_crud.get_user_by_username(username)
        if not user:
            logger.warning(f"Login attempt failed: User '{username}' not found.")
            save_remember_me_preference(username, False) # Clear on failure
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None

        if not user.get('is_active'):
            logger.warning(f"Login attempt failed: User '{username}' is inactive.")
            save_remember_me_preference(username, False) # Clear on failure
            return False, "Ce compte utilisateur est désactivé.", None

        if users_crud.verify_password(user['hashed_password'], password):
            logger.info(f"User '{username}' logged in successfully.")
            users_crud.record_login_time(user['user_id'])

            _current_user_data = {
                'user_id': user['user_id'],
                'username': user['username'],
                'full_name': user.get('full_name'),
                'email': user.get('email'),
                'role_id': user['role_id'],
                'role_name': user.get('role_name')
            }
            # This is where we'd actually get 'remember_me' from the call
            # For now, let's assume it's passed. We'll modify LoginDialog next.
            save_remember_me_preference(username, remember_me) # Save preference on successful login
            return True, None, _current_user_data
        else:
            logger.warning(f"Login attempt failed: Invalid password for user '{username}'.")
            save_remember_me_preference(username, False) # Clear on failure
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None
    except Exception as e:
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        save_remember_me_preference(username, False) # Clear on exception
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

# --- Remember Me Functionality ---
# from PyQt5.QtCore import QSettings # Moved into functions

APP_NAME = "ClientDocManager" # Or your application's name
ORG_NAME = "SaadiyaManagement" # Or your organization's name

REMEMBER_ME_KEY = "auth/remember_me_active"
REMEMBER_ME_USERNAME_KEY = "auth/remembered_username"
# For a more secure approach with a token:
# REMEMBER_ME_TOKEN_KEY = "auth/remember_me_token"

def save_remember_me_preference(username: str, remember: bool):
    """Saves the 'Remember Me' preference and username if remember is True."""
    from PyQt5.QtCore import QSettings # Moved import here
    settings = QSettings(ORG_NAME, APP_NAME)
    if remember and username:
        settings.setValue(REMEMBER_ME_KEY, True)
        settings.setValue(REMEMBER_ME_USERNAME_KEY, username)
        # In a token-based system, you'd store a persistent token here instead of/additionally
        # settings.setValue(REMEMBER_ME_TOKEN_KEY, persistent_session_token)
        logger.info(f"Remember Me preference saved for user: {username}")
    else:
        settings.remove(REMEMBER_ME_KEY)
        settings.remove(REMEMBER_ME_USERNAME_KEY)
        # settings.remove(REMEMBER_ME_TOKEN_KEY)
        logger.info("Remember Me preference cleared.")
    settings.sync() # Ensure changes are written

def get_remembered_user() -> str | None:
    """
    Retrieves the username if 'Remember Me' was active.
    In a token-based system, this would return the token.
    """
    from PyQt5.QtCore import QSettings # Moved import here
    settings = QSettings(ORG_NAME, APP_NAME)
    if settings.value(REMEMBER_ME_KEY, False, type=bool): # Ensure type conversion
        username = settings.value(REMEMBER_ME_USERNAME_KEY, "", type=str)
        # token = settings.value(REMEMBER_ME_TOKEN_KEY, "", type=str)
        # if token: return token # For token-based
        if username:
            logger.info(f"Found remembered user: {username}")
            return username
    logger.info("No remembered user found or preference not active.")
    return None

def clear_remember_me_preference():
    """Clears any stored 'Remember Me' preferences."""
    from PyQt5.QtCore import QSettings # Moved import here
    settings = QSettings(ORG_NAME, APP_NAME)
    settings.remove(REMEMBER_ME_KEY)
    settings.remove(REMEMBER_ME_USERNAME_KEY)
    # settings.remove(REMEMBER_ME_TOKEN_KEY)
    logger.info("Cleared all Remember Me preferences forcefully.")
    settings.sync()
