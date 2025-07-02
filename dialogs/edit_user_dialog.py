# dialogs/edit_user_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QDialogButtonBox, QLabel
)
from PyQt5.QtCore import Qt # Added for Qt.TextSelectableByMouse
from PyQt5.QtGui import QIcon
from db.cruds import users_crud, roles_crud, activity_logs_crud
from auth.permissions import P_MANAGE_USERS, has_permission
from utils import hash_password # Import the hashing function

logger = logging.getLogger(__name__)

class EditUserDialog(QDialog):
    def __init__(self, user_id: str | None, current_admin_user_info: dict, parent=None):
        super().__init__(parent)
        self.user_id_to_edit = user_id
        self.current_admin_user_info = current_admin_user_info
        self.add_mode = (self.user_id_to_edit is None)
        self.user_data_to_edit = {} # Initialize as empty dict

        if self.add_mode:
            self.setWindowTitle(self.tr("Ajouter Utilisateur"))
            self.setWindowIcon(QIcon(":/icons/user-plus.svg"))
            self.user_data_to_edit = {'is_active': True} # Default for new user
        else:
            self.setWindowTitle(self.tr("Modifier Utilisateur"))
            self.setWindowIcon(QIcon(":/icons/user.svg"))
            self._load_user_data_for_edit() # Load data only if editing

        if not self.add_mode and not self.user_data_to_edit:
            # _load_user_data_for_edit would have shown an error and logged
            self.close() # Prevent dialog from showing if load failed in edit mode
            return

        self.setMinimumWidth(400)
        self._setup_ui()
        self._populate_fields()

    def _load_user_data_for_edit(self):
        """Loads user data if in edit mode."""
        if self.add_mode: # Should not be called in add_mode
            return
        self.user_data_to_edit = users_crud.get_user_by_id(self.user_id_to_edit)
        if not self.user_data_to_edit:
            QMessageBox.critical(self, self.tr("Erreur"),
                                 self.tr("Impossible de charger les données de l'utilisateur ID: {0}").format(self.user_id_to_edit))
            logger.error(f"EditUserDialog: Could not load data for user_id: {self.user_id_to_edit}")
            # self.user_data_to_edit remains None or empty, constructor will handle close

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout() # Make it an instance variable to modify later

        # Username field: QLineEdit for add mode, QLabel for edit mode
        if self.add_mode:
            self.username_input = QLineEdit()
            self.form_layout.addRow(self.tr("Nom d'utilisateur:"), self.username_input)
        else:
            # Display User ID (non-editable) in edit mode
            self.user_id_label_display = QLabel(self.user_data_to_edit.get('user_id', self.tr("N/A")))
            self.user_id_label_display.setTextInteractionFlags(Qt.TextSelectableByMouse) # Allow copying
            self.form_layout.addRow(self.tr("ID Utilisateur:"), self.user_id_label_display)

            self.username_label = QLabel(self.user_data_to_edit.get('username', ''))
            self.form_layout.addRow(self.tr("Nom d'utilisateur:"), self.username_label)

        self.full_name_input = QLineEdit()
        self.form_layout.addRow(self.tr("Nom Complet:"), self.full_name_input)

        self.email_input = QLineEdit()
        self.form_layout.addRow(self.tr("Email:"), self.email_input)

        # Password fields (only for add mode)
        if self.add_mode:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.form_layout.addRow(self.tr("Mot de passe:"), self.password_input)

            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.Password)
            self.form_layout.addRow(self.tr("Confirmer le mot de passe:"), self.confirm_password_input)

        self.role_combo = QComboBox()
        self.form_layout.addRow(self.tr("Rôle:"), self.role_combo)

        main_layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button_text = self.tr("Créer") if self.add_mode else self.tr("Sauvegarder")
        self.button_box.button(QDialogButtonBox.Save).setText(save_button_text)
        save_button_icon = QIcon(":/icons/user-plus.svg") if self.add_mode else QIcon(":/icons/save.svg")
        self.button_box.button(QDialogButtonBox.Save).setIcon(save_button_icon)
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))

        self.button_box.accepted.connect(self._save_changes)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _populate_fields(self):
        # Populate common fields if not in add_mode or if there's existing data (e.g. for self-edit)
        if not self.add_mode or (self.add_mode and self.user_id_to_edit): # Latter case for self-edit
            self.full_name_input.setText(self.user_data_to_edit.get('full_name', ''))
            self.email_input.setText(self.user_data_to_edit.get('email', ''))

        # Populate roles combo
        try:
            all_roles = roles_crud.list_roles()
            if all_roles:
                for role in all_roles:
                    self.role_combo.addItem(role['role_name'], role['role_id'])

            # Set current role if editing or if a default is provided for adding
            current_role_id = self.user_data_to_edit.get('role_id')
            if current_role_id is not None:
                index = self.role_combo.findData(current_role_id)
                if index >= 0:
                    self.role_combo.setCurrentIndex(index)
            elif self.add_mode:
                # Optionally set a default role for new users, e.g., "Operator"
                # operator_role_id = roles_crud.get_role_by_name("Operator") # Assuming such a function
                # if operator_role_id:
                #     index = self.role_combo.findData(operator_role_id['role_id'])
                #     if index >= 0: self.role_combo.setCurrentIndex(index)
                pass # No default role set for now, user must select
        except Exception as e: # This is the except for the role population try block
            logger.error(f"Failed to populate roles in EditUserDialog: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement Rôles"),
                                self.tr("Impossible de charger la liste des rôles."))

        # Refinement for "Edit My Account" mode: Disable role_combo for self-edit unless admin
        # This logic should be AFTER the try-except for role population.
        if not self.add_mode and self.user_id_to_edit == self.current_admin_user_info.get('user_id'):
            # User is editing their own account
            current_user_role_name = self.current_admin_user_info.get('role_name')
            if not has_permission(current_user_role_name, P_MANAGE_USERS):
                self.role_combo.setEnabled(False)
                self.role_combo.setToolTip(self.tr("Vous ne pouvez pas modifier votre propre rôle."))
        # No specific "except" needed for the self-edit refinement logic itself, as it's UI manipulation.

    def _save_changes(self):
        admin_role_name = self.current_admin_user_info.get('role_name')
        # Permission check (applies to both add and edit)
        # For self-editing, a more granular check might be needed if P_MANAGE_USERS is too broad.
        # However, the plan is to disable role_combo for self-edit unless admin.
        if not has_permission(admin_role_name, P_MANAGE_USERS):
            QMessageBox.critical(self, self.tr("Accès Refusé"),
                                 self.tr("Vous n'avez pas les permissions pour effectuer cette opération."))
            return

        new_full_name = self.full_name_input.text().strip()
        new_email = self.email_input.text().strip()
        new_role_id = self.role_combo.currentData()

        if not new_full_name:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le nom complet est requis.")); return
        if not new_email: # Basic email format check could be added
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("L'email est requis.")); return
        if new_role_id is None:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Un rôle doit être sélectionné.")); return

        if self.add_mode:
            username = self.username_input.text().strip()
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()

            if not username:
                QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le nom d'utilisateur est requis.")); return
            if users_crud.get_user_by_username(username): # Check if username already exists
                QMessageBox.warning(self, self.tr("Nom d'utilisateur Existant"),
                                    self.tr("Ce nom d'utilisateur existe déjà. Veuillez en choisir un autre."))
                return
            if not password:
                QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le mot de passe est requis.")); return
            if password != confirm_password:
                QMessageBox.warning(self, self.tr("Non Concordance"), self.tr("Les mots de passe ne correspondent pas.")); return
            if len(password) < 8: # Basic complexity
                QMessageBox.warning(self, self.tr("Mot de Passe Trop Court"), self.tr("Le mot de passe doit contenir au moins 8 caractères.")); return

            hashed_pw = hash_password(password)
            created_by_id = self.current_admin_user_info.get('user_id')

            user_payload = {
                "username": username, "hashed_password": hashed_pw, "full_name": new_full_name,
                "email": new_email, "role_id": new_role_id, "is_active": True, # New users active by default
                "created_by_user_id": created_by_id # This field is not directly in Users table but might be for logging or other tables
            }
            # Call users_crud.add_user with individual arguments
            new_user_id = users_crud.add_user(
                username=username,
                password=password, # add_user will hash it
                role_id=new_role_id,
                full_name=new_full_name,
                email=new_email
                # is_active is True by default in add_user
                # created_by_user_id is not a direct param of add_user, it's for user_payload if create_user was used
            )
            if new_user_id:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Utilisateur '{0}' créé avec succès.").format(username))
                # Log activity for user creation
                try:
                    log_data = {
                        "user_id": self.current_admin_user_info.get('user_id'), # User performing the action
                        "action_type": "USER_CREATED",
                        "details": f"Utilisateur '{username}' (ID: {new_user_id}) créé avec le rôle ID: {new_role_id}.",
                        "related_entity_type": "User",
                        "related_entity_id": new_user_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                    logger.info(f"Activity logged for USER_CREATED: {new_user_id} by {self.current_admin_user_info.get('user_id')}")
                except Exception as e_log:
                    logger.error(f"Failed to log USER_CREATED activity for new user {new_user_id}: {e_log}", exc_info=True)
                self.accept()
            else:
                QMessageBox.critical(self, self.tr("Erreur Création"), self.tr("Impossible de créer l'utilisateur."))
        else: # Edit mode
            update_data_user = {}
            changed_details = False

            if new_full_name != self.user_data_to_edit.get('full_name', ''):
                update_data_user['full_name'] = new_full_name
                changed_details = True
            if new_email != self.user_data_to_edit.get('email', ''):
                update_data_user['email'] = new_email
                changed_details = True

            # Self-edit: Prevent role change unless admin.
            # This logic is part of step 2 of the plan, but good to place it here.
            is_self_edit = self.user_id_to_edit == self.current_admin_user_info.get('user_id')

            # The role_combo is already disabled if is_self_edit and no P_MANAGE_USERS.
            # However, if an admin IS self-editing and CAN change their role, this check is still valid.
            # If the combo was disabled, new_role_id should ideally be the same as original,
            # but we double-check here to ensure data integrity if UI somehow allowed a change.
            if is_self_edit and not self.role_combo.isEnabled(): # Check if combo was actually disabled
                 if new_role_id != self.user_data_to_edit.get('role_id'):
                    # This case should ideally not happen if UI is correct, but as a safeguard:
                    logger.warning(f"Attempt to change own role by {admin_role_name} for user {self.user_id_to_edit} even though role_combo was disabled. Reverting to original role_id.")
                    new_role_id = self.user_data_to_edit.get('role_id') # Force original role_id
            elif is_self_edit and not has_permission(admin_role_name, P_MANAGE_USERS): # Redundant if combo disabled, but defense in depth
                if new_role_id != self.user_data_to_edit.get('role_id'):
                     QMessageBox.warning(self, self.tr("Modification Interdite"), self.tr("Vous ne pouvez pas modifier votre propre rôle."))
                     return

            # If admin is editing another user, or admin is editing self (and has P_MANAGE_USERS), role change is allowed by P_MANAGE_USERS check at the start of function.

            user_update_success = True
            if changed_details:
                # updated_by_user_id for auditing, assuming users_crud.update_user handles it
                update_data_user['updated_by_user_id'] = self.current_admin_user_info.get('user_id')
                if not users_crud.update_user(self.user_id_to_edit, update_data_user):
                    user_update_success = False
                    QMessageBox.critical(self, self.tr("Erreur Sauvegarde"),
                                         self.tr("Impossible de sauvegarder les modifications des détails de l'utilisateur."))
                    return
                logger.info(f"User details updated for user_id: {self.user_id_to_edit}")


            role_update_success = True
            changed_role = new_role_id != self.user_data_to_edit.get('role_id')
            if changed_role:
                # updated_by_user_id for auditing, assuming users_crud.update_user_role handles it implicitly or via a wrapper
                if not users_crud.update_user_role(self.user_id_to_edit, new_role_id, updated_by_user_id=self.current_admin_user_info.get('user_id')):
                    role_update_success = False
                    QMessageBox.critical(self, self.tr("Erreur Sauvegarde"),
                                         self.tr("Impossible de sauvegarder la modification du rôle de l'utilisateur."))
                    return
                logger.info(f"User role updated for user_id: {self.user_id_to_edit} to role_id: {new_role_id}")

            if not changed_details and not changed_role:
                QMessageBox.information(self, self.tr("Aucun Changement"), self.tr("Aucune modification n'a été détectée."))
                self.accept()
                return

            if user_update_success and role_update_success:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Utilisateur mis à jour avec succès."))

                # Log activity for user update (details and/or role)
                log_details_parts = []
                if changed_details:
                    log_details_parts.append(f"Détails mis à jour: {update_data_user}")
                if changed_role:
                    new_role_name = self.role_combo.currentText() # Get name for logging
                    log_details_parts.append(f"Rôle changé en '{new_role_name}' (ID: {new_role_id})")

                if log_details_parts: # Only log if something actually changed and was successful
                    try:
                        log_entry_details = "Modifications: " + "; ".join(log_details_parts)
                        log_data = {
                            "user_id": self.current_admin_user_info.get('user_id'), # User performing the action
                            "action_type": "USER_UPDATED",
                            "details": log_entry_details,
                            "related_entity_type": "User",
                            "related_entity_id": self.user_id_to_edit
                        }
                        activity_logs_crud.add_activity_log(log_data)
                        logger.info(f"Activity logged for USER_UPDATED: {self.user_id_to_edit} by {self.current_admin_user_info.get('user_id')}")
                    except Exception as e_log:
                        logger.error(f"Failed to log USER_UPDATED activity for user {self.user_id_to_edit}: {e_log}", exc_info=True)
                self.accept()

if __name__ == '__main__':
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

# ```

# This creates the `EditUserDialog`.
# Now, I'll integrate this dialog into `UserManagementPage._handle_edit_user`.
