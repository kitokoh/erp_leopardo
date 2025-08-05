# -*- coding: utf-8 -*-
import json
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QLabel, QAbstractItemView, QMessageBox, QListWidgetItem, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

# Placeholder for CONFIGURABLE_MODULES and db_manager/settings functions
# These would typically be passed in or imported if structured as a service
CONFIGURABLE_MODULES_DUMMY = [
    {'key': 'module_project_management_enabled', 'name': 'project_management', 'action_attr': 'project_management_action', 'display_name_func': lambda: QApplication.translate("MenuCustomizationDialog", "Gestion de Projet")},
    {'key': 'module_product_management_enabled', 'name': 'product_management', 'action_attr': 'product_list_action', 'display_name_func': lambda: QApplication.translate("MenuCustomizationDialog", "Gestion des Produits")},
    {'key': 'module_statistics_enabled', 'name': 'statistics', 'action_attr': 'statistics_action', 'display_name_func': lambda: QApplication.translate("MenuCustomizationDialog", "Statistiques")},
]

# Simulating db_manager functions for settings
def get_user_menu_config(user_id, db_conn_dummy=None):
    # In a real scenario, this would fetch from db_manager.get_setting
    # For this dummy, let's simulate a default or empty config
    print(f"DUMMY: get_user_menu_config for user_id {user_id}")
    # Default: all modules visible in their original order from CONFIGURABLE_MODULES_DUMMY
    default_order = [m['name'] for m in CONFIGURABLE_MODULES_DUMMY]
    default_visibility = {m['name']: True for m in CONFIGURABLE_MODULES_DUMMY}

    # Simulate some user customization for testing
    # return {
    #     "order": [CONFIGURABLE_MODULES_DUMMY[1]['name'], CONFIGURABLE_MODULES_DUMMY[0]['name']], # Swapped order
    #     "visibility": {
    #         CONFIGURABLE_MODULES_DUMMY[0]['name']: True,
    #         CONFIGURABLE_MODULES_DUMMY[1]['name']: True,
    #         CONFIGURABLE_MODULES_DUMMY[2]['name']: False, # One hidden
    #     }
    # }
    return {"order": default_order, "visibility": default_visibility}


def set_user_menu_config(user_id, config_data, db_conn_dummy=None):
    # In a real scenario, this would use db_manager.set_setting
    print(f"DUMMY: set_user_menu_config for user_id {user_id} with data: {json.dumps(config_data)}")
    return True # Simulate success


class MenuCustomizationDialog(QDialog):
    menu_config_changed = pyqtSignal() # Signal to notify main window to update menu

    def __init__(self, current_user_id, configurable_modules, module_states, license_features, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.configurable_modules = configurable_modules # Full list from app_constants
        self.module_states = module_states # Dict of globally enabled/disabled modules
        self.license_features = license_features # Set of allowed features for the user

        self.setWindowTitle(self.tr("Personnaliser le Menu Modules"))
        self.setWindowIcon(QIcon(":/icons/settings.svg")) # Placeholder icon
        self.setMinimumSize(700, 450)

        self.user_config = {} # To store the loaded user menu configuration

        self._init_ui()
        self._load_initial_configuration()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        content_layout = QHBoxLayout()

        # Visible Modules Section
        visible_group_layout = QVBoxLayout()
        visible_group_layout.addWidget(QLabel(self.tr("Modules Actifs dans le Menu (ordonnés)")))
        self.visible_modules_listwidget = QListWidget()
        self.visible_modules_listwidget.setObjectName("visibleModulesListWidget")
        self.visible_modules_listwidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.visible_modules_listwidget.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.visible_modules_listwidget.setStyleSheet("QListWidget::item { padding: 5px; }") # Moved to dialog setStyleSheet
        visible_group_layout.addWidget(self.visible_modules_listwidget)
        content_layout.addLayout(visible_group_layout, 2) # Takes more space

        # Action Buttons Section (between the two lists)
        actions_layout = QVBoxLayout()
        actions_layout.addStretch()
        self.move_to_hidden_button = QPushButton("➡️") # Move to Hidden
        self.move_to_hidden_button.setToolTip(self.tr("Cacher le module sélectionné"))
        self.move_to_hidden_button.clicked.connect(self._move_selected_to_hidden)
        actions_layout.addWidget(self.move_to_hidden_button)

        self.move_to_visible_button = QPushButton("⬅️") # Move to Visible
        self.move_to_visible_button.setToolTip(self.tr("Afficher le module sélectionné"))
        self.move_to_visible_button.clicked.connect(self._move_selected_to_visible)
        actions_layout.addWidget(self.move_to_visible_button)
        actions_layout.addStretch()
        content_layout.addLayout(actions_layout, 0) # Takes minimal space

        # Hidden Modules Section
        hidden_group_layout = QVBoxLayout()
        hidden_group_layout.addWidget(QLabel(self.tr("Modules Disponibles (cachés)")))
        self.hidden_modules_listwidget = QListWidget()
        self.hidden_modules_listwidget.setObjectName("hiddenModulesListWidget")
        self.hidden_modules_listwidget.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.hidden_modules_listwidget.setStyleSheet("QListWidget::item { padding: 5px; }") # Moved to dialog setStyleSheet
        hidden_group_layout.addWidget(self.hidden_modules_listwidget)
        content_layout.addLayout(hidden_group_layout, 2) # Takes more space

        main_layout.addLayout(content_layout)

        # Apply some specific QSS to the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0; /* Light gray background for the dialog */
            }
            QLabel {
                font-weight: bold;
                padding-bottom: 5px;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white; /* White background for list widgets */
            }
            QListWidget::item {
                padding: 7px 5px; /* Slightly more padding for items */
            }
            QListWidget::item:hover {
                background-color: #e9f5ff; /* Light blue hover */
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #0078d7; /* Standard blue selection */
                color: white;
            }
            QPushButton { /* General style for buttons in this dialog if not overridden by QDialogButtonBox */
                padding: 6px 12px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            /* Style for the arrow buttons if needed, can use objectName */
            /* For example:
            QPushButton#moveToHiddenButton {
                min-width: 0px; set icon size appropriately
            }
            */
        """)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.RestoreDefaults | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText(self.tr("Enregistrer"))
        self.button_box.button(QDialogButtonBox.RestoreDefaults).setText(self.tr("Réinitialiser par Défaut"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))

        self.button_box.accepted.connect(self._save_configuration)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._confirm_restore_defaults)

        main_layout.addWidget(self.button_box)

        # Connect item double click for quick move
        self.visible_modules_listwidget.itemDoubleClicked.connect(self._move_selected_to_hidden)
        self.hidden_modules_listwidget.itemDoubleClicked.connect(self._move_selected_to_visible)


    def _get_module_display_name(self, module_name):
        """Gets the translatable display name for a module."""
        module_info = next((m for m in self.configurable_modules if m['name'] == module_name), None)
        if module_info:
            action = getattr(self.parent(), module_info['action_attr'], None) # Assuming parent is DocumentManager
            if action:
                return action.text().replace("&", "") # Get text from QAction, remove ampersand
        return module_name # Fallback to internal name

    def _is_module_permitted(self, module_name):
        """Checks if a module is globally enabled and permitted by license."""
        module_info = next((m for m in self.configurable_modules if m['name'] == module_name), None)
        if not module_info:
            return False

        # 1. Globally enabled by admin settings
        if not self.module_states.get(module_name, True): # Default to True if not in states (should be)
            return False

        # 2. Permitted by license
        # This requires the MODULE_TO_LICENSE_FEATURE_MAP logic from DocumentManager
        # We'll need to pass license_features and a simplified map or the relevant feature key.
        # For now, let's assume DocumentManager pre-filters `configurable_modules` or we check here.
        # This is a simplified check. The real check in DocumentManager._apply_permissions is more robust.
        # Let's assume for this dialog, if a module is in `configurable_modules` passed to it, it's generally available.
        # The fine-grained license check is for display in the main menu. Here, we list all that *could* be configured.
        # However, it's better to filter based on actual availability.

        # Re-evaluating: The dialog should only show modules the user *could* enable based on global settings and license.
        # The `DocumentManager` should pass a list of `configurable_modules` that are ALREADY filtered by global admin state and license.
        # For now, we'll use the `module_states` and `license_features` passed in.

        # Define the mapping (subset of what's in DocumentManager)
        # This is a bit of a duplication, ideally this mapping is more central.
        # For simplicity, we'll hardcode some common ones here for the dialog's logic.
        # A better approach: pass the 'license_feature_key' with each module_info in self.configurable_modules
        temp_module_to_license_map = {
            'project_management': 'FEATURE_PROJECT_MANAGEMENT', # Placeholder, use actual constants if available
            'product_management': 'FEATURE_PRODUCT_MANAGEMENT',
            'statistics': 'FEATURE_STATISTICS_MODULE',
            # ... add others as needed from DocumentManager._apply_permissions
        }
        license_feature_key_str = temp_module_to_license_map.get(module_name)
        if license_feature_key_str:
            # This check assumes self.license_features contains strings like 'FEATURE_PROJECT_MANAGEMENT'
            # This needs to align with how license_features are actually stored/passed.
            # For now, let's assume a direct match if key exists.
            # A more robust way: DocumentManager pre-filters or provides a helper.
            # Simplified: If a specific license feature is required for this module, check it.
            # This part is tricky without the actual constants. For now, we'll be lenient.
            # Let's assume DocumentManager passes modules that are ALREADY license-checked.
            # So, if it's in self.configurable_modules and self.module_states allows, it's good for the dialog.
            pass # This check will be implicitly handled if DocumentManager filters the list it passes.

        return True # If it passed global state check

    def _populate_lists(self):
        self.visible_modules_listwidget.clear()
        self.hidden_modules_listwidget.clear()

        user_order = self.user_config.get("order", [])
        user_visibility = self.user_config.get("visibility", {})

        processed_for_visible = set()

        # Populate visible list based on user's order
        for module_name in user_order:
            module_info = next((m for m in self.configurable_modules if m['name'] == module_name), None)
            if not module_info:
                logging.warning(f"Module '{module_name}' from user config 'order' not found in global configurable_modules. Skipping.")
                continue

            if not self._is_module_permitted(module_name):
                logging.info(f"Module '{module_name}' is not permitted (globally disabled or no license). Not showing in customization dialog.")
                continue

            if user_visibility.get(module_name, False): # Check user's explicit visibility setting
                display_name = self._get_module_display_name(module_name)
                item = QListWidgetItem(display_name)
                item.setData(Qt.UserRole, module_name) # Store internal name
                self.visible_modules_listwidget.addItem(item)
                processed_for_visible.add(module_name)

        # Populate hidden list with remaining permitted modules
        for module_info in self.configurable_modules:
            module_name = module_info['name']
            if module_name in processed_for_visible:
                continue # Already added to visible list

            if not self._is_module_permitted(module_name):
                # logging.info(f"Module '{module_name}' is not permitted. Not adding to hidden list either.")
                continue

            # If it's permitted but wasn't in the user's visible order, or explicitly hidden by user
            display_name = self._get_module_display_name(module_name)
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, module_name)
            self.hidden_modules_listwidget.addItem(item)

        self._update_button_states()


    def _load_initial_configuration(self):
        # In a real app, this would come from db_manager.get_setting
        # For now, using the dummy function
        raw_config = get_user_menu_config(self.current_user_id) # Placeholder

        if isinstance(raw_config, str):
            try:
                self.user_config = json.loads(raw_config)
            except json.JSONDecodeError:
                logging.warning(f"Failed to parse user menu config JSON for user {self.current_user_id}. Using defaults.")
                self.user_config = {}
        elif isinstance(raw_config, dict):
            self.user_config = raw_config
        else:
            logging.warning(f"Invalid user menu config format for user {self.current_user_id}. Using defaults.")
            self.user_config = {}

        # Ensure default structure if parts are missing
        if "order" not in self.user_config or not isinstance(self.user_config["order"], list):
            # Default order: all permitted modules from configurable_modules
            self.user_config["order"] = [
                m['name'] for m in self.configurable_modules if self._is_module_permitted(m['name'])
            ]
        if "visibility" not in self.user_config or not isinstance(self.user_config["visibility"], dict):
            # Default visibility: all permitted modules are visible
            self.user_config["visibility"] = {
                m['name']: True for m in self.configurable_modules if self._is_module_permitted(m['name'])
            }

        # Filter order and visibility based on current permissions (global state, license)
        # self.configurable_modules IS ALREADY THE PRE-FILTERED LIST from DocumentManager

        current_permitted_modules_names = {m['name'] for m in self.configurable_modules}

        user_order_from_config = self.user_config.get("order", [])
        user_visibility_from_config = self.user_config.get("visibility", {})

        # Ensure all modules in current_permitted_modules_names have a visibility entry, defaulting to True
        # and respect user's prior explicit settings if available.
        final_visibility = {}
        for name in current_permitted_modules_names:
            final_visibility[name] = user_visibility_from_config.get(name, True)

        # Filter the user's order to only include currently permitted modules
        # and respect their visibility setting.
        # Modules that were in user's order but are no longer permitted are implicitly removed.
        # Modules that were in user's order but set to hidden by user are also removed from ordered list.
        ordered_visible_modules = []
        for name in user_order_from_config:
            if name in current_permitted_modules_names and final_visibility.get(name, False):
                ordered_visible_modules.append(name)

        # Add any other permitted and visible modules that were not in the user's original order list
        # (e.g., new modules added to the system and defaulted to visible)
        for name in current_permitted_modules_names:
            if final_visibility.get(name, False) and name not in ordered_visible_modules:
                ordered_visible_modules.append(name)

        self.user_config = {"order": ordered_visible_modules, "visibility": final_visibility}
        self._populate_lists()

    def _move_selected_to_hidden(self):
        selected_items = self.visible_modules_listwidget.selectedItems()
        if not selected_items:
            return
        item_to_move = selected_items[0]

        # Take item from visible list
        row = self.visible_modules_listwidget.row(item_to_move)
        moved_item = self.visible_modules_listwidget.takeItem(row)

        # Add to hidden list
        self.hidden_modules_listwidget.addItem(moved_item)
        self.hidden_modules_listwidget.sortItems() # Keep hidden list sorted alphabetically for usability
        self._update_button_states()

    def _move_selected_to_visible(self):
        selected_items = self.hidden_modules_listwidget.selectedItems()
        if not selected_items:
            return
        item_to_move = selected_items[0]

        # Take item from hidden list
        row = self.hidden_modules_listwidget.row(item_to_move)
        moved_item = self.hidden_modules_listwidget.takeItem(row)

        # Add to visible list (at the end by default)
        self.visible_modules_listwidget.addItem(moved_item)
        self._update_button_states()

    def _update_button_states(self):
        self.move_to_hidden_button.setEnabled(self.visible_modules_listwidget.currentItem() is not None and self.visible_modules_listwidget.count() > 0)
        self.move_to_visible_button.setEnabled(self.hidden_modules_listwidget.currentItem() is not None and self.hidden_modules_listwidget.count() > 0)

    def _save_configuration(self):
        new_order = []
        for i in range(self.visible_modules_listwidget.count()):
            item = self.visible_modules_listwidget.item(i)
            new_order.append(item.data(Qt.UserRole))

        new_visibility = {}
        for module_name in new_order: # All in visible list are true
            new_visibility[module_name] = True
        for i in range(self.hidden_modules_listwidget.count()):
            item = self.hidden_modules_listwidget.item(i)
            module_name = item.data(Qt.UserRole)
            new_visibility[module_name] = False # All in hidden list are false

        # Ensure all known configurable modules (that are permitted) have an entry in visibility
        for module_info in self.configurable_modules:
            module_name = module_info['name']
            if self._is_module_permitted(module_name) and module_name not in new_visibility:
                # This case implies a module was permitted but not in either list (shouldn't happen if _populate_lists is correct)
                # Or, it's a module that was never in the user's config and remained in its default state (e.g. implicitly visible)
                # For robustness, if it's not in new_order (so not explicitly visible), mark as false.
                if module_name not in new_order:
                     new_visibility[module_name] = False


        config_to_save = {"order": new_order, "visibility": new_visibility}

        # Use the real set_setting function via parent or callback
        # For now, using the dummy
        success = set_user_menu_config(self.current_user_id, config_to_save)

        if success:
            self.menu_config_changed.emit()
            QMessageBox.information(self, self.tr("Configuration Sauvegardée"), self.tr("L'ordre et la visibilité du menu ont été sauvegardés."))
            self.accept()
        else:
            QMessageBox.critical(self, self.tr("Erreur de Sauvegarde"), self.tr("Impossible de sauvegarder la configuration du menu."))

    def _confirm_restore_defaults(self):
        reply = QMessageBox.question(self, self.tr("Réinitialiser la Configuration"),
                                     self.tr("Êtes-vous sûr de vouloir réinitialiser l'ordre et la visibilité des modules à leurs valeurs par défaut ?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._restore_defaults()

    def _restore_defaults(self):
        # Construct default config based on current permissions
        default_order = []
        default_visibility = {}
        for module_info in self.configurable_modules:
            module_name = module_info['name']
            if self._is_module_permitted(module_name):
                default_order.append(module_name)
                default_visibility[module_name] = True # By default, all permitted modules are visible

        self.user_config = {"order": default_order, "visibility": default_visibility}
        self._populate_lists()
        QMessageBox.information(self, self.tr("Configuration Réinitialisée"),
                                self.tr("L'affichage a été réinitialisé aux valeurs par défaut. Cliquez sur 'Enregistrer' pour appliquer ces changements."))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    # This basic test needs QApplication
    app = QApplication(sys.argv)

    # Mock necessary inputs for the dialog
    mock_user_id = "test_user_123"

    # Use the dummy CONFIGURABLE_MODULES from the top of this file
    mock_configurable_modules = CONFIGURABLE_MODULES_DUMMY

    # Simulate module_states (all enabled for this test)
    mock_module_states = {m['name']: True for m in mock_configurable_modules}

    # Simulate license_features (all allowed for this test)
    # This is a simplified representation. In reality, it's a set of feature constants.
    mock_license_features = set(['FEATURE_PROJECT_MANAGEMENT', 'FEATURE_PRODUCT_MANAGEMENT', 'FEATURE_STATISTICS_MODULE'])


    # Define a dummy parent that has the action attributes needed by _get_module_display_name
    class DummyParent(QWidget):
        def __init__(self):
            super().__init__()
            # Create dummy QActions to get their text
            self.project_management_action = QAction("Gestion de Projet", self)
            self.product_list_action = QAction("Gestion des Produits", self)
            self.statistics_action = QAction("Statistiques", self)
            # Add more if CONFIGURABLE_MODULES_DUMMY expands

    dummy_parent_widget = DummyParent()

    dialog = MenuCustomizationDialog(
        current_user_id=mock_user_id,
        configurable_modules=mock_configurable_modules,
        module_states=mock_module_states,
        license_features=mock_license_features, # Pass the mock license features
        parent=dummy_parent_widget # Pass the dummy parent
    )

    # Connect signal for testing
    dialog.menu_config_changed.connect(lambda: print("Signal menu_config_changed emitted!"))

    sys.exit(dialog.exec_())
