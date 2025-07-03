import sys
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt
from security_module.biometric_auth import BiometricAuthenticator
# Import get_current_user_id. Assuming this page is displayed only when a user is logged in.
from auth.authentication import get_current_user_id

logger = logging.getLogger(__name__)

class SecuritySettingsPage(QWidget):
    def __init__(self, parent=None): # Added parent parameter
        super().__init__(parent) # Pass parent to QWidget constructor
        # Pass a lambda that returns this widget's window handle ID
        self.authenticator = BiometricAuthenticator(window_handle_provider=lambda: self.winId())
        self.current_user_id = get_current_user_id() # Get the logged-in user's ID

        if not self.current_user_id:
            # This page should ideally not be accessible if no user is logged in.
            # The UI will be disabled by checks within init_ui and load_settings_for_user.
            # Display a message or disable functionality if somehow reached.
            logger.error("SecuritySettingsPage loaded without a logged-in user.")
            # self.init_ui_no_user() # Or simply return / raise error
            # For now, we proceed, but buttons will be disabled if current_user_id is None.

        self.init_ui()
        self.load_settings_for_user()

    def init_ui_no_user(self): # Not actively called, logic moved into init_ui/load_settings
        """Initialize a restricted UI if no user is logged in."""
        self.setWindowTitle(self.tr('Security Settings'))
        layout = QVBoxLayout()
        error_label = QLabel(self.tr("User not logged in. Security settings cannot be configured."))
        error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_label)
        self.setLayout(layout)
        self.setEnabled(False)


    def init_ui(self):
        self.setWindowTitle(self.tr('Security Settings - Biometric Authentication'))
        # self.setGeometry(300, 300, 450, 350) # Adjusted size

        main_layout = QVBoxLayout(self)

        # --- Fingerprint Section ---
        fingerprint_group = QGroupBox(self.tr("Fingerprint Authentication"))
        fingerprint_layout = QVBoxLayout(fingerprint_group)

        self.cb_enable_fingerprint = QCheckBox(self.tr("Enable Fingerprint Authentication"))
        self.cb_enable_fingerprint.toggled.connect(self.toggle_fingerprint_auth)
        fingerprint_layout.addWidget(self.cb_enable_fingerprint)

        self.btn_enroll_fingerprint = QPushButton(self.tr("Enroll Fingerprint (Simulated)"))
        self.btn_enroll_fingerprint.clicked.connect(self.enroll_fingerprint)
        fingerprint_layout.addWidget(self.btn_enroll_fingerprint)

        self.btn_test_fingerprint = QPushButton(self.tr("Test Fingerprint Login (Simulated)"))
        self.btn_test_fingerprint.clicked.connect(self.test_fingerprint_login)
        fingerprint_layout.addWidget(self.btn_test_fingerprint)

        main_layout.addWidget(fingerprint_group)

        # --- Face Section (Placeholder/Disabled for now) ---
        face_group = QGroupBox(self.tr("Face Authentication (Coming Soon)"))
        face_layout = QVBoxLayout(face_group)
        self.cb_enable_face = QCheckBox(self.tr("Enable Face Authentication"))
        self.btn_enroll_face = QPushButton(self.tr("Enroll Face (Simulated)"))
        self.btn_test_face = QPushButton(self.tr("Test Face Login (Simulated)"))

        self.cb_enable_face.toggled.connect(self.toggle_face_auth)
        self.btn_enroll_face.clicked.connect(self.enroll_face)
        self.btn_test_face.clicked.connect(self.test_face_login)

        face_layout.addWidget(self.cb_enable_face)
        face_layout.addWidget(self.btn_enroll_face)
        face_layout.addWidget(self.btn_test_face)
        # face_group.setEnabled(False) # Enable this group now
        main_layout.addWidget(face_group)

        # --- Voice Section (Placeholder/Disabled for now) ---
        voice_group = QGroupBox(self.tr("Voice Authentication (Coming Soon)"))
        voice_layout = QVBoxLayout(voice_group)
        self.cb_enable_voice = QCheckBox(self.tr("Enable Voice Authentication"))
        self.btn_enroll_voice = QPushButton(self.tr("Enroll Voice (Simulated)"))
        self.btn_test_voice = QPushButton(self.tr("Test Voice Login (Simulated)"))

        self.cb_enable_voice.toggled.connect(self.toggle_voice_auth)
        self.btn_enroll_voice.clicked.connect(self.enroll_voice)
        self.btn_test_voice.clicked.connect(self.test_voice_login)

        voice_layout.addWidget(self.cb_enable_voice)
        voice_layout.addWidget(self.btn_enroll_voice)
        voice_layout.addWidget(self.btn_test_voice)
        # voice_group.setEnabled(False) # Enable this group now
        main_layout.addWidget(voice_group)

        main_layout.addStretch(1) # Pushes groups to the top

        self.status_label = QLabel(self.tr("Load your settings or enroll a new biometric method."))
        main_layout.addWidget(self.status_label)

        # Disable controls if no user is logged in
        if not self.current_user_id:
            fingerprint_group.setEnabled(False)
            face_group.setEnabled(False)
            voice_group.setEnabled(False)
            self.status_label.setText(self.tr("No user logged in. Settings unavailable."))


    def load_settings_for_user(self):
        """
        Loads the current user's biometric settings from the database via BiometricAuthenticator
        and updates the UI elements (checkboxes, button states) accordingly.
        Also checks for hardware/software availability for each method.
        """
        fp_enabled, face_enabled, voice_enabled = False, False, False # Initialize to False

        if not self.current_user_id:
            # This case should disable all controls, already handled in init_ui if self.current_user_id is None at that point.
            # If it becomes None later (e.g. user logs out while page is open), this ensures UI updates.
            self.cb_enable_fingerprint.setChecked(False)
            self.btn_enroll_fingerprint.setEnabled(False)
            self.btn_test_fingerprint.setEnabled(False)
            # Also disable other methods' controls here
            return

        is_available = self.authenticator.is_method_available("fingerprint")
        if not is_available:
            self.cb_enable_fingerprint.setEnabled(False)
            self.cb_enable_fingerprint.setText(self.tr("Enable Fingerprint Authentication (Not available on this system)"))
            self.btn_enroll_fingerprint.setEnabled(False)
            self.btn_test_fingerprint.setEnabled(False)
            self.status_label.setText(self.tr("Fingerprint hardware/software not detected."))
            return

        is_enabled = self.authenticator.is_method_enabled_for_user(self.current_user_id, "fingerprint")

        self.cb_enable_fingerprint.blockSignals(True) # Avoid triggering toggle_fingerprint_auth
        self.cb_enable_fingerprint.setChecked(is_enabled)
        self.cb_enable_fingerprint.blockSignals(False)

        self.btn_enroll_fingerprint.setEnabled(is_enabled) # Can only enroll if the main checkbox is ticked
        self.btn_test_fingerprint.setEnabled(is_enabled) # Can only test if enabled

        if is_enabled:
            self.status_label.setText(self.tr("Fingerprint authentication is enabled."))
        else:
            self.status_label.setText(self.tr("Fingerprint authentication is disabled."))

    def toggle_fingerprint_auth(self, checked: bool):
        """
        Handles the state change of the fingerprint authentication checkbox.
        Enables/disables fingerprint auth for the user via BiometricAuthenticator.
        Updates UI elements accordingly.
        """
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            self.cb_enable_fingerprint.setChecked(not checked) # Revert
            return

        if checked:
            # User wants to enable. If not yet enrolled, they must enroll first.
            # For simulation, we assume they must click "Enroll" separately.
            # The actual enabling in DB happens after successful enrollment.
            # Here, we just update UI state.
            # If it's already enabled in DB (e.g. from previous session), this is fine.
            # If it's not enabled in DB, they need to enroll.
            is_actually_enabled_in_db = self.authenticator.is_method_enabled_for_user(self.current_user_id, "fingerprint")
            if not is_actually_enabled_in_db:
                 QMessageBox.information(self, self.tr("Fingerprint Setup"),
                                        self.tr("Please enroll your fingerprint to use this feature."))
                 self.btn_enroll_fingerprint.setEnabled(True) # Enable enroll button
                 self.btn_test_fingerprint.setEnabled(False) # Test only after enrollment
                 # Don't set it to enabled in DB yet, enrollment does that.
                 # The checkbox state reflects user's *intent* to use it, if available.
            else:
                # Already enrolled and enabled in DB, UI reflects this.
                self.btn_enroll_fingerprint.setEnabled(True) # Allow re-enrollment
                self.btn_test_fingerprint.setEnabled(True)
            self.status_label.setText(self.tr("Fingerprint authentication selected. Enroll if needed."))

        else:
            # User wants to disable
            if self.authenticator.disable_fingerprint(self.current_user_id):
                QMessageBox.information(self, self.tr("Fingerprint Disabled"), self.tr("Fingerprint authentication has been disabled."))
                self.status_label.setText(self.tr("Fingerprint authentication disabled."))
                self.btn_enroll_fingerprint.setEnabled(False)
                self.btn_test_fingerprint.setEnabled(False)
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Could not disable fingerprint authentication in the database."))
                self.cb_enable_fingerprint.blockSignals(True)
                self.cb_enable_fingerprint.setChecked(True) # Revert UI if DB operation failed
                self.cb_enable_fingerprint.blockSignals(False)

    def enroll_fingerprint(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        # Simulate enrollment process
        # In a real app, this would trigger OS dialogs.
        # For now, BiometricAuthenticator.enroll_fingerprint handles the simulation and DB update.
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("Simulated Fingerprint Enrollment"))
        msg_box.setText(self.tr("This is a simulation.\nImagine you are now scanning your fingerprint with an OS dialog.\n\nDo you want to simulate successful enrollment?"))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            # The authenticator's enroll_fingerprint method will handle DB update
            if self.authenticator.enroll_fingerprint(self.current_user_id):
                QMessageBox.information(self, self.tr("Enrollment"), self.tr("Fingerprint enrollment (simulated) successful!"))
                self.status_label.setText(self.tr("Fingerprint enrolled and enabled."))
                self.btn_test_fingerprint.setEnabled(True) # Enable test button
                self.cb_enable_fingerprint.setChecked(True) # Ensure checkbox is checked
            else:
                QMessageBox.warning(self, self.tr("Enrollment Failed"), self.tr("Fingerprint enrollment (simulated) failed or DB update error."))
                self.status_label.setText(self.tr("Fingerprint enrollment failed."))
        else:
            QMessageBox.information(self, self.tr("Enrollment Cancelled"), self.tr("Fingerprint enrollment (simulated) cancelled by user."))
            self.status_label.setText(self.tr("Fingerprint enrollment cancelled."))
            # If they cancel enrollment, ensure it's not marked as enabled in DB if it wasn't already
            if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "fingerprint"):
                self.cb_enable_fingerprint.setChecked(False)

    def enroll_fingerprint(self):
        """
        Initiates the (simulated) fingerprint enrollment process for the current user.
        Calls BiometricAuthenticator which in turn would call the OS handler.
        """
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        # UI now provides a more explicit simulation prompt.
        # The BiometricAuthenticator.enroll_fingerprint will call the OS handler,
        # which for now also simulates/guides.
        QMessageBox.information(self,
            self.tr("Fingerprint Enrollment"),
            self.tr("You will now be guided through fingerprint enrollment.\n"
                    "For Windows/macOS, this usually involves system prompts or settings.\n"
                    "This application will update once the OS-level enrollment is (simulated as) complete.")
        )

        # The actual call to BiometricAuthenticator which triggers the handler.
        # The handler itself (windows_handler, macos_handler) currently simulates OS interaction
        # and returns True if the method is available, assuming user completes enrollment via OS.
        if self.authenticator.enroll_fingerprint(self.current_user_id): # Pass window handle if handler needs it.
            QMessageBox.information(self, self.tr("Enrollment Update"), self.tr("Fingerprint enrollment process initiated. Please follow any system prompts.\nThe application has marked fingerprint auth as enabled."))
            self.status_label.setText(self.tr("Fingerprint enrolled and enabled."))
            self.btn_test_fingerprint.setEnabled(True)
            self.cb_enable_fingerprint.blockSignals(True)
            self.cb_enable_fingerprint.setChecked(True)
            self.cb_enable_fingerprint.blockSignals(False)
        else:
            QMessageBox.warning(self, self.tr("Enrollment Failed"), self.tr("Fingerprint enrollment could not be completed or method not available."))
            self.status_label.setText(self.tr("Fingerprint enrollment failed or was cancelled."))
            # Optionally, uncheck if it's not truly enabled in DB
            if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "fingerprint"):
                 self.cb_enable_fingerprint.blockSignals(True)
                 self.cb_enable_fingerprint.setChecked(False)
                 self.cb_enable_fingerprint.blockSignals(False)


    def test_fingerprint_login(self):
        """
        Tests the (simulated) fingerprint login for the current user.
        """
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "fingerprint"):
            QMessageBox.warning(self, self.tr("Not Enabled"), self.tr("Fingerprint authentication is not enabled or enrolled for your account."))
            return

        self.status_label.setText(self.tr("Testing Fingerprint Login..."))
        QApplication.processEvents()

        # Simulate verification process - BiometricAuthenticator handles calling the OS handler
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("Simulated Fingerprint Verification"))
        msg_box.setText(self.tr("This is a simulation.\nImagine the OS is now asking for your fingerprint.\n\nDo you want to simulate successful verification?"))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        reply = msg_box.exec_()

        simulated_verification_result = (reply == QMessageBox.Yes)

        # In a real app, self.authenticator.verify_fingerprint(self.current_user_id) would be called.
        # For this simulation, we use the dialog's result directly.
        # We can call the authenticator's verify method to log, but use our simulated result.

        # Log the attempt (even if we override result for simulation clarity)
        self.authenticator.verify_fingerprint(self.current_user_id)


        if simulated_verification_result:
            QMessageBox.information(self, self.tr("Fingerprint Login"), self.tr("Fingerprint login (simulated) successful!"))
            self.status_label.setText(self.tr("Fingerprint login test successful."))
        else:
            QMessageBox.warning(self, self.tr("Fingerprint Login Failed"), self.tr("Fingerprint login (simulated) failed."))
            self.status_label.setText(self.tr("Fingerprint login test failed."))

    # Placeholder methods for Face and Voice (to be implemented similarly)
    # def test_voice_auth(self): # This will be replaced by test_voice_login
    #     QMessageBox.information(self, self.tr("Coming Soon"), self.tr("Voice authentication test is not yet implemented."))

    # --- Face Authentication Methods ---
    def toggle_face_auth(self, checked):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            self.cb_enable_face.setChecked(not checked) # Revert
            return

        if checked:
            is_actually_enabled_in_db = self.authenticator.is_method_enabled_for_user(self.current_user_id, "face")
            if not is_actually_enabled_in_db:
                 QMessageBox.information(self, self.tr("Face Setup"),
                                        self.tr("Please enroll your face to use this feature."))
                 self.btn_enroll_face.setEnabled(True)
                 self.btn_test_face.setEnabled(False)
            else:
                self.btn_enroll_face.setEnabled(True)
                self.btn_test_face.setEnabled(True)
            self.status_label.setText(self.tr("Face authentication selected. Enroll if needed."))
        else:
            if self.authenticator.disable_face(self.current_user_id):
                QMessageBox.information(self, self.tr("Face Disabled"), self.tr("Face authentication has been disabled."))
                self.status_label.setText(self.tr("Face authentication disabled."))
                self.btn_enroll_face.setEnabled(False)
                self.btn_test_face.setEnabled(False)
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Could not disable face authentication in the database."))
                self.cb_enable_face.blockSignals(True)
                self.cb_enable_face.setChecked(True) # Revert
                self.cb_enable_face.blockSignals(False)

    def enroll_face(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("Simulated Face Enrollment"))
        msg_box.setText(self.tr("This is a simulation.\nImagine you are now looking at your camera for face enrollment.\n\nDo you want to simulate successful enrollment?"))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            if self.authenticator.enroll_face(self.current_user_id):
                QMessageBox.information(self, self.tr("Enrollment"), self.tr("Face enrollment (simulated) successful!"))
                self.status_label.setText(self.tr("Face enrolled and enabled."))
                self.btn_test_face.setEnabled(True)
                self.cb_enable_face.setChecked(True)
            else:
                QMessageBox.warning(self, self.tr("Enrollment Failed"), self.tr("Face enrollment (simulated) failed or DB update error."))
                self.status_label.setText(self.tr("Face enrollment failed."))
        else:
            QMessageBox.information(self, self.tr("Enrollment Cancelled"), self.tr("Face enrollment (simulated) cancelled by user."))
            self.status_label.setText(self.tr("Face enrollment cancelled."))
            if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "face"):
                self.cb_enable_face.setChecked(False)

    def test_face_login(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "face"):
            QMessageBox.warning(self, self.tr("Not Enabled"), self.tr("Face authentication is not enabled or enrolled for your account."))
            return

        self.status_label.setText(self.tr("Testing Face Login (Simulated)..."))
        QApplication.processEvents()

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("Simulated Face Verification"))
        msg_box.setText(self.tr("This is a simulation.\nImagine the OS is now using your camera for face verification.\n\nDo you want to simulate successful verification?"))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        reply = msg_box.exec_()

        simulated_verification_result = (reply == QMessageBox.Yes)
        self.authenticator.verify_face(self.current_user_id) # Log attempt

        if simulated_verification_result:
            QMessageBox.information(self, self.tr("Face Login"), self.tr("Face login (simulated) successful!"))
            self.status_label.setText(self.tr("Face login test successful."))
        else:
            QMessageBox.warning(self, self.tr("Face Login Failed"), self.tr("Face login (simulated) failed."))
            self.status_label.setText(self.tr("Face login test failed."))

    def load_settings_for_user(self): # Overwrite or extend existing
        if not self.current_user_id:
            self.cb_enable_fingerprint.setChecked(False)
            self.btn_enroll_fingerprint.setEnabled(False)
            self.btn_test_fingerprint.setEnabled(False)
            self.cb_enable_face.setChecked(False)
            self.btn_enroll_face.setEnabled(False)
            self.btn_test_face.setEnabled(False)
            # Also disable other methods' controls here
            return

        # Fingerprint
        fp_available = self.authenticator.is_method_available("fingerprint")
        if not fp_available:
            self.cb_enable_fingerprint.setEnabled(False)
            self.cb_enable_fingerprint.setText(self.tr("Enable Fingerprint Authentication (Not available)"))
            self.btn_enroll_fingerprint.setEnabled(False)
            self.btn_test_fingerprint.setEnabled(False)
        else:
            self.cb_enable_fingerprint.setEnabled(True)
            self.cb_enable_fingerprint.setText(self.tr("Enable Fingerprint Authentication"))
            fp_enabled = self.authenticator.is_method_enabled_for_user(self.current_user_id, "fingerprint")
            self.cb_enable_fingerprint.blockSignals(True)
            self.cb_enable_fingerprint.setChecked(fp_enabled)
            self.cb_enable_fingerprint.blockSignals(False)
            self.btn_enroll_fingerprint.setEnabled(fp_enabled)
            self.btn_test_fingerprint.setEnabled(fp_enabled)

        # Face
        face_available = self.authenticator.is_method_available("face")
        face_group = self.cb_enable_face.parentWidget() # Get the QGroupBox
        if not face_available:
            self.cb_enable_face.setEnabled(False)
            self.cb_enable_face.setText(self.tr("Enable Face Authentication (Not available)"))
            self.btn_enroll_face.setEnabled(False)
            self.btn_test_face.setEnabled(False)
            if face_group: face_group.setEnabled(True) # Keep group enabled to show message
        else:
            if face_group: face_group.setEnabled(True) # Ensure group is enabled
            self.cb_enable_face.setEnabled(True)
            self.cb_enable_face.setText(self.tr("Enable Face Authentication"))
            face_enabled = self.authenticator.is_method_enabled_for_user(self.current_user_id, "face")
            self.cb_enable_face.blockSignals(True)
            self.cb_enable_face.setChecked(face_enabled)
            self.cb_enable_face.blockSignals(False)
            self.btn_enroll_face.setEnabled(face_enabled)
            self.btn_test_face.setEnabled(face_enabled)

        # Update status label based on overall state
        if fp_enabled and face_enabled: # Example, can be more nuanced
            self.status_label.setText(self.tr("Fingerprint & Face authentication are enabled."))
        elif fp_enabled:
            self.status_label.setText(self.tr("Fingerprint authentication is enabled."))
        elif face_enabled:
            self.status_label.setText(self.tr("Face authentication is enabled."))
        else:
            self.status_label.setText(self.tr("Biometric authentication is disabled or not enrolled."))

        # Voice
        voice_available = self.authenticator.is_method_available("voice")
        voice_group = self.cb_enable_voice.parentWidget()
        if not voice_available:
            self.cb_enable_voice.setEnabled(False)
            self.cb_enable_voice.setText(self.tr("Enable Voice Authentication (Not available)"))
            self.btn_enroll_voice.setEnabled(False)
            self.btn_test_voice.setEnabled(False)
            if voice_group: voice_group.setEnabled(True) # Keep group enabled to show message
        else:
            if voice_group: voice_group.setEnabled(True) # Ensure group is enabled
            self.cb_enable_voice.setEnabled(True)
            self.cb_enable_voice.setText(self.tr("Enable Voice Authentication"))
            voice_enabled = self.authenticator.is_method_enabled_for_user(self.current_user_id, "voice")
            self.cb_enable_voice.blockSignals(True)
            self.cb_enable_voice.setChecked(voice_enabled)
            self.cb_enable_voice.blockSignals(False)
            self.btn_enroll_voice.setEnabled(voice_enabled)
            self.btn_test_voice.setEnabled(voice_enabled)

        # Update status label based on overall state (simplified, can be more granular)
        enabled_methods = []
        if self.cb_enable_fingerprint.isChecked(): enabled_methods.append("Fingerprint")
        if self.cb_enable_face.isChecked(): enabled_methods.append("Face")
        if self.cb_enable_voice.isChecked(): enabled_methods.append("Voice")

        if enabled_methods:
            self.status_label.setText(self.tr("{} authentication is enabled.").format(" & ".join(enabled_methods)))
        else:
            self.status_label.setText(self.tr("No biometric authentication methods are currently enabled."))


    # --- Voice Authentication Methods ---
    def toggle_voice_auth(self, checked):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            self.cb_enable_voice.setChecked(not checked) # Revert
            return

        if checked:
            is_actually_enabled_in_db = self.authenticator.is_method_enabled_for_user(self.current_user_id, "voice")
            if not is_actually_enabled_in_db:
                 QMessageBox.information(self, self.tr("Voice Setup"),
                                        self.tr("Please enroll your voice to use this feature."))
                 self.btn_enroll_voice.setEnabled(True)
                 self.btn_test_voice.setEnabled(False)
            else:
                self.btn_enroll_voice.setEnabled(True)
                self.btn_test_voice.setEnabled(True)
            self.status_label.setText(self.tr("Voice authentication selected. Enroll if needed."))
        else:
            if self.authenticator.disable_voice(self.current_user_id):
                QMessageBox.information(self, self.tr("Voice Disabled"), self.tr("Voice authentication has been disabled."))
                self.status_label.setText(self.tr("Voice authentication disabled."))
                self.btn_enroll_voice.setEnabled(False)
                self.btn_test_voice.setEnabled(False)
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Could not disable voice authentication in the database."))
                self.cb_enable_voice.blockSignals(True)
                self.cb_enable_voice.setChecked(True) # Revert
                self.cb_enable_voice.blockSignals(False)

    def enroll_voice(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("Simulated Voice Enrollment"))
        msg_box.setText(self.tr("This is a simulation.\nImagine you are now speaking a passphrase for voice enrollment.\n\nDo you want to simulate successful enrollment?"))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            if self.authenticator.enroll_voice(self.current_user_id):
                QMessageBox.information(self, self.tr("Enrollment"), self.tr("Voice enrollment (simulated) successful!"))
                self.status_label.setText(self.tr("Voice enrolled and enabled."))
                self.btn_test_voice.setEnabled(True)
                self.cb_enable_voice.setChecked(True)
            else:
                QMessageBox.warning(self, self.tr("Enrollment Failed"), self.tr("Voice enrollment (simulated) failed or DB update error."))
                self.status_label.setText(self.tr("Voice enrollment failed."))
        else:
            QMessageBox.information(self, self.tr("Enrollment Cancelled"), self.tr("Voice enrollment (simulated) cancelled by user."))
            self.status_label.setText(self.tr("Voice enrollment cancelled."))
            if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "voice"):
                self.cb_enable_voice.setChecked(False)

    def test_voice_login(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Error"), self.tr("No user logged in."))
            return

        if not self.authenticator.is_method_enabled_for_user(self.current_user_id, "voice"):
            QMessageBox.warning(self, self.tr("Not Enabled"), self.tr("Voice authentication is not enabled or enrolled for your account."))
            return

        self.status_label.setText(self.tr("Testing Voice Login (Simulated)..."))
        QApplication.processEvents()

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("Simulated Voice Verification"))
        msg_box.setText(self.tr("This is a simulation.\nImagine the OS is now listening for your voice.\n\nDo you want to simulate successful verification?"))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        reply = msg_box.exec_()

        simulated_verification_result = (reply == QMessageBox.Yes)
        self.authenticator.verify_voice(self.current_user_id) # Log attempt

        if simulated_verification_result:
            QMessageBox.information(self, self.tr("Voice Login"), self.tr("Voice login (simulated) successful!"))
            self.status_label.setText(self.tr("Voice login test successful."))
        else:
            QMessageBox.warning(self, self.tr("Voice Login Failed"), self.tr("Voice login (simulated) failed."))
            self.status_label.setText(self.tr("Voice login test failed."))


if __name__ == '__main__':
    # --- Mocking for __main__ START ---
    # This is crucial for standalone testing if imports from other modules fail.
    import types

    # Mock auth.authentication
    mock_auth_module = types.ModuleType('auth.authentication')
    def mock_get_current_user_id():
        print("MOCK auth.authentication.get_current_user_id() CALLED, returning 'test_user_main'")
        return "test_user_main" # Simulate a logged-in user
    mock_auth_module.get_current_user_id = mock_get_current_user_id
    sys.modules['auth.authentication'] = mock_auth_module

    # Mock db.cruds.users_crud (already in biometric_auth.py's __main__, but good to have here too)
    # This mock needs to be consistent with the one in biometric_auth.py if they interact.
    class MockUsersCrudMain:
        _user_bio_settings_main = {}
        def get_biometric_auth_status(self, user_id):
            print(f"MOCK_CRUD_SETTINGS_PAGE: get_biometric_auth_status for {user_id}")
            return self._user_bio_settings_main.get(user_id, {
                'is_fingerprint_auth_enabled': False, 'fingerprint_template_id': None,
                'is_face_auth_enabled': False, 'face_template_id': None,
                'is_voice_auth_enabled': False, 'voice_profile_id': None,
            })

        def set_biometric_auth_status(self, user_id, method, enabled, template_id=None):
            print(f"MOCK_CRUD_SETTINGS_PAGE: set_biometric_auth_status for {user_id}, method {method}, enabled {enabled}, template_id {template_id}")
            if user_id not in self._user_bio_settings_main:
                self._user_bio_settings_main[user_id] = {}

            field_enabled = f"is_{method}_auth_enabled"
            field_template = f"{method}_template_id" if method != "voice" else "voice_profile_id"

            self._user_bio_settings_main[user_id][field_enabled] = enabled
            self._user_bio_settings_main[user_id][field_template] = template_id if enabled else None
            return True

    mock_users_crud_module = types.ModuleType('db.cruds.users_crud')
    mock_users_crud_module.get_biometric_auth_status = MockUsersCrudMain().get_biometric_auth_status
    mock_users_crud_module.set_biometric_auth_status = MockUsersCrudMain().set_biometric_auth_status

    # Ensure db and db.cruds modules exist in sys.modules before assigning users_crud to db.cruds
    if 'db' not in sys.modules:
        sys.modules['db'] = types.ModuleType('db')
    if 'db.cruds' not in sys.modules:
        sys.modules['db.cruds'] = types.ModuleType('db.cruds')

    sys.modules['db.cruds.users_crud'] = mock_users_crud_module
    # This makes `from db.cruds import users_crud` work in biometric_auth.py when this script is run.
    # --- Mocking for __main__ END ---

    app = QApplication(sys.argv)
    # The page now expects to be able to call get_current_user_id() at __init__
    ex = SecuritySettingsPage()
    ex.show()
    sys.exit(app.exec_())
