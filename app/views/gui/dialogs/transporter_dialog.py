# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QIcon
# No specific QtGui or QtCore imports noted as directly used by this class methods
# other than those implicitly handled by QtWidgets (e.g QPushButton via QDialogButtonBox).

from app.db.cruds.misc import transporters_crud
from app.db.cruds.misc.contacts_crud import add_contact, update_contact, get_contact_by_email
from app.db.cruds.misc.entity_contacts_crud import get_contacts_for_entity, link_contact_to_entity, update_entity_contact_link, unlink_contact_from_entity
from .contact_dialog import ContactDialog # Assuming contact_dialog.py is in the same directory

class TransporterDialog(QDialog):
    def __init__(self, transporter_data=None, parent=None):
        super().__init__(parent)
        self.transporter_data_initial = transporter_data # Store initial data
        self.transporter_id = None # Will be set if editing or after adding a new one
        if self.transporter_data_initial:
            self.transporter_id = self.transporter_data_initial.get('transporter_id')

        self.setWindowTitle(self.tr("Ajouter/Modifier Transporteur"))
        self.setMinimumWidth(600) # Increased width for contacts section
        self.setup_ui()
        if self.transporter_data_initial:
            self.load_transporter_data()
        else:
            # New transporter, disable contact management until saved
            self.update_contact_management_state(enabled=False)


    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Transporter Details Group
        details_group = QGroupBox(self.tr("Détails du Transporteur"))
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
        self.service_area_input = QLineEdit()
        form_layout.addRow(self.tr("Zone de service:"), self.service_area_input)
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(80)
        form_layout.addRow(self.tr("Notes:"), self.notes_input)

        self.latitude_input = QLineEdit()
        form_layout.addRow(self.tr("Latitude:"), self.latitude_input)
        self.longitude_input = QLineEdit()
        form_layout.addRow(self.tr("Longitude:"), self.longitude_input)
        self.current_cargo_input = QTextEdit() # Using QTextEdit for potentially longer text
        self.current_cargo_input.setFixedHeight(60)
        form_layout.addRow(self.tr("Current Cargo:"), self.current_cargo_input)

        details_group.setLayout(form_layout)
        main_layout.addWidget(details_group)

        # Associated Contacts Group
        contacts_group = QGroupBox(self.tr("Contacts Associés"))
        contacts_layout = QVBoxLayout()

        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5) # Name, Email, Phone, Role, Primary
        self.contacts_table.setHorizontalHeaderLabels([
            self.tr("Nom Affiché"), self.tr("Email"), self.tr("Téléphone"),
            self.tr("Rôle (Transporteur)"), self.tr("Principal")
        ])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contacts_table.doubleClicked.connect(self.handle_edit_contact_link) # Edit on double click
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

        # Connect contact button signals (deferred to __init__ or a setup_connections method)
        self.add_contact_button.clicked.connect(self.handle_add_contact_link)
        self.edit_contact_button.clicked.connect(self.handle_edit_contact_link)
        self.delete_link_button.clicked.connect(self.handle_delete_contact_link)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Enregistrer Transporteur"))
        self.button_box.button(QDialogButtonBox.Ok).setObjectName("primaryButton")
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

    def load_transporter_data(self):
        # Load main transporter data
        self.name_input.setText(self.transporter_data_initial.get('name', ''))
        self.contact_person_input.setText(self.transporter_data_initial.get('contact_person', '')) # Keep for now, may deprecate
        self.phone_input.setText(self.transporter_data_initial.get('phone', '')) # Keep for now
        self.email_input.setText(self.transporter_data_initial.get('email', '')) # Keep for now
        self.address_input.setText(self.transporter_data_initial.get('address', ''))
        self.service_area_input.setText(self.transporter_data_initial.get('service_area', ''))
        self.notes_input.setPlainText(self.transporter_data_initial.get('notes', ''))
        self.latitude_input.setText(str(self.transporter_data_initial.get('latitude', '')))
        self.longitude_input.setText(str(self.transporter_data_initial.get('longitude', '')))
        self.current_cargo_input.setPlainText(self.transporter_data_initial.get('current_cargo', ''))

        if self.transporter_id:
            self.load_associated_contacts()
            self.update_contact_management_state(enabled=True)
        else:
            self.update_contact_management_state(enabled=False)

    def load_associated_contacts(self):
        self.contacts_table.setRowCount(0) # Clear existing rows
        if not self.transporter_id:
            return

        contacts = get_contacts_for_entity(self.transporter_id, 'Transporter')
        for contact_data in contacts:
            row_position = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row_position)

            # Store the full contact_data (including link_id etc.) in the first item for retrieval
            name_item = QTableWidgetItem(contact_data.get('displayName', contact_data.get('name', 'N/A')))
            name_item.setData(Qt.UserRole, contact_data) # UserRole stores all data for this contact+link
            self.contacts_table.setItem(row_position, 0, name_item)

            self.contacts_table.setItem(row_position, 1, QTableWidgetItem(contact_data.get('email', '')))
            self.contacts_table.setItem(row_position, 2, QTableWidgetItem(contact_data.get('phone', '')))
            self.contacts_table.setItem(row_position, 3, QTableWidgetItem(contact_data.get('role_in_entity', '')))

            is_primary_widget = QCheckBox()
            is_primary_widget.setChecked(bool(contact_data.get('is_primary', False)))
            is_primary_widget.setEnabled(False) # Display only
            self.contacts_table.setCellWidget(row_position, 4, is_primary_widget)

        self.contacts_table.resizeColumnsToContents()
        self.contacts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


    def handle_add_contact_link(self):
        if not self.transporter_id:
            QMessageBox.information(self, self.tr("Information"), self.tr("Veuillez d'abord enregistrer le transporteur."))
            return

        contact_dialog = ContactDialog(manage_link_fields=True, parent=self)
        if contact_dialog.exec_() == QDialog.Accepted:
            contact_details = contact_dialog.get_contact_data()
            link_details = contact_dialog.get_link_data()

            # Add to central Contacts table
            # TODO: Consider if user_id should be passed to add_contact
            new_contact_id = add_contact(contact_details)
            if new_contact_id:
                # Link to this transporter
                link_contact_to_entity(
                    entity_id=self.transporter_id,
                    entity_type='Transporter',
                    contact_id=new_contact_id,
                    role_in_entity=link_details.get('role_in_entity'),
                    is_primary=link_details.get('is_primary', False),
                    can_receive_documents=link_details.get('can_receive_documents', True),
                    notes=link_details.get('notes')
                )
                self.load_associated_contacts() # Refresh table
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de créer le contact central."))

    def handle_edit_contact_link(self):
        selected_row = self.contacts_table.currentRow()
        if selected_row < 0:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un contact à modifier."))
            return

        # Retrieve the full data stored in UserRole
        table_item = self.contacts_table.item(selected_row, 0)
        if not table_item: return

        full_contact_link_data = table_item.data(Qt.UserRole)
        if not full_contact_link_data or 'contact_id' not in full_contact_link_data or 'entity_contact_id' not in full_contact_link_data:
            QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("Données de contact/lien corrompues."))
            return

        # Prepare data for ContactDialog
        # contact_data for central contact fields
        contact_data_for_dialog = {k: v for k, v in full_contact_link_data.items() if k not in ['entity_contact_id', 'entity_id', 'entity_type', 'role_in_entity', 'is_primary', 'can_receive_documents', 'link_notes', 'link_created_at', 'link_updated_at']}

        # link_data for link-specific fields
        link_data_for_dialog = {
            'role_in_entity': full_contact_link_data.get('role_in_entity'),
            'is_primary': full_contact_link_data.get('is_primary'),
            'can_receive_documents': full_contact_link_data.get('can_receive_documents'),
            'notes': full_contact_link_data.get('link_notes') # Note: using link_notes from the join
        }

        contact_dialog = ContactDialog(contact_data=contact_data_for_dialog, link_data=link_data_for_dialog, manage_link_fields=True, parent=self)

        if contact_dialog.exec_() == QDialog.Accepted:
            updated_contact_details = contact_dialog.get_contact_data()
            updated_link_details = contact_dialog.get_link_data()

            # Update central contact
            update_contact(full_contact_link_data['contact_id'], updated_contact_details)

            # Update link
            update_entity_contact_link(full_contact_link_data['entity_contact_id'], updated_link_details)

            self.load_associated_contacts() # Refresh table

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
            if unlink_contact_from_entity(entity_contact_id):
                self.load_associated_contacts() # Refresh table
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le lien."))


    def get_data(self):
        latitude_text = self.latitude_input.text().strip()
        longitude_text = self.longitude_input.text().strip()
        latitude = None
        longitude = None

        if latitude_text:
            try:
                latitude = float(latitude_text)
            except ValueError:
                # Error will be handled in accept() by checking if data['latitude'] is None
                pass

        if longitude_text:
            try:
                longitude = float(longitude_text)
            except ValueError:
                # Error will be handled in accept() by checking if data['longitude'] is None
                pass

        return {
            "name": self.name_input.text().strip(),
            "contact_person": self.contact_person_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "service_area": self.service_area_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "latitude": latitude,
            "longitude": longitude,
            "current_cargo": self.current_cargo_input.toPlainText().strip()
        }

    def accept(self):
        data = self.get_data()
        if not data['name']:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le nom du transporteur est requis."))
            self.name_input.setFocus()
            return

        # Validate latitude
        latitude_text = self.latitude_input.text().strip()
        if latitude_text and data['latitude'] is None: # Check if text was non-empty but conversion failed
            QMessageBox.warning(self, self.tr("Validation"), self.tr("La latitude doit être un nombre valide (ex: 45.678) ou vide."))
            self.latitude_input.setFocus()
            return

        # Validate longitude
        longitude_text = self.longitude_input.text().strip()
        if longitude_text and data['longitude'] is None: # Check if text was non-empty but conversion failed
            QMessageBox.warning(self, self.tr("Validation"), self.tr("La longitude doit être un nombre valide (ex: -73.123) ou vide."))
            self.longitude_input.setFocus()
            return

        try:
            if self.transporter_id: # Existing transporter
                success = transporters_crud.update_transporter(self.transporter_id, data)
                if success:
                    # Update initial data to reflect changes if dialog is reopened without re-fetching
                    self.transporter_data_initial.update(data)
                    self.transporter_data_initial['transporter_id'] = self.transporter_id
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Transporteur mis à jour avec succès."))
                    super().accept()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de mettre à jour le transporteur."))
                    return
            else: # New transporter
                new_id = transporters_crud.add_transporter(data)
                if new_id:
                    self.transporter_id = new_id # Store the new ID
                    # Update initial data to reflect the newly created transporter
                    self.transporter_data_initial = data
                    self.transporter_data_initial['transporter_id'] = new_id
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Transporteur ajouté avec succès (ID: {0}). Vous pouvez maintenant ajouter des contacts.").format(new_id))
                    self.update_contact_management_state(enabled=True) # Enable contact section
                    # We don't call super().accept() yet, so the user can add contacts.
                    # The OK button text might need to change (e.g. "Enregistrer et Fermer" or have a separate "Fermer")
                    # For now, let's assume the user will click OK again to close after adding contacts, or Cancel.
                    # Or, we can accept and let them re-open to add contacts. Simpler:
                    super().accept()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible d'ajouter le transporteur."))
                    return

            # After successful save (add or update of transporter), handle the main contact logic
            if self.transporter_id and data.get('contact_person'): # If contact_person field has data
                self._handle_main_contact_from_direct_fields(data)

        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def _handle_main_contact_from_direct_fields(self, transporter_main_data):
        """
        Checks direct contact fields (contact_person, email, phone) from the transporter form.
        If they are filled and no primary contact is set via EntityContacts,
        it creates/updates a contact in Contacts table and links it as primary.
        """
        direct_contact_name = transporter_main_data.get('contact_person','').strip()
        direct_email = transporter_main_data.get('email','').strip()
        direct_phone = transporter_main_data.get('phone','').strip() # Still read from form for this logic

        # This method is now primarily for ensuring data consistency if direct fields were somehow still used,
        # or for a one-time setup if a transporter is edited post-migration without prior primary contact.
        # However, the main creation/update of contacts should now happen via the dedicated contact management UI.

        if not self.transporter_id: return # Should not happen if called from accept after save

        if not direct_contact_name and not direct_email and not direct_phone:
            # If all direct fields are empty, there's nothing to infer for a primary contact.
            # If there are old values in DB direct fields, they are now considered deprecated.
            return


        # Check if a primary contact already exists via EntityContacts
        existing_contacts = get_contacts_for_entity(self.transporter_id, 'Transporter')
        primary_entity_contact = next((c for c in existing_contacts if c.get('is_primary')), None)

        if primary_entity_contact:
            # A primary contact is already explicitly set.
            # Optional: We could update this primary contact if the direct fields differ significantly,
            # or simply do nothing and let the user manage it via the contacts table.
            # For now, do nothing if an explicit primary contact exists.
            # The migration script should handle the one-time move.
            # Post-migration, these direct fields in the dialog are for display of primary or legacy data.
            # They are not meant for creating new primary contacts if one is already set via EntityContacts.
            return

        # If no explicit primary contact, and direct fields have data, this implies either:
        # 1. Data from before EntityContacts was used (migration should have handled this).
        # 2. User filled them now, expecting them to work as before.
        # Strategy: Create/link contact based on these fields ONLY IF no primary EntityContact exists.
        # This makes the method's behavior consistent with its original intent pre-migration script,
        # but it's now a fallback.


        contact_to_link_id = None
        # Try to find an existing contact by email to avoid duplicates
        if direct_email:
            existing_central_contact = get_contact_by_email(direct_email)
            if existing_central_contact:
                contact_to_link_id = existing_central_contact['contact_id']
                update_payload = {}
                if direct_contact_name and existing_central_contact.get('displayName') != direct_contact_name:
                    update_payload['displayName'] = direct_contact_name
                    update_payload['name'] = direct_contact_name # Ensure name is also updated

                if direct_phone and existing_central_contact.get('phone') != direct_phone:
                    update_payload['phone'] = direct_phone
                if update_payload:
                    update_contact(contact_to_link_id, update_payload)

        if not contact_to_link_id:
            # Create a new contact only if a name is present
            if not direct_contact_name:
                 logging.warning(f"Cannot create new contact for Transporter {self.transporter_id} from direct fields: contact_person name is missing.")
                 return
            contact_details = {
                'displayName': direct_contact_name,
                'name': direct_contact_name,
                'email': direct_email if direct_email else None,
                'phone': direct_phone if direct_phone else None,
                'employee_status': 'external'

            }
            contact_to_link_id = add_contact(contact_details)

        if contact_to_link_id:

            link_details = {
                'role_in_entity': self.tr("Contact Principal (auto)"),
                'is_primary': True,
                'can_receive_documents': True
            }
            # Check if this contact is already linked (even if not primary)
            already_linked = any(c['contact_id'] == contact_to_link_id for c in existing_contacts)
            if not already_linked:
                 link_contact_to_entity(
                    entity_id=self.transporter_id,
                    entity_type='Transporter',
                    contact_id=contact_to_link_id,
                    **link_details
                )
            else: # If already linked, find its entity_contact_id and update it to be primary
                existing_link_for_this_contact = next((c for c in existing_contacts if c['contact_id'] == contact_to_link_id), None)
                if existing_link_for_this_contact and not existing_link_for_this_contact.get('is_primary'):
                    update_entity_contact_link(existing_link_for_this_contact['entity_contact_id'], link_details)

            self.load_associated_contacts() # Refresh the contacts table in the UI
