from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
                             QPushButton, QFormLayout, QGroupBox, QCalendarWidget,
                             QMessageBox, QTextEdit, QHBoxLayout, QListWidget, QListWidgetItem)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
                             QPushButton, QFormLayout, QGroupBox, QCalendarWidget,
                             QMessageBox, QTextEdit, QHBoxLayout, QListWidget, QListWidgetItem,
                             QDateEdit) # Added QDateEdit
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
import holidays
import pycountry # For listing countries
from .cruds import company_calendar_settings_crud, user_calendar_events_crud, custom_holidays_crud # Added custom_holidays_crud
from .models import CompanyCalendarSettings, UserCalendarEvent, CustomHoliday # Added CustomHoliday model
from typing import Optional, List
import logging

# Assume current_user_id is passed or accessible globally for now
# For a real application, this should be managed properly (e.g., via constructor, signals)
TEMP_USER_ID = "temp_user_01" # Placeholder for user ID

class CalendarWidget(QWidget):
    def __init__(self, parent=None, current_user_id=None):
        super().__init__(parent)
        self.current_user_id = current_user_id if current_user_id else TEMP_USER_ID
        self.company_settings: Optional[CompanyCalendarSettings] = None
        self.user_events: List[UserCalendarEvent] = []
        self.custom_holidays: List[CustomHoliday] = [] # Initialize custom holidays list

        self._init_ui()
        self._load_company_settings() # This will trigger highlight via its own _load_all_calendar_data call
        self._load_all_calendar_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Company Settings Group ---
        settings_group = QGroupBox(self.tr("Paramètres de l'Entreprise pour le Calendrier"))
        settings_layout = QFormLayout()

        self.business_type_combo = QComboBox()
        self.business_type_combo.addItems([self.tr("B2B"), self.tr("B2C"), self.tr("Les Deux")])
        settings_layout.addRow(self.tr("Type d'entreprise:"), self.business_type_combo)

        self.activity_category_edit = QLineEdit()
        settings_layout.addRow(self.tr("Catégorie d'activité:"), self.activity_category_edit)

        self.country_iso_combo = QComboBox()
        self._populate_country_combo() # Populates with self.tr() for placeholder
        self.country_iso_combo.currentIndexChanged.connect(self._update_region_combo)
        settings_layout.addRow(self.tr("Pays:"), self.country_iso_combo)

        self.region_combo = QComboBox()
        settings_layout.addRow(self.tr("Région/État (si applicable):"), self.region_combo)

        self.save_settings_button = QPushButton(self.tr("Sauvegarder Paramètres"))
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
        self.calendar_widget.currentPageChanged.connect(self._on_month_changed)
        calendar_events_layout.addWidget(self.calendar_widget, 2)

        # Event Details and Management
        event_management_group = QGroupBox(self.tr("Gestion des Événements"))
        event_management_layout = QVBoxLayout()

        # Initial text for selected_date_label will be set in _on_date_selected or similar
        self.selected_date_label = QLabel()
        self._on_date_selected(self.calendar_widget.selectedDate()) # Initialize label text
        event_management_layout.addWidget(self.selected_date_label)

        self.events_list_widget = QListWidget()
        event_management_layout.addWidget(self.events_list_widget)

        self.event_description_edit = QLineEdit()
        self.event_description_edit.setPlaceholderText(self.tr("Description de l'événement"))
        event_management_layout.addWidget(self.event_description_edit)

        self.event_type_combo = QComboBox()
        self.event_type_combo.addItems([
            self.tr("Télétravail"),
            self.tr("Jour de Travail"),
            self.tr("Autre Personnel")
        ])
        event_management_layout.addWidget(self.event_type_combo)

        # --- Recurrence Controls ---
        recurrence_group = QGroupBox(self.tr("Récurrence"))
        recurrence_layout = QFormLayout()

        self.recurrence_type_combo = QComboBox()
        self.recurrence_type_combo.addItems([
            self.tr("Aucune"),
            self.tr("Quotidien"),
            self.tr("Hebdomadaire"),
            self.tr("Mensuel")
        ])
        self.recurrence_type_combo.currentIndexChanged.connect(self._on_recurrence_type_changed)
        recurrence_layout.addRow(self.tr("Type:"), self.recurrence_type_combo)

        self.recurrence_end_date_edit = QDateEdit()
        self.recurrence_end_date_edit.setCalendarPopup(True)
        self.recurrence_end_date_edit.setDate(QDate.currentDate().addYears(1)) # Default to one year from now
        self.recurrence_end_date_edit.setVisible(False) # Initially hidden
        self.recurrence_end_date_label = QLabel(self.tr("Date de fin de récurrence:"))
        self.recurrence_end_date_label.setVisible(False) # Initially hidden
        recurrence_layout.addRow(self.recurrence_end_date_label, self.recurrence_end_date_edit)

        recurrence_group.setLayout(recurrence_layout)
        event_management_layout.addWidget(recurrence_group)
        # --- End Recurrence Controls ---

        self.add_event_button = QPushButton(self.tr("Ajouter Événement"))
        self.add_event_button.clicked.connect(self._add_or_update_event)
        event_management_layout.addWidget(self.add_event_button)

        self.delete_event_button = QPushButton(self.tr("Supprimer Événement Sélectionné"))
        self.delete_event_button.clicked.connect(self._delete_event) # Will need to differentiate event types
        event_management_layout.addWidget(self.delete_event_button)

        # --- Custom Holiday Controls ---
        custom_holiday_group = QGroupBox(self.tr("Jours Fériés Personnalisés"))
        custom_holiday_layout = QFormLayout()

        self.custom_holiday_date_edit = QDateEdit()
        self.custom_holiday_date_edit.setCalendarPopup(True)
        self.custom_holiday_date_edit.setDate(QDate.currentDate())
        custom_holiday_layout.addRow(self.tr("Date:"), self.custom_holiday_date_edit)

        self.custom_holiday_desc_edit = QLineEdit()
        self.custom_holiday_desc_edit.setPlaceholderText(self.tr("Description du jour férié"))
        custom_holiday_layout.addRow(self.tr("Description:"), self.custom_holiday_desc_edit)

        self.add_custom_holiday_button = QPushButton(self.tr("Ajouter Jour Férié Personnalisé"))
        self.add_custom_holiday_button.clicked.connect(self._add_custom_holiday)
        custom_holiday_layout.addRow(self.add_custom_holiday_button)

        custom_holiday_group.setLayout(custom_holiday_layout)
        event_management_layout.addWidget(custom_holiday_group)
        # --- End Custom Holiday Controls ---

        event_management_group.setLayout(event_management_layout)
        calendar_events_layout.addWidget(event_management_group, 1)

        main_layout.addLayout(calendar_events_layout)
        self.setLayout(main_layout)
        self.setWindowTitle(self.tr("Module Calendrier"))

    def _populate_country_combo(self):
        self.country_iso_combo.addItem(self.tr("Sélectionner un pays..."), None)
        try:
            # Sort countries by name for user-friendliness
            sorted_countries = sorted(list(pycountry.countries), key=lambda x: x.name)
            for country in sorted_countries:
                self.country_iso_combo.addItem(country.name, country.alpha_2)
        except Exception as e:
            logging.error(f"Impossible de peupler la liste des pays: {e}")
            # Fallback to a minimal list or handle error appropriately
            self.country_iso_combo.addItem(self.tr("Erreur chargement pays"), None)

    def _update_region_combo(self):
        self.region_combo.clear()
        self.region_combo.addItem(self.tr("Toutes / Aucune"), None) # Default option

        selected_country_iso = self.country_iso_combo.currentData()
        if selected_country_iso:
            try:
                country_holidays = holidays.CountryHoliday(selected_country_iso)
                # subdivisions is a list of subdivision codes (e.g., ['CA', 'NY'] for US)
                # For some countries, it might be empty or None if not applicable/supported well by `holidays` lib for that country.
                if hasattr(country_holidays, 'subdivisions') and country_holidays.subdivisions:
                    # `holidays` library gives codes. For display names, it's more complex.
                    # Often, the codes themselves are what users might know (e.g., US states).
                    # We might need a mapping for display names if codes are not user-friendly.
                    # For now, using the codes directly.
                    for region_code in sorted(list(set(country_holidays.subdivisions))): # Use set to ensure uniqueness
                        # Attempt to get a display name for the subdivision if possible
                        # This is a heuristic and might not work for all countries/subdivisions
                        # For example, holidays.CountryHoliday('US', prov='CA')['2023-01-01'] might give a name with state
                        # but there isn't a direct get_subdivision_name(code) function.
                        # We will use the code as both display and data for now.
                        self.region_combo.addItem(region_code, region_code)
                else:
                    logging.info(f"Aucune subdivision trouvée ou applicable pour le pays {selected_country_iso} via la bibliothèque holidays.")
            except Exception as e:
                logging.error(f"Erreur lors de la récupération des subdivisions pour {selected_country_iso}: {e}")

        # If company_settings exist and its region matches one of the new items, select it.
        # This part is tricky because _update_region_combo is called on country change,
        # but also needs to work during initial load.
        if hasattr(self, '_initial_region_to_set') and self._initial_region_to_set:
            index = self.region_combo.findData(self._initial_region_to_set)
            if index >= 0:
                self.region_combo.setCurrentIndex(index)
            self._initial_region_to_set = None # Clear after attempting to set


    def _load_company_settings(self):
        logging.info(f"Chargement des paramètres pour l'utilisateur: {self.current_user_id}")
        settings = company_calendar_settings_crud.get_settings_by_user_id(self.current_user_id)

        # Disconnect signal to prevent _update_region_combo during programmatic country_iso_combo set
        try:
            self.country_iso_combo.currentIndexChanged.disconnect(self._update_region_combo)
        except TypeError: # Was not connected or already disconnected
            pass

        if settings:
            self.company_settings = settings
            self.business_type_combo.setCurrentText(settings.business_type or "")
            self.activity_category_edit.setText(settings.activity_category or "")

            if settings.country_iso:
                index = self.country_iso_combo.findData(settings.country_iso)
                if index >= 0:
                    self.country_iso_combo.setCurrentIndex(index)
                else:
                    logging.warning(f"Code pays stocké '{settings.country_iso}' non trouvé dans la ComboBox.")
                    self.country_iso_combo.setCurrentIndex(0)
            else:
                self.country_iso_combo.setCurrentIndex(0)

            # Store the region to be set after _update_region_combo populates the list
            self._initial_region_to_set = settings.region
            self._update_region_combo() # Populate regions based on loaded country

            logging.info(f"Paramètres chargés: {settings}")
            self._highlight_calendar_dates()
        else:
            logging.info("Aucun paramètre trouvé pour cet utilisateur.")
            self.company_settings = None
            self.business_type_combo.setCurrentIndex(0)
            self.activity_category_edit.clear()
            self.country_iso_combo.setCurrentIndex(0)
            self._initial_region_to_set = None # Ensure it's cleared
            self._update_region_combo() # Populate (likely empty) regions for placeholder country
            # self.region_combo.clear() already handled by _update_region_combo
            # self.region_combo.addItem(self.tr("Toutes / Aucune"), None)

        # Reconnect signal
        self.country_iso_combo.currentIndexChanged.connect(self._update_region_combo)


    def _save_company_settings(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Erreur Utilisateur"), self.tr("ID utilisateur non défini. Impossible de sauvegarder."))
            return

        selected_country_iso = self.country_iso_combo.currentData()
        if not selected_country_iso:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Veuillez sélectionner un pays."))
            return

        selected_region = self.region_combo.currentData()

        settings_data = CompanyCalendarSettings(
            user_id=self.current_user_id,
            business_type=self.business_type_combo.currentText(),
            activity_category=self.activity_category_edit.text().strip(),
            country_iso=selected_country_iso,
            region=selected_region
        )

        logging.info(f"Sauvegarde des paramètres: {settings_data.dict()}")
        saved = company_calendar_settings_crud.save_settings(settings_data)
        if saved:
            self.company_settings = saved # Update local cache
            QMessageBox.information(self, "Succès", "Paramètres sauvegardés avec succès.")
            self._highlight_calendar_dates() # Re-highlight after saving settings
        else:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Échec de la sauvegarde des paramètres."))

    def _load_all_calendar_data(self):
        """Loads user events and custom holidays for the currently visible month."""
        if not self.current_user_id:
            self.user_events = []
            self.custom_holidays = []
            self._highlight_calendar_dates()
            self._update_events_list_for_selected_date()
            return

        current_qdate = self.calendar_widget.selectedDate()
        year = current_qdate.year()
        month = current_qdate.month()

        start_date_month = QDate(year, month, 1).toPyDate()
        end_date_month = QDate(year, month, current_qdate.daysInMonth()).toPyDate()

        logging.info(f"Chargement des données de calendrier pour l'utilisateur {self.current_user_id} pour {year}-{month}")

        self.user_events = user_calendar_events_crud.get_events_by_user_id(
            user_id=self.current_user_id,
            start_date=start_date_month,
            end_date=end_date_month
        )
        logging.info(f"{len(self.user_events)} événements utilisateur chargés.")

        self.custom_holidays = custom_holidays_crud.get_custom_holidays_by_user_id(
            user_id=self.current_user_id,
            start_date=start_date_month,
            end_date=end_date_month
        )
        logging.info(f"{len(self.custom_holidays)} jours fériés personnalisés chargés.")

        self._highlight_calendar_dates()
        self._update_events_list_for_selected_date()


    def _highlight_calendar_dates(self):
        """Highlights legal holidays, custom holidays, and user-defined events on the calendar."""
        self.calendar_widget.setDateTextFormat(QDate(), QTextCharFormat())

        # 1. Legal Holidays (Green)
        if self.company_settings and self.company_settings.country_iso:
            try:
                legal_holidays_lib = holidays.CountryHoliday(
                    self.company_settings.country_iso,
                    prov=self.company_settings.region if self.company_settings.region else None,
                    years=self.calendar_widget.yearShown()
                )
                for date_obj, name in sorted(legal_holidays_lib.items()):
                    q_date = QDate(date_obj.year, date_obj.month, date_obj.day)
                    fmt = self.calendar_widget.dateTextFormat(q_date)
                    fmt.setBackground(QBrush(QColor("lightgreen")))
                    fmt.setToolTip(self.tr("Jour Férié Légal: {0}").format(name))
                    self.calendar_widget.setDateTextFormat(q_date, fmt)
            except Exception as e:
                logging.error(f"Erreur lors de la récupération des jours fériés légaux: {e}")

        # 2. Custom Holidays (Orange)
        custom_holiday_fmt = QTextCharFormat()
        custom_holiday_fmt.setBackground(QBrush(QColor("orange")))
        for ch in self.custom_holidays:
            q_date = QDate(ch.holiday_date.year, ch.holiday_date.month, ch.holiday_date.day)
            fmt = self.calendar_widget.dateTextFormat(q_date) # Get potentially existing format (e.g. legal holiday)
            # Custom holidays override legal ones if on the same day for visual cue
            fmt.setBackground(custom_holiday_fmt.background())
            new_tooltip = self.tr("Jour Férié Personnalisé: {0}").format(ch.description)
            existing_tooltip = fmt.toolTip()
            if existing_tooltip and self.tr("Jour Férié Légal") in existing_tooltip : # Keep legal holiday info if present
                fmt.setToolTip(f"{existing_tooltip}\n{new_tooltip}")
            else:
                fmt.setToolTip(new_tooltip)
            self.calendar_widget.setDateTextFormat(q_date, fmt)

        # 3. User Events (Various colors)
        event_formats = {
            self.tr("Télétravail"): QBrush(QColor("lightblue")),
            self.tr("Jour de Travail"): QBrush(QColor("lightyellow")),
            self.tr("Autre Personnel"): QBrush(QColor("lightcoral")),
        }
        default_event_brush = QBrush(QColor("lightgray"))

        for event in self.user_events: # These are already expanded occurrences
            q_date = QDate(event.event_date.year, event.event_date.month, event.event_date.day)

            current_fmt = self.calendar_widget.dateTextFormat(q_date)
            event_brush = event_formats.get(event.event_type, default_event_brush)

            # User events should not visually override holidays, but can add to tooltip
            # If not already a holiday, set its specific background
            if current_fmt.background() == QBrush(Qt.transparent) or current_fmt.background() == QBrush(QColor(Qt.white)): # Check if no specific holiday bg
                 current_fmt.setBackground(event_brush)

            tooltip_parts = [current_fmt.toolTip()] if current_fmt.toolTip() else []
            tooltip_parts.append(f"{event.event_type}: {event.description or self.tr('N/A')}")
            current_fmt.setToolTip("\n".join(filter(None, tooltip_parts)))

            self.calendar_widget.setDateTextFormat(q_date, current_fmt)

        self.calendar_widget.updateCells()

    def _on_date_selected(self, date: QDate):
        self.selected_date_label.setText(self.tr("Date sélectionnée: {0}").format(date.toString('yyyy-MM-dd')))
        self._update_events_list_for_selected_date()

    def _on_month_changed(self, year, month):
        logging.info(f"Mois changé vers: {year}-{month}. Rechargement des données.")
        self._load_all_calendar_data()

    def _update_events_list_for_selected_date(self):
        self.events_list_widget.clear()
        selected_py_date = self.calendar_widget.selectedDate().toPyDate()

        # Display Legal Holidays
        if self.company_settings and self.company_settings.country_iso:
            try:
                legal_holidays_lib = holidays.CountryHoliday(
                    self.company_settings.country_iso,
                    prov=self.company_settings.region if self.company_settings.region else None,
                    years=selected_py_date.year
                )
                if selected_py_date in legal_holidays_lib:
                    item = QListWidgetItem(self.tr("Jour Férié Légal: {0}").format(legal_holidays_lib[selected_py_date]))
                    item.setForeground(QColor("darkgreen"))
                    item.setData(Qt.UserRole, {"type": "legal_holiday"}) # Mark item type
                    self.events_list_widget.addItem(item)
            except Exception as e:
                logging.warning(f"Impossible de vérifier les jours fériés légaux pour la liste: {e}")

        # Display Custom Holidays
        for ch in self.custom_holidays:
            if ch.holiday_date == selected_py_date:
                item = QListWidgetItem(self.tr("Jour Férié Personnalisé: {0}").format(ch.description))
                item.setForeground(QColor("darkorange"))
                item.setData(Qt.UserRole, ch) # Store CustomHoliday object
                self.events_list_widget.addItem(item)

        # Display User Events (already expanded)
        for event in self.user_events:
            if event.event_date == selected_py_date:
                item_text = f"{event.event_type}: {event.description or self.tr('N/A')}"
                # Add recurrence info if applicable, for clarity (even for single occurrences of a series)
                if event.recurrence_rule:
                    item_text += self.tr(" (Récurrent)")
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, event)
                self.events_list_widget.addItem(list_item)

        self.event_description_edit.clear()
        self.event_type_combo.setCurrentIndex(0)
        self.recurrence_type_combo.setCurrentIndex(0) # Reset recurrence type
        # self.recurrence_end_date_edit visibility is handled by _on_recurrence_type_changed
        self._on_recurrence_type_changed(0) # Ensure end date field is hidden if "Aucune" is selected

    def _on_recurrence_type_changed(self, index):
        # Show/hide recurrence_end_date_edit based on selection
        # Index 0 is "Aucune"
        is_recurring = index > 0
        self.recurrence_end_date_label.setVisible(is_recurring)
        self.recurrence_end_date_edit.setVisible(is_recurring)

    def _add_or_update_event(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Erreur Utilisateur"), self.tr("ID utilisateur non défini."))
            return

        selected_qdate = self.calendar_widget.selectedDate()
        event_date_py = selected_qdate.toPyDate() # This is the DTSTART for rrule
        description = self.event_description_edit.text().strip()
        event_type = self.event_type_combo.currentText()

        if not description:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("La description de l'événement est requise."))
            return

        recurrence_type_text = self.recurrence_type_combo.currentText()
        recurrence_rule_str: Optional[str] = None
        recurrence_end_date_py: Optional[date] = None

        if recurrence_type_text != self.tr("Aucune"):
            recurrence_end_date_py = self.recurrence_end_date_edit.date().toPyDate()
            # Ensure recurrence end date is not before event start date
            if recurrence_end_date_py < event_date_py:
                QMessageBox.warning(self, self.tr("Date Invalide"), self.tr("La date de fin de récurrence ne peut pas être antérieure à la date de début de l'événement."))
                return

            # Construct RRULE string
            # For BYDAY with weekly, QCalendarWidget.selectedDate().dayOfWeek() can be used (Monday=1, Sunday=7)
            # RRULE BYDAY values: MO, TU, WE, TH, FR, SA, SU
            qt_day_to_rrule_day = {1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR", 6: "SA", 7: "SU"}

            if recurrence_type_text == self.tr("Quotidien"):
                recurrence_rule_str = "FREQ=DAILY;INTERVAL=1"
            elif recurrence_type_text == self.tr("Hebdomadaire"):
                day_of_week_rrule = qt_day_to_rrule_day[selected_qdate.dayOfWeek()]
                recurrence_rule_str = f"FREQ=WEEKLY;BYDAY={day_of_week_rrule};INTERVAL=1"
            elif recurrence_type_text == self.tr("Mensuel"):
                # Simple monthly recurrence: on the same day of the month
                recurrence_rule_str = f"FREQ=MONTHLY;BYMONTHDAY={selected_qdate.day()};INTERVAL=1"

            if recurrence_rule_str and recurrence_end_date_py:
                # Add UNTIL to the rrule string, formatted as YYYYMMDDTHHMMSSZ for full compatibility,
                # or YYYYMMDD for date-only UNTIL. dateutil.rrule should handle YYYYMMDD.
                # The 'Z' is for UTC, usually important if dealing with times. For dates, less so but good practice.
                # For simplicity here, just YYYYMMDD.
                # Note: recurrence_end_date_py is inclusive, rrule UNTIL is also inclusive.
                # However, to be safe and common, UNTIL is often specified for the end of the day.
                # For date-only events, dateutil handles it well.
                pass # recurrence_end_date_py is handled by a separate DB column now.
                     # RRULE UNTIL could also be used but might be redundant if DB field exists.
                     # Let's keep DB recurrence_end_date as the primary source of truth for the end.

        event_data = UserCalendarEvent(
            user_id=self.current_user_id,
            event_date=event_date_py,
            event_type=event_type,
            description=description,
            recurrence_rule=recurrence_rule_str,
            recurrence_end_date=recurrence_end_date_py
        )

        new_event = user_calendar_events_crud.add_event(event_data)

        if new_event:
            QMessageBox.information(self, self.tr("Succès"), self.tr("Événement ajouté avec succès."))
            self._load_user_events()
            self.event_description_edit.clear()
            self.recurrence_type_combo.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Échec de l'ajout de l'événement."))

    def _add_custom_holiday(self):
        if not self.current_user_id:
            QMessageBox.warning(self, self.tr("Erreur Utilisateur"), self.tr("ID utilisateur non défini."))
            return

        holiday_qdate = self.custom_holiday_date_edit.date()
        description = self.custom_holiday_desc_edit.text().strip()

        if not description:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("La description du jour férié personnalisé est requise."))
            return

        holiday_data = CustomHoliday(
            user_id=self.current_user_id,
            holiday_date=holiday_qdate.toPyDate(),
            description=description
        )

        new_holiday = custom_holidays_crud.add_custom_holiday(holiday_data)
        if new_holiday:
            QMessageBox.information(self, self.tr("Succès"), self.tr("Jour férié personnalisé ajouté avec succès."))
            self._load_all_calendar_data() # Reload all data
            self.custom_holiday_desc_edit.clear()
        elif new_holiday is None and custom_holidays_crud.get_custom_holidays_by_user_id(self.current_user_id, holiday_qdate.toPyDate(), holiday_qdate.toPyDate()):
             QMessageBox.warning(self, self.tr("Doublon"), self.tr("Un jour férié personnalisé existe déjà pour cette date."))
        else:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Échec de l'ajout du jour férié personnalisé."))


    def _delete_event(self):
        selected_item = self.events_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un élément à supprimer."))
            return

        item_data = selected_item.data(Qt.UserRole)

        if isinstance(item_data, UserCalendarEvent):
            if item_data.id is None: # Should not happen for stored events
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID d'événement manquant."))
                return

            reply = QMessageBox.confirm(
                self, self.tr("Confirmer Suppression Événement"),
                self.tr("Êtes-vous sûr de vouloir supprimer l'événement utilisateur: \"{0}\"?\nNote: Si c'est un événement récurrent, ceci supprimera la règle de base et toutes ses occurrences.").format(item_data.description),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if user_calendar_events_crud.delete_event(item_data.id):
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Événement utilisateur supprimé."))
                    self._load_all_calendar_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), self.tr("Échec de la suppression de l'événement utilisateur."))

        elif isinstance(item_data, CustomHoliday):
            if item_data.id is None: # Should not happen
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID de jour férié personnalisé manquant."))
                return

            reply = QMessageBox.confirm(
                self, self.tr("Confirmer Suppression Jour Férié"),
                self.tr("Êtes-vous sûr de vouloir supprimer le jour férié personnalisé: \"{0}\"?").format(item_data.description),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if custom_holidays_crud.delete_custom_holiday(item_data.id):
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Jour férié personnalisé supprimé."))
                    self._load_all_calendar_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), self.tr("Échec de la suppression du jour férié personnalisé."))

        elif isinstance(item_data, dict) and item_data.get("type") == "legal_holiday":
            QMessageBox.information(self, self.tr("Information"), self.tr("Les jours fériés légaux ne peuvent pas être supprimés depuis cette interface."))

        else:
            QMessageBox.warning(self, self.tr("Type Inconnu"), self.tr("L'élément sélectionné n'est ni un événement utilisateur ni un jour férié personnalisé modifiable."))


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
