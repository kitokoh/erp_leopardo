# auth/authentication.py
import logging
from datetime import datetime, timedelta, timezone # Added timedelta and timezone

# auth/authentication.py
import logging
import traceback # Import for detailed traceback
from datetime import datetime, timedelta, timezone # Added timedelta and timezone

from db.cruds import users_crud, activity_logs_crud, licenses_crud # Added licenses_crud

from db.cruds import user_session_tokens_crud # New CRUD for session tokens
from utils.security_helpers import generate_secure_token, hash_token_for_storage # New helpers
from license_management import manager as license_manager # Already imported below, moved up for clarity
from db.connection import get_db_connection # Already imported below, moved up

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
            # save_remember_me_preference(username, False) # This function was removed, token handling is direct now
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None

        if not user.get('is_active'):
            logger.warning(f"Login attempt failed: User '{username}' is inactive.")
            # save_remember_me_preference(username, False) # This function was removed
            return False, "Ce compte utilisateur est désactivé.", None, None

        # Password verification using users_crud.util_verify_password
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
            # Token handling is now done in the updated login function below.
            # save_remember_me_preference(username, remember_me) # This function was removed

            # License verification
            conn = None
            try:
                conn = get_db_connection()
                is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])

                if not is_license_valid and username == license_manager.ADMIN_USERNAME:
                    logger.warning(f"Admin user '{username}' has an invalid/missing license: {license_msg}. Attempting to create a default 6-month license.")
                    try:
                        # Pass the existing connection 'conn'
                        created_ok, create_msg, new_license_details = license_manager.create_default_admin_license(conn, user['user_id'])
                        if created_ok:
                            logger.info(f"Default admin license created successfully for '{username}'. Re-checking validity.")
                            # Re-check license validity
                            is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])
                        else:
                            logger.error(f"Failed to create default admin license for '{username}': {create_msg}")
                            # Proceed with original invalid license message if creation failed
                            # The original license_msg and license_details (which might be None) are still in scope
                            # We return True for login success, but the license_msg will indicate the issue.
                            return True, create_msg or license_msg, _current_user_data, license_details

                    except Exception as e_create_lic:
                        logger.error(f"Exception during default admin license creation for '{username}': {e_create_lic}", exc_info=True)
                        # Proceed with original invalid license message
                        return True, f"Erreur critique lors de la création de la licence admin: {str(e_create_lic)}", _current_user_data, license_details

                # After potential admin license creation, check final status
                if not is_license_valid:
                    logger.warning(f"Login for '{username}' successful, but license is invalid: {license_msg}")
                    # Return True for login success (user authenticated), but include license error message and details
                    return True, license_msg, _current_user_data, license_details

                logger.info(f"Login and license check successful for {username}.")
                return True, None, _current_user_data, license_details

            except Exception as e_lic:
                logger.error(f"Erreur lors de la vérification de la licence pour {username}: {e_lic}", exc_info=True)
                # Si la vérification de licence échoue critiquement, on peut considérer le login comme échoué
                # ou retourner un statut spécial. Pour l'instant, on propage une erreur.
                # save_remember_me_preference(username, False) # This function was removed
                _current_user_data = None # Ne pas considérer l'utilisateur comme loggué
                return False, "Erreur critique lors de la vérification de la licence.", None, None
            finally:
                if conn:
                    conn.close()

        else: # Mot de passe incorrect
            logger.warning(f"Login attempt failed: Invalid password for user '{username}'.")
            # save_remember_me_preference(username, False) # This function was removed
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None

    except Exception as e: # Erreur générale pendant le login (avant la licence)
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        # save_remember_me_preference(username, False) # This function was removed
        return False, "Une erreur est survenue lors de la connexion.", None, None

# def logout(): # This version of logout is superseded by the one below that handles tokens
#     """Logs out the current user."""
#     global _current_user_data
#     if _current_user_data:
#         logger.info(f"User '{_current_user_data.get('username')}' logged out.")
#         _current_user_data = None
#         # clear_remember_me_preference() # This function was removed, token clearing is handled in new logout
#     else:
#         logger.info("Logout called but no user was logged in.")
#         # clear_remember_me_preference()

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

# --- Remember Me Functionality (Token-Based) ---
from PyQt5.QtCore import QSettings

APP_NAME = "ClientDocManager"
ORG_NAME = "SaadiyaManagement"

REMEMBER_ME_TOKEN_QSETTINGS_KEY = "auth/remember_me_token" # Key for QSettings
SESSION_TOKEN_EXPIRY_DAYS = 60 # How long a "remember me" token is valid in the DB

def save_remember_me_token_to_settings(token: str):
    """Saves the remember me token to QSettings."""
    settings = QSettings(ORG_NAME, APP_NAME)
    if token:
        settings.setValue(REMEMBER_ME_TOKEN_QSETTINGS_KEY, token)
        logger.info("Remember Me token saved to QSettings.")
    else: # Should not happen if we always generate a token, but good for explicit clear
        settings.remove(REMEMBER_ME_TOKEN_QSETTINGS_KEY)
        logger.info("Remember Me token cleared from QSettings (empty token provided).")
    settings.sync()

def get_remembered_token_from_settings() -> str | None:
    """Retrieves the remember me token from QSettings."""
    settings = QSettings(ORG_NAME, APP_NAME)
    token = settings.value(REMEMBER_ME_TOKEN_QSETTINGS_KEY, "", type=str)
    if token:
        logger.info("Found Remember Me token in QSettings.")
        return token
    logger.info("No Remember Me token found in QSettings.")
    return None

def clear_remember_me_token_from_settings():
    """Clears the remember me token from QSettings."""
    settings = QSettings(ORG_NAME, APP_NAME)
    if settings.contains(REMEMBER_ME_TOKEN_QSETTINGS_KEY):
        settings.remove(REMEMBER_ME_TOKEN_QSETTINGS_KEY)
        logger.info("Cleared Remember Me token from QSettings.")
        settings.sync()
    else:
        logger.info("No Remember Me token in QSettings to clear.")

# Updated login function to handle token generation
def login(username: str, password: str, remember_me: bool = False) -> tuple[bool, str | None, dict | None, dict | None]:
    """
    Attempts to log in a user. If remember_me is True, generates and stores a session token.
    """
    print("DEBUG_PRINT: AUTHENTICATION_LOGIN: login function CALLED.") # ADDED
    logger.info("AUTHENTICATION_LOGIN: login function CALLED.")

    global _current_user_data
    # Note: license_manager and get_db_connection are already imported at module level

    # Clear any old token from QSettings before attempting a new login,
    # especially if this login is manual.
    # If login fails, we don't want an old token lingering.
    # If login succeeds and remember_me is false, we also want it cleared.
    clear_remember_me_token_from_settings() # Clear token from QSettings first
    # We also need to clear any associated DB token if one existed and this is a new manual login.
    # This is tricky without knowing the old token. Best to handle DB token clearing on explicit logout
    # or when a new token is successfully generated for the same user.

    try:
        logger.info(f"AUTH_LOGIN: Attempting login for username: '{username}'")
        user = users_crud.get_user_by_username(username)

        if not user:
            logger.warning(f"AUTH_LOGIN: User '{username}' not found in database.")
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None
        
        logger.info(f"AUTH_LOGIN: User '{username}' found. User data: ID={user.get('user_id')}, RoleName={user.get('role_name')}, HashedPW={user.get('hashed_password')}")

        logger.info(f"AUTH_LOGIN: User '{username}' found. User data: ID={user.get('user_id')}, RoleName={user.get('role_name')}, HashedPW={user.get('hashed_password')}")

        logger.info(f"AUTH_LOGIN: User '{username}' found. User data: ID={user.get('user_id')}, RoleName={user.get('role_name')}, HashedPW={user.get('hashed_password')}")

        if not user.get('is_active'):
            logger.warning(f"AUTH_LOGIN: User '{username}' is inactive.")
            return False, "Ce compte utilisateur est désactivé.", None, None

        password_verified, new_hash_if_needed = users_crud.util_verify_password(password, user['hashed_password'])
        logger.info(f"AUTH_LOGIN: Password verification result for '{username}': {password_verified}")

        if password_verified:
            logger.info(f"AUTH_LOGIN: User '{username}' logged in successfully (password verified).")
            users_crud.record_login_time(user['user_id'])

            _current_user_data = {
                'user_id': user['user_id'],
                'username': user['username'],
                'full_name': user.get('full_name'),
                'email': user.get('email'),
                'role_id': user['role_id'],
                'role_name': user.get('role_name')
            }

            conn = None
            try: # Corrected from try { to try:
                logger.debug(f"AUTH_LOGIN: Entered token/license processing block for user '{username}'.")
                conn = get_db_connection()
                logger.debug(f"AUTH_LOGIN: conn object type after get_db_connection(): {type(conn)}") # <<< ADDED THIS LOG
                if remember_me:
                    logger.debug(f"AUTH_LOGIN: 'Remember Me' is true for '{username}'. Processing token.")
                    user_session_tokens_crud.delete_all_user_session_tokens(conn, user['user_id'])
                    new_token = generate_secure_token(48)
                    token_hash = hash_token_for_storage(new_token)
                    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_TOKEN_EXPIRY_DAYS)
                    device_id = None
                    token_record_id = user_session_tokens_crud.add_session_token(
                        conn, user['user_id'], token_hash, expires_at, device_id
                    )
                    if token_record_id:
                        save_remember_me_token_to_settings(new_token)
                        logger.info(f"New session token generated and stored for user {user['user_id']}.")
                        activity_logs_crud.add_activity_log(conn=conn, data={"user_id": user['user_id'], "action_type": "REMEMBER_ME_TOKEN_GENERATED", "details": f"New 'Remember Me' session token generated. Expires: {expires_at.isoformat()}.", "related_entity_type": "UserSessionToken", "related_entity_id": token_record_id})
                    else:
                        logger.error(f"Failed to store new session token in DB for user {user['user_id']}.")
                else:
                    logger.debug(f"AUTH_LOGIN: 'Remember Me' is false for '{username}'. Clearing any existing tokens.")
                    deleted_count = user_session_tokens_crud.delete_all_user_session_tokens(conn, user['user_id'])
                    if deleted_count > 0:
                        logger.info(f"Cleared {deleted_count} 'Remember Me' token(s) for user {user['user_id']} as 'Remember Me' was not checked.")
                        activity_logs_crud.add_activity_log(conn=conn, data={"user_id": user['user_id'], "action_type": "REMEMBER_ME_TOKENS_CLEARED_ON_LOGIN", "details": f"All 'Remember Me' tokens cleared for user as 'Remember Me' was not selected during login. Count: {deleted_count}."})

                logger.debug(f"AUTH_LOGIN: About to call license_manager.check_license_validity for user_id: {user['user_id']}")
                is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])
                logger.debug(f"AUTH_LOGIN: license_manager.check_license_validity result: is_license_valid={is_license_valid}, license_msg='{license_msg}', license_details_type={type(license_details)}, license_details_value={license_details}")

                if not is_license_valid and user.get('role_name') == "Administrator":
                    logger.debug(f"AUTH_LOGIN: Admin user '{username}' has invalid license. Checking if other 'complet' licenses exist.")
                    if not licenses_crud.has_any_active_complete_license(conn):
                        logger.warning(f"Administrator user '{username}' has an invalid/missing license and no other active 'complet' license found. Attempting to create a default 6-month license.")
                        try:
                            created_ok, create_msg, new_license_details = license_manager.create_default_admin_license(conn, user['user_id'])
                            logger.debug(f"AUTH_LOGIN: create_default_admin_license result: created_ok={created_ok}, create_msg='{create_msg}', new_license_details_type={type(new_license_details)}")
                            if created_ok:
                                logger.info(f"Default admin license created successfully for '{username}'. Re-checking validity.")
                                is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])
                                logger.debug(f"AUTH_LOGIN: Re-check after admin license creation: is_license_valid={is_license_valid}, license_msg='{license_msg}', license_details_type={type(license_details)}")
                            else:
                                logger.error(f"Failed to create default admin license for '{username}': {create_msg}")
                                logger.debug(f"AUTH_LOGIN: Returning (True, '{create_msg or license_msg}', user_data, license_details_type={type(license_details)}) due to failed admin license creation.")
                                return True, create_msg or license_msg, _current_user_data, license_details
                        except Exception as e_create_lic:
                            logger.error(f"Exception during default admin license creation for '{username}': {e_create_lic}", exc_info=True)
                            detailed_error_msg = f"Erreur critique lors de la création de la licence admin: {type(e_create_lic).__name__} - {str(e_create_lic)}"
                            logger.debug(f"AUTH_LOGIN: Returning (True, '{detailed_error_msg}', user_data, license_details_type={type(license_details)}) due to exception in admin license creation.")
                            return True, detailed_error_msg, _current_user_data, license_details
                    else:
                        logger.info(f"Administrator user '{username}' has an invalid/missing license, but other 'complet' licenses exist. Default license not created.")

                logger.debug(f"AUTH_LOGIN: Final license state before returning: is_license_valid={is_license_valid}, license_msg='{license_msg}', license_details_type={type(license_details)}")
                if not is_license_valid:
                    logger.debug(f"AUTH_LOGIN: Returning (True, '{license_msg}', user_data, license_details_type={type(license_details)}) because license is not valid.")
                    return True, license_msg, _current_user_data, license_details

                logger.debug(f"AUTH_LOGIN: Returning (True, None, user_data, license_details_type={type(license_details)}) for successful login with valid license.")
                return True, None, _current_user_data, license_details

            except AttributeError as e_attr:
                logger.error(f"AUTH_LOGIN: AttributeError during token/license processing for {username}: {e_attr}", exc_info=True)
                formatted_traceback = traceback.format_exc()
                logger.error(f"Detailed Traceback for AttributeError:\n{formatted_traceback}")
                _current_user_data = None
                if remember_me and conn:

                    user_session_tokens_crud.delete_all_user_session_tokens(conn, user['user_id'])
                clear_remember_me_token_from_settings()
                # Return a more specific error message if possible, or the generic one
                return False, f"Erreur interne (AttributeError): {str(e_attr)}", None, None
            except Exception as e_inner:
                logger.error(f"AUTH_LOGIN: Error during token/license processing for {username}: {e_inner}", exc_info=True)
                _current_user_data = None
                if remember_me and conn:

                    user_session_tokens_crud.delete_all_user_session_tokens(conn, user['user_id'])
                clear_remember_me_token_from_settings()
                return False, f"Erreur interne ({type(e_inner).__name__}).", None, None
            finally:
                if conn:
                    conn.close()
        else: # Password verification failed
            logger.warning(f"Login attempt failed: Invalid password for user '{username}'.")
            # clear_remember_me_token_from_settings() was already called
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None

    except Exception as e: # General error during login (e.g., DB connection before try-with-conn)
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        clear_remember_me_token_from_settings() # Ensure token is cleared on any failure path
        return False, "Une erreur est survenue lors de la connexion.", None, None

def login_with_session_token(token_from_qsettings: str) -> tuple[bool, str | None, dict | None, dict | None]:
    """
    Attempts to log in a user using a session token from QSettings.
    Returns: (success, message, user_data, license_info)
    """
    global _current_user_data
    logger.info("Attempting login with session token.")

    if not token_from_qsettings:
        return False, "No token provided.", None, None

    token_hash = hash_token_for_storage(token_from_qsettings)
    conn = None

    try:

        conn = get_db_connection()
        token_data = user_session_tokens_crud.get_session_token_by_hash(conn, token_hash)

        if not token_data:
            logger.warning("Session token not found in DB or expired. Clearing from QSettings.")
            clear_remember_me_token_from_settings()
            # Log failed token login attempt
            activity_logs_crud.add_activity_log(
                conn=conn,
                data={
                    "user_id": None, # User is unknown at this point
                    "action_type": "REMEMBER_ME_TOKEN_LOGIN_FAILED",
                    "details": f"Failed login attempt with token hash {token_hash[:10]}... Token not found or expired.",
                    "related_entity_type": "UserSessionToken",
                    "related_entity_id": token_hash # Log the hash for investigation
                }
            )
            return False, "Session invalide ou expirée.", None, None

        # Token found and not expired, fetch user
        user = users_crud.get_user_by_id(token_data['user_id'], conn=conn) # Pass conn to reuse
        if not user or not user.get('is_active'):
            logger.warning(f"User for token (ID: {token_data['user_id']}) not found or inactive. Deleting token.")
            user_session_tokens_crud.delete_session_token(conn, token_hash) # Delete the compromised/invalid token
            clear_remember_me_token_from_settings()
            activity_logs_crud.add_activity_log(
                 conn=conn,
                 data={
                    "user_id": token_data.get('user_id'),
                    "action_type": "REMEMBER_ME_TOKEN_LOGIN_FAILED",
                    "details": f"Login with token hash {token_hash[:10]}... failed: User not found or inactive.",
                    "related_entity_type": "UserSessionToken",
                    "related_entity_id": token_hash
                }
            )
            return False, "Utilisateur associé à la session introuvable ou inactif.", None, None

        # User is valid and active, establish session
        _current_user_data = {
            'user_id': user['user_id'],
            'username': user['username'],
            'full_name': user.get('full_name'),
            'email': user.get('email'),
            'role_id': user['role_id'],
            'role_name': user.get('role_name')
        }
        user_session_tokens_crud.update_token_last_used(conn, token_hash)
        users_crud.record_login_time(user['user_id'], conn=conn) # Record login time
        logger.info(f"Successfully logged in user {user['username']} with session token.")
        activity_logs_crud.add_activity_log(
            conn=conn,
            data={
                "user_id": user['user_id'],
                "action_type": "REMEMBER_ME_TOKEN_LOGIN_SUCCESS",
                "details": f"User {user['username']} successfully logged in using a 'Remember Me' session token.",
                "related_entity_type": "UserSessionToken",
                "related_entity_id": token_data['token_id']
            }
        )

        # License Check
        is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])
        # Admin default license creation is not typically part of token login,
        # as it's an interactive step usually following explicit password login.

        if not is_license_valid:
            logger.warning(f"Token login for '{user['username']}' successful, but license is invalid: {license_msg}")
            # User is authenticated, but license is an issue.
            # main.py will handle showing LicenseDialog if needed.
            return True, license_msg, _current_user_data, license_details # Return True for auth, with license message

        return True, None, _current_user_data, license_details


    except Exception as e:

        logger.error(f"Error during login with session token: {e}", exc_info=True)
        clear_remember_me_token_from_settings() # Clear token on error
        if conn and token_hash: # Attempt to delete token from DB if error occurred after hash was known
             user_session_tokens_crud.delete_session_token(conn, token_hash)
        return False, "Erreur interne lors de la connexion par session.", None, None
    finally:
        if conn:
            conn.close()


def logout():
    """Logs out the current user and clears any session token."""
    global _current_user_data

    token_to_clear = get_remembered_token_from_settings() # Get token before clearing _current_user_data

    if _current_user_data:
        logger.info(f"User '{_current_user_data.get('username')}' logged out.")
        _current_user_data = None # Clear current user data from this service
    else:
        logger.info("Logout called but no user was logged in locally in auth_service.")

    if token_to_clear:
        conn = None


        try :
            conn = get_db_connection()
            token_hash = hash_token_for_storage(token_to_clear)
            token_deleted_from_db = user_session_tokens_crud.delete_session_token(conn, token_hash)
            if token_deleted_from_db:
                logger.info("Session token deleted from database during logout.")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        # _current_user_data might be None if logout is called without an active session,
                        # but token_to_clear implies a previous session existed.
                        # We need user_id associated with the token if possible.
                        # This is tricky as delete_session_token only takes hash.
                        # For now, we'll log without user_id if not available in _current_user_data.
                        "user_id": _current_user_data.get('user_id') if _current_user_data else None,
                        "action_type": "REMEMBER_ME_TOKEN_DELETED_ON_LOGOUT",
                        "details": f"Session token (hash: {token_hash[:10]}...) deleted from DB due to logout.",
                        "related_entity_type": "UserSessionToken",
                        "related_entity_id": token_hash
                    }
                )
            else:
                logger.info("No matching session token found in database to delete during logout.")


        except Exception as e:
            logger.error(f"Error deleting session token from DB during logout: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    clear_remember_me_token_from_settings() # Always clear from QSettings on logout
