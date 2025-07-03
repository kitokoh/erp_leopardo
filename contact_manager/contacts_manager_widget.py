# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFormLayout, QLineEdit, QTextEdit, QScrollArea,
    QHeaderView, QAbstractItemView, QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import logging

# Assuming CRUDS and Dialogs will be imported when needed
from db.cruds import contacts_crud #, entity_contacts_crud, client_contacts_crud, company_personnel_crud
from dialogs.contact_dialog import ContactDialog # Corrected relative import path if necessary

logger = logging.getLogger(__name__)

class ContactsManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Gestionnaire Central des Contacts"))
        self.setObjectName("ContactsManagerWidget") # For styling or identification

        self._setup_ui()
        self._connect_signals()
        # self.load_contacts() # Initial load

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Top: Search/Filter area (placeholder for now)
        filter_group = QGroupBox(self.tr("Filtres et Recherche"))
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Rechercher par nom, email..."))
        filter_layout.addWidget(QLabel(self.tr("Rechercher:")))
        filter_layout.addWidget(self.search_input)
        self.filter_button = QPushButton(QIcon.fromTheme("edit-find"), self.tr("Appliquer Filtres"))
        filter_layout.addWidget(self.filter_button)
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # Main content: Splitter for list and details
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Contacts Table
        contacts_list_group = QGroupBox(self.tr("Liste des Contacts"))
        contacts_list_layout = QVBoxLayout()
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5) # Example columns
        self.contacts_table.setHorizontalHeaderLabels([
            self.tr("Nom Affiché"), self.tr("Email Principal"), self.tr("Téléphone Principal"),
            self.tr("Entreprise"), self.tr("Statut Employé")
        ])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contacts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        contacts_list_layout.addWidget(self.contacts_table)

        contacts_list_buttons_layout = QHBoxLayout()
        self.add_contact_button = QPushButton(QIcon.fromTheme("list-add"), self.tr("Ajouter Contact"))
        self.refresh_button = QPushButton(QIcon.fromTheme("view-refresh"), self.tr("Rafraîchir"))
        contacts_list_buttons_layout.addWidget(self.add_contact_button)
        contacts_list_buttons_layout.addStretch()
        contacts_list_buttons_layout.addWidget(self.refresh_button)
        contacts_list_layout.addLayout(contacts_list_buttons_layout)
        contacts_list_group.setLayout(contacts_list_layout)

        splitter.addWidget(contacts_list_group)

        # Right side: Details Panel (Scrollable)
        details_panel_scroll = QScrollArea()
        details_panel_scroll.setWidgetResizable(True)
        details_widget = QWidget()
        details_main_layout = QVBoxLayout(details_widget)

        # Contact Details Group
        contact_details_group = QGroupBox(self.tr("Détails du Contact"))
        self.contact_details_layout = QFormLayout() # Will be populated dynamically
        contact_details_group.setLayout(self.contact_details_layout)
        details_main_layout.addWidget(contact_details_group)

        # Action buttons for selected contact
        contact_actions_layout = QHBoxLayout()
        self.edit_contact_button = QPushButton(QIcon.fromTheme("document-edit"), self.tr("Modifier Contact"))
        self.delete_contact_button = QPushButton(QIcon.fromTheme("edit-delete"), self.tr("Supprimer Contact"))
        self.delete_contact_button.setObjectName("dangerButton") # For styling
        self.link_to_entity_button = QPushButton(QIcon.fromTheme("contact-new"), self.tr("Lier à une Entité"))
        contact_actions_layout.addWidget(self.edit_contact_button)
        contact_actions_layout.addWidget(self.delete_contact_button)
        contact_actions_layout.addWidget(self.link_to_entity_button)
        contact_actions_layout.addStretch()
        details_main_layout.addLayout(contact_actions_layout)

        # Linked Entities Group
        linked_entities_group = QGroupBox(self.tr("Entités Liées"))
        linked_entities_layout = QVBoxLayout()
        self.linked_entities_table = QTableWidget()
        self.linked_entities_table.setColumnCount(3) # Example: Type, Nom Entité, Rôle
        self.linked_entities_table.setHorizontalHeaderLabels([
            self.tr("Type d'Entité"), self.tr("Nom/ID de l'Entité"), self.tr("Rôle")
        ])
        self.linked_entities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.linked_entities_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        linked_entities_layout.addWidget(self.linked_entities_table)
        linked_entities_group.setLayout(linked_entities_layout)
        details_main_layout.addWidget(linked_entities_group)

        details_main_layout.addStretch() # Pushes content to the top
        details_panel_scroll.setWidget(details_widget)
        splitter.addWidget(details_panel_scroll)

        splitter.setSizes([400, 600]) # Initial sizing for list and details
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Initially disable buttons that depend on selection
        self._update_action_buttons_state()


    def _connect_signals(self):
        self.contacts_table.itemSelectionChanged.connect(self.on_contact_selected)
        self.add_contact_button.clicked.connect(self.on_add_contact)
        self.edit_contact_button.clicked.connect(self.on_edit_contact)
        # self.delete_contact_button.clicked.connect(self.on_delete_contact)
        # self.link_to_entity_button.clicked.connect(self.on_link_to_entity)
        self.refresh_button.clicked.connect(self.load_contacts) # Already connected
        # self.search_input.textChanged.connect(self.on_search_text_changed) # Or use a filter button
        # self.filter_button.clicked.connect(self.apply_filters)
        # pass # Connections will be done as methods are implemented

    # Placeholder methods to be implemented in subsequent steps
    def load_contacts(self, filters=None):
        logger.info(f"Chargement des contacts avec filtres : {filters}")
        self.contacts_table.setRowCount(0) # Clear table
        self.contacts_table.setSortingEnabled(False) # Disable sorting during population
        try:
            all_contacts = contacts_crud.get_all_contacts(filters=filters)
            for contact in all_contacts:
                row_position = self.contacts_table.rowCount()
                self.contacts_table.insertRow(row_position)

                name_item = QTableWidgetItem(contact.get('displayName') or contact.get('name', 'N/A'))
                name_item.setData(Qt.UserRole, contact.get('contact_id')) # Store contact_id
                self.contacts_table.setItem(row_position, 0, name_item)

                self.contacts_table.setItem(row_position, 1, QTableWidgetItem(contact.get('email', '')))
                self.contacts_table.setItem(row_position, 2, QTableWidgetItem(contact.get('phone', '')))
                self.contacts_table.setItem(row_position, 3, QTableWidgetItem(contact.get('company_name', '')))

                status_map = {
                    "internal": self.tr("Interne"),
                    "external": self.tr("Externe"),
                    "not_applicable": self.tr("N/A"),
                    None: self.tr("N/A") # Handle None case
                }
                employee_status_display = status_map.get(contact.get('employee_status', '').lower(), contact.get('employee_status', self.tr("N/A")))
                self.contacts_table.setItem(row_position, 4, QTableWidgetItem(employee_status_display))

            self.contacts_table.resizeColumnsToContents()
            self.contacts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Name column stretches
        except Exception as e:
            logger.error(f"Erreur lors du chargement des contacts: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger la liste des contacts."))
        finally:
            self.contacts_table.setSortingEnabled(True)
            self._update_action_buttons_state() # Update button states based on selection

    def _update_action_buttons_state(self):
        has_selection = bool(self.contacts_table.selectedItems())
        self.edit_contact_button.setEnabled(has_selection)
        self.delete_contact_button.setEnabled(has_selection)
        self.link_to_entity_button.setEnabled(has_selection)

    def on_contact_selected(self):
        self._update_action_buttons_state()
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            self._clear_details_panel()
            return

        contact_id = selected_items[0].data(Qt.UserRole)
        if contact_id is not None:
            self.display_contact_details(contact_id)
            self.load_linked_entities(contact_id)
        else:
            self._clear_details_panel()


    def display_contact_details(self, contact_id):
        logger.info(f"Affichage des détails pour contact_id : {contact_id}")
        self._clear_layout(self.contact_details_layout) # Clear previous details

        contact_data = contacts_crud.get_contact_by_id(contact_id)
        if not contact_data:
            self.contact_details_layout.addRow(QLabel(self.tr("Contact non trouvé ou erreur de chargement.")))
            return

        # Define which fields to display and their labels
        # Order matters for QFormLayout
        fields_to_display = [
            ('displayName', self.tr("Nom Affiché:")),
            ('givenName', self.tr("Prénom:")),
            ('familyName', self.tr("Nom de Famille:")),
            ('email', self.tr("Email:")),
            ('phone', self.tr("Téléphone:")),
            ('position', self.tr("Poste/Fonction:")),
            ('company_name', self.tr("Entreprise:")),
            ('employee_status', self.tr("Statut Employé:")),
            ('notes', self.tr("Notes (Contact):")),
            # Advanced fields (can be grouped or shown if present)
            ('phone_type', self.tr("Type téléphone:")),
            ('email_type', self.tr("Type email:")),
            ('address_streetAddress', self.tr("Rue:")),
            ('address_city', self.tr("Ville:")),
            ('address_region', self.tr("Région/État:")),
            ('address_postalCode', self.tr("Code Postal:")),
            ('address_country', self.tr("Pays:")),
            ('organization_name', self.tr("Nom Organisation (Sync):")),
            ('organization_title', self.tr("Titre Organisation (Sync):")),
            ('birthday_date', self.tr("Anniversaire:")),
            ('created_at', self.tr("Créé le:")),
            ('updated_at', self.tr("Mis à jour le:")),
        ]

        for field_key, field_label_text in fields_to_display:
            value = contact_data.get(field_key, '')
            if value is None: value = '' # Ensure empty string for None

            if field_key == 'employee_status':
                status_map = {"internal": self.tr("Interne"), "external": self.tr("Externe"), "not_applicable": self.tr("N/A")}
                value_display = status_map.get(str(value).lower(), str(value))
            elif field_key in ['created_at', 'updated_at']:
                # Basic date formatting, can be improved with QDateTime
                try:
                    dt_obj = datetime.fromisoformat(str(value).replace('Z', '+00:00')) if value else None
                    value_display = dt_obj.strftime('%Y-%m-%d %H:%M:%S') if dt_obj else ''
                except ValueError:
                    value_display = str(value) # Fallback if parsing fails
            else:
                value_display = str(value)

            if field_key == 'notes': # Use QTextEdit for notes for better display
                notes_display = QTextEdit(value_display)
                notes_display.setReadOnly(True)
                notes_display.setFixedHeight(80) # Adjust as needed
                self.contact_details_layout.addRow(QLabel(field_label_text), notes_display)
            else:
                # For other fields, use QLineEdit in read-only mode to allow selection/copy
                value_widget = QLineEdit(value_display)
                value_widget.setReadOnly(True)
                value_widget.setFrame(False) # Make it look like a QLabel
                value_widget.setStyleSheet("QLineEdit { background-color: transparent; border: none; }") # Further styling
                self.contact_details_layout.addRow(QLabel(field_label_text), value_widget)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else: # If it's a layout item
                    child_layout = item.layout()
                    if child_layout is not None:
                        self._clear_layout(child_layout)

    def load_linked_entities(self, contact_id):
        logger.info(f"Chargement des entités liées pour contact_id : {contact_id}")
        # self.linked_entities_table.setRowCount(0)
        # Example for EntityContacts:
        # linked_generic_entities = entity_contacts_crud.get_entities_for_contact(contact_id)
        # for entity in linked_generic_entities:
        #    # Add row to self.linked_entities_table
        #    pass
        # Similar for ClientContacts, CompanyPersonnelContacts etc.
        pass

    def _clear_details_panel(self, clear_contact_form=True, clear_linked_entities=True):
        # if clear_contact_form:
        #    # Clear QLineEdit fields in self.contact_details_layout
        #    pass
        # if clear_linked_entities:
        #    self.linked_entities_table.setRowCount(0)
        pass

    def on_add_contact(self):
        # Assuming self.current_user_id might be set on this widget if user context is needed
        current_user_id = getattr(self, 'current_user_id', None)

        dialog = ContactDialog(manage_link_fields=False, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            contact_data = dialog.get_contact_data()
            if current_user_id:
                contact_data['created_by_user_id'] = current_user_id

            new_id = contacts_crud.add_contact(contact_data)
            if new_id:
                self.load_contacts() # Refresh the list
                # Optionally, select the new contact
                for row in range(self.contacts_table.rowCount()):
                    if self.contacts_table.item(row, 0).data(Qt.UserRole) == new_id:
                        self.contacts_table.selectRow(row)
                        break
                QMessageBox.information(self, self.tr("Succès"), self.tr("Contact ajouté avec succès."))
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ajouter le contact."))

    def on_edit_contact(self):
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un contact à modifier."))
            return

        contact_id = selected_items[0].data(Qt.UserRole)
        if contact_id is None: return # Should not happen if selection is valid

        contact_data_to_edit = contacts_crud.get_contact_by_id(contact_id)
        if not contact_data_to_edit:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Contact non trouvé dans la base de données."))
            self.load_contacts() # Refresh list in case it was deleted elsewhere
            return

        dialog = ContactDialog(contact_data=contact_data_to_edit, manage_link_fields=False, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_contact_data()
            # Add user_id if available for updated_by_user_id if your CRUD supports it
            # current_user_id = getattr(self, 'current_user_id', None)
            # if current_user_id:
            #    updated_data['updated_by_user_id'] = current_user_id # Assuming contacts_crud.update_contact handles this

            if contacts_crud.update_contact(contact_id, updated_data):
                self.load_contacts() # Refresh the list
                # Reselect the row and refresh details
                for row in range(self.contacts_table.rowCount()):
                    if self.contacts_table.item(row, 0).data(Qt.UserRole) == contact_id:
                        self.contacts_table.selectRow(row)
                        # self.on_contact_selected() will be called, which calls display_contact_details
                        break
                QMessageBox.information(self, self.tr("Succès"), self.tr("Contact mis à jour avec succès."))
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de mettre à jour le contact."))

    def on_delete_contact(self):
        # selected_items = self.contacts_table.selectedItems()
        # if not selected_items: return
        # contact_id = selected_items[0].data(Qt.UserRole)
        # contact_name = selected_items[0].text() # Or get from contact_data

        # # Check for linked entities (this is a simplified check)
        # linked_entities_count = self.linked_entities_table.rowCount() # Assuming it's populated for selected contact

        # msg = self.tr(f"Êtes-vous sûr de vouloir supprimer le contact '{contact_name}'?")
        # if linked_entities_count > 0:
        #     msg += self.tr(f"\nCe contact est lié à {linked_entities_count} entité(s). La suppression du contact supprimera ces liens (CASCADE).")

        # reply = QMessageBox.question(self, self.tr("Confirmation"), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        #     if contacts_crud.delete_contact(contact_id):
        #         self.load_contacts()
        #         self._clear_details_panel()
        #         QMessageBox.information(self, self.tr("Succès"), self.tr("Contact supprimé."))
        #     else:
        #         QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le contact."))
        pass

    def on_link_to_entity(self):
        # This will be more complex:
        # 1. Get selected contact_id.
        # 2. Open a dialog to choose entity type (Transporter, Client, etc.).
        # 3. Open another dialog to choose the specific entity instance.
        # 4. Open ContactDialog with manage_link_fields=True, pre-filled with contact_data.
        # 5. On accept, call the appropriate link function (e.g., entity_contacts_crud.link_contact_to_entity).
        # 6. Refresh linked entities table.
        QMessageBox.information(self, self.tr("Non implémenté"), self.tr("La fonctionnalité 'Lier à une Entité' sera implémentée."))
        pass

    def on_search_text_changed(self, text):
        # Basic search logic, can be refined with a timer to avoid too many DB calls
        # self.load_contacts(filters={'name_email_company_like': text})
        pass

    def apply_filters(self):
        # More advanced filtering based on multiple criteria
        search_term = self.search_input.text().strip()
        filters = {}
        if search_term:
            filters['name_email_company_like'] = search_term # Example filter key
        # Add other filter criteria from UI elements if any
        self.load_contacts(filters=filters)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # This is for basic UI testing. Full functionality requires DB and other modules.

    # Example: Mocking for UI testing without full backend
    class MockContactsCRUD:
        def get_all_contacts(self, filters=None): return []
        def get_contact_by_id(self, contact_id): return None
        def add_contact(self, data): return None
        def update_contact(self, contact_id, data): return False
        def delete_contact(self, contact_id): return False

    # If running this file directly, you might want to replace actual cruds with mocks
    # contacts_crud = MockContactsCRUD()
    # entity_contacts_crud = ... (mock)

    manager_widget = ContactsManagerWidget()
    manager_widget.show()
    sys.exit(app.exec_())
