import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QSpacerItem, QSizePolicy, QFrame, QWidget, QCheckBox, QGridLayout
)
from PyQt5.QtGui import QPixmap, QFont, QIcon # Added QIcon
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from app.db.connection import get_db_connection
from app.db.cruds.users import users_crud
from app.services.auth import authentication
from app.security_module.biometric_auth import BiometricAuthenticator

import uuid
import logging # Added for logging
import random # Added for promotional text

class LoginWindow(QDialog):
    PROMOTIONAL_TEXTS = [
        "Streamline your client documentation and project management effortlessly.",
        "Secure, efficient, and professional document handling.",
        "Welcome! Let's get your documents organized.",
        "Unlock productivity with ClientDocManager.",
        "Your success, documented.",
        "Focus on your clients, we'll handle the paperwork."
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginWindow") # Set object name for the dialog

        self.setWindowTitle(self.tr("User Login"))
        self.setMinimumWidth(760)
        self.session_token = None
        self.current_user = None
        self.init_ui()

        # Load Remember Me state
        settings = QSettings()
        remember_me_active = settings.value("auth/remember_me_active", False, type=bool)
        self.remember_me_checkbox.setChecked(remember_me_active)
        # If active, could potentially auto-fill username, but token logic is for auto-login later
        if remember_me_active:
            saved_username = settings.value("auth/username", "")
            if saved_username:
                self.username_input.setText(saved_username)


    def init_ui(self):
        # Main horizontal layout
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # --- Left Side (Form Area) ---
        left_widget = QWidget()
        left_widget.setObjectName("loginFormArea")
        left_widget.setFixedWidth(360) # Set fixed width for the form area

        self.form_layout = QVBoxLayout(left_widget)
        self.form_layout.setContentsMargins(30, 40, 30, 40)
        self.form_layout.setSpacing(15)



        # Logo
        logo_label = QLabel()
        pixmap = QPixmap()
        if pixmap.isNull():
            logo_label.setText(self.tr("Company Logo"))
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("font-size: 14px; color: #888;")
        else:
            logo_label.setPixmap(pixmap.scaledToWidth(120, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
        self.form_layout.addWidget(logo_label)

        # Title Label
        title_label = QLabel(self.tr("Welcome Back!"))
        title_label.setObjectName("dialogHeaderLabel")
        title_label.setAlignment(Qt.AlignCenter)
        self.form_layout.addWidget(title_label)

        # Subtitle or instruction
        instruction_label = QLabel(self.tr("Please enter your credentials to log in."))
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("font-size: 10pt; color: #6c757d;")
        self.form_layout.addWidget(instruction_label)

        self.form_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(self.tr("Username"))
        self.username_input.textChanged.connect(self.check_biometric_options_for_user) # Check on text change

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr("Password"))
        self.password_input.setEchoMode(QLineEdit.Password)

        self.form_layout.addWidget(QLabel(self.tr("Username:")))
        self.form_layout.addWidget(self.username_input)
        self.form_layout.addWidget(QLabel(self.tr("Password:")))
        self.form_layout.addWidget(self.password_input)

        # Remember Me and Forgot Password (placeholder)
        extra_options_layout = QHBoxLayout()
        self.remember_me_checkbox = QCheckBox(self.tr("Remember Me"))
        # forgot_password_button = QPushButton(self.tr("Forgot Password?"))
        # forgot_password_button.setObjectName("linkButton")
        extra_options_layout.addWidget(self.remember_me_checkbox)
        extra_options_layout.addStretch(1)
        # extra_options_layout.addWidget(forgot_password_button)
        self.form_layout.addLayout(extra_options_layout)


        # Login Buttons Layout (Password and Biometric)
        login_buttons_layout = QGridLayout() # Using QGridLayout for flexibility

        self.login_button = QPushButton(self.tr("Login with Password"))
        self.login_button.setObjectName("primaryButton")
        self.login_button.setMinimumHeight(35)
        self.login_button.clicked.connect(self.handle_password_login)
        login_buttons_layout.addWidget(self.login_button, 0, 0, 1, 2) # Span 2 columns

        self.fingerprint_login_button = QPushButton("👆 " + self.tr("Login with Fingerprint"))
        self.fingerprint_login_button.setObjectName("secondaryButton") # Or a specific biometric button style
        self.fingerprint_login_button.setMinimumHeight(35)
        self.fingerprint_login_button.clicked.connect(self.handle_fingerprint_login)
        self.fingerprint_login_button.setVisible(False) # Initially hidden
        login_buttons_layout.addWidget(self.fingerprint_login_button, 1, 0, 1, 2) # Span 2 columns

        self.face_login_button = QPushButton("😀 " + self.tr("Login with Face"))
        self.face_login_button.setObjectName("secondaryButton")
        self.face_login_button.setMinimumHeight(35)
        self.face_login_button.clicked.connect(self.handle_face_login)
        self.face_login_button.setVisible(False) # Initially hidden
        login_buttons_layout.addWidget(self.face_login_button, 2, 0, 1, 2) # Row 2

        # self.voice_login_button = QPushButton("🗣️ " + self.tr("Login with Voice"))
        # self.voice_login_button.setObjectName("secondaryButton")
        # self.voice_login_button.setMinimumHeight(35)
        # self.voice_login_button.clicked.connect(self.handle_voice_login)
        # self.voice_login_button.setVisible(False) # Initially hidden
        # login_buttons_layout.addWidget(self.voice_login_button, 3, 0, 1, 2) # Row 3

        self.form_layout.addLayout(login_buttons_layout)


        self.form_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Register Button (as a link)
        register_button = QPushButton(self.tr("Don't have an account? Create one"))
        register_button.setObjectName("linkButton")
        register_button.setCursor(Qt.PointingHandCursor)
        register_button.clicked.connect(self.open_registration_window)
        self.form_layout.addWidget(register_button, 0, Qt.AlignCenter)

        self.form_layout.addStretch(1)

        # --- Right Side (Promo Area) ---
        promo_frame = QFrame()
        promo_frame.setObjectName("promoAreaFrame")
        # promo_frame.setStyleSheet("#promoAreaFrame { background-color: #007bff; border-left: 1px solid #ddd; }") # Style from QSS
        promo_frame.setMinimumWidth(300)

        promo_layout = QVBoxLayout(promo_frame)
        promo_layout.setContentsMargins(30, 40, 30, 40) # Consistent margins
        promo_layout.setSpacing(20)
        promo_layout.setAlignment(Qt.AlignCenter)

        self.promoHeaderLabel = QLabel(self.tr("ClientDocManager"))
        self.promoHeaderLabel.setObjectName("promoHeaderLabel")
        self.promoHeaderLabel.setAlignment(Qt.AlignCenter) # Set alignment in Python
        self.promoHeaderLabel.setWordWrap(True)

        self.promoTextLabel = QLabel()
        self.promoTextLabel.setObjectName("promoTextLabel")
        self.promoTextLabel.setAlignment(Qt.AlignCenter) # Set alignment in Python
        self.promoTextLabel.setWordWrap(True)

        # New Order: Stretch, Header, Spacing, Text, Stretch
        promo_layout.addStretch(1)
        promo_layout.addWidget(self.promoHeaderLabel)
        promo_layout.addSpacing(10)
        promo_layout.addWidget(self.promoTextLabel)
        promo_layout.addStretch(1)

        self.update_promo_text() # Set initial random text

        # Add left and right widgets to main horizontal layout
        main_h_layout.addWidget(left_widget, 1)

        main_h_layout.addWidget(promo_frame, 1) # Give promo area a stretch factor of 1

        # No need to call self.setLayout() as main_h_layout was passed `self`
        self.biometric_authenticator = BiometricAuthenticator(window_handle_provider=lambda: self.winId()) # Pass window handle provider
        self.check_biometric_options_for_user() # Initial check if username is pre-filled

    def check_biometric_options_for_user(self):
        """
        Checks if biometric options are available and enabled for the entered username
        and updates the visibility of biometric login buttons.
        """
        username = self.username_input.text().strip()
        self.fingerprint_login_button.setVisible(False)
        if hasattr(self, 'face_login_button'): self.face_login_button.setVisible(False)

        if not username:
            return

        db_session = None
        try:
            db_session = get_db_connection()
            user = users_crud.get_user_by_username(db_session, username)
            if user:
                # Fingerprint
                if self.biometric_authenticator.is_method_available("fingerprint") and user.is_fingerprint_auth_enabled:
                    self.fingerprint_login_button.setVisible(True)
                    logging.info(f"Fingerprint login option shown for user {username}")
                # Face
                if hasattr(self, 'face_login_button') and self.biometric_authenticator.is_method_available("face") and user.is_face_auth_enabled:
                    self.face_login_button.setVisible(True)
                    logging.info(f"Face login option shown for user {username}")
            else:
                logging.debug(f"User {username} not found, biometric options hidden.")
        except Exception as e:
            logging.error(f"Error checking biometric options for {username}: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()


    def _perform_login_success(self, user_data: dict):
        """Shared logic for successful login (password or biometric)."""
        self.current_user = user_data
        self.session_token = uuid.uuid4().hex

        authentication.set_current_user(user_data)

        # "Remember Me" is now handled entirely within authentication.login,
        # but for biometric login, we might need to decide if it implies remember_me.
        # For now, we assume biometric does not trigger remember_me token generation.

        logging.info(f"Login successful for user: {user_data['username']}. Session token: {self.session_token}")
        self.accept()


    def handle_password_login(self):
        """Handles login attempt using username and password."""
        logger.info("LOGIN_WINDOW: handle_password_login called.") # ADDED
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, self.tr("Login Failed"), self.tr("Username and password are required."))
            return

        # Use the main authentication.login function
        success, message, user_data, license_details = authentication.login(
            username,
            password,
            remember_me=self.remember_me_checkbox.isChecked()
        )

        if success:
            # The global current_user is set by authentication.login()
            self.current_user = authentication.get_current_user()
            self.accept()
        else:
            self.current_user = None
            QMessageBox.warning(self, self.tr("Login Failed"), message or self.tr("Invalid username or password."))

    def handle_fingerprint_login(self):
        self._handle_biometric_login("fingerprint")

    def handle_face_login(self):
        self._handle_biometric_login("face")

    def handle_voice_login(self):
        self._handle_biometric_login("voice")

    def _handle_biometric_login(self, method: str):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, self.tr("Login Failed"), self.tr(f"Username is required for {method} login."))
            return

        db_session = None
        try:
            db_session = get_db_connection()
            user = users_crud.get_user_by_username(db_session, username)

            if not user:
                QMessageBox.warning(self, self.tr("Login Failed"), self.tr("User not found."))
                return

            if not getattr(user, f'is_{method}_auth_enabled', False):
                QMessageBox.warning(self, self.tr("Login Failed"), self.tr(f"{method.capitalize()} login is not enabled for this user."))
                return

            # Placeholder for UI prompt, actual prompt is handled by authenticator
            QMessageBox.information(self, self.tr(f"{method.capitalize()} Login"), self.tr(f"Please use your {method} sensor."))

            # The actual biometric verification call
            verify_function = getattr(self.biometric_authenticator, f"verify_{method}")
            if verify_function(user.user_id):
                logging.info(f"{method.capitalize()} login successful for user: {username}")
                users_crud.record_login_time(db_session, user.user_id)

                # Convert the ORM object to a dict for _perform_login_success
                user_data_dict = {
                    'user_id': user.user_id, 'username': user.username, 'full_name': user.full_name,
                    'email': user.email, 'role_id': user.role_id,
                    'role_name': user.role.role_name if user.role else 'N/A'
                }
                self._perform_login_success(user_data_dict)
            else:
                QMessageBox.warning(self, self.tr("Login Failed"), self.tr(f"{method.capitalize()} verification failed."))
                logging.warning(f"{method.capitalize()} login failed for user: {username}")

        except Exception as e:
            logging.error(f"Error during {method} login for {username}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Error"), self.tr("An unexpected error occurred during login."))
        finally:
            if db_session:
                db_session.close()


    def get_session_token(self) -> str | None:
        # This might be less relevant if session is managed globally by auth.authentication
        return self.session_token

    def get_current_user(self) -> dict | None:
        return self.current_user

    def open_registration_window(self):
        self.hide()
        # Pass self.parent() if LoginWindow itself has a parent (e.g. the main app window, though not typical for initial login)
        # Or pass None if RegistrationWindow should not have a specific Qt parent from LoginWindow's context.
        # If LoginWindow is the top-level window before main app shows, self.parent() might be None.
        # For simplicity, creating RegistrationWindow potentially without a direct Qt parent from here,
        # or with self if it makes sense in the application structure.
        # Let's assume self (LoginWindow instance) can be a logical parent.
        from .registration_window import  RegistrationWindow
        reg_window = RegistrationWindow(parent=self)
        reg_window.exec_()
        self.show()

    def update_promo_text(self):
        selected_promo_text = random.choice(LoginWindow.PROMOTIONAL_TEXTS)
        if hasattr(self, 'promoTextLabel'): # Ensure label exists
            self.promoTextLabel.setText(self.tr(selected_promo_text))

    def showEvent(self, event):
        super().showEvent(event)
        self.update_promo_text() # Update promo text when dialog is shown

    # The __main__ block might have issues running directly from here
    # if db.py relies on other parts of the application being initialized,
    # or if sys.path isn't set up to find 'db' when run as a script from the 'auth' directory.
    # However, when LoginWindow is imported and used by main.py (or equivalent),
    # the 'import db' should work as expected.
if __name__ == '__main__':
    # This is for testing the LoginWindow independently
    # For this test to work directly, you might need to adjust PYTHONPATH
    # to include the root directory, e.g., PYTHONPATH=. python auth/login_window.py
    # or run as a module: python -m auth.login_window

    # A simple way to test if db can be imported if this script is run directly:
    # try:
    #     import db # db.py is no longer directly used for user auth here
    #     print("db.py found and imported for test.")
    # except ImportError:
    #     print("Failed to import db.py directly. Ensure PYTHONPATH is set or run as a module from root.")
        # Fallback to a mock for direct execution if db is not found
        # class PlaceholderDB: # No longer needed as we import users_crud_instance
        #     def verify_user_password(self, username, password):
        #         print(f"Placeholder verify_user_password called with {username}, {password}")
        #         if username == "test" and password == "password": return {"username": "test"}
        #         return None
        # db = PlaceholderDB()


    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
