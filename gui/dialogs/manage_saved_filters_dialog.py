# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QAbstractItemView, QLineEdit
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QCoreApplication # Added QCoreApplication for fallback tr
from db.cruds import user_saved_filters_crud

# It's good practice to define tr at the module level or ensure it's available
# For now, we'll use a helper in the class or rely on parent's tr.

class ManageSavedFiltersDialog(QDialog):
    def __init__(self, current_user_id, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.changes_made = False  # Flag to indicate if any filter was deleted/renamed

        self.setWindowTitle(self._tr("Gérer les Filtres Sauvegardés"))
        self.setMinimumWidth(450) # Slightly wider for better layout
        self.setMinimumHeight(300)
        self.init_ui()
        self.load_filters()

    def _tr(self, text_key):
        # Attempt to use parent's tr method if available (e.g., if parent is DocumentManager)
        if self.parent() and hasattr(self.parent(), 'tr'):
            return self.parent().tr(text_key)
        # Fallback for standalone testing or if parent doesn't have tr
        return QCoreApplication.translate("ManageSavedFiltersDialog", text_key)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10) # Add some spacing

        instruction_label = QLabel(self._tr("Sélectionnez un filtre pour le gérer."))
        main_layout.addWidget(instruction_label)

        self.filters_list_widget = QListWidget()
        self.filters_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.filters_list_widget.itemSelectionChanged.connect(self.update_button_states)
        self.filters_list_widget.itemDoubleClicked.connect(self.rename_selected_filter_on_doubleclick) # Edit on double click
        main_layout.addWidget(self.filters_list_widget)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.rename_button = QPushButton(self._tr("Renommer"))
        self.rename_button.setText("✏️")
        self.rename_button.setToolTip(self._tr("Renommer le filtre sélectionné"))
        self.rename_button.clicked.connect(self.rename_selected_filter)
        button_layout.addWidget(self.rename_button)

        self.delete_button = QPushButton(self._tr("Supprimer"))
        self.delete_button.setText("🗑️")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setToolTip(self._tr("Supprimer le filtre sélectionné"))
        self.delete_button.clicked.connect(self.delete_selected_filter)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch(1)

        self.close_button = QPushButton(self._tr("Fermer"))
        self.close_button.setDefault(True) # Make it default
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)
        self.update_button_states()

    def load_filters(self):
        self.filters_list_widget.clear()
        try:
            saved_filters = user_saved_filters_crud.get_saved_filters_for_user(self.current_user_id)
            if saved_filters:
                for filt in saved_filters:
                    item_text = filt.get('filter_name', self._tr("Filtre Sans Nom"))
                    list_item = QListWidgetItem(item_text)
                    list_item.setData(Qt.UserRole, filt)
                    self.filters_list_widget.addItem(list_item)
            logging.info(f"Loaded {len(saved_filters) if saved_filters else 0} filters for user {self.current_user_id} in management dialog.")
        except Exception as e:
            logging.error(f"Error loading filters in ManageSavedFiltersDialog: {e}", exc_info=True)
            QMessageBox.critical(self, self._tr("Erreur Chargement"), self._tr("Impossible de charger les filtres sauvegardés."))
        finally:
            self.update_button_states()

    def update_button_states(self):
        has_selection = bool(self.filters_list_widget.selectedItems())
        self.rename_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def rename_selected_filter_on_doubleclick(self, item):
        # This slot is connected to itemDoubleClicked
        if item: # Ensure an item was actually double-clicked
            self.rename_selected_filter()

    def rename_selected_filter(self):
        selected_items = self.filters_list_widget.selectedItems()
        if not selected_items:
            # This case might occur if called not from double-click and no selection
            if not self.filters_list_widget.currentItem(): # Check if a current item exists even if not "selected" (e.g. focus)
                 QMessageBox.information(self, self._tr("Aucune Sélection"), self._tr("Veuillez sélectionner un filtre à renommer."))
                 return
            current_item = self.filters_list_widget.currentItem()
        else:
            current_item = selected_items[0]

        filter_data = current_item.data(Qt.UserRole)
        if not filter_data:
            logging.error("Rename failed: No data associated with selected list item.")
            QMessageBox.warning(self, self._tr("Erreur Interne"), self._tr("Données du filtre non trouvées."))
            return

        saved_filter_id = filter_data.get('id')
        current_name = filter_data.get('filter_name', '')

        new_name, ok = QInputDialog.getText(self, self._tr("Renommer Filtre"),
                                            self._tr("Nouveau nom pour le filtre:"),
                                            QLineEdit.Normal, current_name)

        if ok and new_name:
            new_name_stripped = new_name.strip()
            if not new_name_stripped:
                QMessageBox.warning(self, self._tr("Nom Invalide"), self._tr("Le nom du filtre ne peut pas être vide."))
                return
            if new_name_stripped == current_name:
                return # No change

            try:
                # Check for name collision before attempting update
                existing_filters = user_saved_filters_crud.get_saved_filters_for_user(self.current_user_id)
                if any(f['filter_name'] == new_name_stripped and f['id'] != saved_filter_id for f in existing_filters):
                    QMessageBox.warning(self, self._tr("Nom Dupliqué"), self._tr("Un autre filtre avec le nom '{0}' existe déjà.").format(new_name_stripped))
                    return

                success = user_saved_filters_crud.update_saved_filter(
                    saved_filter_id=saved_filter_id,
                    user_id=self.current_user_id,
                    new_name=new_name_stripped
                )
                if success:
                    self.changes_made = True
                    self.load_filters()
                else:
                    QMessageBox.warning(self, self._tr("Échec"), self._tr("Impossible de renommer le filtre."))
            except Exception as e:
                logging.error(f"Error renaming filter ID {saved_filter_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self._tr("Erreur"), self._tr("Une erreur est survenue lors du renommage."))


    def delete_selected_filter(self):
        selected_items = self.filters_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self._tr("Aucune Sélection"), self._tr("Veuillez sélectionner un filtre à supprimer."))
            return

        current_item = selected_items[0]
        filter_data = current_item.data(Qt.UserRole)
        if not filter_data:
            logging.error("Delete failed: No data associated with selected list item.")
            QMessageBox.warning(self, self._tr("Erreur Interne"), self._tr("Données du filtre non trouvées."))
            return

        saved_filter_id = filter_data.get('id')
        filter_name = filter_data.get('filter_name', self._tr("ce filtre"))

        reply = QMessageBox.question(self, self._tr("Confirmer Suppression"),
                                     self._tr("Êtes-vous sûr de vouloir supprimer le filtre sauvegardé '{0}'?").format(filter_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                success = user_saved_filters_crud.delete_saved_filter(saved_filter_id, self.current_user_id)
                if success:
                    self.changes_made = True
                    self.load_filters()
                else:
                    QMessageBox.warning(self, self._tr("Échec"), self._tr("Impossible de supprimer le filtre."))
            except Exception as e:
                logging.error(f"Error deleting filter ID {saved_filter_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self._tr("Erreur"), self._tr("Une erreur est survenue lors de la suppression."))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    # Setup basic logging for standalone testing
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # Dummy CRUD functions for standalone testing
    class DummyUserSavedFiltersCRUD:
        _filters_db = [
            {'id': 1, 'user_id': 'test_user', 'filter_name': 'French Prospects Active', 'filter_parameters_json': '{"status_id": 1, "country_id": 75, "archive_filter": false}', 'created_at':'2023-01-01', 'updated_at':'2023-01-01'},
            {'id': 2, 'user_id': 'test_user', 'filter_name': 'US Archived Clients', 'filter_parameters_json': '{"country_id": 233, "archive_filter": true}', 'created_at':'2023-01-02', 'updated_at':'2023-01-02'},
            {'id': 3, 'user_id': 'other_user', 'filter_name': 'Other User Filter', 'filter_parameters_json': '{}', 'created_at':'2023-01-03', 'updated_at':'2023-01-03'},
        ]

        def get_saved_filters_for_user(self, user_id):
            logging.debug(f"Dummy CRUD: get_saved_filters_for_user called for {user_id}")
            # Simulate JSON parsing for parameters
            results = []
            for f_dict in self._filters_db:
                if f_dict['user_id'] == user_id:
                    try:
                        params = json.loads(f_dict['filter_parameters_json'])
                        # Create a new dict to avoid modifying the original _filters_db structure during test
                        results.append({**f_dict, 'filter_parameters': params })
                    except json.JSONDecodeError:
                         results.append({**f_dict, 'filter_parameters': {} }) # Add with empty params on error
            return results


        def delete_saved_filter(self, saved_filter_id, user_id):
            logging.debug(f"Dummy CRUD: delete_saved_filter called for id {saved_filter_id}, user {user_id}")
            initial_len = len(self._filters_db)
            self._filters_db = [f for f in self._filters_db if not (f['id'] == saved_filter_id and f['user_id'] == user_id)]
            return len(self._filters_db) < initial_len

        def update_saved_filter(self, saved_filter_id, user_id, new_name=None, new_filter_parameters=None):
            logging.debug(f"Dummy CRUD: update_saved_filter for id {saved_filter_id}, user {user_id} with name {new_name}")
            for filt in self._filters_db:
                if filt['id'] == saved_filter_id and filt['user_id'] == user_id:
                    if new_name:
                        # Check for name collision with other filters of the same user
                        if any(f['filter_name'] == new_name and f['id'] != saved_filter_id for f in self._filters_db if f['user_id'] == user_id):
                            logging.warning("Dummy CRUD: Name collision during rename.")
                            return False
                        filt['filter_name'] = new_name
                    # new_filter_parameters not handled in this dummy update for simplicity
                    return True
            return False

    # Replace real CRUD with dummy for test
    user_saved_filters_crud = DummyUserSavedFiltersCRUD()

    app = QApplication(sys.argv)
    dialog = ManageSavedFiltersDialog(current_user_id="test_user")
    dialog.show()
    sys.exit(app.exec_())

# Ensure QCoreApplication is imported if using QCoreApplication.translate
# from PyQt5.QtCore import QCoreApplication
# No, it's already imported via Qt
