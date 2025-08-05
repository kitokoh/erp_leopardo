# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QMessageBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QHeaderView, QAbstractItemView, QCheckBox
)
from PyQt5.QtGui import QIcon
import logging

# Assuming CRUD functions are directly importable from their modules
try:
    import db.cruds.money_transfer_agents_crud as mta_crud
    import db.cruds.contacts_crud as contacts_crud
    import db.cruds.entity_contacts_crud as entity_contacts_crud
    from db.cruds.locations_crud import get_all_countries, get_cities_for_country # For country/city dropdowns
    from .contact_dialog import ContactDialog
except ImportError as e:
    logging.error(f"CRITICAL: Failed to import CRUD modules for MoneyTransferAgentDialog: {e}", exc_info=True)
    # Fallback or raise, depending on desired behavior when modules are missing
    QMessageBox.critical(None, "Dev Error", f"MoneyTransferAgentDialog failed to load database modules: {e}. Functionality will be limited.")
    # Define dummy CRUDS if needed for UI to load in a broken state for testing UI parts
    class DummyMtaCRUD:
        def add_money_transfer_agent(self, *args, **kwargs): return None
        def update_money_transfer_agent(self, *args, **kwargs): return False
        def get_all_countries(self, *args, **kwargs): return []
        def get_cities_for_country(self, *args, **kwargs): return []
    mta_crud = DummyMtaCRUD()
    contacts_crud = object() # Placeholder
    entity_contacts_crud = object() # Placeholder
    get_all_countries = lambda conn=None: []
    get_cities_for_country = lambda country_id, conn=None: []
    ContactDialog = QDialog


logger = logging.getLogger(__name__)

class MoneyTransferAgentDialog(QDialog):
    def __init__(self, agent_data=None, parent=None):
        super().__init__(parent)
        self.agent_data_initial = agent_data
        self.agent_id = None
        if self.agent_data_initial:
            self.agent_id = self.agent_data_initial.get('agent_id')

        self.setWindowTitle(self.tr("Ajouter/Modifier Agent de Transfert d'Argent"))
        self.setMinimumWidth(650) # Adjusted width
        self.countries_map = {} # To store country_name: country_id
        self.cities_map = {}    # To store city_name: city_id for current country

        self.setup_ui()
        if self.agent_data_initial:
            self.load_agent_data()
        else:
            self.update_contact_management_state(enabled=False)
            self.country_combo.setCurrentIndex(-1) # No selection for new agent
            self.city_combo.setEnabled(False)


    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Agent Details Group
        details_group = QGroupBox(self.tr("Détails de l'Agent"))
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        form_layout.addRow(self.tr("Nom de l'agent*:"), self.name_input)

        self.agent_type_combo = QComboBox()
        self.agent_type_combo.addItems(["Bank", "Individual Agent", "Other"])
        form_layout.addRow(self.tr("Type d'agent*:"), self.agent_type_combo)

        self.phone_input = QLineEdit() # Direct contact field
        form_layout.addRow(self.tr("Numéro de téléphone (principal):"), self.phone_input)

        self.email_input = QLineEdit() # Direct contact field
        form_layout.addRow(self.tr("Email (principal):"), self.email_input)

        self.country_combo = QComboBox()
        self.country_combo.currentIndexChanged.connect(self.on_country_changed)
        form_layout.addRow(self.tr("Pays:"), self.country_combo)
        self._load_countries()

        self.city_combo = QComboBox()
        form_layout.addRow(self.tr("Ville:"), self.city_combo)

        details_group.setLayout(form_layout)
        main_layout.addWidget(details_group)

        # Associated Contacts Group (similar to TransporterDialog)
        contacts_group = QGroupBox(self.tr("Contacts Associés"))
        contacts_layout = QVBoxLayout()
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5)
        self.contacts_table.setHorizontalHeaderLabels([
            self.tr("Nom Affiché"), self.tr("Email"), self.tr("Téléphone"),
            self.tr("Rôle (Agent)"), self.tr("Principal")
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
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Enregistrer Agent"))
        self.button_box.button(QDialogButtonBox.Ok).setObjectName("primaryButton")
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept_agent_data) # Renamed to avoid conflict
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _load_countries(self):
        self.country_combo.clear()
        self.countries_map.clear()
        self.country_combo.addItem(self.tr("Sélectionner un pays..."), None)
        try:
            countries = get_all_countries()
            for country in countries:
                self.country_combo.addItem(country['country_name'], country['country_id'])
                self.countries_map[country['country_id']] = country['country_name']
        except Exception as e:
            logger.error(f"Failed to load countries: {e}")
            QMessageBox.warning(self, self.tr("Erreur de chargement"), self.tr("Impossible de charger la liste des pays."))

    def on_country_changed(self, index):
        self.city_combo.clear()
        self.cities_map.clear()
        country_id = self.country_combo.itemData(index)
        if country_id is not None:
            self.city_combo.setEnabled(True)
            self.city_combo.addItem(self.tr("Sélectionner une ville..."), None)
            try:
                cities = get_cities_for_country(country_id)
                for city in cities:
                    self.city_combo.addItem(city['city_name'], city['city_id'])
                    self.cities_map[city['city_id']] = city['city_name']
            except Exception as e:
                logger.error(f"Failed to load cities for country {country_id}: {e}")
                QMessageBox.warning(self, self.tr("Erreur de chargement"), self.tr("Impossible de charger la liste des villes."))
        else:
            self.city_combo.setEnabled(False)

    def update_contact_management_state(self, enabled: bool):
        self.contacts_table.setEnabled(enabled)
        self.add_contact_button.setEnabled(enabled)
        self.edit_contact_button.setEnabled(enabled)
        self.delete_link_button.setEnabled(enabled)

    def load_agent_data(self):
        self.name_input.setText(self.agent_data_initial.get('name', ''))
        agent_type = self.agent_data_initial.get('agent_type', 'Other')
        if self.agent_type_combo.findText(agent_type) != -1:
            self.agent_type_combo.setCurrentText(agent_type)
        else: # Fallback if type is not in standard list
            self.agent_type_combo.setCurrentText("Other")
            # Optionally, if combo is editable, set the lineEdit text
            # if self.agent_type_combo.isEditable(): self.agent_type_combo.lineEdit().setText(agent_type)


        self.phone_input.setText(self.agent_data_initial.get('phone_number', ''))
        self.email_input.setText(self.agent_data_initial.get('email', ''))

        country_id = self.agent_data_initial.get('country_id')
        if country_id:
            index = self.country_combo.findData(country_id)
            if index != -1:
                self.country_combo.setCurrentIndex(index)
                # City loading will be triggered by on_country_changed
                # We need to set city after cities are loaded for that country
                city_id = self.agent_data_initial.get('city_id')
                if city_id:
                    # Ensure cities are loaded before trying to set city_combo index
                    # This might require a slight delay or ensuring on_country_changed finishes
                    # For simplicity, we assume on_country_changed populates cities before this line is hit effectively
                    # or we can call it explicitly before setting city
                    self.on_country_changed(index) # Ensure cities are loaded
                    city_index = self.city_combo.findData(city_id)
                    if city_index != -1:
                         self.city_combo.setCurrentIndex(city_index)
        else:
            self.country_combo.setCurrentIndex(0) # "Sélectionner un pays..."
            self.city_combo.setEnabled(False)


        if self.agent_id:
            self.load_associated_contacts()
            self.update_contact_management_state(enabled=True)
        else:
            self.update_contact_management_state(enabled=False)

    def load_associated_contacts(self):
        self.contacts_table.setRowCount(0)
        if not self.agent_id:
            return
        contacts = entity_contacts_crud.get_contacts_for_entity(self.agent_id, 'MoneyTransferAgent')
        for contact_data in contacts:
            row = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row)
            name_item = QTableWidgetItem(contact_data.get('displayName', contact_data.get('name', 'N/A')))
            name_item.setData(Qt.UserRole, contact_data)
            self.contacts_table.setItem(row, 0, name_item)
            self.contacts_table.setItem(row, 1, QTableWidgetItem(contact_data.get('email', '')))
            self.contacts_table.setItem(row, 2, QTableWidgetItem(contact_data.get('phone', '')))
            self.contacts_table.setItem(row, 3, QTableWidgetItem(contact_data.get('role_in_entity', '')))
            is_primary_cb = QCheckBox()
            is_primary_cb.setChecked(bool(contact_data.get('is_primary', False)))
            is_primary_cb.setEnabled(False)
            self.contacts_table.setCellWidget(row, 4, is_primary_cb)
        self.contacts_table.resizeColumnsToContents()
        self.contacts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


    def handle_add_contact_link(self):
        if not self.agent_id:
            QMessageBox.information(self, self.tr("Information"), self.tr("Veuillez d'abord enregistrer l'agent."))
            return
        dialog = ContactDialog(manage_link_fields=True, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            contact_data = dialog.get_contact_data()
            link_data = dialog.get_link_data()
            new_contact_id = contacts_crud.add_contact(contact_data)
            if new_contact_id:
                entity_contacts_crud.link_contact_to_entity(
                    self.agent_id, 'MoneyTransferAgent', new_contact_id,
                    role_in_entity=link_data.get('role_in_entity'),
                    is_primary=link_data.get('is_primary'),
                    can_receive_documents=link_data.get('can_receive_documents'),
                    notes=link_data.get('notes')
                )
                self.load_associated_contacts()
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de créer le contact central."))

    def handle_edit_contact_link(self):
        selected_row = self.contacts_table.currentRow()
        if selected_row < 0: return
        item = self.contacts_table.item(selected_row, 0)
        if not item: return
        full_data = item.data(Qt.UserRole)

        contact_part = {k: v for k, v in full_data.items() if k in contacts_crud.get_contact_by_id(1, conn=contacts_crud._get_conn_from_pool()).keys() } # Hacky way to get keys
        link_part = {
            'role_in_entity': full_data.get('role_in_entity'),
            'is_primary': full_data.get('is_primary'),
            'can_receive_documents': full_data.get('can_receive_documents'),
            'notes': full_data.get('link_notes')
        }

        dialog = ContactDialog(contact_data=contact_part, link_data=link_part, manage_link_fields=True, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_contact = dialog.get_contact_data()
            updated_link = dialog.get_link_data()
            contacts_crud.update_contact(full_data['contact_id'], updated_contact)
            entity_contacts_crud.update_entity_contact_link(full_data['entity_contact_id'], updated_link)
            self.load_associated_contacts()

    def handle_delete_contact_link(self):
        selected_row = self.contacts_table.currentRow()
        if selected_row < 0: return
        item = self.contacts_table.item(selected_row, 0)
        if not item: return
        full_data = item.data(Qt.UserRole)
        entity_contact_id = full_data.get('entity_contact_id')
        contact_name = full_data.get('displayName', 'ce contact')

        reply = QMessageBox.question(self, self.tr("Confirmation"),
                                     self.tr(f"Supprimer le lien avec {contact_name} ? Le contact central ne sera pas affecté."),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if entity_contacts_crud.unlink_contact_from_entity(entity_contact_id):
                self.load_associated_contacts()
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le lien."))

    def get_agent_data_from_form(self):
        country_id = self.country_combo.currentData()
        city_id = self.city_combo.currentData()
        return {
            "name": self.name_input.text().strip(),
            "agent_type": self.agent_type_combo.currentText(),
            "phone_number": self.phone_input.text().strip(), # Direct field
            "email": self.email_input.text().strip(),       # Direct field
            "country_id": country_id if country_id is not None else None,
            "city_id": city_id if city_id is not None else None,
            # created_at, updated_at are handled by CRUD
        }

    def accept_agent_data(self): # Renamed from accept
        data = self.get_agent_data_from_form()
        if not data['name'] or not data['agent_type']:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le nom et le type de l'agent sont requis."))
            return

        original_agent_id = self.agent_id # Keep track if it was an existing agent

        try:
            if self.agent_id: # Update existing
                success = mta_crud.update_money_transfer_agent(self.agent_id, data)
                if success:
                    self.agent_data_initial.update(data)
                    self.agent_data_initial['agent_id'] = self.agent_id
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Agent mis à jour avec succès."))
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de mettre à jour l'agent."))
                    return
            else: # Add new
                new_id = mta_crud.add_money_transfer_agent(data) # add_money_transfer_agent needs to be implemented in CRUD
                if new_id:
                    self.agent_id = new_id
                    self.agent_data_initial = data
                    self.agent_data_initial['agent_id'] = new_id
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Agent ajouté. Vous pouvez ajouter des contacts."))
                    self.update_contact_management_state(enabled=True)
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible d'ajouter l'agent."))
                    return

            # Handle direct fields for NEWLY created agents only
            if original_agent_id is None and self.agent_id and \
               (data.get('name') or data.get('email') or data.get('phone_number')): # Using name as contact_person
                # Adapt data for _handle_main_contact_from_direct_fields
                direct_contact_info = {
                    'contact_person': data.get('name'), # Using agent name as contact person
                    'email': data.get('email'),
                    'phone': data.get('phone_number')
                }
                self._handle_main_contact_from_direct_fields(direct_contact_info)

            super().accept()
        except AttributeError as ae: # Catch if CRUD functions like add_money_transfer_agent are missing
             logger.error(f"CRUD function possibly missing for MoneyTransferAgents: {ae}", exc_info=True)
             QMessageBox.critical(self, self.tr("Erreur Développeur"), self.tr(f"Fonctionnalité manquante: {ae}"))
        except Exception as e:
            logger.error(f"Error saving money transfer agent: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def _handle_main_contact_from_direct_fields(self, agent_main_data):
        # Similar to TransporterDialog._handle_main_contact_from_direct_fields
        # Adapted for MoneyTransferAgent fields
        direct_contact_name = agent_main_data.get('contact_person','').strip() # name from agent becomes contact_person
        direct_email = agent_main_data.get('email','').strip()
        direct_phone = agent_main_data.get('phone','').strip()

        if not self.agent_id: return
        if not direct_contact_name and not direct_email and not direct_phone: return

        existing_contacts = entity_contacts_crud.get_contacts_for_entity(self.agent_id, 'MoneyTransferAgent')
        primary_contact = next((c for c in existing_contacts if c.get('is_primary')), None)

        if primary_contact: return # Explicit primary contact exists

        contact_id_to_link = None
        if direct_email:
            central_contact = contacts_crud.get_contact_by_email(direct_email)
            if central_contact:
                contact_id_to_link = central_contact['contact_id']
                payload = {}
                if direct_contact_name and central_contact.get('displayName') != direct_contact_name:
                    payload['displayName'] = direct_contact_name
                    payload['name'] = direct_contact_name
                if direct_phone and central_contact.get('phone') != direct_phone:
                    payload['phone'] = direct_phone
                if payload:
                    contacts_crud.update_contact(contact_id_to_link, payload)

        if not contact_id_to_link:
            if not direct_contact_name: return # Cannot create contact without a name
            details = {
                'displayName': direct_contact_name, 'name': direct_contact_name,
                'email': direct_email or None, 'phone': direct_phone or None,
                'employee_status': 'external'
            }
            contact_id_to_link = contacts_crud.add_contact(details)

        if contact_id_to_link:
            link_data = {'role_in_entity': self.tr("Contact Principal (auto)"), 'is_primary': True, 'can_receive_documents': True}
            already_linked = any(c['contact_id'] == contact_id_to_link for c in existing_contacts)
            if not already_linked:
                entity_contacts_crud.link_contact_to_entity(self.agent_id, 'MoneyTransferAgent', contact_id_to_link, **link_data)
            else:
                existing_link = next((c for c in existing_contacts if c['contact_id'] == contact_id_to_link), None)
                if existing_link and not existing_link.get('is_primary'):
                    entity_contacts_crud.update_entity_contact_link(existing_link['entity_contact_id'], link_data)
            self.load_associated_contacts()

# Example Usage
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # This is a basic test, real usage would involve database interaction
    # Ensure db.connection.DATABASE_PATH is correctly set or provide a test DB

    # Mocking CRUD functions if they are not fully implemented or DB is not available
    # This allows testing the UI part of the dialog
    if isinstance(mta_crud, DummyMtaCRUD):
        def mock_add_mta(data):
            print(f"Mock Add MTA: {data}")
            return "new_mta_id_123"
        def mock_update_mta(mta_id, data):
            print(f"Mock Update MTA {mta_id}: {data}")
            return True
        mta_crud.add_money_transfer_agent = mock_add_mta
        mta_crud.update_money_transfer_agent = mock_update_mta
        # You'd also mock contacts_crud and entity_contacts_crud for full UI flow

    dialog = MoneyTransferAgentDialog()
    # To test editing:
    # sample_agent = {'agent_id': 'agt1', 'name': 'Test Bank', 'agent_type': 'Bank', 'phone_number': '111', 'email': 'bank@test.com'}
    # dialog = MoneyTransferAgentDialog(agent_data=sample_agent)

    if dialog.exec_() == QDialog.Accepted:
        print("Money Transfer Agent Dialog Accepted.")
    else:
        print("Money Transfer Agent Dialog Cancelled.")
    sys.exit(app.exec_())
