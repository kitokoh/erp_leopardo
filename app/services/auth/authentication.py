import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from PyQt5.QtCore import QSettings

from app.db.cruds.users import users_crud, user_session_tokens_crud
from app.db.cruds.misc.activity_logs_crud import add_activity_log
from app.db.cruds.misc.application_settings_crud import get_setting
from app.utils.security_helpers import generate_secure_token, hash_token_for_storage
from app.utils.auth import verify_password as util_verify_password
from app.db.session_manager import session_manager
from app.license_management import manager as license_manager

logger = logging.getLogger(__name__)

_current_user_data = None
_current_license_details = None

APP_NAME = "ClientDocManager"
ORG_NAME = "SaadiyaManagement"
REMEMBER_ME_TOKEN_QSETTINGS_KEY = "auth/remember_me_token"
SESSION_TOKEN_EXPIRY_DAYS = 60

def get_current_user() -> dict | None:
    return _current_user_data

def set_current_user(user_data: dict | None):
    global _current_user_data
    _current_user_data = user_data

def get_current_user_id() -> str | None:
    return _current_user_data.get('user_id') if _current_user_data else None

def get_current_user_role() -> str | None:
    return _current_user_data.get('role_name') if _current_user_data else None

def get_current_license_details() -> dict | None:
    return _current_license_details

def save_remember_me_token_to_settings(token: str):
    settings = QSettings(ORG_NAME, APP_NAME)
    if token:
        settings.setValue(REMEMBER_ME_TOKEN_QSETTINGS_KEY, token)
    else:
        settings.remove(REMEMBER_ME_TOKEN_QSETTINGS_KEY)
    settings.sync()

def get_remembered_token_from_settings() -> str | None:
    settings = QSettings(ORG_NAME, APP_NAME)
    return settings.value(REMEMBER_ME_TOKEN_QSETTINGS_KEY, "", type=str) or None

def clear_remember_me_token_from_settings():
    settings = QSettings(ORG_NAME, APP_NAME)
    if settings.contains(REMEMBER_ME_TOKEN_QSETTINGS_KEY):
        settings.remove(REMEMBER_ME_TOKEN_QSETTINGS_KEY)
        settings.sync()

def login(db: Session, username: str, password: str, remember_me: bool = False) -> tuple[bool, str | None, dict | None, dict | None]:
    """
    Attempts to log in a user using a provided database session.
    """
    global _current_user_data, _current_license_details
    _current_user_data, _current_license_details = None, None
    clear_remember_me_token_from_settings()

    try:
        user = users_crud.get_user_by_username(db, username)
        if not user:
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None
        if not user.is_active:
            return False, "Ce compte utilisateur est désactivé.", None, None

        password_verified, _ = util_verify_password(password, user.hashed_password)
        if not password_verified:
            return False, "Nom d'utilisateur ou mot de passe incorrect.", None, None

        users_crud.record_login_time(db, user.user_id)
        _current_user_data = {'user_id': user.user_id, 'username': user.username, 'full_name': user.full_name, 'email': user.email, 'role_id': user.role_id, 'role_name': user.role.role_name if user.role else 'N/A'}

        should_check_license = get_setting(key='check_license_on_startup', default='True', conn=db).lower() == 'true'
        if not should_check_license:
            is_license_valid, license_msg, license_details = True, "Vérification de la licence contournée.", {"license_type": "bypass_setting", "is_active": True, "user_id": user.user_id}
            add_activity_log(data={"user_id": user.user_id, "action_type": "LICENSE_CHECK_BYPASSED"}, conn=db)
        else:
            is_license_valid, license_msg, license_details = license_manager.check_license_validity(db, user.user_id)
            if user.role.role_name == "Administrator" and not is_license_valid:
                created_ok, create_msg, new_details = license_manager.create_default_admin_license(db, user.user_id)
                if created_ok:
                    is_license_valid, license_msg, license_details = True, None, new_details
                else:
                    license_msg = f"Échec de la création/renouvellement de la licence admin: {create_msg}."

        if remember_me:
            user_session_tokens_crud.delete_all_user_session_tokens(db, user.user_id)
            new_token = generate_secure_token(48)
            token_hash = hash_token_for_storage(new_token)
            expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_TOKEN_EXPIRY_DAYS)
            if user_session_tokens_crud.add_session_token(db, user.user_id, token_hash, expires_at):
                save_remember_me_token_to_settings(new_token)
                add_activity_log(data={"user_id": user.user_id, "action_type": "REMEMBER_ME_TOKEN_GENERATED"}, conn=db)

        if not is_license_valid:
            _current_license_details = license_details
            return True, license_msg, _current_user_data, license_details

        _current_license_details = license_details
        return True, None, _current_user_data, license_details

    except Exception as e:
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        return False, "Une erreur est survenue lors de la connexion.", None, None

def login_with_session_token(db: Session, token_from_qsettings: str) -> tuple[bool, str | None, dict | None, dict | None]:
    """
    Attempts to log in a user using a session token and a provided database session.
    """
    global _current_user_data, _current_license_details
    _current_user_data, _current_license_details = None, None

    if not token_from_qsettings:
        return False, "No token provided.", None, None

    token_hash = hash_token_for_storage(token_from_qsettings)

    try:
        token_data = user_session_tokens_crud.get_session_token_by_hash(db, token_hash)
        if not token_data:
            clear_remember_me_token_from_settings()
            add_activity_log(data={"action_type": "REMEMBER_ME_TOKEN_LOGIN_FAILED", "details": f"Token hash {token_hash[:10]}... not found or expired."}, conn=db)
            return False, "Session invalide ou expirée.", None, None

        user = users_crud.get_user_by_id(db, token_data['user_id'])
        if not user or not user.get('is_active'):
            user_session_tokens_crud.delete_session_token(db, token_hash)
            clear_remember_me_token_from_settings()
            add_activity_log(data={"user_id": token_data.get('user_id'), "action_type": "REMEMBER_ME_TOKEN_LOGIN_FAILED", "details": "User not found or inactive."}, conn=db)
            return False, "Utilisateur associé à la session introuvable ou inactif.", None, None

        _current_user_data = {'user_id': user['user_id'], 'username': user['username'], 'full_name': user.get('full_name'), 'email': user.get('email'), 'role_id': user['role_id'], 'role_name': user.get('role_name')}
        user_session_tokens_crud.update_token_last_used(db, token_hash)
        users_crud.record_login_time(db, user['user_id'])
        add_activity_log(data={"user_id": user['user_id'], "action_type": "REMEMBER_ME_TOKEN_LOGIN_SUCCESS"}, conn=db)

        is_license_valid, license_msg, license_details = license_manager.check_license_validity(db, user['user_id'])
        if not is_license_valid:
            _current_license_details = license_details
            return True, license_msg, _current_user_data, license_details

        _current_license_details = license_details
        return True, None, _current_user_data, license_details

    except Exception as e:
        logger.error(f"Error during login with session token: {e}", exc_info=True)
        clear_remember_me_token_from_settings()
        return False, "Erreur interne lors de la connexion par session.", None, None

def logout():
    """Logs out the current user and clears any session token."""
    global _current_user_data
    token_to_clear = get_remembered_token_from_settings()
    user_id = get_current_user_id()

    if _current_user_data:
        logger.info(f"User '{_current_user_data.get('username')}' logged out.")
        _current_user_data = None

    if token_to_clear:
        with session_manager.get_session() as session:
            try:
                token_hash = hash_token_for_storage(token_to_clear)
                if user_session_tokens_crud.delete_session_token(session, token_hash):
                    add_activity_log(data={"user_id": user_id, "action_type": "REMEMBER_ME_TOKEN_DELETED_ON_LOGOUT"}, conn=session)
            except Exception as e:
                logger.error(f"Error deleting session token from DB during logout: {e}", exc_info=True)

    clear_remember_me_token_from_settings()
