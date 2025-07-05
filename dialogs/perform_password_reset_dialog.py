# dialogs/perform_password_reset_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QDialogButtonBox, QHBoxLayout, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from auth.password_reset_service import PasswordResetService

logger = logging.getLogger(__name__)

class PerformPasswordResetDialog(QDialog):
    def __init__(self, initial_token: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Réinitialiser le mot de passe"))
        self.setWindowIcon(QIcon(":/icons/lock.svg"))
        self.setMinimumWidth(400)
        self.setModal(True)

        self.password_reset_service = PasswordResetService()

        self._init_ui()

        if initial_token:
            self.token_input.setText(initial_token)
            self.new_password_input.setFocus() # Focus password if token is pre-filled

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText(self.tr("Jeton de réinitialisation reçu par e-mail"))
        form_layout.addRow(self.tr("Jeton de réinitialisation :"), self.token_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText(self.tr("Nouveau mot de passe"))
        form_layout.addRow(self.tr("Nouveau mot de passe :"), self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText(self.tr("Confirmer le nouveau mot de passe"))
        form_layout.addRow(self.tr("Confirmer le mot de passe :"), self.confirm_password_input)

        main_layout.addLayout(form_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Réinitialiser"))
        self.button_box.button(QDialogButtonBox.Ok).setIcon(QIcon(":/icons/save.svg")) # Assuming save icon
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))

        self.button_box.accepted.connect(self._handle_submit)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Allow Enter key to trigger OK
        self.token_input.returnPressed.connect(self.button_box.button(QDialogButtonBox.Ok).click)
        self.new_password_input.returnPressed.connect(self.button_box.button(QDialogButtonBox.Ok).click)
        self.confirm_password_input.returnPressed.connect(self.button_box.button(QDialogButtonBox.Ok).click)


    def _handle_submit(self):
        token = self.token_input.text().strip()
        new_password = self.new_password_input.text() # No strip, allow spaces if user wants (though not typical)
        confirm_password = self.confirm_password_input.text()

        if not token:
            self.status_label.setText(self.tr("Veuillez entrer le jeton de réinitialisation."))
            self.token_input.setFocus()
            return

        if not new_password:
            self.status_label.setText(self.tr("Veuillez entrer un nouveau mot de passe."))
            self.new_password_input.setFocus()
            return

        if new_password != confirm_password:
            self.status_label.setText(self.tr("Les mots de passe ne correspondent pas."))
            self.confirm_password_input.setFocus()
            self.confirm_password_input.selectAll()
            return

        # Basic password strength (example: min length) - can be expanded
        if len(new_password) < 6:
            self.status_label.setText(self.tr("Le mot de passe doit contenir au moins 6 caractères."))
            self.new_password_input.setFocus()
            self.new_password_input.selectAll()
            return

        self.status_label.setText(self.tr("Traitement en cours..."))
        self.button_box.setEnabled(False) # Disable both OK and Cancel during processing

        QApplication.processEvents()

        try:
            success, message = self.password_reset_service.reset_password_with_token(token, new_password)
            if success:
                QMessageBox.information(self, self.tr("Succès"), message)
                self.accept()
            else:
                QMessageBox.warning(self, self.tr("Échec"), message)
                self.status_label.setText("") # Clear "Processing..."
        except Exception as e:
            logger.error(f"Unexpected error in PerformPasswordResetDialog._handle_submit: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur inattendue est survenue."))
            self.status_label.setText(self.tr("Erreur inattendue."))
        finally:
            self.button_box.setEnabled(True)


# For testing this dialog standalone
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    # from app_setup import setup_logging, APP_ROOT_DIR, CONFIG
    # import db
    # setup_logging()
    # db.initialize_database(CONFIG)

    app = QApplication(sys.argv)

    # To test with a pre-filled token (e.g., from a simulated link click):
    # test_token = "example_reset_token_from_email"
    # dialog = PerformPasswordResetDialog(initial_token=test_token)

    dialog = PerformPasswordResetDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("Perform Password Reset Dialog Accepted (Password successfully reset).")
    else:
        print("Perform Password Reset Dialog Cancelled.")
    sys.exit(app.exec_())

"""
