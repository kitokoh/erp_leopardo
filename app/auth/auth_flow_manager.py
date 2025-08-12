# -*- coding: utf-8 -*-
import sys
import logging
from PyQt5.QtWidgets import QDialog, QMessageBox

# Project-specific imports
from app.gui.dialogs.login_dialog import LoginDialog
from app.license_management.ui import LicenseDialog
from app.auth import authentication as auth_service
from app.license_management import manager as license_manager
from app.db.connection import get_db_connection

class AuthFlowManager:
    """
    Orchestrates the entire user authentication and license verification process.
    """
    def __init__(self, session_manager, splash_screen=None):
        """
        Initializes the AuthFlowManager.

        Args:
            session_manager: An instance of the SessionManager.
            splash_screen: An optional splash screen instance to hide on exit.
        """
        self.session_manager = session_manager
        self.splash = splash_screen

    def execute_auth_flow(self):
        """
        Executes the full authentication and licensing flow.

        This method attempts to log in with a remembered token. If that fails,
        it presents the login dialog and handles license checks.

        Returns:
            tuple: A tuple of (bool, dict, dict) representing:
                   - success (True if authenticated with valid license, False otherwise)
                   - user_info (dictionary of the logged-in user)
                   - license_info (dictionary of the active license)
        """
        # Try to log in with a 'Remember Me' token first
        success, user_info, license_info = self._try_token_login()
        if success:
            return True, user_info, license_info

        # If token login fails, proceed with the dialog-based login loop
        return self._run_login_dialog_loop()

    def _try_token_login(self):
        """Attempts to authenticate using a saved session token."""
        remembered_token = auth_service.get_remembered_token_from_settings()
        if not remembered_token:
            return False, None, None

        token_auth_success, _, token_user_info, token_license_info = auth_service.login_with_session_token(remembered_token)

        if token_auth_success and token_user_info:
            if token_license_info and token_license_info.get('is_active'):
                # Start session using the manager
                self.session_manager.start_session(
                    token=auth_service.get_current_session_token(),
                    user_id=token_user_info['user_id'],
                    user_role=token_user_info['role']
                )
                logging.info(f"Successfully logged in with remembered token for user: {token_user_info.get('username')}")
                return True, token_user_info, token_license_info
            else:
                QMessageBox.warning(None, "Licence Requise", "Votre session a été restaurée, mais votre licence n'est plus valide.\nVeuillez vous reconnecter.")
                auth_service.logout() # Clear the invalid session

        return False, None, None

    def _run_login_dialog_loop(self):
        """
        Manages the interactive login process using the LoginDialog.
        This includes handling license checks and activation after a successful login.
        """
        # Ensure any previous user session is cleared before showing login
        if auth_service.get_current_user():
            auth_service.logout()

        while True:
            login_dialog = LoginDialog()
            login_dialog_result = login_dialog.exec_()

            if login_dialog_result != QDialog.Accepted:
                self._handle_exit("Login dialog was cancelled by the user.")
                return False, None, None # Exit state

            auth_success, auth_message, user_info, license_info = login_dialog.get_raw_login_output() or (False, "Login failed.", None, None)

            if not auth_success or not user_info:
                QMessageBox.warning(login_dialog, "Échec de la Connexion", auth_message or "Nom d'utilisateur ou mot de passe incorrect.")
                continue # Show login dialog again

            # User is authenticated, now check license
            if license_info and license_info.get('is_active'):
                logging.info(f"User '{user_info.get('username')}' logged in with an active license.")
                return True, user_info, license_info # Success state

            # Handle cases with no license or an inactive one
            success, new_license_info = self._handle_license_activation(user_info, license_info)
            if success:
                return True, user_info, new_license_info # Success after activation

            # If license activation was cancelled or failed, the loop continues,
            # but a more definitive action might be better (e.g., exit).
            # For now, let's assume if _handle_license_activation returns false, we should exit.
            if not success:
                self._handle_exit("License activation failed or was cancelled.")
                return False, None, None

    def _handle_license_activation(self, user_info, current_license_info):
        """
        Handles the flow for activating a license if the user doesn't have a valid one.
        This includes offering a free trial.
        """
        # Offer free license if applicable
        if "aucune licence" in (current_license_info.get('message') or "").lower() or "expiré" in (current_license_info.get('message') or "").lower():
            conn = None
            try:
                conn = get_db_connection()
                machine_id = license_manager.get_machine_identifier()
                existing_free_on_machine = license_manager.cruds.get_licenses_by_machine_info(conn, machine_id, license_type="gratuit")
                has_had_free_on_machine_for_user = any(lic['user_id'] == user_info['user_id'] for lic in existing_free_on_machine)

                if not has_had_free_on_machine_for_user:
                    reply = QMessageBox.question(None, "Licence Gratuite", "Aucune licence valide trouvée. Souhaitez-vous activer une licence gratuite de 30 jours ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if reply == QMessageBox.Yes:
                        free_lic_details, free_msg = license_manager.activate_free_license(conn, user_info['user_id'])
                        if free_lic_details:
                            QMessageBox.information(None, "Licence Gratuite Activée", free_msg)
                            return True, free_lic_details # Success with new free license
                        else:
                            QMessageBox.warning(None, "Échec Activation Gratuite", free_msg)
            finally:
                if conn:
                    conn.close()

        # If free trial was not taken or not applicable, show the main license dialog
        license_dialog = LicenseDialog(current_user_info=user_info, initial_license_info=current_license_info, parent=None)
        if license_dialog.exec_() == QDialog.Accepted:
            updated_license = license_dialog.get_current_valid_license_info()
            if updated_license and updated_license.get('is_active'):
                return True, updated_license # Success with new/updated license

        return False, None # Failure or cancellation

    def _handle_exit(self, reason=""):
        """Hides the splash screen and logs the exit reason."""
        if reason:
            logging.info(f"Exiting authentication flow: {reason}")
        if self.splash:
            self.splash.hide()
        # The decision to call sys.exit() is moved to the caller (main_crm.py)
        # This makes the AuthFlowManager more reusable.
