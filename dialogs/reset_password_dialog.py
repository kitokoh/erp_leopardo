# dialogs/reset_password_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QDialogButtonBox, QLabel
)
from PyQt5.QtGui import QIcon

logger = logging.getLogger(__name__)

class ResetPasswordDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username_to_reset = username
        self._new_password = ""

        self.setWindowTitle(self.tr("Réinitialiser le mot de passe pour ") + username)
        self.setWindowIcon(QIcon(":/icons/lock.svg")) # Placeholder
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.info_label = QLabel(self.tr("Réinitialisation du mot de passe pour : <b>{0}</b>").format(self.username_to_reset))
        main_layout.addWidget(self.info_label)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.tr("Nouveau mot de passe:"), self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.tr("Confirmer le mot de passe:"), self.confirm_password_input)

        # Allow submission on Enter from confirm field
        self.confirm_password_input.returnPressed.connect(self._validate_and_accept)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Réinitialiser"))
        self.button_box.button(QDialogButtonBox.Ok).setIcon(QIcon(":/icons/save.svg")) # Placeholder
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))

        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.new_password_input.setFocus()

    def _validate_and_accept(self):
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not new_password:
            QMessageBox.warning(self, self.tr("Mot de Passe Requis"),
                                self.tr("Le nouveau mot de passe ne peut pas être vide."))
            self.new_password_input.setFocus()
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, self.tr("Non Concordance"),
                                self.tr("Les mots de passe ne correspondent pas."))
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            return

        # Basic complexity check (example: at least 8 characters)
        if len(new_password) < 8:
            QMessageBox.warning(self, self.tr("Mot de Passe Trop Court"),
                                self.tr("Le mot de passe doit contenir au moins 8 caractères."))
            self.new_password_input.setFocus()
            return

        self._new_password = new_password
        self.accept()

    def get_new_password(self) -> str:
        return self._new_password

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    dialog = ResetPasswordDialog(username="testuser")
    if dialog.exec_() == QDialog.Accepted:
        print(f"New password for testuser: {dialog.get_new_password()}")
    else:
        print("Password reset cancelled.")
```
