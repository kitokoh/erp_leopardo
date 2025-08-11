# auth/password_reset_service.py
import logging
from datetime import datetime, timedelta, timezone
import os # For path construction for email templates

from app.db.cruds import users_crud, password_reset_tokens_crud, user_session_tokens_crud, activity_logs_crud # Added activity_logs_crud
from app.utils.security_helpers import generate_secure_token, hash_token_for_storage
from app.services.email_service import EmailSenderService
from app.db.connection import get_db_connection
from app_setup import CONFIG, APP_ROOT_DIR # Added APP_ROOT_DIR

logger = logging.getLogger(__name__)

TOKEN_VALIDITY_HOURS = 1
APP_NAME = CONFIG.get("app_display_name", "ClientDocManager")
# BASE_URL for reset links, e.g., "https://myapp.com/reset-password" - for web apps.
# For desktop, the link might be conceptual or a custom scheme, or user just copies token.
# For now, we'll assume the user will copy the token from the email.
# If a web component is available:
# APP_BASE_URL = CONFIG.get("app_base_url", "http://localhost:8000")

class PasswordResetService:
    def __init__(self):
        # Email service can be initialized per request or kept if lightweight
        pass

    def request_password_reset(self, email: str) -> tuple[bool, str]:
        """
        Initiates a password reset request for a user by their email.
        Generates a token, stores it, and sends a reset email.
        """
        conn = None
        try:
            conn = get_db_connection()
            user = users_crud.get_user_by_email(email, conn=conn)

            if not user:
                logger.warning(f"Password reset request for non-existent email: {email}")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": None, # User is unknown
                        "action_type": "PASSWORD_RESET_REQUEST_UNKNOWN_EMAIL",
                        "details": f"Password reset requested for non-existent or non-disclosed email: {email}.",
                    }
                )
                # Return a generic message to avoid disclosing whether an email exists
                return True, "Si un compte est associé à cet e-mail, un lien de réinitialisation a été envoyé."

            user_id = user['user_id'] # Get user_id early for logging
            if not user.get('is_active'):
                logger.warning(f"Password reset request for inactive user: {email} (User ID: {user_id})")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": user_id,
                        "action_type": "PASSWORD_RESET_REQUEST_INACTIVE_USER",
                        "details": f"Password reset requested for inactive user (Email: {email}).",
                        "related_entity_type": "User",
                        "related_entity_id": user_id
                    }
                )
                return False, "Ce compte utilisateur est désactivé. Réinitialisation de mot de passe non permise."

            original_token = generate_secure_token(32) # 32 bytes = 43 URL-safe chars
            token_hash = hash_token_for_storage(original_token)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_VALIDITY_HOURS)

            if not password_reset_tokens_crud.create_reset_token(conn, user_id, token_hash, expires_at):
                logger.error(f"Failed to create password reset token in DB for user {user_id}.")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": user_id,
                        "action_type": "PASSWORD_RESET_TOKEN_CREATION_FAILED",
                        "details": "Database error while attempting to create password reset token.",
                        "related_entity_type": "User",
                        "related_entity_id": user_id
                    }
                )
                return False, "Erreur interne lors de la création de la demande de réinitialisation."

            activity_logs_crud.add_activity_log(
                conn=conn,
                data={
                    "user_id": user_id,
                    "action_type": "PASSWORD_RESET_TOKEN_CREATED",
                    "details": f"Password reset token generated and stored. Expires: {expires_at.isoformat()}",
                    "related_entity_type": "User",
                    "related_entity_id": user_id
                }
            )

            # Send email
            # Construct reset link (conceptual for desktop, user might copy token)
            # reset_link = f"{APP_BASE_URL}/reset-password?token={original_token}"
            # For desktop, we'll emphasize copying the token.
            reset_link_placeholder = f"app://reset-password?token={original_token}" # Example custom scheme

            email_context = {
                "user_full_name": user.get("full_name", user.get("username", "Utilisateur")),
                "reset_link": reset_link_placeholder, # User will likely copy the token itself
                "reset_token": original_token,
                "token_validity_hours": TOKEN_VALIDITY_HOURS,
                "app_name": APP_NAME,
            }

            # Determine email language - for now, assume French or use a setting
            # This could be enhanced by storing user's preferred language
            lang_code = "fr" # Default or from user profile/app settings

            # Load the HTML content from file
            # This path needs to be relative to where EmailSenderService expects it or absolute
            # For now, assuming EmailSenderService can find it or path is adjusted.
            # Let's assume app_setup.APP_ROOT_DIR is available for constructing path.
            from app_setup import APP_ROOT_DIR
            template_filename = f"password_reset_email_{lang_code}.html"
            template_path = os.path.join(APP_ROOT_DIR, "email_template_designs", template_filename)

            html_body_content = ""
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_body_content = f.read()
            except FileNotFoundError:
                logger.error(f"Password reset email template not found: {template_path}")
                # Fallback to a very basic text email if template is missing
                html_body_content = f"Veuillez utiliser ce jeton pour réinitialiser votre mot de passe : {original_token}"
                # Consider not sending if template is critical and missing.
                # return False, "Erreur interne: Modèle d'e-mail manquant."


            email_subject = f"Réinitialisation de votre mot de passe pour {APP_NAME}"
            if lang_code == "en":
                email_subject = f"Password Reset Request for {APP_NAME}"


            # Initialize EmailSenderService - it will use default SMTP config
            email_service = EmailSenderService()
            if not email_service.smtp_config:
                 logger.error("SMTP configuration not available for password reset email.")
                 return False, "Service d'envoi d'e-mail non configuré. Impossible d'envoyer l'e-mail de réinitialisation."

            email_sent, email_msg = email_service.send_email(
                recipient_email=user['email'],
                subject_template=email_subject, # Subject is already personalized or fixed
                body_html_content_or_filename=html_body_content, # Pass direct HTML content
                context_data=email_context, # Context for placeholder replacement
                # template_obj=None, # Not using DB template object for this system email
                attachments=[]
            )

            if email_sent:
                logger.info(f"Password reset email sent to {user['email']} for user {user_id}.")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": user_id,
                        "action_type": "PASSWORD_RESET_EMAIL_SENT",
                        "details": f"Password reset email successfully sent to {user['email']}.",
                        "related_entity_type": "User",
                        "related_entity_id": user_id
                    }
                )
                return True, "Si un compte est associé à cet e-mail, un lien de réinitialisation a été envoyé."
            else:
                logger.error(f"Failed to send password reset email to {user['email']}: {email_msg}")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": user_id,
                        "action_type": "PASSWORD_RESET_EMAIL_FAILED",
                        "details": f"Failed to send password reset email to {user['email']}. Error: {email_msg}",
                        "related_entity_type": "User",
                        "related_entity_id": user_id
                    }
                )
                # Don't expose detailed email sending failure to user for security.
                # But we need to rollback or mark the token as unusable if email failed.
                # For simplicity now, the token remains but won't be usable if user can't get it.
                # A more robust system might retry or log for admin attention.
                return False, "Impossible d'envoyer l'e-mail de réinitialisation pour le moment. Veuillez réessayer plus tard."

        except Exception as e:
            logger.error(f"Unexpected error in request_password_reset for {email}: {e}", exc_info=True)
            # Log generic failure if specific user_id isn't available yet
            user_id_for_log = user.get('user_id') if 'user' in locals() and user else None
            activity_logs_crud.add_activity_log(
                conn=conn, # conn might be None if get_db_connection failed
                data={
                    "user_id": user_id_for_log,
                    "action_type": "PASSWORD_RESET_REQUEST_EXCEPTION",
                    "details": f"Exception during password reset request for email {email}: {str(e)}",
                }
            )
            return False, "Une erreur inattendue est survenue."
        finally:
            if conn:
                conn.close()

    def verify_reset_token(self, token: str) -> str | None:
        """
        Verifies a password reset token.
        Returns the user_id if the token is valid, None otherwise.
        """
        if not token:
            return None

        token_hash = hash_token_for_storage(token)
        conn = None
        try:
            conn = get_db_connection()
            token_data = password_reset_tokens_crud.get_reset_token_by_hash(conn, token_hash)
            if token_data:
                return token_data['user_id']
            return None
        except Exception as e:
            logger.error(f"Error verifying reset token: {e}", exc_info=True)
            return None
        finally:
            if conn:
                conn.close()

    def reset_password_with_token(self, token: str, new_password: str) -> tuple[bool, str]:
        """
        Resets a user's password using a valid reset token.
        """
        if not token or not new_password:
            return False, "Jeton ou nouveau mot de passe manquant."

        token_hash = hash_token_for_storage(token)
        conn = None
        try:
            conn = get_db_connection()
            token_data = password_reset_tokens_crud.get_reset_token_by_hash(conn, token_hash)

            if not token_data:
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": None, # User ID unknown if token is invalid
                        "action_type": "PASSWORD_RESET_INVALID_TOKEN",
                        "details": f"Attempt to reset password with invalid/expired/used token hash {token_hash[:10]}...",
                        "related_entity_id": token_hash
                    }
                )
                return False, "Jeton de réinitialisation invalide, expiré ou déjà utilisé."

            user_id = token_data['user_id']

            # Update user's password
            if not users_crud.update_user_password(user_id, new_password, conn=conn):
                logger.error(f"Failed to update password in DB for user {user_id} during reset.")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": user_id,
                        "action_type": "PASSWORD_RESET_DB_UPDATE_FAILED",
                        "details": "Database error while updating user's password during reset.",
                        "related_entity_type": "User",
                        "related_entity_id": user_id
                    }
                )
                return False, "Erreur lors de la mise à jour du mot de passe."

            # Mark reset token as used
            if not password_reset_tokens_crud.mark_token_as_used(conn, token_hash):
                logger.warning(f"Failed to mark reset token {token_hash[:10]}... as used for user {user_id}. This might allow reuse if not handled.")
                activity_logs_crud.add_activity_log(
                    conn=conn,
                    data={
                        "user_id": user_id,
                        "action_type": "PASSWORD_RESET_TOKEN_MARK_USED_FAILED",
                        "details": f"Failed to mark reset token {token_hash[:10]}... as used. Potential reuse risk.",
                        "related_entity_type": "PasswordResetToken",
                        "related_entity_id": token_hash
                    }
                )
                # This is a potential issue but password has been reset. Continue with success for user.

            # Invalidate all active "Remember Me" session tokens for this user
            deleted_session_tokens = user_session_tokens_crud.delete_all_user_session_tokens(conn, user_id)
            logger.info(f"Invalidated {deleted_session_tokens} active session token(s) for user {user_id} after password reset.")
            activity_logs_crud.add_activity_log(
                conn=conn,
                data={
                    "user_id": user_id,
                    "action_type": "SESSION_TOKENS_INVALIDATED_POST_PASSWORD_RESET",
                    "details": f"{deleted_session_tokens} 'Remember Me' session token(s) invalidated after password reset.",
                    "related_entity_type": "User",
                    "related_entity_id": user_id
                }
            )

            # Optionally, send password change confirmation email here
            # ...

            logger.info(f"Password successfully reset for user {user_id}.")
            activity_logs_crud.add_activity_log(
                conn=conn,
                data={
                    "user_id": user_id,
                    "action_type": "PASSWORD_RESET_SUCCESS",
                    "details": "User password successfully reset using a token.",
                    "related_entity_type": "User",
                    "related_entity_id": user_id
                }
            )
            return True, "Votre mot de passe a été réinitialisé avec succès."

        except Exception as e:
            logger.error(f"Error during password reset with token: {e}", exc_info=True)
            user_id_for_log = token_data.get('user_id') if 'token_data' in locals() and token_data else None
            activity_logs_crud.add_activity_log(
                conn=conn, # conn might be None if get_db_connection failed earlier
                data={
                    "user_id": user_id_for_log,
                    "action_type": "PASSWORD_RESET_WITH_TOKEN_EXCEPTION",
                    "details": f"Exception during password reset with token: {str(e)}",
                    "related_entity_id": token_hash[:10] if token_hash else "N/A"
                }
            )
            # Rollback might be needed if conn was used for multiple ops, but users_crud and password_reset_tokens_crud manage their own commits.
            return False, "Une erreur interne est survenue lors de la réinitialisation du mot de passe."
        finally:
            if conn:
                conn.close()

# Instantiate if you want to use it as `auth_service.password_reset_service.request_password_reset()`
# Or keep as a class and instantiate where needed.
# For now, let's assume it will be instantiated on demand or be part of a larger auth service object.
# password_reset_service_instance = PasswordResetService()
