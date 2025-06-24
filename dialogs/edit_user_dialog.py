# dialogs/edit_user_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QDialogButtonBox, QLabel
)
from PyQt5.QtGui import QIcon
from db.cruds import users_crud, roles_crud
from auth.permissions import P_MANAGE_USERS, has_permission # For internal check if needed, though dialog access is already controlled

logger = logging.getLogger(__name__)

class EditUserDialog(QDialog):
    def __init__(self, user_id: str, current_admin_user_info: dict, parent=None):
        super().__init__(parent)
        self.user_id_to_edit = user_id
        self.current_admin_user_info = current_admin_user_info # Info of the admin performing the edit
        self.user_data_to_edit = None

        self.setWindowTitle(self.tr("Modifier Utilisateur"))
        self.setWindowIcon(QIcon(":/icons/user.svg")) # Placeholder icon
        self.setMinimumWidth(400)

        self._load_user_data()
        if not self.user_data_to_edit:
            # Error already shown by _load_user_data, just prevent dialog setup
            # Schedule close, so constructor finishes before dialog is destroyed.
            self.close()
            return

        self._setup_ui()
        self._populate_fields()

    def _load_user_data(self):
        self.user_data_to_edit = users_crud.get_user_by_id(self.user_id_to_edit)
        if not self.user_data_to_edit:
            QMessageBox.critical(self, self.tr("Erreur"),
                                 self.tr("Impossible de charger les données de l'utilisateur ID: {0}").format(self.user_id_to_edit))
            logger.error(f"EditUserDialog: Could not load data for user_id: {self.user_id_to_edit}")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_label = QLabel(self.user_data_to_edit.get('username', ''))
        form_layout.addRow(self.tr("Nom d'utilisateur:"), self.username_label)

        self.full_name_input = QLineEdit()
        form_layout.addRow(self.tr("Nom Complet:"), self.full_name_input)

        self.email_input = QLineEdit()
        form_layout.addRow(self.tr("Email:"), self.email_input)

        self.role_combo = QComboBox()
        form_layout.addRow(self.tr("Rôle:"), self.role_combo)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText(self.tr("Sauvegarder"))
        self.button_box.button(QDialogButtonBox.Save).setIcon(QIcon(":/icons/save.svg")) # Placeholder
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))

        self.button_box.accepted.connect(self._save_changes)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _populate_fields(self):
        if not self.user_data_to_edit:
            return

        self.full_name_input.setText(self.user_data_to_edit.get('full_name', ''))
        self.email_input.setText(self.user_data_to_edit.get('email', ''))

        # Populate roles combo
        try:
            all_roles = roles_crud.list_roles()
            if all_roles:
                for role in all_roles:
                    self.role_combo.addItem(role['role_name'], role['role_id'])

            # Set current role
            current_role_id = self.user_data_to_edit.get('role_id')
            if current_role_id is not None:
                index = self.role_combo.findData(current_role_id)
                if index >= 0:
                    self.role_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Failed to populate roles in EditUserDialog: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement Rôles"),
                                self.tr("Impossible de charger la liste des rôles."))

    def _save_changes(self):
        admin_role = self.current_admin_user_info.get('role_name')
        if not has_permission(admin_role, P_MANAGE_USERS):
            QMessageBox.critical(self, self.tr("Accès Refusé"), self.tr("Vous n'avez pas les permissions pour modifier les utilisateurs."))
            return

        new_full_name = self.full_name_input.text().strip()
        new_email = self.email_input.text().strip()
        new_role_id = self.role_combo.currentData()

        if not new_full_name: # Basic validation
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le nom complet est requis."))
            return
        if not new_email:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("L'email est requis."))
            return
        if new_role_id is None:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Un rôle doit être sélectionné."))
            return

        update_data_user = {}
        changed = False

        if new_full_name != self.user_data_to_edit.get('full_name', ''):
            update_data_user['full_name'] = new_full_name
            changed = True

        if new_email != self.user_data_to_edit.get('email', ''):
            update_data_user['email'] = new_email
            changed = True

        user_update_success = True
        if update_data_user: # Only update if there are changes to user details
            # Add updated_by_user_id if Users table supports it (from previous audit work)
            # For now, users_crud.update_user does not explicitly take updated_by_user_id
            # but if it's in `update_data_user` and `users_crud` handles it, it's fine.
            # This was handled in `ContactController` by adding it to the data dict.
            # Here, `users_crud.update_user` would need similar logic or direct param.
            # Let's assume for now `users_crud.update_user` handles `updated_at` automatically.
            if users_crud.update_user(self.user_id_to_edit, update_data_user):
                logger.info(f"User details updated for user_id: {self.user_id_to_edit}")
            else:
                user_update_success = False
                QMessageBox.critical(self, self.tr("Erreur Sauvegarde"),
                                     self.tr("Impossible de sauvegarder les modifications des détails de l'utilisateur."))
                return

        role_update_success = True
        if new_role_id != self.user_data_to_edit.get('role_id'):
            changed = True
            if users_crud.update_user_role(self.user_id_to_edit, new_role_id):
                logger.info(f"User role updated for user_id: {self.user_id_to_edit} to role_id: {new_role_id}")
            else:
                role_update_success = False
                QMessageBox.critical(self, self.tr("Erreur Sauvegarde"),
                                     self.tr("Impossible de sauvegarder la modification du rôle de l'utilisateur."))
                return

        if not changed:
            QMessageBox.information(self, self.tr("Aucun Changement"), self.tr("Aucune modification n'a été détectée."))
            self.accept() # Close dialog even if no changes
            return

        if user_update_success and role_update_success:
            QMessageBox.information(self, self.tr("Succès"), self.tr("Utilisateur mis à jour avec succès."))
            self.accept()
        # Else, error messages already shown

if __name__ == '__main__':
    # This is a simplified test, assumes DB is set up and roles exist.
    from PyQt5.QtWidgets import QApplication
    import sys
    logging.basicConfig(level=logging.DEBUG)

    # Mock current_admin_user_info for testing
    mock_admin_info = {
        'user_id': 'admin_uuid',
        'username': 'test_admin',
        'role_name': 'Administrator' # Ensure this role has P_MANAGE_USERS
    }

    # You would need a valid user_id from your database to test editing
    # For example, if you seeded an 'admin' user.
    # Ensure users_crud.get_user_by_username('admin') works and gives you an ID.

    # Example: Fetching the seeded admin user's ID to test the dialog
    # This requires DB connection and seeded data.
    # test_user_to_edit_id = None
    # try:
    #     admin_user = users_crud.get_user_by_username("admin") # Default seeded admin
    #     if admin_user:
    #         test_user_to_edit_id = admin_user['user_id']
    # except Exception as e:
    #     print(f"Could not fetch admin user for testing EditUserDialog: {e}")

    # if not test_user_to_edit_id:
    #     print("Cannot run EditUserDialog test without a valid user_id_to_edit and seeded data.")
    #     sys.exit()

    app = QApplication(sys.argv)
    # Replace 'some_user_uuid_to_edit' with an actual user_id from your DB for testing
    # For a quick test, ensure you have a user. If not, this dialog will show an error and close.
    dialog = EditUserDialog(user_id_to_edit='some_user_uuid_to_edit',
                            current_admin_user_info=mock_admin_info)
    if dialog.isVisible(): # Check if dialog didn't close itself due to load error
        dialog.exec_()
    else:
        print("Dialog closed on init, likely due to user_id not found or other load error.")

```

This creates the `EditUserDialog`.
Now, I'll integrate this dialog into `UserManagementPage._handle_edit_user`.
