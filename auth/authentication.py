# auth/authentication.py
import logging
from db.cruds import users_crud # Assuming users_crud.py is in db/cruds/

logger = logging.getLogger(__name__)

# Module-level variable to store the current user's data
_current_user_data = None

def login(username: str, password: str, remember_me: bool = False) -> tuple[bool, str | None, dict | None, dict | None]:
    """
    Attempts to log in a user.

    Args:
        username (str): The username.
        password (str): The password.
        remember_me (bool): Whether the user selected "Remember Me".

    Returns:
        tuple[bool, str | None, dict | None, dict | None]:
            (success_status, error_message_or_None, user_data_or_None, license_info_or_None)
            user_data includes user_id, username, full_name, role_name, role_id, email.
            license_info includes details of the current valid license, or info about expired/missing license.
    """
    global _current_user_data
    from license_management import manager as license_manager # Importation locale
    from db.connection import get_db_connection # Pour obtenir une connexion DB

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

        # Corrected function call: users_crud.util_verify_password
        # The users_crud module imports verify_password as util_verify_password from utils
        # and then has its own wrapper verify_user_password.
        # However, the original error indicates a direct call to a function named verify_password
        # within the users_crud namespace, which was likely the util_verify_password before a potential refactor
        # or an intended direct call to the utility.
        # Given the error "Did you mean: 'util_verify_password'?",
        # the most direct fix is to use users_crud.util_verify_password.
        #
        # An alternative would be to use users_crud.verify_user_password(username, password)
        # but that function does more than just verify the password string (it also gets the user, checks active status).
        # Since we already have the user object and checked active status,
        # calling the lower-level password verification directly is more appropriate here.
        # The users_crud module makes util_verify_password available via:
        # from utils import verify_password as util_verify_password
        if users_crud.util_verify_password(password, user['hashed_password'])[0]: # util_verify_password returns (bool, str|None)
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

            # Vérification de la licence
            conn = None
            try:
                conn = get_db_connection()
                is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])

                # Le login est réussi, mais la licence peut être invalide.
                # Le message d'erreur de la licence sera prioritaire s'il y en a un.
                # La fonction login retourne maintenant aussi license_details pour que main.py puisse agir.
                if not is_license_valid:
                    logger.warning(f"Login réussi pour {username} mais licence invalide: {license_msg}")
                    # On ne retourne pas False pour le login, car l'utilisateur est authentifié.
                    # C'est à l'appelant (main.py) de gérer le flux de licence.
                    # Cependant, on peut enrichir le message d'erreur.
                    # Le `license_details` ici pourrait être None ou contenir les infos de la licence invalide.
                    return True, license_msg, _current_user_data, license_details # license_details peut être la licence invalide

                logger.info(f"Login et vérification de licence réussis pour {username}.")
                return True, None, _current_user_data, license_details

            except Exception as e_lic:
                logger.error(f"Erreur lors de la vérification de la licence pour {username}: {e_lic}", exc_info=True)
                # Si la vérification de licence échoue critiquement, on peut considérer le login comme échoué
                # ou retourner un statut spécial. Pour l'instant, on propage une erreur.
                save_remember_me_preference(username, False) # Effacer remember_me en cas d'erreur critique de licence
                _current_user_data = None # Ne pas considérer l'utilisateur comme loggué
                return False, "Erreur critique lors de la vérification de la licence.", None, None
            finally:
                if conn:
                    conn.close()

        else: # Mot de passe incorrect
            logger.warning(f"Login attempt failed: Invalid password for user '{username}'.")
            save_remember_me_preference(username, False) # Clear on failure
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None

    except Exception as e: # Erreur générale pendant le login (avant la licence)
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        save_remember_me_preference(username, False) # Clear on exception
        return False, "Une erreur est survenue lors de la connexion.", None, None

def logout():
    """Logs out the current user."""
    global _current_user_data
    if _current_user_data:
        logger.info(f"User '{_current_user_data.get('username')}' logged out.")
        _current_user_data = None
        clear_remember_me_preference() # Clear remember me on explicit logout
    else:
        logger.info("Logout called but no user was logged in.")
        # Optionally, clear remember me even if no user was logged in,
        # as a safety measure if logout is called unexpectedly.
        clear_remember_me_preference()

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
from PyQt5.QtCore import QSettings

APP_NAME = "ClientDocManager" # Or your application's name
ORG_NAME = "SaadiyaManagement" # Or your organization's name

REMEMBER_ME_KEY = "auth/remember_me_active"
REMEMBER_ME_USERNAME_KEY = "auth/remembered_username"
# For a more secure approach with a token:
# REMEMBER_ME_TOKEN_KEY = "auth/remember_me_token"

def save_remember_me_preference(username: str, remember: bool):
    """Saves the 'Remember Me' preference and username if remember is True."""
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
    settings = QSettings(ORG_NAME, APP_NAME)
    settings.remove(REMEMBER_ME_KEY)
    settings.remove(REMEMBER_ME_USERNAME_KEY)
    # settings.remove(REMEMBER_ME_TOKEN_KEY)
    logger.info("Cleared all Remember Me preferences forcefully.")
    settings.sync()
