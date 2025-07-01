# user_management/page.py
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton,
                             QHBoxLayout, QMessageBox, QDialog) # Added QDialog for EditUserDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAbstractItemView

from db.cruds import users_crud, activity_logs_crud, roles_crud
from auth.permissions import has_permission, P_MANAGE_USERS
# EditUserDialog and ResetPasswordDialog will be imported in their respective handlers
# to avoid potential circular dependencies at module level if they also import this page,
# though in this case, it's less likely for dialogs to import the page.

logger = logging.getLogger(__name__)

class UserManagementPage(QWidget):
    def __init__(self, current_user_info: dict, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.parent_window = parent # Might be DocumentManager or another QWidget

        self._setup_ui()
        self.load_users_to_table() # Initial load
        self._apply_permissions() # Apply permissions based on current user
        self._update_action_buttons_state() # Set initial state of buttons

    def _apply_permissions(self):
        role_name = self.current_user_info.get('role_name')
        can_manage_users_perm = has_permission(role_name, P_MANAGE_USERS)

        self.add_user_button.setEnabled(can_manage_users_perm)
        # Other buttons' enabled state (edit, delete, toggle, reset) depends on selection AND permission,
        # so they are primarily handled in _update_action_buttons_state, but base permission is checked there too.
        # We can set tooltips here if the user fundamentally lacks permission for any action.
        if not can_manage_users_perm:
            self.add_user_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.edit_user_button.setToolTip(self.tr("Permissions insuffisantes pour modifier"))
            self.toggle_active_button.setToolTip(self.tr("Permissions insuffisantes pour changer le statut"))
            self.reset_password_button.setToolTip(self.tr("Permissions insuffisantes pour réinitialiser MDP"))
            self.delete_user_button.setToolTip(self.tr("Permissions insuffisantes pour supprimer"))

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
        self.status_filter_combo.addItem(self.tr("Tous"), "all") # Default
        self.status_filter_combo.addItem(self.tr("Actif"), "active")
        self.status_filter_combo.addItem(self.tr("Inactif"), "inactive")
        # Consider adding "Supprimé" if users_crud.list_users gets an include_deleted_only flag
        filters_layout.addWidget(self.status_filter_combo)
        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)

        self._populate_role_filter()

        self.role_filter_combo.currentIndexChanged.connect(self.load_users_to_table)
        self.status_filter_combo.currentIndexChanged.connect(self.load_users_to_table)

        # Action Buttons Layout
        action_layout = QHBoxLayout()
        self.add_user_button = QPushButton(QIcon(":/icons/user-plus.svg"), self.tr("Ajouter Utilisateur"))
        self.add_user_button.clicked.connect(self._handle_add_user)
        action_layout.addWidget(self.add_user_button)

        self.edit_user_button = QPushButton(QIcon(":/icons/pencil.svg"), self.tr("Modifier Utilisateur"))
        self.edit_user_button.clicked.connect(self._handle_edit_user)
        action_layout.addWidget(self.edit_user_button)

        self.toggle_active_button = QPushButton(QIcon(":/icons/power.svg"), self.tr("Activer/Désactiver")) # Using power icon
        self.toggle_active_button.clicked.connect(self._handle_toggle_active)
        action_layout.addWidget(self.toggle_active_button)

        self.reset_password_button = QPushButton(QIcon(":/icons/lock.svg"), self.tr("Réinitialiser MDP")) # Using lock icon
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

        # Users Table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            self.tr("ID Utilisateur"), self.tr("Nom d'utilisateur"), self.tr("Nom Complet"),
            self.tr("Email"), self.tr("Rôle"), self.tr("Actif"), self.tr("Supprimé")
        ])
        self.users_table.setColumnHidden(0, True) # user_id
        self.users_table.setColumnHidden(6, True) # is_deleted (internal state)

        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Username
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Full Name
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Email
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Role
        self.users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Active

        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.itemSelectionChanged.connect(self._update_action_buttons_state)
        self.users_table.itemDoubleClicked.connect(self._handle_edit_user_from_item) # For double-click to edit
        main_layout.addWidget(self.users_table)

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
            if idx != -1: self.role_filter_combo.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement Rôles"),
                                 self.tr("Impossible de charger les rôles pour le filtre : {0}").format(str(e)))
            logging.error(f"Error populating role filter: {e}", exc_info=True)
        finally:
            self.role_filter_combo.blockSignals(False)

    def _get_selected_user_id(self):
        current_row = self.users_table.currentRow()
        if current_row < 0: return None
        id_item = self.users_table.item(current_row, 0)
        return id_item.text() if id_item else None

    def _get_selected_user_is_deleted_flag(self) -> bool:
        current_row = self.users_table.currentRow()
        if current_row < 0: return False # Default to not deleted if no selection
        deleted_item = self.users_table.item(current_row, 6) # Column for "Supprimé" text
        if deleted_item and deleted_item.text() == self.tr("Oui"):
            return True
        return False

    def _update_action_buttons_state(self):
        has_selection = bool(self.users_table.selectedItems())
        role_name = self.current_user_info.get('role_name')
        can_manage_users_perm = has_permission(role_name, P_MANAGE_USERS)

        is_selected_user_deleted = self._get_selected_user_is_deleted_flag() if has_selection else False

        selected_user_id = self._get_selected_user_id()
        is_selected_user_self = has_selection and (selected_user_id == self.current_user_info.get('user_id'))

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
            if selected_status_filter_val == "active": status_arg = "active"
            elif selected_status_filter_val == "inactive": status_arg = "inactive"

            users_list = users_crud.list_users(
                role_id_filter=selected_role_id,
                status_filter=status_arg,
                include_deleted=False # We don't show soft-deleted users in this main view
            )

            if users_list:
                self.users_table.setRowCount(len(users_list))
                for row, user_data in enumerate(users_list):
                    col = 0
                    self.users_table.setItem(row, col, QTableWidgetItem(str(user_data.get("user_id")))); col+=1
                    self.users_table.setItem(row, col, QTableWidgetItem(user_data.get("username", ""))); col+=1
                    self.users_table.setItem(row, col, QTableWidgetItem(user_data.get("full_name", ""))); col+=1
                    self.users_table.setItem(row, col, QTableWidgetItem(user_data.get("email", ""))); col+=1
                    self.users_table.setItem(row, col, QTableWidgetItem(user_data.get("role_name", ""))); col+=1

                    active_item = QTableWidgetItem(self.tr("Oui") if user_data.get("is_active") else self.tr("Non"))
                    active_item.setTextAlignment(Qt.AlignCenter)
                    self.users_table.setItem(row, col, active_item); col+=1

                    deleted_item = QTableWidgetItem(self.tr("Oui") if user_data.get("is_deleted") else self.tr("Non"))
                    self.users_table.setItem(row, col, deleted_item); col+=1
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"),
                                 self.tr("Impossible de charger la liste des utilisateurs : {0}").format(str(e)))
            logging.error(f"Error loading users to table: {e}", exc_info=True)
        finally:
            self._update_action_buttons_state()

    def refresh_view(self):
        self._populate_role_filter() # Refresh roles in case they changed
        self.load_users_to_table()

    def _handle_edit_user_from_item(self, item): # Activated by double-click
        if item and not self._get_selected_user_is_deleted_flag(): # Check if not deleted before allowing edit
            self._handle_edit_user()
        elif self._get_selected_user_is_deleted_flag():
             QMessageBox.information(self, self.tr("Action Impossible"), self.tr("Cet utilisateur est supprimé et ne peut pas être modifié."))


    def _handle_add_user(self):
        from dialogs.edit_user_dialog import EditUserDialog
        if not has_permission(self.current_user_info.get('role_name'), P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission d'ajouter des utilisateurs."))
            return
        dialog = EditUserDialog(user_id_to_edit=None, current_admin_user_info=self.current_user_info, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users_to_table()
            if hasattr(self.parent_window, 'user_menu_button_instance') and \
               hasattr(self.parent_window.user_menu_button_instance, '_populate_user_actions_menu'):
                self.parent_window.user_menu_button_instance._populate_user_actions_menu()


    def _handle_edit_user(self):
        from dialogs.edit_user_dialog import EditUserDialog
        if not has_permission(self.current_user_info.get('role_name'), P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission de modifier les utilisateurs."))
            return
        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un utilisateur à modifier."))
            return
        if self._get_selected_user_is_deleted_flag():
            QMessageBox.information(self, self.tr("Action Impossible"), self.tr("Cet utilisateur est supprimé et ne peut pas être modifié."))
            return

        dialog = EditUserDialog(user_id_to_edit=selected_user_id, current_admin_user_info=self.current_user_info, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users_to_table()
            if selected_user_id == self.current_user_info.get('user_id'): # If admin edited themselves
                # Need to update current_user_info in DocumentManager and UserMenuButton
                # This is complex as it requires DocumentManager to re-fetch its own user info
                QMessageBox.information(self, self.tr("Mise à Jour"), self.tr("Vos propres informations ont été modifiées. Certains changements peuvent nécessiter une reconnexion pour être pleinement appliqués."))
                # Potentially signal main_window to refresh current_user_info
                if hasattr(self.parent_window, 'refresh_current_user_session_info'):
                    self.parent_window.refresh_current_user_session_info()


    def _handle_toggle_active(self):
        if not has_permission(self.current_user_info.get('role_name'), P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission de modifier le statut des utilisateurs."))
            return
        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un utilisateur."))
            return
        if selected_user_id == self.current_user_info.get('user_id'):
            QMessageBox.warning(self, self.tr("Action Interdite"), self.tr("Vous ne pouvez pas désactiver votre propre compte."))
            return
        if self._get_selected_user_is_deleted_flag():
            QMessageBox.information(self, self.tr("Action Impossible"), self.tr("Le statut actif d'un utilisateur supprimé ne peut pas être changé."))
            return

        user_data = users_crud.get_user_by_id(selected_user_id)
        if not user_data: QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé.")); return

        current_status_active = user_data.get('is_active') == 1
        new_status = not current_status_active
        action_text = self.tr("désactiver") if new_status == False else self.tr("activer")
        username_to_display = user_data.get('username', selected_user_id)

        reply = QMessageBox.question(self, self.tr("Confirmer Action"),
                                     self.tr("Êtes-vous sûr de vouloir {0} l'utilisateur '{1}' ?").format(action_text, username_to_display),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if users_crud.set_user_active_status(selected_user_id, new_status):
                QMessageBox.information(self, self.tr("Succès"), self.tr("Statut de '{0}' mis à jour.").format(username_to_display))
                self.load_users_to_table()
                activity_logs_crud.add_activity_log({
                    "user_id": self.current_user_info.get('user_id'), "action_type": "USER_STATUS_CHANGED",
                    "details": f"Statut de '{username_to_display}' (ID: {selected_user_id}) changé à {'Actif' if new_status else 'Inactif'}.",
                    "related_entity_type": "User", "related_entity_id": selected_user_id
                })
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de mettre à jour le statut pour '{0}'.").format(username_to_display))

    def _handle_reset_password(self):
        from dialogs.reset_password_dialog import ResetPasswordDialog
        if not has_permission(self.current_user_info.get('role_name'), P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission de réinitialiser les mots de passe."))
            return
        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un utilisateur."))
            return
        if self._get_selected_user_is_deleted_flag():
            QMessageBox.information(self, self.tr("Action Impossible"), self.tr("Le mot de passe d'un utilisateur supprimé ne peut pas être réinitialisé."))
            return

        user_data = users_crud.get_user_by_id(selected_user_id)
        if not user_data: QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé.")); return
        username_to_display = user_data.get('username', selected_user_id)

        reset_dialog = ResetPasswordDialog(username=username_to_display, parent=self)
        if reset_dialog.exec_() == QDialog.Accepted:
            new_password = reset_dialog.get_new_password()
            if users_crud.update_user_password(selected_user_id, new_password):
                QMessageBox.information(self, self.tr("Succès"), self.tr("Mot de passe pour '{0}' réinitialisé.").format(username_to_display))
                activity_logs_crud.add_activity_log({
                    "user_id": self.current_user_info.get('user_id'), "action_type": "USER_PASSWORD_RESET",
                    "details": f"Mot de passe réinitialisé pour '{username_to_display}' (ID: {selected_user_id}).",
                    "related_entity_type": "User", "related_entity_id": selected_user_id
                })
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de réinitialiser le mot de passe pour '{0}'.").format(username_to_display))

    def _handle_delete_user(self):
        if not has_permission(self.current_user_info.get('role_name'), P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission de supprimer des utilisateurs."))
            return
        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un utilisateur à supprimer."))
            return

        # users_crud.soft_delete_user handles self-deletion check.
        # We also check if already deleted here for better UX.
        user_data = users_crud.get_user_by_id(selected_user_id, include_deleted=True)
        if not user_data: QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé.")); return
        username_to_display = user_data.get('username', selected_user_id)
        if user_data.get('is_deleted'):
            QMessageBox.information(self, self.tr("Déjà Supprimé"), self.tr("L'utilisateur '{0}' est déjà marqué comme supprimé.").format(username_to_display))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer (logiquement) l'utilisateur '{0}' ?\n"
                                             "Ce compte sera désactivé et ne pourra plus se connecter.").format(username_to_display),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            admin_user_id = self.current_user_info.get('user_id')
            success = users_crud.soft_delete_user(user_id_to_delete=selected_user_id, current_user_id=admin_user_id)
            if success:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Utilisateur '{0}' supprimé (logiquement).").format(username_to_display))
                self.load_users_to_table()
                activity_logs_crud.add_activity_log({
                    "user_id": admin_user_id, "action_type": "USER_SOFT_DELETED",
                    "details": f"Utilisateur '{username_to_display}' (ID: {selected_user_id}) supprimé logiquement.",
                    "related_entity_type": "User", "related_entity_id": selected_user_id
                })
            else:
                # Check if it was a self-deletion attempt (already handled by CRUD, but good for specific message)
                if selected_user_id == admin_user_id:
                     QMessageBox.warning(self, self.tr("Action Interdite"), self.tr("Vous ne pouvez pas vous supprimer vous-même."))
                else: # Other DB error
                    QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de supprimer l'utilisateur '{0}'.").format(username_to_display))
```
