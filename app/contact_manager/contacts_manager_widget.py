# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFormLayout, QLineEdit, QTextEdit, QScrollArea,
    QHeaderView, QAbstractItemView, QSplitter, QGroupBox, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import logging

# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFormLayout, QLineEdit, QTextEdit, QScrollArea,
    QHeaderView, QAbstractItemView, QSplitter, QGroupBox, QInputDialog, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import logging
from datetime import datetime

# Corrected, organized and absolute imports
from app.db.cruds.clients import contacts_crud, client_contacts_crud
from app.db.cruds.misc import entity_contacts_crud, company_personnel_crud
from app.gui.dialogs.contact_dialog import ContactDialog

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
        self.delete_contact_button.clicked.connect(self.on_delete_contact)
        self.link_to_entity_button.clicked.connect(self.on_link_to_entity)
        self.refresh_button.clicked.connect(lambda: self.load_contacts()) # Ensure it calls without args for refresh
        self.search_input.returnPressed.connect(self.apply_filters) # Search on Enter
        self.filter_button.clicked.connect(self.apply_filters)

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
        self.linked_entities_table.setRowCount(0)
        self.linked_entities_table.setSortingEnabled(False)

        # Helper to add a row
        def add_linked_entity_row(entity_type_display, entity_name_or_id, role_in_link):
            row = self.linked_entities_table.rowCount()
            self.linked_entities_table.insertRow(row)
            self.linked_entities_table.setItem(row, 0, QTableWidgetItem(entity_type_display))
            self.linked_entities_table.setItem(row, 1, QTableWidgetItem(str(entity_name_or_id)))
            self.linked_entities_table.setItem(row, 2, QTableWidgetItem(str(role_in_link)))

        try:
            # 1. Generic Entities from EntityContacts
            # We need a way to get the "name" of the entity_id (e.g., transporter name)
            # This might require joining in the CRUD or separate lookups here.
            # For now, we'll display entity_id.
            generic_entities = entity_contacts_crud.get_entities_for_contact(contact_id)
            for entity in generic_entities:
                entity_type = entity.get('entity_type', 'N/A')
                # TODO: Fetch actual name of the entity (e.g. transporter name, partner name)
                # For now, using entity_id. This could be improved by a helper function.
                entity_identifier = entity.get('entity_id', 'N/A')
                add_linked_entity_row(
                    self.tr(entity_type), # Translate entity_type if possible
                    entity_identifier,
                    entity.get('role_in_entity', '')
                )

            # 2. Clients from ClientContacts
            linked_clients = client_contacts_crud.get_clients_for_contact(contact_id)

            for client in linked_clients:
                role = self.tr("Contact")
                if client.get('is_primary_for_client'):
                    role = self.tr("Contact Principal")
                add_linked_entity_row(
                    self.tr("Client"),
                    client.get('client_name', client.get('company_name', 'N/A')),
                    role
                )

            # 3. Company Personnel from CompanyPersonnelContacts
            linked_personnel_list = company_personnel_crud.get_personnel_linked_to_contact(contact_id)
            for personnel in linked_personnel_list:
                role_display = personnel.get('role', '') # This is CompanyPersonnel.role
                # The link specific role (if any was designed for CompanyPersonnelContacts) isn't directly here.
                # We could add 'is_primary_for_personnel' to the display if relevant.
                if personnel.get('is_primary_for_personnel'):
                     role_display += f" ({self.tr('Contact Principal du Personnel')})"
                add_linked_entity_row(
                    self.tr("Personnel Compagnie"),
                    personnel.get('name', 'N/A'),
                    role_display
                )


            self.linked_entities_table.resizeColumnsToContents()
            self.linked_entities_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        except Exception as e:

            logger.error(f"Erreur majeure lors du chargement des entités liées pour contact {contact_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur critique est survenue lors du chargement des entités liées."))
        finally:
            self.linked_entities_table.setSortingEnabled(True)


    def _clear_details_panel(self, clear_contact_form=True, clear_linked_entities=True):
        if clear_contact_form:
           self._clear_layout(self.contact_details_layout)
        if clear_linked_entities:
           self.linked_entities_table.setRowCount(0)
        # pass # Removed pass

    def on_add_contact(self):
        # Assuming self.current_user_id might be set on this widget if user context is needed
        current_user_id = getattr(self, 'current_user_id', None)

        dialog = ContactDialog(manage_link_fields=False, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            contact_data = dialog.get_contact_data()
            if current_user_id:
                contact_data['created_by_user_id'] = current_user_id

            try:
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
                    QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ajouter le contact (pas d'ID retourné)."))
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout du contact: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur critique est survenue lors de l'ajout du contact:\n{e}"))

    def on_edit_contact(self):
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un contact à modifier."))
            return

        contact_id = selected_items[0].data(Qt.UserRole)
        if contact_id is None: return

        try:
            contact_data_to_edit = contacts_crud.get_contact_by_id(contact_id)
            if not contact_data_to_edit:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Contact non trouvé dans la base de données."))
                self.load_contacts() # Refresh list
                return
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contact {contact_id} pour édition: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("Impossible de récupérer les détails du contact pour édition."))
            return

        dialog = ContactDialog(contact_data=contact_data_to_edit, manage_link_fields=False, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_contact_data()
            try:
                if contacts_crud.update_contact(contact_id, updated_data):
                    self.load_contacts() # Refresh the list
                    # Reselect the row
                    for row in range(self.contacts_table.rowCount()):
                        if self.contacts_table.item(row, 0).data(Qt.UserRole) == contact_id:
                            self.contacts_table.selectRow(row)
                            break
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Contact mis à jour avec succès."))
                else:
                    QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de mettre à jour le contact (opération échouée)."))
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du contact {contact_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur critique est survenue lors de la mise à jour du contact:\n{e}"))

    def on_delete_contact(self):
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un contact à supprimer."))
            return

        contact_id = selected_items[0].data(Qt.UserRole)
        contact_name_display = selected_items[0].text()
        if contact_id is None: return

        linked_count = 0
        try:
            linked_count += len(entity_contacts_crud.get_entities_for_contact(contact_id) or [])
            linked_count += len(client_contacts_crud.get_clients_for_contact(contact_id) or [])
            linked_count += len(company_personnel_crud.get_personnel_linked_to_contact(contact_id) or [])
        except Exception as e:
            logger.error(f"Erreur lors du comptage des entités liées pour le contact {contact_id}: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Comptage"), self.tr("Impossible de vérifier complètement les liens du contact. Procéder avec prudence."))
            # Optionally, allow to proceed or not based on this partial info. For now, we proceed.

        msg = self.tr(f"Êtes-vous sûr de vouloir supprimer définitivement le contact '{contact_name_display}'?")
        if linked_count > 0:
            msg += self.tr(f"\n\nCe contact est lié à {linked_count} entité(s).\nLa suppression entraînera la suppression de ces liens.")
        else:
            msg += self.tr("\n\nCe contact n'est actuellement lié à aucune autre entité connue.")
        msg += self.tr("\nCette action est irréversible.")

        reply = QMessageBox.question(self, self.tr("Confirmation de Suppression"), msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                if contacts_crud.delete_contact(contact_id):
                    self.load_contacts()
                    self._clear_details_panel(clear_contact_form=True, clear_linked_entities=True)
                    self._update_action_buttons_state()
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Contact supprimé avec succès."))
                else:
                    QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le contact (opération échouée)."))
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du contact {contact_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur critique est survenue lors de la suppression du contact:\n{e}"))

    def on_link_to_entity(self):
        selected_items = self.contacts_table.selectedItems()
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
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez sélectionner un contact à supprimer."))
            return

        contact_id = selected_items[0].data(Qt.UserRole)
        # It's better to get the name from the DB to be sure, but for the message, table item is usually fine.
        contact_name_display = selected_items[0].text()

        if contact_id is None: return

        # Count linked entities for a more informative message
        # Note: This might be slightly slow if there are many link types or very large tables.
        # For now, it's acceptable for user confirmation.
        linked_count = 0
        try:
            linked_count += len(entity_contacts_crud.get_entities_for_contact(contact_id))
            linked_count += len(client_contacts_crud.get_clients_for_contact(contact_id))

            linked_count += len(company_personnel_crud.get_personnel_linked_to_contact(contact_id))
        except Exception as e:
            logger.error(f"Erreur lors du comptage des entités liées pour le contact {contact_id}: {e}")
            # Proceed with a generic message if counting fails

        msg = self.tr(f"Êtes-vous sûr de vouloir supprimer définitivement le contact '{contact_name_display}'?")
        if linked_count > 0:
            msg += self.tr(f"\n\nCe contact est lié à {linked_count} entité(s) (clients, personnel, transporteurs, etc.).\n"
                           "La suppression de ce contact central entraînera également la suppression de tous ces liens, "
                           "conformément aux règles de la base de données (ON DELETE CASCADE).")
        else:
            msg += self.tr("\n\nCe contact n'est actuellement lié à aucune autre entité.")

        msg += self.tr("\nCette action est irréversible.")

        reply = QMessageBox.question(self, self.tr("Confirmation de Suppression"), msg,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if contacts_crud.delete_contact(contact_id):
                self.load_contacts() # Refresh the main list
                self._clear_details_panel(clear_contact_form=True, clear_linked_entities=True) # Clear details
                self._update_action_buttons_state() # Disable buttons as selection is lost
                QMessageBox.information(self, self.tr("Succès"), self.tr("Contact supprimé avec succès."))
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le contact de la base de données."))

    def on_link_to_entity(self):
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection"), self.tr("Veuillez d'abord sélectionner un contact à lier."))
            return

        contact_id = selected_items[0].data(Qt.UserRole)
        contact_data_for_dialog = contacts_crud.get_contact_by_id(contact_id)
        if not contact_data_for_dialog:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer les données du contact sélectionné."))
            return

        entity_types = {
            "Transporter": "Transporter",
            "FreightForwarder": "FreightForwarder",
            "MoneyTransferAgent": "MoneyTransferAgent",
            "Client": "Client",
            "CompanyPersonnel": "CompanyPersonnel"
            # Add "Partner" here if a PartnerDialog for selection exists or is simple enough for QInputDialog
        }

        chosen_type_key, ok = QInputDialog.getItem(self, self.tr("Choisir le Type d'Entité"),
                                                self.tr("À quel type d'entité voulez-vous lier ce contact ?"),
                                                list(entity_types.keys()), 0, False)

        if ok and chosen_type_key:
            entity_type_str = entity_types[chosen_type_key]

            # This is a simplification. Ideally, a proper selection dialog for entities would be used.
            entity_id_str, ok_id = QInputDialog.getText(self, self.tr(f"ID de l'{chosen_type_key}"),
                                                        self.tr(f"Entrez l'ID de {chosen_type_key} :"))

            if ok_id and entity_id_str.strip():
                entity_id = entity_id_str.strip()

                # Check if this exact link already exists to prevent duplicates before opening dialog
                # This is a basic check. ContactDialog should ideally handle this on accept too.
                if entity_type_str in ["Transporter", "FreightForwarder", "MoneyTransferAgent", "Partner"]:
                    existing_links = entity_contacts_crud.get_contacts_for_entity(entity_id, entity_type_str)
                    if any(str(link.get('contact_id')) == str(contact_id) for link in existing_links):
                        QMessageBox.information(self, self.tr("Lien Existant"),
                                                self.tr(f"Ce contact est déjà lié à {chosen_type_key} ID {entity_id}."))
                        return
                elif entity_type_str == "Client":
                    # client_contacts_crud.get_specific_client_contact_link_details might be useful
                    pass # Add similar check for clients if needed
                elif entity_type_str == "CompanyPersonnel":
                    # company_personnel_crud.get_contacts_for_personnel might be useful
                    pass # Add similar check for personnel if needed


                link_dialog = ContactDialog(contact_data=contact_data_for_dialog,
                                            link_data={}, # New link, so empty link_data
                                            manage_link_fields=True,
                                            parent=self)
                link_dialog.setWindowTitle(self.tr(f"Lier Contact à {chosen_type_key} (ID: {entity_id})"))

                if link_dialog.exec_() == QDialog.Accepted:
                    link_details = link_dialog.get_link_data()
                    success = False
                    new_link_id = None

                    try:

                        entity_id_to_use = entity_id # Default to string for generic entities

                        if entity_type_str in ["Transporter", "FreightForwarder", "MoneyTransferAgent", "Partner"]:
                            # For these, entity_id might be a string or int depending on their specific schemas.
                            # entity_contacts_crud.link_contact_to_entity should handle type appropriately.
                            # If they must be int, conversion with error handling would be needed here too.
                            # For now, assume entity_contacts_crud is flexible or their IDs are typically strings.
                            pass # entity_id_to_use remains as string from input for these

                        elif entity_type_str == "Client":
                            try:
                                entity_id_to_use = int(entity_id)
                            except ValueError:
                                logger.error(f"Invalid Client ID format: {entity_id}. Must be an integer.")
                                QMessageBox.warning(self, self.tr("Erreur ID Client"), self.tr("L'ID du client doit être un nombre entier."))
                                return # Abort if client ID is invalid

                        elif entity_type_str == "CompanyPersonnel":
                            try:
                                entity_id_to_use = int(entity_id)
                            except ValueError:
                                logger.error(f"Invalid Personnel ID format: {entity_id}. Must be an integer.")
                                QMessageBox.warning(self, self.tr("Erreur ID Personnel"), self.tr("L'ID du personnel doit être un nombre entier."))
                                return # Abort if personnel ID is invalid

                        # Proceed with linking only if entity_id_to_use is valid for the type
                        if entity_type_str in ["Transporter", "FreightForwarder", "MoneyTransferAgent", "Partner"]:
                            new_link_id = entity_contacts_crud.link_contact_to_entity(
                                entity_id=entity_id_to_use, # Use potentially string ID
                                entity_type=entity_type_str,
                                contact_id=contact_id,
                                role_in_entity=link_details.get('role_in_entity'),
                                is_primary=link_details.get('is_primary', False),
                                can_receive_documents=link_details.get('can_receive_documents', True),
                                notes=link_details.get('notes')
                            )
                            success = new_link_id is not None
                        elif entity_type_str == "Client":
                            new_link_id = client_contacts_crud.link_contact_to_client(
                                client_id=entity_id_to_use,
                                contact_id=contact_id,
                                is_primary=link_details.get('is_primary', False),
                                can_receive_documents=link_details.get('can_receive_documents', True)
                            )
                            success = new_link_id is not None
                        elif entity_type_str == "CompanyPersonnel":
                            new_link_id = company_personnel_crud.link_existing_contact_to_personnel(
                                personnel_id=entity_id_to_use,
                                contact_id=contact_id,
                                is_primary=link_details.get('is_primary', False),
                                can_receive_documents=link_details.get('can_receive_documents', True)
                            )
                            success = new_link_id is not None



                        if success:
                            QMessageBox.information(self, self.tr("Succès"), self.tr("Contact lié avec succès."))
                            self.load_linked_entities(contact_id) # Refresh
                        else:
                            QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de lier le contact à l'entité."))
                    except Exception as e_link:
                        logger.error(f"Erreur lors de la liaison du contact {contact_id} à {entity_type_str} {entity_id}: {e_link}", exc_info=True)
                        QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la liaison."))
            else:
                QMessageBox.information(self, self.tr("Annulé"), self.tr("ID d'entité non fourni."))
        else:
            QMessageBox.information(self, self.tr("Annulé"), self.tr("Aucun type d'entité choisi."))


    def on_search_text_changed(self, text):
        # This could be used for live search with a QTimer debounce
        # For now, we use the filter_button or Enter key.
        pass

    def apply_filters(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            self.load_contacts(filters=None) # Load all if search is empty
            return

        # The contacts_crud.get_all_contacts expects specific filter keys like 'name' or 'email'.
        # We can try to search in multiple fields by setting up the filter dict accordingly.
        # However, the current get_all_contacts in contacts_crud.py seems to only support 'name' (for name/displayName) and 'email' separately.
        # Let's assume we want to search the term in either name/displayName OR email.
        # This would require a more complex filter structure or modification in the CRUD.
        # For simplicity with current CRUD: pass it as a 'name' filter, which searches name and displayName.
        # Users wanting to search specifically by email would need a different UI or the CRUD to handle a generic search term.

        # Simple approach: Use the 'name' filter in CRUD which searches name and displayName
        filters = {'name': search_term}
        # To also search email with the same term, the CRUD would need adjustment or we do two queries and merge.
        # For now, let's stick to what the CRUD directly supports for 'name' key.
        # If we want to search for the term in email as well, we'd need a more general filter in CRUD,
        # e.g., filters={'general_search': search_term}
        # and then the CRUD would build "name LIKE ? OR displayName LIKE ? OR email LIKE ? OR company_name LIKE ?"

        # Current CRUD structure of get_all_contacts:
        # if 'name' in filters: clauses.append("(name LIKE ? OR displayName LIKE ?)")
        # if 'email' in filters: clauses.append("email LIKE ?")
        # if 'company_name' in filters: clauses.append("company_name LIKE ?")

        # We will pass the search term for multiple fields if the CRUD is adapted or we manage it here.
        # For now, let's assume a generic search term that the CRUD can handle (e.g. by searching in name, displayname, email, company)
        # If CRUD's get_all_contacts is not adapted, we'll use a simple name/displayName search.

        # Let's make the filter key more generic for the widget, and the CRUD can interpret it.
        # Or, we can construct specific filters if the user has options to choose what to search.
        # For a single search box, a generic 'search_term_any_field' is often expected.

        # Given the current CRUD, let's try to filter by name/displayName for simplicity here.
        # If the user types an email, it won't be found unless it's also in the name/displayName.
        # This is a limitation of the current simple filter implementation.

        # To make it more useful, let's construct a filter that the existing CRUD can understand
        # by trying the search term for both 'name' and 'email' fields.
        # This means results will be an OR between these.
        # The CRUD's get_all_contacts would need to be able to handle this (e.g. if multiple filter keys are passed, how are they combined - AND/OR?)
        # The current CRUD combines multiple filter keys with AND.

        # For a simple single search box, it's better if the CRUD handles a generic search term.
        # Let's adapt the widget to call load_contacts with a filter key that the CRUD can be modified to understand.
        # For now, we'll use the 'name' filter as it's already supported for name/displayName.

        # Simplest implementation with current CRUD: search in name/displayName
        active_filters = {'name': search_term}

        # If you want the search term to also apply to email or company, you'd add them:
        # filters['email'] = search_term # This would make it "name/displayName LIKE term AND email LIKE term"
        # filters['company_name'] = search_term # "AND company_name LIKE term"
        # This is probably not what user expects from a single search box.

        # A better approach for a single search box is often to have a dedicated 'q' or 'search' filter in CRUD
        # that searches across multiple fields with OR.
        # Since that's not there, we will just search by name/displayName.

        logger.info(f"Applying filters: {active_filters}")
        self.load_contacts(filters=active_filters)


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
