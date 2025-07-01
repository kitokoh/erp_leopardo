# user_management/page.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton,
                             QHBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAbstractItemView

# Assuming users_crud and roles_crud are accessible for fetching data
# and auth.permissions for permission checking if actions were added here.
from db.cruds import users_crud # For list_users
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

        self.edit_user_button.setEnabled(can_manage_users_perm)
        self.toggle_active_button.setEnabled(can_manage_users_perm)
        self.reset_password_button.setEnabled(can_manage_users_perm)
        # Add User button will also be controlled by this in a later phase
        # self.add_user_button.setEnabled(can_manage_users_perm)

        # If the current user cannot manage users at all, they shouldn't even see these buttons.
        # However, the page itself is usually hidden by main_window's menu action.
        # Disabling them is a secondary measure.
        if not can_manage_users_perm:
            self.edit_user_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.toggle_active_button.setToolTip(self.tr("Permissions insuffisantes"))
            self.reset_password_button.setToolTip(self.tr("Permissions insuffisantes"))


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel(self.tr("Gestion des Utilisateurs"))
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter) # Center title

        # Filters Layout
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel(self.tr("Filtrer par Rôle:")))
        self.role_filter_combo = QComboBox()
        self.role_filter_combo.addItem(self.tr("Tous les rôles"), None) # Option pour afficher tous
        filters_layout.addWidget(self.role_filter_combo)

        filters_layout.addSpacing(20)

        filters_layout.addWidget(QLabel(self.tr("Filtrer par Statut:")))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem(self.tr("Tous les statuts"), "all")
        self.status_filter_combo.addItem(self.tr("Actif"), "active")
        self.status_filter_combo.addItem(self.tr("Inactif"), "inactive")
        filters_layout.addWidget(self.status_filter_combo)
        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)

        # Populate role filter combo
        self._populate_role_filter()

        # Connect filter signals
        self.role_filter_combo.currentIndexChanged.connect(self.load_users_to_table)
        self.status_filter_combo.currentIndexChanged.connect(self.load_users_to_table)

        # Placeholder for action buttons (Add User, Edit User etc. - for later phases)
        action_layout = QHBoxLayout()

        self.add_user_button = QPushButton(QIcon(":/icons/user-plus.svg"), self.tr("Ajouter Utilisateur"))
        self.add_user_button.clicked.connect(self._handle_add_user)
        action_layout.addWidget(self.add_user_button)

        self.edit_user_button = QPushButton(QIcon(":/icons/pencil.svg"), self.tr("Modifier Utilisateur"))
        self.edit_user_button.clicked.connect(self._handle_edit_user)
        action_layout.addWidget(self.edit_user_button)

        self.toggle_active_button = QPushButton(QIcon(":/icons/log-out.svg"), self.tr("Activer/Désactiver")) # Changed to existing log-out.svg
        self.toggle_active_button.clicked.connect(self._handle_toggle_active)
        action_layout.addWidget(self.toggle_active_button)

        self.reset_password_button = QPushButton(QIcon(":/icons/settings.svg"), self.tr("Réinitialiser MDP")) # Changed to existing settings.svg
        self.reset_password_button.clicked.connect(self._handle_reset_password)
        action_layout.addWidget(self.reset_password_button)

        action_layout.addStretch()
        self.refresh_button = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser"))
        self.refresh_button.clicked.connect(self.load_users_to_table)
        action_layout.addWidget(self.refresh_button)
        main_layout.addLayout(action_layout)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6) # user_id (hidden), Username, Full Name, Email, Role, Active
        self.users_table.setHorizontalHeaderLabels([
            self.tr("ID Utilisateur"), self.tr("Nom d'utilisateur"), self.tr("Nom Complet"),
            self.tr("Email"), self.tr("Rôle"), self.tr("Actif")
        ])
        self.users_table.setColumnHidden(0, True) # Hide user_id column

        # Set column resize modes
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Username
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Full Name
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Email
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Role
        self.users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Active

        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read-only table for Phase 1
        self.users_table.setAlternatingRowColors(True)
        self.users_table.itemSelectionChanged.connect(self._update_action_buttons_state) # Connect selection change
        self.users_table.itemDoubleClicked.connect(self._handle_edit_user_from_item) # Connect double click


        main_layout.addWidget(self.users_table)
        self.setLayout(main_layout)

    def _populate_role_filter(self):
        """Populates the role filter combo box with roles from the database."""
        try:
            roles = roles_crud.list_roles()
            if roles:
                for role in roles:
                    self.role_filter_combo.addItem(role['role_name'], role['role_id'])
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement Rôles"),
                                 self.tr("Impossible de charger les rôles pour le filtre : {0}").format(str(e)))
            print(f"Error populating role filter: {e}")

    def _handle_add_user(self):
        """Handles the Add User button click. Placeholder for now."""
        # QMessageBox.information(self, self.tr("Fonctionnalité à venir"), self.tr("L'ajout d'utilisateurs sera implémenté prochainement."))
        # For now, try to open the EditUserDialog in 'add' mode if it supports it, or a specific AddUserDialog.
        # Assuming EditUserDialog can handle user_id_to_edit=None for add mode.
        from dialogs.edit_user_dialog import EditUserDialog # Local import to avoid circular if EditUserDialog imports this module

        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission d'ajouter des utilisateurs."))
            return

        add_dialog = EditUserDialog(user_id_to_edit=None, # Indicates 'add' mode
                                    current_admin_user_info=self.current_user_info,
                                    parent=self)
        if add_dialog.exec_() == QDialog.Accepted:
            self.load_users_to_table() # Refresh list if user was added

    def _update_action_buttons_state(self):
        """Enable/disable action buttons based on table selection and base permissions."""
        has_selection = bool(self.users_table.selectedItems())
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_users_perm = has_permission(role_name, P_MANAGE_USERS)

        self.edit_user_button.setEnabled(has_selection and can_manage_users_perm)
        self.toggle_active_button.setEnabled(has_selection and can_manage_users_perm)
        self.reset_password_button.setEnabled(has_selection and can_manage_users_perm)


    def load_users_to_table(self):
        self.users_table.setRowCount(0) # Clear existing rows
        try:
            selected_role_id = self.role_filter_combo.currentData()
            selected_status_filter = self.status_filter_combo.currentData() # 'all', 'active', 'inactive'

            # If 'all' is selected for status, pass None to list_users for status_filter
            status_arg = None
            if selected_status_filter == "active":
                status_arg = "active"
            elif selected_status_filter == "inactive":
                status_arg = "inactive"

            users_list = users_crud.list_users(role_id_filter=selected_role_id, status_filter=status_arg)

            if users_list:
                self.users_table.setRowCount(len(users_list))
                for row, user_data in enumerate(users_list):
                    col = 0
                    # User ID (Hidden)
                    user_id_item = QTableWidgetItem(str(user_data.get("user_id")))
                    self.users_table.setItem(row, col, user_id_item); col += 1

                    # Username
                    username_item = QTableWidgetItem(user_data.get("username", self.tr("N/A")))
                    self.users_table.setItem(row, col, username_item); col += 1

                    # Full Name
                    fullname_item = QTableWidgetItem(user_data.get("full_name", ""))
                    self.users_table.setItem(row, col, fullname_item); col += 1

                    # Email
                    email_item = QTableWidgetItem(user_data.get("email", ""))
                    self.users_table.setItem(row, col, email_item); col += 1

                    # Role Name
                    role_name_item = QTableWidgetItem(user_data.get("role_name", self.tr("N/A")))
                    self.users_table.setItem(row, col, role_name_item); col += 1

                    # Active Status
                    is_active_val = user_data.get("is_active", 0) # DB stores 0 or 1
                    active_status_str = self.tr("Oui") if is_active_val == 1 else self.tr("Non")
                    active_item = QTableWidgetItem(active_status_str)
                    active_item.setTextAlignment(Qt.AlignCenter)
                    self.users_table.setItem(row, col, active_item); col += 1
            else:
                # Handle case where no users are returned (e.g., display a message in the table)
                # For now, table will just be empty.
                pass
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"),
                                 self.tr("Impossible de charger la liste des utilisateurs : {0}").format(str(e)))
            print(f"Error loading users to table: {e}") # For debugging

    def refresh_view(self):
        """Public method to allow parent to trigger a refresh."""
        self.load_users_to_table()

    def _get_selected_user_id(self):
        """Helper to get the user_id from the selected row's hidden ID column."""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            return None
        id_item = self.users_table.item(current_row, 0) # Hidden ID column
        return id_item.text() if id_item else None

    def _handle_edit_user_from_item(self, item):
        """Handles double-click on a table item to edit user."""
        if item: # Check if item is valid
            self._handle_edit_user()


    def _handle_edit_user(self):
        """Handles the Edit User button click."""
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de modifier les utilisateurs."))
            return

        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"),
                                    self.tr("Veuillez sélectionner un utilisateur à modifier."))
            return

        from dialogs.edit_user_dialog import EditUserDialog

        edit_dialog = EditUserDialog(user_id_to_edit=selected_user_id,
                                     current_admin_user_info=self.current_user_info,
                                     parent=self)
        if edit_dialog.exec_() == QDialog.Accepted:
            self.load_users_to_table()
        # --- End Placeholder ---


    def _handle_toggle_active(self):
        """Handles the Activate/Deactivate User button click."""
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        if not has_permission(role_name, P_MANAGE_USERS):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de modifier le statut des utilisateurs."))
            return

        selected_user_id = self._get_selected_user_id()
        if not selected_user_id:
            QMessageBox.information(self, self.tr("Aucune Sélection"),
                                    self.tr("Veuillez sélectionner un utilisateur pour changer son statut."))
            return

        user_data = users_crud.get_user_by_id(selected_user_id) # Fetches full user data including current 'is_active'
        if not user_data:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Utilisateur non trouvé."))
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
            else:
                QMessageBox.critical(self, self.tr("Erreur"),
                                     self.tr("Impossible de mettre à jour le statut de l'utilisateur '{0}'.").format(username_to_display))

    def _handle_reset_password(self):
        """Handles the Reset Password button click."""
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
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

        username_to_display = user_data.get('username', selected_user_id)

        from dialogs.reset_password_dialog import ResetPasswordDialog

        reset_dialog = ResetPasswordDialog(username=username_to_display, parent=self)
        if reset_dialog.exec_() == QDialog.Accepted:
            new_password = reset_dialog.get_new_password()
            if users_crud.update_user_password(selected_user_id, new_password):
                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Mot de passe pour '{0}' réinitialisé avec succès.").format(username_to_display))
                # No need to reload table as password change isn't visible in the user list
            else:
                QMessageBox.critical(self, self.tr("Erreur"),
                                     self.tr("Impossible de réinitialiser le mot de passe pour '{0}'.").format(username_to_display))
        # --- End Placeholder ---
# ```
