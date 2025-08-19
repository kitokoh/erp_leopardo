# dialogs/role_management_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QLabel, QInputDialog, QLineEdit, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from app.db.cruds.users import roles_crud, users_crud, permissions_crud
from app.db.cruds.users import role_permissions_crud
# from auth.permissions import has_permission, P_MANAGE_ROLES # For later, if dialog itself checks perms
from PyQt5.QtWidgets import QWidget
import logging

class RoleManagementDialog(QDialog):
    # Signal to indicate roles might have changed, so other parts of UI can refresh
    roles_changed_signal = pyqtSignal()

    def __init__(self, current_user_info: dict, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info # Needed for logging and potentially permissions
        self.parent_window = parent
        self.setWindowTitle(self.tr("Gestion des Rôles et Permissions"))
        self.setMinimumSize(800, 600) # Increased size for permissions panel

        self._setup_ui()
        self.load_roles()
        self._update_buttons_state()
        self._load_all_available_permissions() # Load all permissions once

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Splitter for Roles list and Permissions editor
        splitter = QSplitter(Qt.Horizontal)

        # Left Pane: Roles Management
        roles_pane_widget = QWidget()
        roles_layout = QVBoxLayout(roles_pane_widget)

        title_label = QLabel(self.tr("Liste des Rôles"))
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        roles_layout.addWidget(title_label)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels([
            self.tr("ID Rôle"), self.tr("Nom du Rôle"), self.tr("Description")
        ])
        self.roles_table.setColumnHidden(0, True)
        self.roles_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.roles_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.roles_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.roles_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.itemSelectionChanged.connect(self._on_role_selection_changed)
        roles_layout.addWidget(self.roles_table)

        role_buttons_layout = QHBoxLayout()
        self.add_role_button = QPushButton("➕ " + self.tr("Ajouter Rôle"))
        self.add_role_button.clicked.connect(self._handle_add_role) # Connect action
        role_buttons_layout.addWidget(self.add_role_button)

        self.edit_role_button = QPushButton("✏️ " + self.tr("Modifier Rôle"))
        self.edit_role_button.clicked.connect(self._handle_edit_role) # Connect action
        role_buttons_layout.addWidget(self.edit_role_button)

        self.delete_role_button = QPushButton("🗑️ " + self.tr("Supprimer Rôle"))
        self.delete_role_button.clicked.connect(self._handle_delete_role) # Connect action
        role_buttons_layout.addWidget(self.delete_role_button)
        roles_layout.addLayout(role_buttons_layout)
        roles_pane_widget.setLayout(roles_layout)
        splitter.addWidget(roles_pane_widget)

        # Right Pane: Permissions Management
        permissions_pane_widget = QGroupBox(self.tr("Permissions pour le Rôle Sélectionné"))
        permissions_layout = QVBoxLayout(permissions_pane_widget)

        self.permissions_list_widget = QListWidget()
        # Populate with all available permissions, checking ones assigned to the selected role
        # Items will be checkable
        permissions_layout.addWidget(self.permissions_list_widget)

        self.save_permissions_button = QPushButton("💾 " + self.tr("Sauvegarder Permissions"))
        self.save_permissions_button.clicked.connect(self._handle_save_permissions)
        self.save_permissions_button.setEnabled(False) # Enabled when a role is selected
        permissions_layout.addWidget(self.save_permissions_button)

        permissions_pane_widget.setLayout(permissions_layout)
        splitter.addWidget(permissions_pane_widget)

        main_layout.addWidget(splitter)

        # Overall Dialog Buttons (Refresh, Close)
        dialog_buttons_layout = QHBoxLayout()
        dialog_buttons_layout.addStretch()
        self.refresh_button = QPushButton("🔄 " + self.tr("Actualiser Tout"))
        self.refresh_button.clicked.connect(self.load_roles_and_permissions) # Refresh both roles and current permissions view
        dialog_buttons_layout.addWidget(self.refresh_button)

        self.close_button = QPushButton(self.tr("Fermer"))
        self.close_button.clicked.connect(self.accept)
        dialog_buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(dialog_buttons_layout)
        self.setLayout(main_layout)

        # Set initial splitter sizes (e.g., 40% for roles, 60% for permissions)
        splitter.setSizes([self.width() * 4 // 10, self.width() * 6 // 10])


    def _on_role_selection_changed(self):
        self._update_buttons_state()
        self._load_permissions_for_selected_role()

    def load_roles_and_permissions(self):
        self.load_roles()
        # This will also trigger _load_permissions_for_selected_role if a role remains selected
        # or clear permissions if no role is selected.

    def load_roles(self):
        """Loads roles from the database into the table widget."""
        current_selected_id = self._get_selected_role_id()
        self.roles_table.setRowCount(0)
        self.permissions_list_widget.clear() # Clear permissions when roles are reloaded
        try:
            roles = roles_crud.list_roles()
            if roles:
                self.roles_table.setRowCount(len(roles))
                for row_idx, role_data in enumerate(roles):
                    role_id_item = QTableWidgetItem(str(role_data.get("role_id")))
                    # Store role_id in user data for easy retrieval, though it's also in column 0
                    role_id_item.setData(Qt.UserRole, role_data.get("role_id"))

                    name_item = QTableWidgetItem(role_data.get("role_name", self.tr("N/A")))
                    description_item = QTableWidgetItem(role_data.get("description", ""))

                    self.roles_table.setItem(row_idx, 0, role_id_item)
                    self.roles_table.setItem(row_idx, 1, name_item)
                    self.roles_table.setItem(row_idx, 2, description_item)

            # Try to reselect the previously selected role
            if current_selected_id is not None:
                for r_idx in range(self.roles_table.rowCount()):
                    if int(self.roles_table.item(r_idx, 0).text()) == current_selected_id:
                        self.roles_table.selectRow(r_idx)
                        break

            self._update_buttons_state() # This will also trigger permission load if selection changes
            if not self.roles_table.selectedItems(): # If nothing is selected (e.g. list empty or prev selection gone)
                 self.permissions_list_widget.clear()
                 self.save_permissions_button.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"),
                                 self.tr("Impossible de charger la liste des rôles : {0}").format(str(e)))
            logging.error(f"Error loading roles into dialog: {e}", exc_info=True)


    def _load_all_available_permissions(self):
        """Loads all permissions from DB and stores them for populating the list."""
        try:
            self.all_available_permissions = permissions_crud.list_all_permissions()
            if not self.all_available_permissions:
                QMessageBox.warning(self, self.tr("Permissions non trouvées"),
                                    self.tr("Aucune permission n'a été trouvée dans la base de données. "
                                         "La gestion des permissions sera limitée."))
        except Exception as e:
            self.all_available_permissions = []
            QMessageBox.critical(self, self.tr("Erreur Chargement Permissions"),
                                 self.tr("Impossible de charger la liste globale des permissions : {0}").format(str(e)))
            logging.error(f"Error loading all available permissions: {e}", exc_info=True)

    def _load_permissions_for_selected_role(self):
        """Loads permissions for the currently selected role into the QListWidget."""
        self.permissions_list_widget.clear()
        selected_role_id = self._get_selected_role_id()

        if selected_role_id is None:
            self.save_permissions_button.setEnabled(False)
            return

        try:
            assigned_permissions = role_permissions_crud.get_permissions_for_role(selected_role_id)
            assigned_set = set(assigned_permissions)

            for perm_data in self.all_available_permissions:
                perm_key = perm_data['permission_key']
                perm_desc = perm_data.get('description', perm_key) # Use key if desc is missing

                item = QListWidgetItem(f"{perm_key} - {perm_desc}")
                item.setData(Qt.UserRole, perm_key) # Store key for later retrieval
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if perm_key in assigned_set:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.permissions_list_widget.addItem(item)

            self.save_permissions_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Permissions Rôle"),
                                 self.tr("Impossible de charger les permissions pour le rôle ID {0}: {1}").format(selected_role_id, str(e)))
            logging.error(f"Error loading permissions for role {selected_role_id}: {e}", exc_info=True)
            self.save_permissions_button.setEnabled(False)


    def _handle_save_permissions(self):
        """Saves the checked permissions for the selected role."""
        selected_role_id = self._get_selected_role_id()
        if selected_role_id is None:
            QMessageBox.warning(self, self.tr("Aucun Rôle Sélectionné"),
                                self.tr("Veuillez sélectionner un rôle avant de sauvegarder les permissions."))
            return

        selected_role_data = self._get_selected_role_data()
        role_name_for_log = selected_role_data.get("role_name", f"ID {selected_role_id}") if selected_role_data else f"ID {selected_role_id}"


        permissions_to_assign = []
        for i in range(self.permissions_list_widget.count()):
            item = self.permissions_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                permissions_to_assign.append(item.data(Qt.UserRole)) # Get stored permission_key

        try:
            success = role_permissions_crud.set_permissions_for_role(selected_role_id, permissions_to_assign)
            if success:
                QMessageBox.information(self, self.tr("Permissions Sauvegardées"),
                                        self.tr("Les permissions pour le rôle '{0}' ont été mises à jour.").format(role_name_for_log))
                self.roles_changed_signal.emit() # Notify main window (important for has_permission to reflect changes)

                # Log activity
                try:
                    from db.cruds import activity_logs_crud
                    log_data = {
                        "user_id": self.current_user_info.get('user_id'),
                        "action_type": "ROLE_PERMISSIONS_UPDATED",
                        "details": f"Permissions mises à jour pour le rôle '{role_name_for_log}' (ID: {selected_role_id}). Nouvelles permissions: {', '.join(permissions_to_assign) if permissions_to_assign else 'Aucune'}.",
                        "related_entity_type": "Role",
                        "related_entity_id": selected_role_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                except Exception as e_log:
                    logging.error(f"Failed to log ROLE_PERMISSIONS_UPDATED for role {selected_role_id}: {e_log}", exc_info=True)

            else:
                QMessageBox.critical(self, self.tr("Erreur Sauvegarde"),
                                     self.tr("Une erreur est survenue lors de la sauvegarde des permissions pour le rôle '{0}'.").format(role_name_for_log))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"),
                                 self.tr("Une erreur inattendue est survenue: {0}").format(str(e)))
            logging.error(f"Unexpected error saving permissions for role {selected_role_id}: {e}", exc_info=True)


    def _get_selected_role_id(self) -> int | None:
        """Helper to get the role_id from the selected row."""
        selected_items = self.roles_table.selectedItems()
        if not selected_items:
            return None
        # Assuming role_id is in the first column (column 0)
        role_id_item = self.roles_table.item(selected_items[0].row(), 0)
        return int(role_id_item.text()) if role_id_item else None

    def _get_selected_role_data(self) -> dict | None:
        """Helper to get all data for the selected role."""
        selected_row = self.roles_table.currentRow()
        if selected_row < 0:
            return None

        role_id = int(self.roles_table.item(selected_row, 0).text())
        role_name = self.roles_table.item(selected_row, 1).text()
        description = self.roles_table.item(selected_row, 2).text()

        return {"role_id": role_id, "role_name": role_name, "description": description}

    def _update_buttons_state(self):
        """Enable/disable action buttons based on table selection."""
        has_selection = bool(self.roles_table.selectedItems())
        self.edit_role_button.setEnabled(has_selection)
        self.delete_role_button.setEnabled(has_selection)
        # Add_role_button is always enabled (or based on general permission if implemented here)

    def _handle_add_role(self):
        """Handles adding a new role."""
        role_name, ok_name = QInputDialog.getText(self, self.tr("Ajouter un Rôle"),
                                                  self.tr("Nom du nouveau rôle:"), QLineEdit.Normal)
        if not (ok_name and role_name.strip()):
            if ok_name: # User pressed OK but entered empty or whitespace-only name
                QMessageBox.warning(self, self.tr("Nom Invalide"),
                                    self.tr("Le nom du rôle ne peut pas être vide."))
            return # User cancelled or entered invalid name

        description, ok_desc = QInputDialog.getText(self, self.tr("Ajouter un Rôle"),
                                                    self.tr("Description du rôle (optionnel):"), QLineEdit.Normal)
        if not ok_desc:
            return # User cancelled description input

        try:
            new_role_id = roles_crud.add_role(role_name.strip(), description.strip())
            if new_role_id is not None:
                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Le rôle '{0}' a été ajouté avec succès.").format(role_name.strip()))
                self.load_roles() # Refresh the list
                self.roles_changed_signal.emit() # Notify that roles have changed

                # Log activity (assuming activity_logs_crud is available or imported)
                try:
                    from db.cruds import activity_logs_crud # Local import if not already at top
                    log_data = {
                        "user_id": self.current_user_info.get('user_id'),
                        "action_type": "ROLE_ADDED",
                        "details": f"Rôle '{role_name.strip()}' (ID: {new_role_id}) ajouté. Description: '{description.strip()}'.",
                        "related_entity_type": "Role",
                        "related_entity_id": new_role_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                    logging.info(f"Activity logged for ROLE_ADDED: {new_role_id} by {self.current_user_info.get('user_id')}")
                except ImportError:
                    logging.warning("activity_logs_crud not found, skipping logging for ROLE_ADDED.")
                except Exception as e_log:
                    logging.error(f"Failed to log ROLE_ADDED activity for role {new_role_id}: {e_log}", exc_info=True)

            else:
                QMessageBox.critical(self, self.tr("Erreur"),
                                     self.tr("Impossible d'ajouter le rôle. Le nom du rôle existe peut-être déjà."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"),
                                 self.tr("Une erreur est survenue lors de l'ajout du rôle : {0}").format(str(e)))
            logging.error(f"Unexpected error adding role '{role_name.strip()}': {e}", exc_info=True)

    def _handle_edit_role(self):
        """Handles editing an existing role."""
        selected_role_data = self._get_selected_role_data()
        if not selected_role_data:
            QMessageBox.warning(self, self.tr("Aucune Sélection"),
                                self.tr("Veuillez sélectionner un rôle à modifier."))
            return

        role_id = selected_role_data["role_id"]
        current_name = selected_role_data["role_name"]
        current_description = selected_role_data["description"]

        # Prompt for new name
        new_name, ok_name = QInputDialog.getText(self, self.tr("Modifier le Rôle"),
                                                 self.tr("Nouveau nom pour '{0}':").format(current_name),
                                                 QLineEdit.Normal, current_name)
        if not (ok_name and new_name.strip()):
            if ok_name: # User pressed OK but entered empty or whitespace-only name
                QMessageBox.warning(self, self.tr("Nom Invalide"),
                                    self.tr("Le nom du rôle ne peut pas être vide."))
            return # User cancelled or entered invalid name

        # Prompt for new description
        new_description, ok_desc = QInputDialog.getText(self, self.tr("Modifier le Rôle"),
                                                        self.tr("Nouvelle description pour '{0}' (optionnel):").format(new_name.strip()),
                                                        QLineEdit.Normal, current_description)
        if not ok_desc:
            return # User cancelled description input

        try:
            success = roles_crud.update_role(role_id, new_name.strip(), new_description.strip())
            if success:
                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Le rôle '{0}' a été mis à jour.").format(new_name.strip()))
                self.load_roles() # Refresh the list
                self.roles_changed_signal.emit() # Notify

                # Log activity
                try:
                    from db.cruds import activity_logs_crud # Local import
                    log_data = {
                        "user_id": self.current_user_info.get('user_id'),
                        "action_type": "ROLE_UPDATED",
                        "details": f"Rôle ID {role_id} ('{current_name}' -> '{new_name.strip()}') mis à jour. Description: ('{current_description}' -> '{new_description.strip()}').",
                        "related_entity_type": "Role",
                        "related_entity_id": role_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                    logging.info(f"Activity logged for ROLE_UPDATED: {role_id} by {self.current_user_info.get('user_id')}")
                except ImportError:
                    logging.warning("activity_logs_crud not found, skipping logging for ROLE_UPDATED.")
                except Exception as e_log:
                    logging.error(f"Failed to log ROLE_UPDATED activity for role {role_id}: {e_log}", exc_info=True)
            else:
                QMessageBox.critical(self, self.tr("Erreur"),
                                     self.tr("Impossible de mettre à jour le rôle. Le nouveau nom existe peut-être déjà ou le rôle n'a pas été trouvé."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"),
                                 self.tr("Une erreur est survenue lors de la mise à jour du rôle : {0}").format(str(e)))
            logging.error(f"Unexpected error updating role ID {role_id}: {e}", exc_info=True)

    def _handle_delete_role(self):
        """Handles deleting an existing role, with safeguards."""
        selected_role_data = self._get_selected_role_data()
        if not selected_role_data:
            QMessageBox.warning(self, self.tr("Aucune Sélection"),
                                self.tr("Veuillez sélectionner un rôle à supprimer."))
            return

        role_id = selected_role_data["role_id"]
        role_name = selected_role_data["role_name"]

        # Prevent deletion of core roles like "Administrateur" if they have special IDs or names
        # This is a simple check; more robust would be a flag in the DB 'is_system_role'
        if role_name.lower() == "administrateur" or role_id == 1: # Assuming ID 1 is admin
             QMessageBox.critical(self, self.tr("Suppression Interdite"),
                                 self.tr("Le rôle Administrateur ne peut pas être supprimé."))
             return

        # Check if the role is used by any users
        try:
            if roles_crud.is_role_used(role_id):
                QMessageBox.warning(self, self.tr("Rôle Utilisé"),
                                    self.tr("Le rôle '{0}' est actuellement assigné à des utilisateurs "
                                         "et ne peut pas être supprimé. Veuillez d'abord réassigner ces utilisateurs à d'autres rôles.").format(role_name))
                return
        except Exception as e_check:
            QMessageBox.critical(self, self.tr("Erreur de Vérification"),
                                 self.tr("Impossible de vérifier si le rôle est utilisé : {0}").format(str(e_check)))
            logging.error(f"Error checking if role {role_id} is used: {e_check}", exc_info=True)
            return # Abort deletion if check fails

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer définitivement le rôle '{0}' ? "
                                          "Cette action ne peut pas être annulée.").format(role_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                success = roles_crud.delete_role(role_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"),
                                            self.tr("Le rôle '{0}' a été supprimé.").format(role_name))
                    self.load_roles() # Refresh the list
                    self.roles_changed_signal.emit() # Notify

                    # Log activity
                    try:
                        from db.cruds import activity_logs_crud # Local import
                        log_data = {
                            "user_id": self.current_user_info.get('user_id'),
                            "action_type": "ROLE_DELETED",
                            "details": f"Rôle '{role_name}' (ID: {role_id}) supprimé.",
                            "related_entity_type": "Role",
                            "related_entity_id": role_id # The ID still useful for historical logs
                        }
                        activity_logs_crud.add_activity_log(log_data)
                        logging.info(f"Activity logged for ROLE_DELETED: {role_id} by {self.current_user_info.get('user_id')}")
                    except ImportError:
                        logging.warning("activity_logs_crud not found, skipping logging for ROLE_DELETED.")
                    except Exception as e_log:
                        logging.error(f"Failed to log ROLE_DELETED activity for role {role_id}: {e_log}", exc_info=True)
                else:
                    # This case might occur if the role was deleted by another admin between check and delete,
                    # or if a DB-level constraint (not implemented here but possible) prevented it.
                    QMessageBox.critical(self, self.tr("Erreur"),
                                         self.tr("Impossible de supprimer le rôle '{0}'. "
                                              "Il se peut qu'il ait déjà été supprimé ou qu'une erreur se soit produite.").format(role_name))
            except Exception as e: # Catch unexpected errors during deletion itself
                QMessageBox.critical(self, self.tr("Erreur Inattendue"),
                                     self.tr("Une erreur est survenue lors de la suppression du rôle : {0}").format(str(e)))
                logging.error(f"Unexpected error deleting role ID {role_id}: {e}", exc_info=True)

if __name__ == '__main__':
    # This is for testing the dialog independently
    import sys
    from PyQt5.QtWidgets import QApplication
    # Mock current_user_info for testing
    mock_user_info = {"user_id": "test_admin_id", "username": "test_admin", "role_name": "Administrateur"}

    # Mock roles_crud for standalone testing if db is not available
    class MockRolesCRUD:
        def list_roles(self):
            return [
                {"role_id": 1, "role_name": "Administrateur", "description": "Accès total"},
                {"role_id": 2, "role_name": "Éditeur", "description": "Peut modifier le contenu"},
                {"role_id": 3, "role_name": "Lecteur", "description": "Accès en lecture seule"}
            ]
        # Add mock add_role, update_role, delete_role if needed for deeper testing of handlers later

    # Uncomment to use mock if your DB setup is complex for quick UI tests
    # roles_crud = MockRolesCRUD()

    app = QApplication(sys.argv)
    # Ensure resources are loaded (if your icons are in a .qrc file)
    # import resources_rc # Assuming you have a resources_rc.py from pyrcc5

    dialog = RoleManagementDialog(current_user_info=mock_user_info)
    dialog.show()
    sys.exit(app.exec_())
