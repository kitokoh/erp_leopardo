# -*- coding: utf-8 -*-
import logging
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QAbstractItemView, QHeaderView, QMessageBox, QDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
# from ..dialogs import ContactDialog # Will be passed or accessed via section_widget.main_widget

class ClientContactsInternalTab(QWidget):
    CONTACT_PAGE_LIMIT = 15

    def __init__(self, client_info, section_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.section_widget = section_widget # Reference to parent ClientInfoSection
        self.main_widget = section_widget.main_widget # Grandparent ClientMainWidget

        self.current_contact_offset = 0
        self.total_contacts_count = 0

        self.ContactDialog = getattr(self.main_widget, 'ContactDialog', None)

        self._setup_ui()
        self.load_contacts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5)
        self.contacts_table.setHorizontalHeaderLabels([
            self.tr("Nom"), self.tr("Email"), self.tr("Téléphone"),
            self.tr("Position"), self.tr("Principal")
        ])
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.setAlternatingRowColors(True)
        self.contacts_table.cellDoubleClicked.connect(self.edit_contact)

        self.contacts_empty_label = QLabel(self.tr("Aucun contact ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
        self.contacts_empty_label.setAlignment(Qt.AlignCenter)
        font_empty = self.contacts_empty_label.font(); font_empty.setPointSize(10)
        self.contacts_empty_label.setFont(font_empty)

        layout.addWidget(self.contacts_empty_label)
        layout.addWidget(self.contacts_table)

        pagination_layout = QHBoxLayout()
        self.prev_contact_button = QPushButton("<< Précédent")
        self.prev_contact_button.setObjectName("paginationButton")
        self.prev_contact_button.clicked.connect(self.prev_contact_page)
        self.contact_page_info_label = QLabel("Page 1 / 1")
        self.contact_page_info_label.setObjectName("paginationLabel")
        self.next_contact_button = QPushButton("Suivant >>")
        self.next_contact_button.setObjectName("paginationButton")
        self.next_contact_button.clicked.connect(self.next_contact_page)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_contact_button)
        pagination_layout.addWidget(self.contact_page_info_label)
        pagination_layout.addWidget(self.next_contact_button)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        btn_layout = QHBoxLayout()
        self.add_contact_btn = QPushButton(self.tr("Ajouter")); self.add_contact_btn.setIcon(QIcon(":/icons/user-plus.svg"))
        self.add_contact_btn.clicked.connect(self.add_contact); btn_layout.addWidget(self.add_contact_btn)
        self.edit_contact_btn = QPushButton(self.tr("Modifier")); self.edit_contact_btn.setIcon(QIcon(":/icons/pencil.svg"))
        self.edit_contact_btn.clicked.connect(self.edit_contact); btn_layout.addWidget(self.edit_contact_btn)
        self.remove_contact_btn = QPushButton(self.tr("Supprimer")); self.remove_contact_btn.setIcon(QIcon(":/icons/trash.svg"))
        self.remove_contact_btn.setObjectName("dangerButton"); self.remove_contact_btn.clicked.connect(self.remove_contact); btn_layout.addWidget(self.remove_contact_btn)
        layout.addLayout(btn_layout)

        self.update_buttons_state()


    def load_contacts(self):
        self.contacts_empty_label.setVisible(True)
        self.contacts_table.setVisible(False)
        self.contacts_table.setRowCount(0)

        client_uuid = self.client_info.get("client_id")
        if not client_uuid:
            self.update_contact_pagination_controls()
            self.update_buttons_state()
            return

        try:
            self.total_contacts_count = db_manager.get_contacts_for_client_count(client_id=client_uuid)
            contacts_data = db_manager.get_contacts_for_client(
                client_id=client_uuid,
                limit=self.CONTACT_PAGE_LIMIT,
                offset=self.current_contact_offset
            ) or []

            if not contacts_data and self.current_contact_offset == 0: # No contacts at all
                self.contacts_empty_label.setVisible(True)
                self.contacts_table.setVisible(False)
            else:
                self.contacts_empty_label.setVisible(False)
                self.contacts_table.setVisible(True)
                self.contacts_table.setRowCount(len(contacts_data))
                for row, contact in enumerate(contacts_data):
                    name_item = QTableWidgetItem(contact.get('name', 'N/A'))
                    name_item.setData(Qt.UserRole, {
                        'contact_id': contact.get('contact_id'),
                        'client_contact_id': contact.get('client_contact_id')
                    })
                    self.contacts_table.setItem(row, 0, name_item)
                    self.contacts_table.setItem(row, 1, QTableWidgetItem(contact.get('email', '')))
                    self.contacts_table.setItem(row, 2, QTableWidgetItem(contact.get('phone', '')))
                    self.contacts_table.setItem(row, 3, QTableWidgetItem(contact.get('position', '')))
                    primary_text = self.tr("Oui") if contact.get('is_primary_for_client') else self.tr("Non")
                    primary_item = QTableWidgetItem(primary_text)
                    primary_item.setTextAlignment(Qt.AlignCenter)
                    self.contacts_table.setItem(row, 4, primary_item)
        except Exception as e:
            logging.error(f"Error loading contacts in ClientContactsInternalTab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Erreur de chargement des contacts:\n{0}").format(str(e)))
            self.total_contacts_count = 0
        finally:
            self.update_contact_pagination_controls()
            self.update_buttons_state()

    def add_contact(self):
        client_uuid = self.client_info.get("client_id")
        if not client_uuid or not self.ContactDialog: return
        dialog = self.ContactDialog(client_uuid, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_contact_offset = 0 # Reset to first page
            self.load_contacts()

    def edit_contact(self, row=None, column=None):
        current_row = self.contacts_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un contact à modifier."))
            return

        name_item = self.contacts_table.item(current_row, 0)
        if not name_item or not self.ContactDialog: return

        item_data = name_item.data(Qt.UserRole)
        contact_id = item_data.get('contact_id')
        if not contact_id: return

        client_uuid = self.client_info.get("client_id")
        full_contact_details = db_manager.get_contact_by_id(contact_id)
        if not full_contact_details: return

        client_contact_link_info = db_manager.get_specific_client_contact_link_details(client_uuid, contact_id)
        if client_contact_link_info:
            full_contact_details['is_primary_for_client'] = client_contact_link_info.get('is_primary_for_client', False)
            full_contact_details['client_contact_id'] = client_contact_link_info.get('client_contact_id')

        dialog = self.ContactDialog(client_id=client_uuid, contact_data=full_contact_details, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_contacts()

    def remove_contact(self):
        current_row = self.contacts_table.currentRow()
        if current_row < 0: return

        name_item = self.contacts_table.item(current_row, 0)
        if not name_item: return

        item_data = name_item.data(Qt.UserRole)
        client_contact_id = item_data.get('client_contact_id')
        contact_name = name_item.text()
        if not client_contact_id: return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer le lien vers le contact '{0}' pour ce client?").format(contact_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unlink_contact_from_client_by_link_id(client_contact_id):
                QMessageBox.information(self, self.tr("Succès"), self.tr("Lien vers le contact '{0}' supprimé.").format(contact_name))
                self.load_contacts()
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Échec de la suppression du lien."))

    def prev_contact_page(self):
        if self.current_contact_offset > 0:
            self.current_contact_offset -= self.CONTACT_PAGE_LIMIT
            self.load_contacts()

    def next_contact_page(self):
        if (self.current_contact_offset + self.CONTACT_PAGE_LIMIT) < self.total_contacts_count:
            self.current_contact_offset += self.CONTACT_PAGE_LIMIT
            self.load_contacts()

    def update_contact_pagination_controls(self):
        total_pages = math.ceil(self.total_contacts_count / self.CONTACT_PAGE_LIMIT) if self.total_contacts_count > 0 else 1
        current_page = (self.current_contact_offset // self.CONTACT_PAGE_LIMIT) + 1
        self.contact_page_info_label.setText(f"Page {current_page} / {total_pages}")
        self.prev_contact_button.setEnabled(self.current_contact_offset > 0)
        self.next_contact_button.setEnabled((self.current_contact_offset + self.CONTACT_PAGE_LIMIT) < self.total_contacts_count)

    def update_buttons_state(self):
        has_selection = bool(self.contacts_table.selectedItems())
        self.edit_contact_btn.setEnabled(has_selection)
        self.remove_contact_btn.setEnabled(has_selection)

    def tr(self, text, disambiguation=None, n=-1):
        if hasattr(self.main_widget, 'tr'):
            return self.main_widget.tr(text, disambiguation, n)
        from PyQt5.QtWidgets import QApplication
        return QApplication.translate("ClientContactsInternalTab", text, disambiguation, n)
