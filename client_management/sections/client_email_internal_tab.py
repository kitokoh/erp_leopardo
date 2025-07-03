# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
# SendEmailDialog will be accessed via self.section_widget.main_widget

class ClientEmailInternalTab(QWidget):
    def __init__(self, client_info, section_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.section_widget = section_widget # Reference to parent ClientInfoSection
        self.main_widget = section_widget.main_widget # Grandparent ClientMainWidget

        self.SendEmailDialog = getattr(self.main_widget, 'SendEmailDialog', None)
        self.config = getattr(self.main_widget, 'config', None)


        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.open_email_dialog_btn = QPushButton(self.tr("Composer un Email..."))
        self.open_email_dialog_btn.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg")))
        self.open_email_dialog_btn.clicked.connect(self.open_send_email_dialog_action)
        layout.addWidget(self.open_email_dialog_btn)
        layout.addStretch()

    def open_send_email_dialog_action(self):
        if not self.SendEmailDialog or not self.config:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant d'envoi d'email n'est pas configuré."))
            return

        # Determine primary email for the client (simplified)
        # This logic might need to be more robust or centralized
        primary_email = ""
        client_uuid = self.client_info.get("client_id")
        if client_uuid:
            # Assume db_manager is accessible; ideally, pass it or use a method from main_widget
            if hasattr(self.main_widget, 'db_manager'): # Check if main_widget has db_manager
                contacts = self.main_widget.db_manager.get_contacts_for_client(client_uuid)
                if contacts:
                    for contact in contacts:
                        if contact.get('is_primary_for_client') and contact.get('email'):
                            primary_email = contact['email']
                            break
                    if not primary_email and contacts[0].get('email'):
                        primary_email = contacts[0]['email']
            else: # Fallback or log error if db_manager isn't directly accessible
                logging.warning("db_manager not accessible via main_widget in ClientEmailInternalTab")


        dialog = self.SendEmailDialog(
            client_email=primary_email,
            config=self.config,
            client_id=client_uuid,
            parent=self
        )
        dialog.exec_()

    def tr(self, text, disambiguation=None, n=-1):
        if hasattr(self.main_widget, 'tr'):
            return self.main_widget.tr(text, disambiguation, n)
        from PyQt5.QtWidgets import QApplication
        return QApplication.translate("ClientEmailInternalTab", text, disambiguation, n)
