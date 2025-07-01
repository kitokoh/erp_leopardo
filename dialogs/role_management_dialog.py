# dialogs/role_management_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QLabel, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from db.cruds import roles_crud
# from auth.permissions import has_permission, P_MANAGE_ROLES # Pour un contrôle plus fin des actions

logger = logging.getLogger(__name__)

class RoleManagementDialog(QDialog):
    def __init__(self, current_user_info: dict, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info # Peut être utilisé pour les permissions futures
        self.setWindowTitle(self.tr("Gestion des Rôles"))
        self.setMinimumSize(400, 300)
        self.setWindowIcon(QIcon(":/icons/team.svg")) # Placeholder icon

        self._setup_ui()
        self.load_roles()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel(self.tr("Liste des Rôles Existants"))
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(title_label)

        self.roles_list_widget = QListWidget()
        self.roles_list_widget.itemSelectionChanged.connect(self._update_action_buttons_state)
        main_layout.addWidget(self.roles_list_widget)

        actions_layout = QHBoxLayout()
        self.add_role_button = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Ajouter Rôle"))
        self.add_role_button.clicked.connect(self._handle_add_role)
        actions_layout.addWidget(self.add_role_button)

        self.edit_role_button = QPushButton(QIcon(":/icons/pencil.svg"), self.tr("Modifier Rôle"))
        self.edit_role_button.clicked.connect(self._handle_edit_role)
        actions_layout.addWidget(self.edit_role_button)

        self.delete_role_button = QPushButton(QIcon(":/icons/trash.svg"), self.tr("Supprimer Rôle"))
        self.delete_role_button.setObjectName("dangerButton")
        self.delete_role_button.clicked.connect(self._handle_delete_role)
        actions_layout.addWidget(self.delete_role_button)

        main_layout.addLayout(actions_layout)

        self.close_button = QPushButton(self.tr("Fermer"))
        self.close_button.clicked.connect(self.accept) # Accept pour fermer simplement
        main_layout.addWidget(self.close_button, alignment=Qt.AlignRight)

        self._update_action_buttons_state() # Initial state

    def _update_action_buttons_state(self):
        has_selection = bool(self.roles_list_widget.selectedItems())
        self.edit_role_button.setEnabled(has_selection)
        self.delete_role_button.setEnabled(has_selection)

    def load_roles(self):
        self.roles_list_widget.clear()
        try:
            roles = roles_crud.list_roles()
            if roles:
                for role in roles:
                    item_text = f"{role['role_name']}"
                    if role.get('description'):
                        item_text += f" - ({role['description']})"
                    list_item = QListWidgetItem(item_text)
                    list_item.setData(Qt.UserRole, role['role_id']) # Store role_id
                    list_item.setData(Qt.UserRole + 1, role['role_name']) # Store role_name
                    list_item.setData(Qt.UserRole + 2, role.get('description', '')) # Store description
                    self.roles_list_widget.addItem(list_item)
            self._update_action_buttons_state()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement"),
                                 self.tr("Impossible de charger la liste des rôles: {0}").format(str(e)))
            logger.error(f"Error loading roles: {e}", exc_info=True)

    def _handle_add_role(self):
        # Simple dialog for name and description
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Ajouter un Nouveau Rôle"))
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        name_edit = QLineEdit()
        form_layout.addRow(self.tr("Nom du Rôle:"), name_edit)
        desc_edit = QLineEdit()
        form_layout.addRow(self.tr("Description (optionnel):"), desc_edit)

        layout.addLayout(form_layout)

        button_box = QPushButton(self.tr("Créer Rôle"), dialog)
        button_box.clicked.connect(dialog.accept)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            role_name = name_edit.text().strip()
            description = desc_edit.text().strip()
            if not role_name:
                QMessageBox.warning(self, self.tr("Nom Requis"), self.tr("Le nom du rôle est obligatoire."))
                return

            try:
                if roles_crud.get_role_by_name(role_name):
                    QMessageBox.warning(self, self.tr("Rôle Existant"), self.tr("Un rôle avec ce nom existe déjà."))
                    return

                new_role_id = roles_crud.add_role(role_name, description)
                if new_role_id:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Rôle '{0}' ajouté avec succès.").format(role_name))
                    self.load_roles()
                    # TODO: Signal that roles list changed so other parts of UI can update (e.g., UserManagementPage filter)
                else:
                    QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Impossible d'ajouter le rôle."))
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur: {0}").format(str(e)))
                logger.error(f"Error adding role '{role_name}': {e}", exc_info=True)


    def _handle_edit_role(self):
        selected_items = self.roles_list_widget.selectedItems()
        if not selected_items:
            return

        current_item = selected_items[0]
        role_id = current_item.data(Qt.UserRole)
        current_name = current_item.data(Qt.UserRole + 1)
        current_desc = current_item.data(Qt.UserRole + 2)

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Modifier le Rôle"))
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        name_edit = QLineEdit(current_name)
        form_layout.addRow(self.tr("Nom du Rôle:"), name_edit)
        desc_edit = QLineEdit(current_desc)
        form_layout.addRow(self.tr("Description (optionnel):"), desc_edit)

        layout.addLayout(form_layout)

        button_box = QPushButton(self.tr("Sauvegarder"), dialog)
        button_box.clicked.connect(dialog.accept)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            new_name = name_edit.text().strip()
            new_desc = desc_edit.text().strip()

            if not new_name:
                QMessageBox.warning(self, self.tr("Nom Requis"), self.tr("Le nom du rôle est obligatoire."))
                return

            if new_name != current_name: # Check if name changed before checking for existence
                existing_role = roles_crud.get_role_by_name(new_name)
                if existing_role and existing_role['role_id'] != role_id:
                    QMessageBox.warning(self, self.tr("Rôle Existant"), self.tr("Un autre rôle avec le nom '{0}' existe déjà.").format(new_name))
                    return

            try:
                if roles_crud.update_role(role_id, new_name, new_desc):
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Rôle mis à jour avec succès."))
                    self.load_roles()
                    # TODO: Signal role change
                else:
                    QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Impossible de mettre à jour le rôle."))
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur: {0}").format(str(e)))
                 logger.error(f"Error updating role ID {role_id}: {e}", exc_info=True)


    def _handle_delete_role(self):
        selected_items = self.roles_list_widget.selectedItems()
        if not selected_items:
            return

        role_id = selected_items[0].data(Qt.UserRole)
        role_name = selected_items[0].data(Qt.UserRole + 1)

        # Check if the role is currently in use by any user
        users_with_role = users_crud.list_users(role_id_filter=role_id, include_deleted=True) # Check even soft-deleted users
        if users_with_role:
            QMessageBox.warning(self, self.tr("Suppression Impossible"),
                                self.tr("Le rôle '{0}' est actuellement assigné à {1} utilisateur(s) et ne peut pas être supprimé.\n"
                                        "Veuillez d'abord réassigner ces utilisateurs à un autre rôle.").format(role_name, len(users_with_role)))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer le rôle '{0}' ?\n"
                                             "Cette action est irréversible.").format(role_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if roles_crud.delete_role(role_id):
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Rôle '{0}' supprimé.").format(role_name))
                    self.load_roles()
                    # TODO: Signal role change
                else:
                    QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Impossible de supprimer le rôle. Il est peut-être encore utilisé ou une erreur s'est produite."))
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur: {0}").format(str(e)))
                logger.error(f"Error deleting role ID {role_id}: {e}", exc_info=True)


if __name__ == '__main__':
    # This part needs a QApplication instance to run QDialogs.
    # It also needs a functional database connection for the CRUD operations.
    # For standalone testing, you might need to mock db_manager or ensure DB is set up.

    # Simplified __main__ for basic dialog structure test (without DB interaction)
    from PyQt5.QtWidgets import QApplication
    import sys
    logging.basicConfig(level=logging.DEBUG)

    # Mock current_user_info
    mock_user = {'user_id': 'test_admin_id', 'username': 'test_admin', 'role_name': 'Administrator'}

    # Mock roles_crud for UI testing if DB is not available for __main__
    class MockRolesCRUD:
        def list_roles(self): return [{'role_id': 1, 'role_name': 'Admin', 'description': 'Administrator role'}, {'role_id': 2, 'role_name': 'User', 'description': 'Standard user'}]
        def get_role_by_name(self, name): return None # Simulate not found for new roles
        def add_role(self, name, desc): print(f"Mock: Add role {name}"); return 3
        def update_role(self, id, name, desc): print(f"Mock: Update role {id}"); return True
        def delete_role(self, id): print(f"Mock: Delete role {id}"); return True

    class MockUsersCRUD:
        def list_users(self, role_id_filter=None, include_deleted=False):
            if role_id_filter == 1: # Simulate Admin role in use
                return [{'user_id': 'user1', 'username': 'admin_user'}]
            return [] # Simulate other roles not in use

    # Replace actual cruds with mocks for this test run
    original_roles_crud = roles_crud
    original_users_crud = users_crud
    roles_crud = MockRolesCRUD()
    users_crud = MockUsersCRUD()

    app = QApplication(sys.argv)
    dialog = RoleManagementDialog(current_user_info=mock_user)
    dialog.show()
    result = app.exec_()

    # Restore original cruds if needed by other tests in same session (not typical for __main__)
    roles_crud = original_roles_crud
    users_crud = original_users_crud

    sys.exit(result)

[end of dialogs/role_management_dialog.py]
