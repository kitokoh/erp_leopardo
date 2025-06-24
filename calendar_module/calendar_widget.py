from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
                             QPushButton, QFormLayout, QGroupBox, QCalendarWidget,
                             QMessageBox, QTextEdit, QHBoxLayout, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
import holidays # To be added to requirements.txt
from .cruds import company_calendar_settings_crud, user_calendar_events_crud
from .models import CompanyCalendarSettings, UserCalendarEvent
import logging

# Assume current_user_id is passed or accessible globally for now
# For a real application, this should be managed properly (e.g., via constructor, signals)
TEMP_USER_ID = "temp_user_01" # Placeholder for user ID

class CalendarWidget(QWidget):
    def __init__(self, parent=None, current_user_id=None):
        super().__init__(parent)
        self.current_user_id = current_user_id if current_user_id else TEMP_USER_ID # Use passed ID or fallback
        self.company_settings: Optional[CompanyCalendarSettings] = None
        self.user_events: List[UserCalendarEvent] = []

        self._init_ui()
        self._load_company_settings()
        self._load_user_events() # Load events for the current month initially

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Company Settings Group ---
        settings_group = QGroupBox("Paramètres de l'Entreprise pour le Calendrier")
        settings_layout = QFormLayout()

        self.business_type_combo = QComboBox()
        self.business_type_combo.addItems(["B2B", "B2C", "Les Deux"])
        settings_layout.addRow("Type d'entreprise:", self.business_type_combo)

        self.activity_category_edit = QLineEdit()
        settings_layout.addRow("Catégorie d'activité:", self.activity_category_edit)

        self.country_iso_edit = QLineEdit()
        self.country_iso_edit.setPlaceholderText("ex: FR, US, GB")
        settings_layout.addRow("Code Pays (ISO 3166-1 alpha-2):", self.country_iso_edit)

        self.region_edit = QLineEdit()
        self.region_edit.setPlaceholderText("Optionnel: ex: IDF (pour la France), CA (pour les US)")
        settings_layout.addRow("Région/État (si applicable):", self.region_edit)

        self.save_settings_button = QPushButton("Sauvegarder Paramètres")
        self.save_settings_button.clicked.connect(self._save_company_settings)
        settings_layout.addRow(self.save_settings_button)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # --- Calendar View and Event Management ---
        calendar_events_layout = QHBoxLayout()

        # Calendar Widget
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.clicked[QDate].connect(self._on_date_selected)
        self.calendar_widget.currentPageChanged.connect(self._on_month_changed) # To reload events for new month
        calendar_events_layout.addWidget(self.calendar_widget, 2) # Calendar takes more space

        # Event Details and Management
        event_management_group = QGroupBox("Gestion des Événements")
        event_management_layout = QVBoxLayout()

        self.selected_date_label = QLabel(f"Date sélectionnée: {self.calendar_widget.selectedDate().toString('yyyy-MM-dd')}")
        event_management_layout.addWidget(self.selected_date_label)

        self.events_list_widget = QListWidget()
        event_management_layout.addWidget(self.events_list_widget)

        self.event_description_edit = QLineEdit()
        self.event_description_edit.setPlaceholderText("Description de l'événement")
        event_management_layout.addWidget(self.event_description_edit)

        self.event_type_combo = QComboBox()
        self.event_type_combo.addItems(["Télétravail", "Jour de Travail", "Autre Personnel"])
        event_management_layout.addWidget(self.event_type_combo)

        self.add_event_button = QPushButton("Ajouter Événement")
        self.add_event_button.clicked.connect(self._add_or_update_event)
        event_management_layout.addWidget(self.add_event_button)

        self.delete_event_button = QPushButton("Supprimer Événement Sélectionné")
        self.delete_event_button.clicked.connect(self._delete_event)
        event_management_layout.addWidget(self.delete_event_button)


        event_management_group.setLayout(event_management_layout)
        calendar_events_layout.addWidget(event_management_group, 1)

        main_layout.addLayout(calendar_events_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Module Calendrier")

    def _load_company_settings(self):
        logging.info(f"Chargement des paramètres pour l'utilisateur: {self.current_user_id}")
        settings = company_calendar_settings_crud.get_settings_by_user_id(self.current_user_id)
        if settings:
            self.company_settings = settings
            self.business_type_combo.setCurrentText(settings.business_type or "")
            self.activity_category_edit.setText(settings.activity_category or "")
            self.country_iso_edit.setText(settings.country_iso or "")
            self.region_edit.setText(settings.region or "")
            logging.info(f"Paramètres chargés: {settings}")
            self._highlight_calendar_dates() # Re-highlight after loading settings
        else:
            logging.info("Aucun paramètre trouvé pour cet utilisateur.")
            self.company_settings = None # Ensure it's None if not found
            # Clear fields or set defaults if desired
            self.business_type_combo.setCurrentIndex(0)
            self.activity_category_edit.clear()
            self.country_iso_edit.clear()
            self.region_edit.clear()


    def _save_company_settings(self):
        if not self.current_user_id:
            QMessageBox.warning(self, "Erreur Utilisateur", "ID utilisateur non défini. Impossible de sauvegarder.")
            return

        country_iso = self.country_iso_edit.text().strip().upper()
        if not country_iso:
            QMessageBox.warning(self, "Champ Requis", "Le code pays ISO est requis.")
            return

        settings_data = CompanyCalendarSettings(
            user_id=self.current_user_id,
            business_type=self.business_type_combo.currentText(),
            activity_category=self.activity_category_edit.text().strip(),
            country_iso=country_iso,
            region=self.region_edit.text().strip() or None # Store None if empty
        )

        logging.info(f"Sauvegarde des paramètres: {settings_data.dict()}")
        saved = company_calendar_settings_crud.save_settings(settings_data)
        if saved:
            self.company_settings = saved # Update local cache
            QMessageBox.information(self, "Succès", "Paramètres sauvegardés avec succès.")
            self._highlight_calendar_dates() # Re-highlight after saving settings
        else:
            QMessageBox.critical(self, "Erreur", "Échec de la sauvegarde des paramètres.")

    def _load_user_events(self):
        """Loads events for the currently visible month and the logged-in user."""
        if not self.current_user_id:
            return

        current_qdate = self.calendar_widget.selectedDate() # Or monthShown() / yearShown()
        year = current_qdate.year()
        month = current_qdate.month()

        start_date = QDate(year, month, 1).toPyDate()
        end_date = QDate(year, month, current_qdate.daysInMonth()).toPyDate()

        logging.info(f"Chargement des événements pour l'utilisateur {self.current_user_id} entre {start_date} et {end_date}")
        self.user_events = user_calendar_events_crud.get_events_by_user_id(
            user_id=self.current_user_id,
            start_date=start_date,
            end_date=end_date
        )
        logging.info(f"{len(self.user_events)} événements chargés.")
        self._highlight_calendar_dates()
        self._update_events_list_for_selected_date()


    def _highlight_calendar_dates(self):
        """Highlights holidays and user-defined events on the calendar."""
        self.calendar_widget.setDateTextFormat(QDate(), QTextCharFormat()) # Clear previous formats for all dates

        # Highlight Holidays
        holiday_format = QTextCharFormat()
        holiday_format.setBackground(QBrush(QColor("lightgreen")))
        holiday_format.setToolTip("Jour férié")

        if self.company_settings and self.company_settings.country_iso:
            try:
                country_holidays = holidays.CountryHoliday(
                    self.company_settings.country_iso,
                    prov=self.company_settings.region if self.company_settings.region else None,
                    years=self.calendar_widget.yearShown() # Only for the current year displayed
                )
                for date_obj, name in sorted(country_holidays.items()):
                    q_date = QDate(date_obj.year, date_obj.month, date_obj.day)
                    fmt = self.calendar_widget.dateTextFormat(q_date) # Get existing format
                    fmt.setBackground(QBrush(QColor("lightgreen"))) # Apply holiday background
                    fmt.setToolTip(f"Jour férié: {name}")
                    self.calendar_widget.setDateTextFormat(q_date, fmt)
            except KeyError:
                logging.warning(f"Code pays ou région non valide pour la bibliothèque holidays: {self.company_settings.country_iso}, {self.company_settings.region}")
            except Exception as e:
                logging.error(f"Erreur lors de la récupération des jours fériés: {e}")

        # Highlight User Events
        # Define formats for different user event types
        event_formats = {
            "Télétravail": QTextCharFormat(),
            "Jour de Travail": QTextCharFormat(),
            "Autre Personnel": QTextCharFormat(),
        }
        event_formats["Télétravail"].setBackground(QBrush(QColor("lightblue")))
        event_formats["Jour de Travail"].setBackground(QBrush(QColor("lightyellow")))
        event_formats["Autre Personnel"].setBackground(QBrush(QColor("lightcoral")))

        for event in self.user_events:
            q_date = QDate(event.event_date.year, event.event_date.month, event.event_date.day)
            fmt_key = event.event_type
            if event.event_type not in event_formats: # Fallback for unknown types
                fmt_key = "Autre Personnel"

            current_fmt_for_date = self.calendar_widget.dateTextFormat(q_date)
            # Merge backgrounds if a holiday and user event fall on the same day (simple override for now)
            # A more sophisticated approach might blend colors or use borders.
            if current_fmt_for_date.background() != QBrush(QColor("lightgreen")): # Don't override holiday green if it's already set
                 current_fmt_for_date.setBackground(event_formats[fmt_key].background())

            tooltip_parts = [current_fmt_for_date.toolTip()] if current_fmt_for_date.toolTip() else []
            tooltip_parts.append(f"{event.event_type}: {event.description or 'N/A'}")
            current_fmt_for_date.setToolTip("\n".join(filter(None, tooltip_parts)))

            self.calendar_widget.setDateTextFormat(q_date, current_fmt_for_date)

        self.calendar_widget.updateCells() # Ensure calendar redraws with new formats


    def _on_date_selected(self, date: QDate):
        self.selected_date_label.setText(f"Date sélectionnée: {date.toString('yyyy-MM-dd')}")
        self._update_events_list_for_selected_date()

    def _on_month_changed(self, year, month):
        # Called when the user navigates to a new month/year in QCalendarWidget
        logging.info(f"Mois changé vers: {year}-{month}. Rechargement des événements.")
        self._load_user_events() # This will reload events for the new month and re-highlight

    def _update_events_list_for_selected_date(self):
        self.events_list_widget.clear()
        selected_py_date = self.calendar_widget.selectedDate().toPyDate()

        # Add holidays for the selected date
        if self.company_settings and self.company_settings.country_iso:
            try:
                country_holidays = holidays.CountryHoliday(
                    self.company_settings.country_iso,
                    prov=self.company_settings.region if self.company_settings.region else None,
                    years=selected_py_date.year
                )
                if selected_py_date in country_holidays:
                    item = QListWidgetItem(f"Jour Férié: {country_holidays[selected_py_date]}")
                    item.setForeground(QColor("darkgreen"))
                    self.events_list_widget.addItem(item)
            except Exception as e:
                logging.warning(f"Impossible de vérifier les jours fériés pour la liste: {e}")

        # Add user events
        for event in self.user_events:
            if event.event_date == selected_py_date:
                item_text = f"{event.event_type}: {event.description or 'N/A'}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, event) # Store the event object
                self.events_list_widget.addItem(list_item)

        # Clear input fields when date changes if no item is selected or for new event
        self.event_description_edit.clear()
        self.event_type_combo.setCurrentIndex(0)


    def _add_or_update_event(self):
        if not self.current_user_id:
            QMessageBox.warning(self, "Erreur Utilisateur", "ID utilisateur non défini.")
            return

        selected_qdate = self.calendar_widget.selectedDate()
        event_date_py = selected_qdate.toPyDate()
        description = self.event_description_edit.text().strip()
        event_type = self.event_type_combo.currentText()

        if not description:
            QMessageBox.warning(self, "Champ Requis", "La description de l'événement est requise.")
            return

        event_data = UserCalendarEvent(
            user_id=self.current_user_id,
            event_date=event_date_py,
            event_type=event_type,
            description=description
        )

        # Basic logic: for now, always add. Update logic can be more complex.
        # To implement update, you'd check if an event for this type/date exists or if an item is selected.
        # For simplicity, this example adds a new event.

        new_event = user_calendar_events_crud.add_event(event_data)

        if new_event:
            QMessageBox.information(self, "Succès", "Événement ajouté avec succès.")
            self._load_user_events() # Reload events for the current month
            self.event_description_edit.clear()
        else:
            QMessageBox.critical(self, "Erreur", "Échec de l'ajout de l'événement.")

    def _delete_event(self):
        selected_item = self.events_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un événement à supprimer.")
            return

        event_data = selected_item.data(Qt.UserRole)
        if not isinstance(event_data, UserCalendarEvent) or event_data.id is None:
            QMessageBox.warning(self, "Erreur", "Cet élément ne peut pas être supprimé (ce n'est pas un événement utilisateur ou il manque un ID).")
            return

        reply = QMessageBox.confirm(
            self, "Confirmer Suppression",
            f"Êtes-vous sûr de vouloir supprimer l'événement: {event_data.description}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if user_calendar_events_crud.delete_event(event_data.id):
                QMessageBox.information(self, "Succès", "Événement supprimé.")
                self._load_user_events() # Reload and re-highlight
            else:
                QMessageBox.critical(self, "Erreur", "Échec de la suppression de l'événement.")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    # Setup basic logging for the example
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    app = QApplication(sys.argv)

    # --- Mocking CRUD operations for standalone execution ---
    # This is important for the __main__ block to run without a full DB setup.
    # In a real app, these mocks wouldn't be here.

    mock_settings_db = {}
    mock_events_db = {}
    mock_event_id_counter = 1

    def mock_get_settings(user_id):
        logging.info(f"[MOCK] get_settings_by_user_id for {user_id}")
        data = mock_settings_db.get(user_id)
        return CompanyCalendarSettings(**data) if data else None

    def mock_save_settings(settings: CompanyCalendarSettings):
        global mock_settings_db
        logging.info(f"[MOCK] save_settings: {settings.dict()}")
        mock_settings_db[settings.user_id] = settings.dict()
        # Simulate ID assignment if it were a real DB insert for a new record
        if 'id' not in mock_settings_db[settings.user_id] or mock_settings_db[settings.user_id]['id'] is None:
             mock_settings_db[settings.user_id]['id'] = hash(settings.user_id) # Simple mock ID
        return CompanyCalendarSettings(**mock_settings_db[settings.user_id])

    def mock_add_event(event: UserCalendarEvent):
        global mock_events_db, mock_event_id_counter
        logging.info(f"[MOCK] add_event: {event.dict()}")
        event_id = mock_event_id_counter
        mock_event_id_counter += 1

        # Store with date as string key for easier range queries in mock
        event_dict = event.dict()
        event_dict['id'] = event_id

        if event.user_id not in mock_events_db:
            mock_events_db[event.user_id] = {}
        date_key = event.event_date.isoformat()
        if date_key not in mock_events_db[event.user_id]:
            mock_events_db[event.user_id][date_key] = []

        mock_events_db[event.user_id][date_key].append(event_dict)
        return UserCalendarEvent(**event_dict)

    def mock_get_events(user_id, start_date=None, end_date=None):
        logging.info(f"[MOCK] get_events_by_user_id for {user_id}, range: {start_date} - {end_date}")
        user_specific_events = mock_events_db.get(user_id, {})
        results = []
        for date_str, events_on_date in user_specific_events.items():
            event_py_date = QDate.fromString(date_str, "yyyy-MM-dd").toPyDate()
            if (start_date is None or event_py_date >= start_date) and \
               (end_date is None or event_py_date <= end_date):
                for ev_dict in events_on_date:
                    results.append(UserCalendarEvent(**ev_dict))
        return sorted(results, key=lambda e: e.event_date)

    def mock_delete_event(event_id):
        global mock_events_db
        logging.info(f"[MOCK] delete_event with id: {event_id}")
        for user_id, date_events in mock_events_db.items():
            for date_str, events_on_date in list(date_events.items()): # Iterate over copy for modification
                new_events_on_date = [ev for ev in events_on_date if ev['id'] != event_id]
                if len(new_events_on_date) != len(events_on_date):
                    if not new_events_on_date:
                        del mock_events_db[user_id][date_str]
                    else:
                        mock_events_db[user_id][date_str] = new_events_on_date
                    return True # Found and deleted
        return False # Not found


    # Apply mocks
    company_calendar_settings_crud.get_settings_by_user_id = mock_get_settings
    company_calendar_settings_crud.save_settings = mock_save_settings
    user_calendar_events_crud.add_event = mock_add_event
    user_calendar_events_crud.get_events_by_user_id = mock_get_events
    user_calendar_events_crud.delete_event = mock_delete_event

    # Pre-populate some mock data for testing
    mock_save_settings(CompanyCalendarSettings(user_id=TEMP_USER_ID, business_type="B2B", activity_category="Tech", country_iso="FR", region="IDF"))
    mock_add_event(UserCalendarEvent(user_id=TEMP_USER_ID, event_date=QDate.currentDate().addDays(2).toPyDate(), event_type="Télétravail", description="Remote work day"))
    mock_add_event(UserCalendarEvent(user_id=TEMP_USER_ID, event_date=QDate.currentDate().addDays(3).toPyDate(), event_type="Autre Personnel", description="Dentist appointment"))

    widget = CalendarWidget(current_user_id=TEMP_USER_ID) # Pass the user_id
    widget.show()
    sys.exit(app.exec_())
