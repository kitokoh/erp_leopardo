# dialogs/login_dialog.py
import logging
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, # Added QApplication
    QLineEdit, QPushButton, QMessageBox, QLabel, QDialogButtonBox
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox

# Assuming auth.authentication module is accessible
# Adjust import path if necessary based on project structure
from auth import authentication
import icons_rc # For icons

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    # Signal to indicate successful login, emitting user data
    login_successful = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Connexion - Gestionnaire de Documents"))
        self.setWindowIcon(QIcon(":/icons/logo.svg")) # Assuming logo.svg is in resources
        self.setMinimumSize(350, 250)
        self.user_data = None # To store user data upon successful login
        self._raw_login_output = None # To store all 4 return values from authentication.login
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Optional: Add a logo or header image
        logo_label = QLabel(self)
        pixmap = QPixmap(":/icons/leopard_logo.svg") # Or your app logo
        if not pixmap.isNull():
             logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
             logo_label.setAlignment(Qt.AlignCenter)
             main_layout.addWidget(logo_label)
        else:
            # Fallback if logo not found or for simplicity
            header_label = QLabel(self.tr("Authentification Requise"))
            header_label.setObjectName("dialogHeaderLabel") # Assuming this style exists
            header_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(header_label)


        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText(self.tr("Nom d'utilisateur"))
        form_layout.addRow(self.tr("Utilisateur:"), self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText(self.tr("Mot de passe"))
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.tr("Mot de passe:"), self.password_input)

        # Allow login on Enter press from password field
        self.password_input.returnPressed.connect(self._attempt_login)
        print(f"DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: init_ui - password_input.returnPressed.connect result: <connected>")


        # Remember Me Checkbox
        self.remember_me_checkbox = QCheckBox(self.tr("Se souvenir de moi"))
        self.remember_me_checkbox.setChecked(False) # Default to unchecked for security
        # Add checkbox to a new QHBoxLayout for better alignment if needed, or directly to form_layout/main_layout
        remember_me_layout = QHBoxLayout()
        remember_me_layout.addStretch() # Push to the right
        remember_me_layout.addWidget(self.remember_me_checkbox)
        # form_layout.addRow(remember_me_layout) # Alternative placement

        main_layout.addLayout(form_layout) # Add form layout first
        main_layout.addLayout(remember_me_layout) # Then add remember_me layout
        main_layout.addStretch(1)

        # Buttons
        self.button_box = QDialogButtonBox()
        self.login_button = self.button_box.addButton(self.tr("Connexion"), QDialogButtonBox.AcceptRole) # Store as instance member
        self.login_button.setIcon(QIcon(":/icons/log-out.svg")) # Corrected: log-out.svg exists and is suitable
        self.login_button.setObjectName("primaryButton") # For styling

        # DEBUG PRINT ADDITIONS
        print("DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: init_ui - Before login_button connect (button_box.accepted)")
        # The QDialogButtonBox's accepted signal is connected, not the button's clicked signal directly here.
        # So, we check the connection to self.button_box.accepted.
        # connection_success_accepted = self.button_box.accepted.connect(self._attempt_login)
        # print(f"DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: init_ui - button_box.accepted.connect result: {connection_success_accepted}")
        # Also, the password input's returnPressed is connected:
        # connection_success_return = self.password_input.returnPressed.connect(self._attempt_login)
        # print(f"DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: init_ui - password_input.returnPressed.connect result: {connection_success_return}")
        # For direct button click, if it's also desired (though QDialogButtonBox usually handles it via roles):
        # self.login_button.clicked.connect(self._attempt_login) # This would be an alternative or additional connection

        cancel_button = self.button_box.addButton(QDialogButtonBox.Cancel)
        cancel_button.setText(self.tr("Annuler"))
        # cancel_button.setIcon(QIcon(":/icons/dialog-cancel.svg")) # Standard icon often set by style

        print("DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: init_ui - Before button_box.accepted.connect")
        self.button_box.accepted.connect(self._attempt_login)
        print("DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: init_ui - After button_box.accepted.connect")

        self.button_box.rejected.connect(self.reject) # Standard reject closes dialog

        main_layout.addWidget(self.button_box)

        # Forgot Password Link/Button
        forgot_password_layout = QHBoxLayout()
        forgot_password_layout.addStretch()
        self.forgot_password_button = QPushButton(self.tr("Mot de passe oublié ?"))
        self.forgot_password_button.setObjectName("linkButton") # For link-like styling
        self.forgot_password_button.setFlat(True)
        self.forgot_password_button.clicked.connect(self._handle_forgot_password)
        forgot_password_layout.addWidget(self.forgot_password_button)
        forgot_password_layout.addStretch()
        main_layout.addLayout(forgot_password_layout)


        self.username_input.setFocus() # Set focus to username field initially
        self._load_remembered_user_or_token()


    def _load_remembered_user_or_token(self):
        """
        Checks for a remembered token and pre-fills username if possible.
        The actual token is not pre-filled for security.
        """
        # This function name is a bit of a misnomer now with token-based auth,
        # as we don't pre-fill username from token directly.
        # However, if old username-based remember-me was still partially active, this would handle it.
        # For token-based, QSettings stores the token, not username.
        # The main.py handles token-based auto-login before this dialog is even shown.
        # If this dialog is shown, it means token auto-login failed or no token.
        # So, this function might be simplified or removed if only token-based is used.

        # For now, let's assume it might still be useful if we want to pre-fill username
        # if a token exists (e.g. by decoding part of it, though not recommended for security).
        # A simpler approach: if a token exists, maybe just check "Remember Me".

        # Current `authentication.get_remembered_user()` is the old one.
        # It should be `authentication.get_remembered_token_from_settings()`.
        # Since `main.py` handles token login, this dialog showing means manual input is needed.
        # We can check if a token *was* present to pre-check "Remember Me",
        # but not pre-fill username from it.

        # Let's check if a token was present, to decide if "Remember Me" should be checked.
        # This is more for UX consistency if user previously chose "Remember Me".
        if authentication.get_remembered_token_from_settings(): # Using the new function name conceptually
            self.remember_me_checkbox.setChecked(True)
            logger.info("A 'Remember Me' token was found; checkbox pre-checked.")
            # Don't pre-fill username from token for security.

        self.username_input.setFocus() # Always focus username for manual entry.


    def _handle_forgot_password(self):
        logger.info("Forgot password button clicked.")
        # Import here to avoid circular dependencies if dialogs import each other indirectly
        from dialogs.request_password_reset_dialog import RequestPasswordResetDialog

        # We can optionally pass the email from the current username input
        # if the user has already typed something there.
        # current_email_attempt = self.username_input.text().strip()
        # if "@" not in current_email_attempt: # Simple check if it looks like an email
        # current_email_attempt = ""

        reset_dialog = RequestPasswordResetDialog(self)
        # if current_email_attempt:
        #     reset_dialog.email_input.setText(current_email_attempt)

        reset_dialog.exec_()
        # The RequestPasswordResetDialog handles its own logic and user feedback.
        # No further action needed here after it closes.

    def _attempt_login(self):
        print("DEBUG_PRINT: DIALOGS_LOGIN_DIALOG: _attempt_login called.") # ADDED
        username = self.username_input.text().strip()
        password = self.password_input.text() # No strip for password

        if not username or not password:
            QMessageBox.warning(self, self.tr("Champs Requis"), self.tr("Veuillez entrer votre nom d'utilisateur et votre mot de passe."))
            return

        # Use the stored self.login_button instance
        self.login_button.setEnabled(False) # Disable button during processing
        QApplication.processEvents() # Ensure UI updates

        try:
            remember_me_checked = self.is_remember_me_checked()
            # authentication.login now returns 4 values: success, error_message, user_info, license_info
            self._raw_login_output = authentication.login(username, password, remember_me=remember_me_checked)
            success, error_message, user_info, license_info = self._raw_login_output

            if success and user_info:
                # License check is handled by main.py using the full raw_login_output.
                # Here, we just care about authentication success for dialog closing.
                logger.info(f"Login attempt in dialog for user: {username}. Auth Success: {success}. Remember Me: {remember_me_checked}. License Info: {license_info is not None}")
                self.user_data = user_info
                self.login_successful.emit(user_info) # Emit signal with user data
                self.accept() # Close the dialog with QDialog.Accepted status
            else:
                logger.warning(f"Login failed for user: {username}. Reason: {error_message}")
                QMessageBox.critical(self, self.tr("Échec de la Connexion"), error_message or self.tr("Nom d'utilisateur ou mot de passe incorrect."))
                self.password_input.clear() # Clear password field on failure
                self.password_input.setFocus()
        except ImportError as ie: # Catch if auth module itself isn't found
            logger.critical(f"Authentication module not found: {ie}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Module d'authentification manquant. L'application ne peut pas continuer."))
            self.reject() # Close dialog, indicating critical failure
        except Exception as e:
            logger.critical(f"Unexpected error during login attempt: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur inattendue est survenue: {0}").format(str(e)))
            self.password_input.clear()
        finally:
            # Use the stored self.login_button instance
            self.login_button.setEnabled(True) # Re-enable button


    def get_user_data(self) -> dict | None:
        """
        Returns the user data if login was successful.
        Call this after the dialog has been accepted.
        """
        return self.user_data

    def is_remember_me_checked(self) -> bool:
        """Returns the state of the 'Remember Me' checkbox."""
        return self.remember_me_checkbox.isChecked()

    def get_raw_login_output(self) -> tuple | None:
        """
        Returns all values from the authentication.login call.
        This is used by main.py to get user_info and license_info.
        """
        return self._raw_login_output

# Example Usage (for testing the dialog itself, not part of the main app flow here)
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    # Mock the auth module for standalone testing if needed
    class MockAuth:
        def login(self, username, password):
            if username == "admin" and password == "password":
                return True, None, {"user_id": "uuid-admin-001", "username": "admin", "full_name": "Administrator", "role_name": "Administrator"}
            elif username == "user" and password == "pass":
                 return True, None, {"user_id": "uuid-user-002", "username": "user", "full_name": "Test User", "role_name": "Operator"}
            else:
                return False, "Invalid credentials (mock).", None

    # Replace the actual auth module with the mock for this test run
    # This is tricky to do if auth is imported directly at module level.
    # For a real test, you'd use unittest.mock.patch.
    # For this illustrative example, we'll assume if we run this file directly,
    # we might want to use a mock. A better way is to pass the auth_service to the dialog.

    # Let's assume for this direct run, we can't easily mock the imported `authentication`
    # So, this example will try to use the actual `auth.authentication`
    # which means `users_crud` and the DB setup would need to be working.

    app = QApplication(sys.argv)

    # Setup basic logging to see output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    # Ensure icons are loaded (if your main app does this, it might not be needed here)
    # import icons_rc

    dialog = LoginDialog()

    def handle_login_success(user_data):
        print(f"Login successful signal received! User: {user_data.get('username')}, Role: {user_data.get('role_name')}")

    dialog.login_successful.connect(handle_login_success)

    if dialog.exec_() == QDialog.Accepted:
        print("Login Dialog Accepted.")
        retrieved_user_data = dialog.get_user_data()
        if retrieved_user_data:
            print(f"Logged in user: {retrieved_user_data.get('username')}")
            print(f"User data: {retrieved_user_data}")
        else:
            print("Login accepted, but no user data returned (should not happen).")
    else:
        print("Login Dialog Cancelled or Rejected.")

    # sys.exit(app.exec_()) # Not needed if just testing dialog logic once
