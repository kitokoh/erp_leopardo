# dialogs/request_password_reset_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QDialogButtonBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Assuming password_reset_service will be accessible, e.g., via an auth_service module
# from auth import auth_service # Or directly: from auth.password_reset_service import PasswordResetService
from auth.password_reset_service import PasswordResetService


logger = logging.getLogger(__name__)

class RequestPasswordResetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Réinitialisation du mot de passe"))
        self.setWindowIcon(QIcon(":/icons/lock.svg")) # Assuming a lock icon exists
        self.setMinimumWidth(350)
        self.setModal(True)

        self.password_reset_service = PasswordResetService() # Instantiate the service

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        instruction_label = QLabel(
            self.tr("Veuillez entrer votre adresse e-mail. Si un compte est associé à cet e-mail, "
                    "nous vous enverrons des instructions pour réinitialiser votre mot de passe.")
        )
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(self.tr("Entrez votre adresse e-mail"))
        main_layout.addWidget(self.email_input)

        self.status_label = QLabel("") # For showing processing status or errors
        self.status_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton(self.tr("Envoyer la demande"))
        self.submit_button.setIcon(QIcon(":/icons/send.svg")) # Assuming send icon
        self.submit_button.clicked.connect(self._handle_submit)

        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.submit_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.email_input.returnPressed.connect(self.submit_button.click)


    def _handle_submit(self):
        email = self.email_input.text().strip()
        if not email:
            self.status_label.setText(self.tr("Veuillez entrer une adresse e-mail."))
            return

        # Basic email format validation (very simple)
        if "@" not in email or "." not in email.split("@")[-1]:
            self.status_label.setText(self.tr("Format d'e-mail invalide."))
            return

        self.status_label.setText(self.tr("Traitement en cours..."))
        self.submit_button.setEnabled(False)
        self.email_input.setEnabled(False)

        QApplication.processEvents() # Ensure UI updates

        try:
            success, message = self.password_reset_service.request_password_reset(email)

            if success:
                # Show the generic success/info message regardless of whether email was actually found/sent
                QMessageBox.information(self, self.tr("Demande envoyée"), message)
                self.accept() # Close the dialog
            else:
                # Show a more specific error if the service indicates a definite failure (not just "email not found")
                # However, request_password_reset is designed to return a generic success message for privacy.
                # If message implies an actual error (e.g., email service down), show it.
                if "erreur" in message.lower() or "impossible" in message.lower() or "failed" in message.lower() : # Heuristic
                    QMessageBox.warning(self, self.tr("Échec de la demande"), message)
                else: # Should be the generic privacy-preserving message
                     QMessageBox.information(self, self.tr("Demande envoyée"), message)
                self.status_label.setText("") # Clear processing message
                # If it was a true failure, don't close, let user retry or cancel.
                # If it was the generic "email sent if account exists", we might close.
                # For now, if not success, we keep dialog open and re-enable fields.
                # self.accept() # Only accept on clear success from service if that's the design
        except Exception as e:
            logger.error(f"Unexpected error in RequestPasswordResetDialog._handle_submit: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur inattendue est survenue."))
            self.status_label.setText(self.tr("Erreur inattendue."))
        finally:
            self.submit_button.setEnabled(True)
            self.email_input.setEnabled(True)

# For testing this dialog standalone
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    # Ensure db is initialized for service to work, and SMTP config exists in DB for email sending
    # This requires running from project root or having paths set up.
    # from app_setup import setup_logging, APP_ROOT_DIR, CONFIG
    # import db
    # setup_logging()
    # db.initialize_database(CONFIG)


    app = QApplication(sys.argv)
    dialog = RequestPasswordResetDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("Request Password Reset Dialog Accepted (implies email was 'sent' or user informed).")
    else:
        print("Request Password Reset Dialog Cancelled.")
    sys.exit(app.exec_())
"""
