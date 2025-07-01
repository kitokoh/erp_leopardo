# user_management/page.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton,
                             QHBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAbstractItemView
import logging # Added logging

# Assuming users_crud and roles_crud are accessible for fetching data
# and auth.permissions for permission checking if actions were added here.
from db.cruds import users_crud, activity_logs_crud # For list_users and logging
from auth.permissions import has_permission, P_MANAGE_USERS
from db.cruds import roles_crud # For populating roles in edit dialog

# Placeholder for EditUserDialog, will be created later
# from dialogs.edit_user_dialog import EditUserDialog

class UserManagementPage(QWidget):
    def __init__(self, current_user_info: dict, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.parent_window = parent

        self._setup_ui()
        self.load_users_to_table()
        self._apply_permissions()
        self._update_action_buttons_state() # Initial state

    def _apply_permissions(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_users_perm = has_permission(role_name, P_MANAGE_USERS)

        self.add_user_button.setEnabled(can_manage_users_perm) # Control add button
        self.edit_user_button.setEnabled(can_manage_users_perm)
        self.toggle_active_button.setEnabled(can_manage_users_perm)
        self.reset_password_button.setEnabled(can_manage_users_perm)
        self.delete_user_button.setEnabled(can_manage_users_perm)

        if not can_manage_users_perm:
            self.add_user_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.edit_user_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.toggle_active_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.reset_password_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.delete_user_button.setToolTip(self.tr("Permissions insuffisantes"))


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel(self.tr("Gestion des Utilisateurs"))
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Filters Layout
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel(self.tr("Filtrer par Rôle:")))
        self.role_filter_combo = QComboBox()
        self.role_filter_combo.addItem(self.tr("Tous les rôles"), None)
        filters_layout.addWidget(self.role_filter_combo)

        filters_layout.addSpacing(20)

        filters_layout.addWidget(QLabel(self.tr("Filtrer par Statut:")))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem(self.tr("Tous les statuts"), "all")
        self.status_filter_combo.addItem(self.tr("Actif"), "active")
        self.status_filter_combo.addItem(self.tr("Inactif"), "inactive")
        # Option to view soft-deleted users could be added here if needed
        filters_layout.addWidget(self.status_filter_combo)
        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)

        self._populate_role_filter()

        self.role_filter_combo.currentIndexChanged.connect(self.load_users_to_table)
        self.status_filter_combo.currentIndexChanged.connect(self.load_users_to_table)

        action_layout = QHBoxLayout()
        self.add_user_button = QPushButton(QIcon(":/icons/user-plus.svg"), self.tr("Ajouter Utilisateur"))
        self.add_user_button.clicked.connect(self._handle_add_user)
        action_layout.addWidget(self.add_user_button)

        self.edit_user_button = QPushButton(QIcon(":/icons/pencil.svg"), self.tr("Modifier Utilisateur"))
        self.edit_user_button.clicked.connect(self._handle_edit_user)
        action_layout.addWidget(self.edit_user_button)

        self.toggle_active_button = QPushButton(QIcon(":/icons/log-out.svg"), self.tr("Activer/Désactiver"))
        self.toggle_active_button.clicked.connect(self._handle_toggle_active)
        action_layout.addWidget(self.toggle_active_button)

        self.reset_password_button = QPushButton(QIcon(":/icons/settings.svg"), self.tr("Réinitialiser MDP"))
        self.reset_password_button.clicked.connect(self._handle_reset_password)
        action_layout.addWidget(self.reset_password_button)

        self.delete_user_button = QPushButton(QIcon(":/icons/trash.svg"), self.tr("Supprimer Utilisateur"))
        self.delete_user_button.setObjectName("dangerButton")
        self.delete_user_button.clicked.connect(self._handle_delete_user)
        action_layout.addWidget(self.delete_user_button)

        action_layout.addStretch()
        self.refresh_button = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser"))
        self.refresh_button.clicked.connect(self.load_users_to_table)
        action_layout.addWidget(self.refresh_button)
        main_layout.addLayout(action_layout)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            self.tr("ID Utilisateur"), self.tr("Nom d'utilisateur"), self.tr("Nom Complet"),
            self.tr("Email"), self.tr("Rôle"), self.tr("Actif"), self.tr("Supprimé")
        ])
        self.users_table.setColumnHidden(0, True) # Hide user_id column
        self.users_table.setColumnHidden(6, True) # Hide is_deleted column (text "Oui"/"Non")

        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Username
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Full Name
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Email
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Role
        self.users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Active

        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.itemSelectionChanged.connect(self._update_action_buttons_state)
        self.users_table.itemDoubleClicked.connect(self._handle_edit_user_from_item)

        main_layout.addWidget(self.users_table)
        self.setLayout(main_layout)

    def _populate_role_filter(self):
        current_selection = self.role_filter_combo.currentData()
        self.role_filter_combo.blockSignals(True)
        self.role_filter_combo.clear()
        self.role_filter_combo.addItem(self.tr("Tous les rôles"), None)
        try:
            roles = roles_crud.list_roles()
            if roles:
                for role in roles:
                    self.role_filter_combo.addItem(role['role_name'], role['role_id'])
            idx = self.role_filter_combo.findData(current_selection)
            if idx != -1:
                self.role_filter_combo.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement Rôles"),
                                 self.tr("Impossible de charger les rôles pour le filtre : {0}").format(str(e)))
            logging.error(f"Error populating role filter: {e}", exc_info=True)
        finally:
            self.role_filter_combo.blockSignals(False)


    def _handle_add_user(self):
        from dialogs.edit_user_dialog import EditUserDialog
        role_name = self.current_user_info.get('role_name')
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission d'ajouter des utilisateurs."))
            return

        add_dialog = EditUserDialog(user_id_to_edit=None,
                                    current_admin_user_info=self.current_user_info,
                                    parent=self)
        if add_dialog.exec_() == QDialog.Accepted:
            self.load_users_to_table()

    def _update_action_buttons_state(self):
        has_selection = bool(self.users_table.selectedItems())
        role_name = self.current_user_info.get('role_name')
        can_manage_users_perm = has_permission(role_name, P_MANAGE_USERS)

        is_selected_user_deleted = False
        is_selected_user_self = False
        selected_user_id = None

        if has_selection:
            current_row = self.users_table.currentRow()
            id_item = self.users_table.item(current_row, 0) # user_id
            deleted_item = self.users_table.item(current_row, 6) # is_deleted column text

            if id_item:
                selected_user_id = id_item.text()
                if selected_user_id == self.current_user_info.get('user_id'):
                    is_selected_user_self = True

            if deleted_item and deleted_item.text() == self.tr("Oui"): # Assuming "Oui" means deleted
                is_selected_user_deleted = True

        self.edit_user_button.setEnabled(has_selection and can_manage_users_perm and not is_selected_user_deleted)
        self.toggle_active_button.setEnabled(has_selection and can_manage_users_perm and not is_selected_user_deleted and not is_selected_user_self)
        self.reset_password_button.setEnabled(has_selection and can_manage_users_perm and not is_selected_user_deleted)
        self.delete_user_button.setEnabled(has_selection and can_manage_users_perm and not is_selected_user_deleted and not is_selected_user_self)


    def load_users_to_table(self):
        self.users_table.setRowCount(0)
        try:
            selected_role_id = self.role_filter_combo.currentData()
            selected_status_filter_val = self.status_filter_combo.currentData()

            status_arg = None
            if selected_status_filter_val == "active":
                status_arg = "active"
            elif selected_status_filter_val == "inactive":
                status_arg = "inactive"

            # By default, list_users now excludes soft-deleted users.
            # Pass include_deleted=True if a filter for "Deleted" users is added.
            users_list = users_crud.list_users(
                role_id_filter=selected_role_id,
                status_filter=status_arg,
                include_deleted=False # Do not show soft-deleted users in the main list
            )

            if users_list:
                self.users_table.setRowCount(len(users_list))
                for row, user_data in enumerate(users_list):
                    col = 0
                    user_id_item = QTableWidgetItem(str(user_data.get("user_id")))
                    self.users_table.setItem(row, col, user_id_item); col += 1

                    username_item = QTableWidgetItem(user_data.get("username", self.tr("N/A")))
                    self.users_table.setItem(row, col, username_item); col += 1

                    fullname_item = QTableWidgetItem(user_data.get("full_name", ""))
                    self.users_table.setItem(row, col, fullname_item); col += 1

                    email_item = QTableWidgetItem(user_data.get("email", ""))
                    self.users_table.setItem(row, col, email_item); col += 1

                    role_name_item = QTableWidgetItem(user_data.get("role_name", self.tr("N/A")))
                    self.users_table.setItem(row, col, role_name_item); col += 1

                    is_active_val = user_data.get("is_active", 0)
                    active_status_str = self.tr("Oui") if is_active_val == 1 else self.tr("Non")
                    active_item = QTableWidgetItem(active_status_str)
                    active_item.setTextAlignment(Qt.AlignCenter)
                    self.users_table.setItem(row, col, active_item); col += 1

                    is_deleted_val = user_data.get("is_deleted", 0) # Fetch is_deleted
                    deleted_status_str = self.tr("Oui") if is_deleted_val == 1 else self.tr("Non")
                    deleted_item = QTableWidgetItem(deleted_status_str)
                    self.users_table.setItem(row, col, deleted_item); col += 1
            else:
                pass
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"),
                                 self.tr("Impossible de charger la liste des utilisateurs : {0}").format(str(e)))
            logging.error(f"Error loading users to table: {e}", exc_info=True)
        finally:
            self._update_action_buttons_state()

    def refresh_view(self):
        self.load_users_to_table()

    def _get_selected_user_id(self):
        current_row = self.users_table.currentRow()
        if current_row < 0:
            return None
        id_item = self.users_table.item(current_row, 0)
        return id_item.text() if id_item else None

    def _handle_edit_user_from_item(self, item):
        if item:
            self._handle_edit_user()

    def _handle_edit_user(self):
        role_name = self.current_user_info.get('role_name')
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de modifier les utilisateurs."))
            return

        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"),
                                    self.tr("Veuillez sélectionner un utilisateur à modifier."))
            return

        user_data = users_crud.get_user_by_id(selected_user_id) # Check if user is deleted before editing
        if not user_data or user_data.get('is_deleted'):
             QMessageBox.warning(self, self.tr("Action Impossible"), self.tr("Cet utilisateur est marqué comme supprimé et ne peut pas être modifié. Pour le réactiver, une autre fonctionnalité serait nécessaire."))
             return


        from dialogs.edit_user_dialog import EditUserDialog
        edit_dialog = EditUserDialog(user_id_to_edit=selected_user_id,
                                     current_admin_user_info=self.current_user_info,
                                     parent=self)
        if edit_dialog.exec_() == QDialog.Accepted:
            self.load_users_to_table()

    def _handle_toggle_active(self):
        role_name = self.current_user_info.get('role_name')
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de modifier le statut des utilisateurs."))
            return

        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"),
                                    self.tr("Veuillez sélectionner un utilisateur pour changer son statut."))
            return

        if selected_user_id == self.current_user_info.get('user_id'):
            QMessageBox.warning(self, self.tr("Action Interdite"), self.tr("Vous ne pouvez pas désactiver votre propre compte."))
            return

        user_data = users_crud.get_user_by_id(selected_user_id)
        if not user_data:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé."))
            return

        if user_data.get('is_deleted'):
            QMessageBox.warning(self, self.tr("Action Impossible"), self.tr("Cet utilisateur est marqué comme supprimé. Son statut actif ne peut pas être changé directement."))
            return

        current_status_active = user_data.get('is_active') == 1
        new_status = not current_status_active
        action_text = self.tr("désactiver") if new_status == False else self.tr("activer")
        username_to_display = user_data.get('username', selected_user_id)

        reply = QMessageBox.question(self, self.tr("Confirmer Action"),
                                     self.tr("Êtes-vous sûr de vouloir {0} l'utilisateur '{1}' ?").format(action_text, username_to_display),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success = users_crud.set_user_active_status(selected_user_id, new_status)
            if success:
                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Statut de l'utilisateur '{0}' mis à jour.").format(username_to_display))
                self.load_users_to_table()
                try:
                    log_data = {
                        "user_id": self.current_user_info.get('user_id'),
                        "action_type": "USER_STATUS_CHANGED",
                        "details": f"Statut de l'utilisateur '{username_to_display}' (ID: {selected_user_id}) changé à {'Actif' if new_status else 'Inactif'}.",
                        "related_entity_type": "User",
                        "related_entity_id": selected_user_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                    logging.info(f"Activity logged for USER_STATUS_CHANGED: {selected_user_id} by {self.current_user_info.get('user_id')}")
                except Exception as e_log:
                    logging.error(f"Failed to log USER_STATUS_CHANGED activity for user {selected_user_id}: {e_log}", exc_info=True)
            else:
                QMessageBox.critical(self, self.tr("Erreur"),
                                     self.tr("Impossible de mettre à jour le statut de l'utilisateur '{0}'.").format(username_to_display))

    def _handle_reset_password(self):
        role_name = self.current_user_info.get('role_name')
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de réinitialiser les mots de passe."))
            return

        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"),
                                    self.tr("Veuillez sélectionner un utilisateur pour réinitialiser son mot de passe."))
            return

        user_data = users_crud.get_user_by_id(selected_user_id)
        if not user_data:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé."))
            return

        if user_data.get('is_deleted'):
            QMessageBox.warning(self, self.tr("Action Impossible"), self.tr("Le mot de passe d'un utilisateur supprimé ne peut pas être réinitialisé."))
            return

        username_to_display = user_data.get('username', selected_user_id)
        from dialogs.reset_password_dialog import ResetPasswordDialog
        reset_dialog = ResetPasswordDialog(username=username_to_display, parent=self)
        if reset_dialog.exec_() == QDialog.Accepted:
            new_password = reset_dialog.get_new_password()
            if users_crud.update_user_password(selected_user_id, new_password):
                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Mot de passe pour '{0}' réinitialisé avec succès.").format(username_to_display))
                try:
                    log_data = {
                        "user_id": self.current_user_info.get('user_id'),
                        "action_type": "USER_PASSWORD_RESET",
                        "details": f"Mot de passe réinitialisé pour l'utilisateur '{username_to_display}' (ID: {selected_user_id}).",
                        "related_entity_type": "User",
                        "related_entity_id": selected_user_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                    logging.info(f"Activity logged for USER_PASSWORD_RESET: {selected_user_id} by {self.current_user_info.get('user_id')}")
                except Exception as e_log:
                    logging.error(f"Failed to log USER_PASSWORD_RESET activity for user {selected_user_id}: {e_log}", exc_info=True)
            else:
                QMessageBox.critical(self, self.tr("Erreur"),
                                     self.tr("Impossible de réinitialiser le mot de passe pour '{0}'.").format(username_to_display))

    def _handle_delete_user(self):
        """Handles the Soft Delete User button click."""
        role_name_performing_action = self.current_user_info.get('role_name')
        if not has_permission(role_name_performing_action, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de supprimer des utilisateurs."))
            return

        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"),
                                    self.tr("Veuillez sélectionner un utilisateur à supprimer."))
            return

        # users_crud.soft_delete_user already handles self-deletion check
        # if selected_user_id == self.current_user_info.get('user_id'):
        #     QMessageBox.warning(self, self.tr("Action Interdite"),
        #                         self.tr("Vous ne pouvez pas vous supprimer vous-même."))
        #     return

        user_data = users_crud.get_user_by_id(selected_user_id, include_deleted=True)
        if not user_data:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé."))
            return

        username_to_display = user_data.get('username', selected_user_id)
        if user_data.get('is_deleted'):
            QMessageBox.information(self, self.tr("Déjà Supprimé"),
                                    self.tr("L'utilisateur '{0}' est déjà marqué comme supprimé.").format(username_to_display))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer (logiquement) l'utilisateur '{0}' ?\n"
                                             "Ce compte sera désactivé et marqué comme supprimé.").format(username_to_display),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            admin_user_id = self.current_user_info.get('user_id')
            success = users_crud.soft_delete_user(user_id_to_delete=selected_user_id, current_user_id=admin_user_id)
            if success:
                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Utilisateur '{0}' supprimé (logiquement) avec succès.").format(username_to_display))
                self.load_users_to_table()
                try:
                    log_data = {
                        "user_id": admin_user_id,
                        "action_type": "USER_SOFT_DELETED",
                        "details": f"Utilisateur '{username_to_display}' (ID: {selected_user_id}) supprimé logiquement.",
                        "related_entity_type": "User",
                        "related_entity_id": selected_user_id
                    }
                    activity_logs_crud.add_activity_log(log_data)
                    logging.info(f"Activity logged for USER_SOFT_DELETED: {selected_user_id} by {admin_user_id}")
                except Exception as e_log:
                    logging.error(f"Failed to log USER_SOFT_DELETED activity for user {selected_user_id}: {e_log}", exc_info=True)
            else:
                # Check if it was a self-deletion attempt that was blocked by users_crud
                if selected_user_id == admin_user_id:
                     QMessageBox.warning(self, self.tr("Action Interdite"), self.tr("Vous ne pouvez pas vous supprimer vous-même."))
                else:
                    QMessageBox.critical(self, self.tr("Erreur"),
                                        self.tr("Impossible de supprimer (logiquement) l'utilisateur '{0}'.").format(username_to_display))

# ```
