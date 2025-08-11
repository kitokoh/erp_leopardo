# auth/authentication.py
import logging
import sqlite3
from datetime import datetime, timedelta, timezone # Added timedelta and timezone

# auth/authentication.py
import logging
import traceback # Import for detailed traceback
from datetime import datetime, timedelta, timezone # Added timedelta and timezone

from app.db.cruds.users import users_crud
from app.db.cruds.misc.activity_logs_crud import add_activity_log
from app.db.cruds.misc.application_settings_crud import get_setting
from app.db.cruds.users import user_session_tokens_crud
from app.utils.security_helpers import generate_secure_token, hash_token_for_storage # New helpers
from app.license_management import manager as license_manager # Already imported below, moved up for clarity
from app.db.connection import get_db_connection # Already imported below, moved up

logger = logging.getLogger(__name__)

# Module-level variable to store the current user's data
_current_user_data = None

# Removed the older, duplicated login function.
# The active login function is defined further down (starting around line 227 in original file).

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

                # --- License Check Bypass Logic ---
                should_check_license_str = get_setting('check_license_on_startup', default='True', conn=conn) # Pass conn
                should_check_license = should_check_license_str.lower() == 'true'
                logger.info(f"AUTH_LOGIN: License check setting 'check_license_on_startup' is '{should_check_license_str}', parsed as: {should_check_license}")

                is_license_valid = False # Default to false, will be updated by actual check or bypass
                license_msg = None
                license_details = None

                if not should_check_license:
                    logger.warning(f"AUTH_LOGIN: Bypassing license check for user '{username}' due to 'check_license_on_startup' setting.")
                    is_license_valid = True
                    license_msg = "Vérification de la licence contournée par paramètre."
                    license_details = {
                        "license_type": "bypass_setting",
                        "is_active": True,
                        "license_id": "BYPASS_VIA_SETTINGS",
                        "user_id": _current_user_data['user_id'],
                        "activation_date": datetime.now(timezone.utc).isoformat(),
                        "expiration_date": (datetime.now(timezone.utc) + timedelta(days=365*100)).isoformat(), # Long expiry
                        "machine_info": "N/A_BYPASS",
                        "allowed_features": "all" # Assuming bypass grants all features
                    }
                    # Log activity for bypass
                    add_activity_log(conn=conn, data={
                        "user_id": _current_user_data['user_id'], "action_type": "LICENSE_CHECK_BYPASSED",
                        "details": "License check was bypassed due to application setting.",
                        "related_entity_type": "User", "related_entity_id": _current_user_data['user_id']
                    })
                # --- End License Check Bypass Logic ---

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
                        add_activity_log(conn=conn, data={"user_id": user['user_id'], "action_type": "REMEMBER_ME_TOKEN_GENERATED", "details": f"New 'Remember Me' session token generated. Expires: {expires_at.isoformat()}.", "related_entity_type": "UserSessionToken", "related_entity_id": token_record_id})
                    else:
                        logger.error(f"Failed to store new session token in DB for user {user['user_id']}.")
                else:
                    logger.debug(f"AUTH_LOGIN: 'Remember Me' is false for '{username}'. Clearing any existing tokens.")
                    deleted_count = user_session_tokens_crud.delete_all_user_session_tokens(conn, user['user_id'])
                    if deleted_count > 0:
                        logger.info(f"Cleared {deleted_count} 'Remember Me' token(s) for user {user['user_id']} as 'Remember Me' was not checked.")
                        add_activity_log(conn=conn, data={"user_id": user['user_id'], "action_type": "REMEMBER_ME_TOKENS_CLEARED_ON_LOGIN", "details": f"All 'Remember Me' tokens cleared for user as 'Remember Me' was not selected during login. Count: {deleted_count}."})

                # --- Actual License Check (if not bypassed) ---
                if should_check_license: # Only perform these if license check is not bypassed
                    logger.debug(f"AUTH_LOGIN: About to call license_manager.check_license_validity for user_id: {user['user_id']}")
                    is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])
                    logger.debug(f"AUTH_LOGIN: license_manager.check_license_validity result: is_license_valid={is_license_valid}, license_msg='{license_msg}', license_details_value={license_details}")

                    # If the user is an Administrator and their license is not valid, attempt to create/renew the default admin license.
                    if user.get('role_name') == "Administrator" and not is_license_valid:
                        logger.warning(f"Administrator user '{username}' has an invalid/missing license (Initial check: {license_msg}). Attempting to create/renew default 6-month license.")
                        try:
                            # The create_default_admin_license function in manager.py will handle deactivating old ones.
                            created_ok, create_msg, new_license_details = license_manager.create_default_admin_license(conn, user['user_id'])
                            logger.debug(f"AUTH_LOGIN: create_default_admin_license result: created_ok={created_ok}, create_msg='{create_msg}', new_license_details={new_license_details}")

                            if created_ok and new_license_details:
                                logger.info(f"Default admin license created/renewed successfully for '{username}'. Overriding previous license state.")
                                is_license_valid = True # Mark as valid because we just created/renewed it
                                license_msg = None # Clear any previous error message
                                license_details = new_license_details # Use the new license details
                            else:
                                # If creation failed, the original license_msg and license_details are still relevant.
                                # We augment the message to indicate creation failure.
                                logger.error(f"Failed to create/renew default admin license for '{username}': {create_msg}")
                                license_msg = f"Échec de la création/renouvellement de la licence admin: {create_msg}. Problème initial: {license_msg if license_msg else 'Licence invalide.'}"
                                # is_license_valid remains False
                                # license_details remains the potentially problematic ones from the first check, or None
                        except Exception as e_create_lic:
                            logger.error(f"Exception during default admin license creation/renewal for '{username}': {e_create_lic}", exc_info=True)
                            license_msg = f"Erreur critique lors de la création/renouvellement de la licence admin: {type(e_create_lic).__name__}. Problème initial: {license_msg if license_msg else 'Licence invalide.'}"
                            # is_license_valid remains False
                            # license_details remains the potentially problematic ones from the first check, or None
                # --- End Actual License Check ---

                # Final check on license status before returning (is_license_valid is now set by either bypass or actual check)
                logger.debug(f"AUTH_LOGIN: Final license state before returning: is_license_valid={is_license_valid}, license_msg='{license_msg}', license_details={license_details}")
                if not is_license_valid: # This condition is met if should_check_license was True AND the check failed
                    # User is authenticated, but license is not valid. Return success for auth, but with license message.
                    logger.warning(f"Login for '{username}' successful, but license is invalid: {license_msg}")
                    return True, license_msg, _current_user_data, license_details

                # Login and license are both OK (either by bypass or successful check).
                logger.info(f"Login and license check successful for {username}.")
                return True, None, _current_user_data, license_details # license_msg is None if valid or bypassed successfully

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
            add_activity_log(
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
            add_activity_log(
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
        add_activity_log(
            conn=conn,
            data={
                "user_id": user['user_id'],
                "action_type": "REMEMBER_ME_TOKEN_LOGIN_SUCCESS",
                "details": f"User {user['username']} successfully logged in using a 'Remember Me' session token.",
                "related_entity_type": "UserSessionToken",
                "related_entity_id": token_data['token_id']
            }
        )

        # --- License Check Bypass Logic (for token login) ---
        should_check_license_str = get_setting('check_license_on_startup', default='True', conn=conn)
        should_check_license = should_check_license_str.lower() == 'true'
        logger.info(f"AUTH_TOKEN_LOGIN: License check setting 'check_license_on_startup' is '{should_check_license_str}', parsed as: {should_check_license}")

        is_license_valid = False
        license_msg = None
        license_details = None

        if not should_check_license:
            logger.warning(f"AUTH_TOKEN_LOGIN: Bypassing license check for user '{user['username']}' (token login) due to setting.")
            is_license_valid = True
            license_msg = "Vérification de la licence contournée par paramètre (session restaurée)."
            license_details = {
                "license_type": "bypass_setting_token",
                "is_active": True,
                "license_id": "BYPASS_VIA_SETTINGS_TOKEN",
                "user_id": _current_user_data['user_id'],
                "activation_date": datetime.now(timezone.utc).isoformat(),
                "expiration_date": (datetime.now(timezone.utc) + timedelta(days=365*100)).isoformat(),
                "machine_info": "N/A_BYPASS_TOKEN",
                "allowed_features": "all"
            }
            add_activity_log(conn=conn, data={
                "user_id": _current_user_data['user_id'], "action_type": "LICENSE_CHECK_BYPASSED_TOKEN",
                "details": "License check (token login) was bypassed due to application setting.",
                "related_entity_type": "User", "related_entity_id": _current_user_data['user_id']
            })
        else:
            # --- Actual License Check (if not bypassed for token login) ---
            logger.debug(f"AUTH_TOKEN_LOGIN: Performing license check for user '{user['username']}'.")
            is_license_valid, license_msg, license_details = license_manager.check_license_validity(conn, user['user_id'])
            # Admin default license creation is not typically part of token login,
            # as it's an interactive step usually following explicit password login.

        # --- End License Check Logic for token login ---

        logger.debug(f"AUTH_TOKEN_LOGIN: Final license state: valid={is_license_valid}, msg='{license_msg}', details={license_details}")
        if not is_license_valid: # This implies should_check_license was True and the check failed
            logger.warning(f"Token login for '{user['username']}' successful, but license is invalid: {license_msg}")
            # User is authenticated, but license is an issue.
            # main.py will handle showing LicenseDialog if needed.
            return True, license_msg, _current_user_data, license_details # Return True for auth, with license message

        return True, None, _current_user_data, license_details # Auth and license OK (either by check or bypass)


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
                add_activity_log(
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
