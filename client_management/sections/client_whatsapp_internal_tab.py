# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon
# SendWhatsAppDialog will be accessed via self.section_widget.main_widget
import db as db_manager


class ClientWhatsAppInternalTab(QWidget):
    def __init__(self, client_info, section_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.section_widget = section_widget # Reference to parent ClientInfoSection
        self.main_widget = section_widget.main_widget # Grandparent ClientMainWidget

        self.SendWhatsAppDialog = getattr(self.main_widget, 'SendWhatsAppDialog', None)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.open_whatsapp_dialog_btn = QPushButton(self.tr("Envoyer message WhatsApp..."))
        # Assuming a WhatsApp or phone icon is available, e.g., ":/icons/whatsapp.svg" or ":/icons/phone.svg"
        self.open_whatsapp_dialog_btn.setText("💬")
        self.open_whatsapp_dialog_btn.clicked.connect(self.open_send_whatsapp_dialog_action)
        layout.addWidget(self.open_whatsapp_dialog_btn)
        layout.addStretch()

    def open_send_whatsapp_dialog_action(self):
        if not self.SendWhatsAppDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant d'envoi WhatsApp n'est pas configuré."))
            return

        client_uuid = self.client_info.get("client_id")
        client_name = self.client_info.get("client_name", "")
        primary_phone = ""
        fallback_phone = ""

        if not client_uuid:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        try:
            # Assuming db_manager is accessible; ideally, pass it or use a method from main_widget
            if hasattr(self.main_widget, 'db_manager'):
                 contacts = self.main_widget.db_manager.get_contacts_for_client(client_uuid, limit=10, offset=0)
            else: # Fallback for direct import if needed, though less ideal for modularity
                 contacts = db_manager.get_contacts_for_client(client_uuid, limit=10, offset=0)

            if contacts:
                for contact in contacts:
                    if contact.get('phone'):
                        if not fallback_phone: fallback_phone = contact['phone']
                        if contact.get('is_primary_for_client'):
                            primary_phone = contact['phone']
                            break
                selected_phone = primary_phone if primary_phone else fallback_phone
                if selected_phone:
                    dialog = self.SendWhatsAppDialog(phone_number=selected_phone, client_name=client_name, parent=self)
                    dialog.exec_()
                else:
                    QMessageBox.information(self, self.tr("Aucun Numéro"), self.tr("Aucun numéro de téléphone trouvé pour ce client."))
            else:
                QMessageBox.information(self, self.tr("Aucun Contact"), self.tr("Aucun contact trouvé pour ce client."))
        except Exception as e:
            logging.error(f"Error fetching contacts for WhatsApp: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Contacts"), self.tr("Impossible de récupérer les informations de contact: {0}").format(str(e)))

    def tr(self, text, disambiguation=None, n=-1):
        if hasattr(self.main_widget, 'tr'):
            return self.main_widget.tr(text, disambiguation, n)
        from PyQt5.QtWidgets import QApplication
        return QApplication.translate("ClientWhatsAppInternalTab", text, disambiguation, n)
