# dialogs/role_management_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QLabel, QInputDialog, QLineEdit, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from db.cruds import roles_crud, users_crud # Assuming users_crud might be needed for checking role usage
# from auth.permissions import has_permission, P_MANAGE_ROLES # For later, if dialog itself checks perms

import logging

class RoleManagementDialog(QDialog):
    # Signal to indicate roles might have changed, so other parts of UI can refresh
    roles_changed_signal = pyqtSignal()

    def __init__(self, current_user_info: dict, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info # Needed for logging and potentially permissions
        self.parent_window = parent
        self.setWindowTitle(self.tr("Gestion des Rôles"))
        self.setWindowIcon(QIcon(":/icons/shield.svg")) # Or another appropriate icon
        self.setMinimumSize(500, 350)

        self._setup_ui()
        self.load_roles()
        self._update_buttons_state()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel(self.tr("Liste des Rôles"))
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Using QTableWidget for more structured display (ID, Name, Description)
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels([
            self.tr("ID Rôle"), self.tr("Nom du Rôle"), self.tr("Description")
        ])
        self.roles_table.setColumnHidden(0, True) # Hide role_id column
        self.roles_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.roles_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.roles_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.roles_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.itemSelectionChanged.connect(self._update_buttons_state)
        # self.roles_table.itemDoubleClicked.connect(self._handle_edit_role) # Optional: double click to edit

        main_layout.addWidget(self.roles_table)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        self.add_role_button = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Ajouter Rôle"))
        self.add_role_button.clicked.connect(self._handle_add_role) # Connect action
        buttons_layout.addWidget(self.add_role_button)

        self.edit_role_button = QPushButton(QIcon(":/icons/pencil.svg"), self.tr("Modifier Rôle"))
        self.edit_role_button.clicked.connect(self._handle_edit_role) # Connect action
        buttons_layout.addWidget(self.edit_role_button)

        self.delete_role_button = QPushButton(QIcon(":/icons/trash-2.svg"), self.tr("Supprimer Rôle"))
        self.delete_role_button.clicked.connect(self._handle_delete_role) # Connect action
        buttons_layout.addWidget(self.delete_role_button)

        buttons_layout.addStretch()

        self.refresh_button = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser"))
        self.refresh_button.clicked.connect(self.load_roles)
        buttons_layout.addWidget(self.refresh_button)

        self.close_button = QPushButton(self.tr("Fermer"))
        self.close_button.clicked.connect(self.accept) # Or self.reject depending on desired behavior
        buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def load_roles(self):
        """Loads roles from the database into the table widget."""
        self.roles_table.setRowCount(0)
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
            self._update_buttons_state()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"),
                                 self.tr("Impossible de charger la liste des rôles : {0}").format(str(e)))
            logging.error(f"Error loading roles into dialog: {e}", exc_info=True)

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
