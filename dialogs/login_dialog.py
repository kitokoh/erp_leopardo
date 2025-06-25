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
        self.login_button.setIcon(QIcon(":/icons/log-in.svg")) # Assuming log-in.svg exists
        self.login_button.setObjectName("primaryButton") # For styling

        cancel_button = self.button_box.addButton(QDialogButtonBox.Cancel)
        cancel_button.setText(self.tr("Annuler"))
        # cancel_button.setIcon(QIcon(":/icons/dialog-cancel.svg")) # Standard icon often set by style

        self.button_box.accepted.connect(self._attempt_login)
        self.button_box.rejected.connect(self.reject) # Standard reject closes dialog

        main_layout.addWidget(self.button_box)

        self.username_input.setFocus() # Set focus to username field initially
        self._load_remembered_user()


    def _load_remembered_user(self):
        """Checks for a remembered user and pre-fills the form."""
        remembered_username = authentication.get_remembered_user()
        if remembered_username:
            self.username_input.setText(remembered_username)
            self.remember_me_checkbox.setChecked(True)
            self.password_input.setFocus() # Move focus to password if username is filled
            logger.info(f"Pre-filled login form for remembered user: {remembered_username}")
        else:
            self.username_input.setFocus() # Default focus if no user remembered

    def _attempt_login(self):
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
            success, error_message, user_info = authentication.login(username, password, remember_me=remember_me_checked)

            if success and user_info:
                logger.info(f"Login successful for user: {username}. Remember Me: {remember_me_checked}")
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
