import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QMessageBox, QCheckBox, QHBoxLayout, QLabel
)
from app.client_management.client_controller import ClientController # Assumed path

logger = logging.getLogger(__name__)

class ReferentDetailsDialog(QDialog):
    def __init__(self, client_id: str, client_name: str, controller: ClientController,
                 referent_data: dict | None = None, current_user_id: str | None = None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.client_name = client_name
        self.controller = controller
        self.referent_data = referent_data # If None, it's creation mode
        self.current_user_id = current_user_id

        self.is_edit_mode = referent_data is not None

        self.setWindowTitle(f"{'Modifier' if self.is_edit_mode else 'Désigner'} Référent : {self.client_name}")
        self.setMinimumWidth(500)

        self._init_ui()
        self._load_countries()
        if self.is_edit_mode:
            self._populate_fields()
        else:
            # For new referents, try to pre-select client's current country if available
            try:
                client_details = self.controller.get_client_by_id_for_dialog(self.client_id)
                if client_details and client_details.get('country_id'):
                    self.country_combo.setCurrentData(client_details['country_id'])
            except AttributeError:
                logger.error(f"Controller missing 'get_client_by_id_for_dialog' or similar method.")
            except Exception as e:
                logger.error(f"Error fetching client details for pre-selection: {e}", exc_info=True)
            # is_active_checkbox is True by default for new, not shown until edit.

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.country_combo = QComboBox()
        self.country_combo.currentIndexChanged.connect(self._on_country_selected)
        form_layout.addRow("Pays:", self.country_combo)

        # Region: ComboBox for existing, LineEdit for new
        self.region_layout = QHBoxLayout()
        self.region_combo = QComboBox()
        self.region_combo.setMinimumWidth(200)
        self.region_new_edit = QLineEdit()
        self.region_new_edit.setPlaceholderText("Ou nouvelle région...")
        self.region_layout.addWidget(self.region_combo)
        self.region_layout.addWidget(QLabel("ou"))
        self.region_layout.addWidget(self.region_new_edit)
        form_layout.addRow("Région:", self.region_layout)

        # City: ComboBox for existing, LineEdit for new
        self.city_layout = QHBoxLayout()
        self.city_combo = QComboBox()
        self.city_combo.setMinimumWidth(200)
        self.city_new_edit = QLineEdit()
        self.city_new_edit.setPlaceholderText("Ou nouvelle ville...")
        self.city_layout.addWidget(self.city_combo)
        self.city_layout.addWidget(QLabel("ou"))
        self.city_layout.addWidget(self.city_new_edit)
        form_layout.addRow("Ville:", self.city_layout)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes spécifiques au rôle de référent...")
        form_layout.addRow("Notes:", self.notes_edit)

        self.is_active_checkbox = QCheckBox("Référent Actif")
        if self.is_edit_mode:
            form_layout.addRow(self.is_active_checkbox)
        else:
            self.is_active_checkbox.setChecked(True) # Default to active for new
            # self.is_active_checkbox.setVisible(False) # Hide for new creation, active by default

        layout.addLayout(form_layout)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(self.buttons_layout)

        self.setLayout(layout)

    def _load_countries(self):
        self.country_combo.blockSignals(True)
        self.country_combo.clear()
        self.country_combo.addItem("-- Sélectionner un pays --", None)
        try:
            countries = self.controller.get_all_countries()
            if countries:
                for country in countries:
                    self.country_combo.addItem(country['country_name'], country['country_id'])
        except Exception as e:
            logger.error(f"Failed to load countries: {e}", exc_info=True)
            QMessageBox.warning(self, "Erreur Chargement", "Impossible de charger la liste des pays.")
        self.country_combo.blockSignals(False)
        if not self.is_edit_mode and self.country_combo.count() > 1:
             # Pre-select client's current country if available (done in init)
             pass
        elif self.is_edit_mode and self.referent_data and self.referent_data.get('country_id'):
            self.country_combo.setCurrentData(self.referent_data['country_id'])


    def _on_country_selected(self, index):
        country_id = self.country_combo.itemData(index)
        self._load_regions(country_id)
        self._load_cities(country_id) # Cities depend on country, not region directly for this UI

    def _load_regions(self, country_id):
        self.region_combo.blockSignals(True)
        self.region_combo.clear()
        self.region_combo.addItem("-- Sélectionner une région --", None)
        self.region_new_edit.clear()
        if country_id is not None:
            try:
                regions = self.controller.get_regions_for_country(country_id)
                if regions:
                    for region in regions:
                        self.region_combo.addItem(region['region_name'], region['region_id'])
            except Exception as e:
                logger.error(f"Failed to load regions for country_id {country_id}: {e}", exc_info=True)
        self.region_combo.blockSignals(False)
        if self.is_edit_mode and self.referent_data and self.referent_data.get('region_id'):
            self.region_combo.setCurrentData(self.referent_data['region_id'])

    def _load_cities(self, country_id):
        self.city_combo.blockSignals(True)
        self.city_combo.clear()
        self.city_combo.addItem("-- Sélectionner une ville --", None)
        self.city_new_edit.clear()
        if country_id is not None:
            try:
                cities = self.controller.get_cities_for_country(country_id)
                if cities:
                    for city in cities:
                        self.city_combo.addItem(city['city_name'], city['city_id'])
            except Exception as e:
                logger.error(f"Failed to load cities for country_id {country_id}: {e}", exc_info=True)
        self.city_combo.blockSignals(False)
        if self.is_edit_mode and self.referent_data and self.referent_data.get('city_id'):
             self.city_combo.setCurrentData(self.referent_data['city_id'])


    def _populate_fields(self):
        if not self.referent_data:
            return

        self.country_combo.setCurrentData(self.referent_data.get('country_id'))
        # _on_country_selected will be triggered, which will load regions and cities.
        # We need to ensure that after they are loaded, the correct region/city is selected.
        # This is handled by the setCurrentData in _load_regions and _load_cities if is_edit_mode.

        self.notes_edit.setText(self.referent_data.get('notes', ''))
        self.is_active_checkbox.setChecked(self.referent_data.get('is_active', True))


    def get_data(self):
        country_id = self.country_combo.currentData()
        if country_id is None:
            QMessageBox.warning(self, "Données Manquantes", "Veuillez sélectionner un pays.")
            return None

        region_name = self.region_new_edit.text().strip()
        # region_id will be determined by controller using region_name and country_id

        city_name = self.city_new_edit.text().strip()
        # city_id will be determined by controller using city_name and country_id

        # If a region/city is selected from combo, its name should be used if new_edit is empty
        if not region_name and self.region_combo.currentData() is not None:
            region_name = self.region_combo.currentText()

        if not city_name and self.city_combo.currentData() is not None:
            city_name = self.city_combo.currentText()

        return {
            "client_id": self.client_id,
            "country_id": country_id,
            "region_name": region_name if region_name else None, # Pass name for controller to resolve
            "city_name": city_name if city_name else None,     # Pass name for controller to resolve
            "notes": self.notes_edit.toPlainText().strip(),
            "is_active": self.is_active_checkbox.isChecked(),
            "user_id": self.current_user_id,
            "referent_id": self.referent_data.get('referent_id') if self.is_edit_mode else None
        }

    def accept(self):
        data = self.get_data()
        if data is None:
            return

        if not self.current_user_id:
            QMessageBox.critical(self, "Erreur Utilisateur", "ID de l'utilisateur actuel non disponible.")
            return

        if self.is_edit_mode:
            result = self.controller.update_referent_details(
                referent_id=data['referent_id'],
                country_id=data['country_id'],
                region_name=data['region_name'],
                city_name=data['city_name'],
                notes=data['notes'],
                is_active=data['is_active'],
                user_id=data['user_id']
            )
            if result and result.get('success'):
                QMessageBox.information(self, "Succès", "Détails du référent mis à jour.")
                super().accept()
            else:
                error_msg = result.get('error', 'Erreur inconnue.') if result else 'Erreur inconnue.'
                QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour le référent: {error_msg}")
        else:
            result = self.controller.make_client_referent(
                client_id=data['client_id'],
                country_id=data['country_id'],
                region_name=data['region_name'],
                city_name=data['city_name'],
                notes=data['notes'],
                user_id=data['user_id']
            )
            if result and result.get('success'):
                QMessageBox.information(self, "Succès", f"Client {self.client_name} désigné comme référent.")
                super().accept()
            else:
                error_msg = result.get('error', 'Erreur inconnue.') if result else 'Erreur inconnue.'
                status_msg = result.get('status', '') if result else ''
                if status_msg == 'already_exists':
                    QMessageBox.warning(self, "Information", f"Ce client est déjà un référent.")
                    super().reject() # Or accept if we want to allow editing immediately
                else:
                    QMessageBox.critical(self, "Erreur", f"Impossible de désigner le client comme référent: {error_msg}")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    # This is a mock controller for testing the dialog standalone
    class MockClientController:
        def get_all_countries(self):
            return [{'country_id': 1, 'country_name': 'France'}, {'country_id': 2, 'country_name': 'USA'}]
        def get_regions_for_country(self, country_id):
            if country_id == 1: return [{'region_id': 10, 'region_name': 'Île-de-France'}, {'region_id': 11, 'region_name': 'Occitanie'}]
            if country_id == 2: return [{'region_id': 20, 'region_name': 'California'}, {'region_id': 21, 'region_name': 'New York State'}]
            return []
        def get_cities_for_country(self, country_id):
            if country_id == 1: return [{'city_id': 100, 'city_name': 'Paris'}, {'city_id': 101, 'city_name': 'Toulouse'}]
            if country_id == 2: return [{'city_id': 200, 'city_name': 'Los Angeles'}, {'city_id': 201, 'city_name': 'New York City'}]
            return []
        def get_or_add_region(self, name, country_id):
            logger.info(f"MOCK: Get or add region: {name} for country {country_id}")
            # Simulate adding by returning a new ID if not in predefined list
            if country_id == 1 and name == "Nouvelle Aquitaine": return {'region_id': 12, 'region_name': 'Nouvelle Aquitaine'}
            return {'region_id': hash(name) % 1000, 'region_name': name} # mock
        def add_city(self, name, country_id): # add_city in controller uses get_or_add_city from db_manager
            logger.info(f"MOCK: Add city: {name} for country {country_id}")
            return {'city_id': hash(name) % 1000, 'city_name': name} # mock
        def make_client_referent(self, client_id, country_id, region_name, city_name, notes, user_id):
            logger.info(f"MOCK: Make client {client_id} referent. Country: {country_id}, Region: {region_name}, City: {city_name}, Notes: {notes}, User: {user_id}")
            return {'success': True, 'referent_id': 'mock-ref-uuid-new'}
        def update_referent_details(self, referent_id, country_id, region_name, city_name, notes, is_active, user_id):
            logger.info(f"MOCK: Update referent {referent_id}. Country: {country_id}, Region: {region_name}, City: {city_name}, Notes: {notes}, Active: {is_active}, User: {user_id}")
            return {'success': True}

        class MockClientsCRUD: # Nested mock for simplicity
            def get_client_by_id(self, client_id):
                if client_id == "client_test_123":
                    return {"client_id": "client_test_123", "client_name": "Client Test", "country_id": 1}
                return None

        def __init__(self): # Add init to assign the nested mock
            self.clients_crud = self.MockClientsCRUD()


    app = QApplication(sys.argv)
    mock_controller = MockClientController()

    # Test creation mode
    # dialog_create = ReferentDetailsDialog(client_id="client_test_123", client_name="Client Alpha", controller=mock_controller, current_user_id="user_xyz")
    # if dialog_create.exec_() == QDialog.Accepted:
    #     print("Create Dialog Accepted. Data:", dialog_create.get_data())
    # else:
    #     print("Create Dialog Cancelled.")

    # Test edit mode
    existing_ref_data = {
        'referent_id': 'ref-uuid-abc', 'client_id': 'client_test_123',
        'country_id': 1, 'region_id': 10, 'city_id': 100,
        'notes': 'Initial notes from DB.', 'is_active': True,
        'country_name': 'France', 'region_name': 'Île-de-France', 'city_name': 'Paris' # For display in dialog title etc if needed
    }
    dialog_edit = ReferentDetailsDialog(client_id="client_test_123", client_name="Client Alpha",
                                        controller=mock_controller, referent_data=existing_ref_data,
                                        current_user_id="user_xyz")
    if dialog_edit.exec_() == QDialog.Accepted:
        print("Edit Dialog Accepted. Data:", dialog_edit.get_data())
    else:
        print("Edit Dialog Cancelled.")

    sys.exit(app.exec_())
