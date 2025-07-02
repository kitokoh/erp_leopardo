# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QIcon
# No specific QtGui or QtCore imports noted as directly used by this class methods
# other than those implicitly handled by QtWidgets.

import db.cruds.freight_forwarders_crud as freight_forwarders_crud
import db.cruds.contacts_crud as contacts_crud
import db.cruds.entity_contacts_crud as entity_contacts_crud
from .contact_dialog import ContactDialog

class FreightForwarderDialog(QDialog):
    def __init__(self, forwarder_data=None, parent=None):
        super().__init__(parent)
        self.forwarder_data_initial = forwarder_data
        self.forwarder_id = None
        if self.forwarder_data_initial:
            self.forwarder_id = self.forwarder_data_initial.get('forwarder_id')

        self.setWindowTitle(self.tr("Ajouter/Modifier Transitaire"))
        self.setMinimumWidth(600) # Increased width
        self.setup_ui()
        if self.forwarder_data_initial:
            self.load_forwarder_data()
        else:
            self.update_contact_management_state(enabled=False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Freight Forwarder Details Group
        details_group = QGroupBox(self.tr("Détails du Transitaire"))
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        form_layout.addRow(self.tr("Nom:"), self.name_input)
        self.contact_person_input = QLineEdit()
        form_layout.addRow(self.tr("Personne à contacter:"), self.contact_person_input)
        self.phone_input = QLineEdit()
        form_layout.addRow(self.tr("Téléphone:"), self.phone_input)
        self.email_input = QLineEdit()
        form_layout.addRow(self.tr("Email:"), self.email_input)
        self.address_input = QLineEdit()
        form_layout.addRow(self.tr("Adresse:"), self.address_input)
        self.services_offered_input = QTextEdit()
        self.services_offered_input.setFixedHeight(60)
        form_layout.addRow(self.tr("Services Offerts:"), self.services_offered_input)
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)
        form_layout.addRow(self.tr("Notes:"), self.notes_input)

        details_group.setLayout(form_layout)
        main_layout.addWidget(details_group)

        # Associated Contacts Group
        contacts_group = QGroupBox(self.tr("Contacts Associés"))
        contacts_layout = QVBoxLayout()

        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5) # Name, Email, Phone, Role, Primary
        self.contacts_table.setHorizontalHeaderLabels([
            self.tr("Nom Affiché"), self.tr("Email"), self.tr("Téléphone"),
            self.tr("Rôle (Transitaire)"), self.tr("Principal")
        ])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contacts_table.doubleClicked.connect(self.handle_edit_contact_link)
        contacts_layout.addWidget(self.contacts_table)

        contact_buttons_layout = QHBoxLayout()
        self.add_contact_button = QPushButton(QIcon.fromTheme("list-add"), self.tr("Ajouter Contact"))
        self.edit_contact_button = QPushButton(QIcon.fromTheme("document-edit"), self.tr("Modifier Contact/Lien"))
        self.delete_link_button = QPushButton(QIcon.fromTheme("list-remove"), self.tr("Supprimer Lien"))

        contact_buttons_layout.addWidget(self.add_contact_button)
        contact_buttons_layout.addWidget(self.edit_contact_button)
        contact_buttons_layout.addWidget(self.delete_link_button)
        contacts_layout.addLayout(contact_buttons_layout)

        contacts_group.setLayout(contacts_layout)
        main_layout.addWidget(contacts_group)

        self.add_contact_button.clicked.connect(self.handle_add_contact_link)
        self.edit_contact_button.clicked.connect(self.handle_edit_contact_link)
        self.delete_link_button.clicked.connect(self.handle_delete_contact_link)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Enregistrer Transitaire"))
        self.button_box.button(QDialogButtonBox.Ok).setObjectName("primaryButton") # Keep if used for styling
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def update_contact_management_state(self, enabled: bool):
        self.contacts_table.setEnabled(enabled)
        self.add_contact_button.setEnabled(enabled)
        self.edit_contact_button.setEnabled(enabled)
        self.delete_link_button.setEnabled(enabled)

    def load_forwarder_data(self):
        self.name_input.setText(self.forwarder_data_initial.get('name', ''))
        self.contact_person_input.setText(self.forwarder_data_initial.get('contact_person', '')) # Keep for now
        self.phone_input.setText(self.forwarder_data_initial.get('phone', '')) # Keep for now
        self.email_input.setText(self.forwarder_data_initial.get('email', '')) # Keep for now
        self.address_input.setText(self.forwarder_data_initial.get('address', ''))
        self.services_offered_input.setPlainText(self.forwarder_data_initial.get('services_offered', ''))
        self.notes_input.setPlainText(self.forwarder_data_initial.get('notes', ''))

        if self.forwarder_id:
            self.load_associated_contacts()
            self.update_contact_management_state(enabled=True)
        else:
            self.update_contact_management_state(enabled=False)

    def load_associated_contacts(self):
        self.contacts_table.setRowCount(0)
        if not self.forwarder_id:
            return

        contacts = entity_contacts_crud.get_contacts_for_entity(self.forwarder_id, 'FreightForwarder')
        for contact_data in contacts:
            row_position = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row_position)

            name_item = QTableWidgetItem(contact_data.get('displayName', contact_data.get('name', 'N/A')))
            name_item.setData(Qt.UserRole, contact_data)
            self.contacts_table.setItem(row_position, 0, name_item)

            self.contacts_table.setItem(row_position, 1, QTableWidgetItem(contact_data.get('email', '')))
            self.contacts_table.setItem(row_position, 2, QTableWidgetItem(contact_data.get('phone', '')))
            self.contacts_table.setItem(row_position, 3, QTableWidgetItem(contact_data.get('role_in_entity', '')))

            is_primary_widget = QCheckBox()
            is_primary_widget.setChecked(bool(contact_data.get('is_primary', False)))
            is_primary_widget.setEnabled(False)
            self.contacts_table.setCellWidget(row_position, 4, is_primary_widget)

        self.contacts_table.resizeColumnsToContents()
        self.contacts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def handle_add_contact_link(self):
        if not self.forwarder_id:
            QMessageBox.information(self, self.tr("Information"), self.tr("Veuillez d'abord enregistrer le transitaire."))
            return

        contact_dialog = ContactDialog(manage_link_fields=True, parent=self)
        if contact_dialog.exec_() == QDialog.Accepted:
            contact_details = contact_dialog.get_contact_data()
            link_details = contact_dialog.get_link_data()

            new_contact_id = contacts_crud.add_contact(contact_details)
            if new_contact_id:
                entity_contacts_crud.link_contact_to_entity(
                    entity_id=self.forwarder_id,
                    entity_type='FreightForwarder',
                    contact_id=new_contact_id,
                    role_in_entity=link_details.get('role_in_entity'),
                    is_primary=link_details.get('is_primary', False),
                    can_receive_documents=link_details.get('can_receive_documents', True),
                    notes=link_details.get('notes')
                )
                self.load_associated_contacts()
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de créer le contact central."))

    def handle_edit_contact_link(self):
        selected_row = self.contacts_table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un contact à modifier."))
            return

        table_item = self.contacts_table.item(selected_row, 0)
        if not table_item: return

        full_contact_link_data = table_item.data(Qt.UserRole)
        if not full_contact_link_data or 'contact_id' not in full_contact_link_data or 'entity_contact_id' not in full_contact_link_data:
            QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("Données de contact/lien corrompues."))
            return

        contact_data_for_dialog = {k: v for k, v in full_contact_link_data.items() if k not in ['entity_contact_id', 'entity_id', 'entity_type', 'role_in_entity', 'is_primary', 'can_receive_documents', 'link_notes', 'link_created_at', 'link_updated_at']}
        link_data_for_dialog = {
            'role_in_entity': full_contact_link_data.get('role_in_entity'),
            'is_primary': full_contact_link_data.get('is_primary'),
            'can_receive_documents': full_contact_link_data.get('can_receive_documents'),
            'notes': full_contact_link_data.get('link_notes')
        }

        contact_dialog = ContactDialog(contact_data=contact_data_for_dialog, link_data=link_data_for_dialog, manage_link_fields=True, parent=self)

        if contact_dialog.exec_() == QDialog.Accepted:
            updated_contact_details = contact_dialog.get_contact_data()
            updated_link_details = contact_dialog.get_link_data()

            contacts_crud.update_contact(full_contact_link_data['contact_id'], updated_contact_details)
            entity_contacts_crud.update_entity_contact_link(full_contact_link_data['entity_contact_id'], updated_link_details)
            self.load_associated_contacts()

    def handle_delete_contact_link(self):
        selected_row = self.contacts_table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un lien de contact à supprimer."))
            return

        table_item = self.contacts_table.item(selected_row, 0)
        if not table_item: return

        full_contact_link_data = table_item.data(Qt.UserRole)
        entity_contact_id = full_contact_link_data.get('entity_contact_id')
        contact_name = full_contact_link_data.get('displayName', full_contact_link_data.get('name', 'ce contact'))

        if not entity_contact_id:
             QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("ID du lien de contact manquant."))
             return

        reply = QMessageBox.question(self, self.tr("Confirmation"),
                                     self.tr(f"Êtes-vous sûr de vouloir supprimer le lien avec {contact_name}?\nLe contact central ne sera pas supprimé."),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if entity_contacts_crud.unlink_contact_from_entity(entity_contact_id):
                self.load_associated_contacts()
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le lien."))

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "contact_person": self.contact_person_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "services_offered": self.services_offered_input.toPlainText().strip(),
            "notes": self.notes_input.toPlainText().strip()
        }

    def accept(self):
        data = self.get_data()
        if not data['name']:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le nom du transitaire est requis."))
            self.name_input.setFocus()
            return

        try:
            if self.forwarder_id: # Existing
                success = freight_forwarders_crud.update_freight_forwarder(self.forwarder_id, data)
                if success:
                    self.forwarder_data_initial.update(data)
                    self.forwarder_data_initial['forwarder_id'] = self.forwarder_id
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Transitaire mis à jour avec succès."))
                    super().accept()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de mettre à jour le transitaire."))
                    return
            else: # New
                new_id = freight_forwarders_crud.add_freight_forwarder(data)
                if new_id:
                    self.forwarder_id = new_id
                    self.forwarder_data_initial = data
                    self.forwarder_data_initial['forwarder_id'] = new_id
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Transitaire ajouté avec succès (ID: {0}). Vous pouvez maintenant ajouter des contacts.").format(new_id))
                    self.update_contact_management_state(enabled=True)
                    # super().accept() # Keep open for contact adding, similar to TransporterDialog
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible d'ajouter le transitaire."))
                    return

            # After successful save (add or update), handle the main contact logic
            if self.forwarder_id and (data.get('contact_person') or data.get('email') or data.get('phone')):
                self._handle_main_contact_from_direct_fields(data)

            super().accept() # Now accept the dialog
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def _handle_main_contact_from_direct_fields(self, forwarder_main_data):
        """
        Handles creating/linking a primary contact from direct form fields
        if no explicit primary contact is set via EntityContacts.
        """
        direct_contact_name = forwarder_main_data.get('contact_person','').strip()
        direct_email = forwarder_main_data.get('email','').strip()
        direct_phone = forwarder_main_data.get('phone','').strip()

        if not direct_contact_name and not direct_email and not direct_phone:
            return

        existing_contacts = entity_contacts_crud.get_contacts_for_entity(self.forwarder_id, 'FreightForwarder')
        primary_entity_contact = next((c for c in existing_contacts if c.get('is_primary')), None)

        if primary_entity_contact:
            return # Explicit primary contact already exists

        contact_to_link_id = None
        if direct_email:
            existing_central_contact = contacts_crud.get_contact_by_email(direct_email)
            if existing_central_contact:
                contact_to_link_id = existing_central_contact['contact_id']
                update_payload = {}
                if direct_contact_name and existing_central_contact.get('displayName') != direct_contact_name:
                    update_payload['displayName'] = direct_contact_name
                if direct_phone and existing_central_contact.get('phone') != direct_phone:
                    update_payload['phone'] = direct_phone
                if update_payload:
                    contacts_crud.update_contact(contact_to_link_id, update_payload)

        if not contact_to_link_id:
            contact_details = {
                'displayName': direct_contact_name,
                'name': direct_contact_name,
                'email': direct_email,
                'phone': direct_phone,
                'employee_status': 'external'
            }
            contact_to_link_id = contacts_crud.add_contact(contact_details)

        if contact_to_link_id:
            link_details = {
                'role_in_entity': self.tr("Contact Principal (auto)"),
                'is_primary': True,
                'can_receive_documents': True
            }
            already_linked = any(c['contact_id'] == contact_to_link_id for c in existing_contacts)
            if not already_linked:
                entity_contacts_crud.link_contact_to_entity(
                    entity_id=self.forwarder_id,
                    entity_type='FreightForwarder',
                    contact_id=contact_to_link_id,
                    **link_details
                )
            else:
                existing_link = next((c for c in existing_contacts if c['contact_id'] == contact_to_link_id), None)
                if existing_link and not existing_link.get('is_primary'):
                    entity_contacts_crud.update_entity_contact_link(existing_link['entity_contact_id'], link_details)

            self.load_associated_contacts()
