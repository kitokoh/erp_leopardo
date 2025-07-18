# -*- coding: utf-8 -*-
import os
import logging
import traceback
import sip # For checking if C++ object is deleted
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSplitter, QHBoxLayout,
    QGroupBox, QFormLayout, QTableWidget, QHeaderView, QTabWidget, QProgressBar,
    QTableWidgetItem, QStackedWidget, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QTimer, QRunnable, QThreadPool, QDate
from PyQt5.QtWidgets import QDateEdit

from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Matplotlib imports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import folium
from branca.colormap import StepColormap
import csv

from .map_utils import generate_folium_map_html

from db import (
    get_total_clients_count,
    get_active_clients_count,
    get_country_by_name,
    get_total_projects_count,
    get_active_projects_count,
    get_total_products_count,
    get_client_segmentation_by_city,
    get_client_segmentation_by_status,
    get_client_segmentation_by_category,
    get_client_counts_by_country,
    get_country_by_id,
    get_city_by_id,
    get_status_setting_by_id,
    get_status_setting_by_name # Added for chart click
)
from db.cruds.clients_crud import clients_crud_instance
from db.connection import get_db_connection
from db.cruds.client_project_products_crud import get_product_usage_counts
from db.cruds.proforma_invoices_crud import get_total_sales_amount_for_period, get_total_proforma_sales_for_country_id
from db.cruds.projects_crud import get_active_project_count_by_country_id

from client_management.add_new_client_dialog import AddNewClientDialog
from client_management.client_controller import ClientController


from app_setup import APP_ROOT_DIR


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class GlobalStatsWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(GlobalStatsWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit((e, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class MapInteractionHandler(QObject):
    country_clicked_signal = pyqtSignal(str)
    client_clicked_on_map_signal = pyqtSignal(str, str)
    request_map_refresh_signal = pyqtSignal()
    map_view_changed_signal = pyqtSignal(float, float, int)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(str)
    def countryClicked(self, country_name):
        logging.info(f"MapInteractionHandler: countryClicked received: {country_name}")
        self.country_clicked_signal.emit(country_name)

    @pyqtSlot(str, str)
    def clientClickedOnMap(self, client_id, client_name):
        logging.info(f"MapInteractionHandler: clientClickedOnMap received ID: {client_id}, Name: {client_name}")
        self.client_clicked_on_map_signal.emit(client_id, client_name)

    @pyqtSlot()
    def requestMapRefresh(self):
        """Slot callable from JavaScript to request a map refresh."""
        logging.info("MapInteractionHandler: requestMapRefresh called from JS.")
        self.request_map_refresh_signal.emit()

    @pyqtSlot(float, float, int)
    def onMapViewChanged(self, lat, lng, zoom):
        self.map_view_changed_signal.emit(lat, lng, zoom)


class StatisticsDashboard(QWidget):
    request_add_client_for_country = pyqtSignal(str)
    request_view_client_details = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatisticsDashboard")
        self.setWindowTitle(self.tr("Tableau de Bord Statistiques Interactif"))
        try:
            self.threadpool = QThreadPool()
            logging.info(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10,10,10,10)
            main_layout.setSpacing(10)

            top_bar_layout = QHBoxLayout()
            self.dashboard_tabs = QTabWidget()
            self.dashboard_tabs.addTab(QWidget(), self.tr("Dashboard Principal"))
            self.dashboard_tabs.addTab(QWidget(), self.tr("Analyses Approfondies"))
            top_bar_layout.addWidget(self.dashboard_tabs)

            self.global_refresh_button = QPushButton()
            self.global_refresh_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
            self.global_refresh_button.setToolTip(self.tr("Rafraîchir les données"))
            self.global_refresh_button.setObjectName("refreshButton")
            self.global_refresh_button.clicked.connect(self.refresh_all_dashboard_content)
            top_bar_layout.addWidget(self.global_refresh_button)

            main_layout.addLayout(top_bar_layout)

            self.main_splitter = QSplitter(Qt.Horizontal, self)
            self.left_widget_for_map = QWidget()
            self.left_widget_for_map.setObjectName("mapContainerWidget")
            self._left_map_actual_layout = QVBoxLayout()
            self._left_map_actual_layout.setContentsMargins(0,0,0,0)
            self.left_widget_for_map.setLayout(self._left_map_actual_layout)

            self.map_view = None
            self.main_splitter.addWidget(self.left_widget_for_map)

            self.right_widget_for_stats = QWidget()
            self.right_widget_for_stats.setObjectName("statsContainerWidget")
            right_stats_layout = QVBoxLayout(self.right_widget_for_stats)
            right_stats_layout.setContentsMargins(10,10,10,10)
            self.right_widget_for_stats.setLayout(right_stats_layout)
            self.main_splitter.addWidget(self.right_widget_for_stats)

            QTimer.singleShot(0, lambda: self.main_splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)]))

            self.dashboard_tabs.widget(0).setLayout(main_layout)
            main_layout.addWidget(self.main_splitter)
            self.setLayout(main_layout)

            self.map_interaction_handler = None
            self._setup_stats_display_ui(right_stats_layout)
            self.populate_views_combo()

            QTimer.singleShot(100, self._initialize_map_and_load_data)
            logging.info("StatisticsDashboard initialized. Map components and initial data load deferred.")
        except Exception as e:
            logging.error(f"Failed to initialize StatisticsDashboard: {e}", exc_info=True)
            error_layout = QVBoxLayout(self)
            error_label = QLabel(self.tr("Could not initialize the statistics dashboard.\nPlease check the logs for more information."))
                error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            self.setLayout(error_layout)

    def _initialize_map_and_load_data(self):
        logging.info("StatisticsDashboard: _initialize_map_and_load_data called.")
        if self.map_view is None:
            self.map_view = QWebEngineView()
            self.map_view.setObjectName("mapViewWidget")
            self._left_map_actual_layout.addWidget(self.map_view)
            logging.info("QWebEngineView (self.map_view) created and added to layout.")

            self.map_interaction_handler = MapInteractionHandler(self)
            self.map_interaction_handler.country_clicked_signal.connect(self._on_map_country_clicked)
            self.map_interaction_handler.client_clicked_on_map_signal.connect(self._display_client_details_in_panel)
                self.map_interaction_handler.request_map_refresh_signal.connect(self.update_map)
            self.map_interaction_handler.map_view_changed_signal.connect(self._on_map_view_changed)

            self.web_channel = QWebChannel(self.map_view.page())
            self.map_view.page().setWebChannel(self.web_channel)
            self.web_channel.registerObject("pyMapConnector", self.map_interaction_handler)
            logging.info("MapInteractionHandler and QWebChannel set up.")

            # Load the local HTML file
            map_file_path = os.path.join(APP_ROOT_DIR, "map.html")
            if os.path.exists(map_file_path):
                with open(map_file_path, 'r') as f:
                    html_content = f.read()
                self.map_view.setHtml(html_content)
            else:
                logging.error(f"map.html not found at {map_file_path}")
                self.map_view.setHtml("<h1>Error: map.html not found</h1>")

        self.refresh_all_dashboard_content()
        logging.info("Initial map and data load sequence completed.")


    @pyqtSlot(str)
    def _on_map_country_clicked(self, country_name):
        logging.info(f"Map country clicked: {country_name}. Switching to country stats view.")
        self._show_country_stats_view(country_name)

    @pyqtSlot(str, str)
    def _on_map_client_clicked(self, client_id, client_name):
        logging.info(f"Map client clicked: {client_name} (ID: {client_id}). Displaying details in panel.")
        self._display_client_details_in_panel(client_id, client_name)

    def _on_map_view_changed(self, lat, lng, zoom):
        db_session = get_db_connection()
        try:
            from db.cruds.application_settings_crud import set_setting
            set_setting('map_last_lat', str(lat), db_session)
            set_setting('map_last_lng', str(lng), db_session)
            set_setting('map_last_zoom', str(zoom), db_session)
        finally:
            db_session.close()

    def refresh_all_dashboard_content(self):
        logging.info("Refreshing all dashboard content...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.refresh_statistics_data()
            if self.map_view and self.map_interaction_handler:
                self.update_map()
            else:
                logging.warning("Map view or interaction handler not yet initialized, skipping map update.")
        finally:
            QApplication.restoreOverrideCursor()
        logging.info("All dashboard content refresh completed.")

    def _setup_stats_display_ui(self, layout_to_populate):
        self.stats_stack = QStackedWidget()
        self.stats_stack.setObjectName("statsStack")
        layout_to_populate.addWidget(self.stats_stack)

        # --- Global Stats Widget ---
        self.global_stats_widget = QWidget()
        self.global_stats_widget.setObjectName("globalStatsWidget")
        global_stats_page_layout = QVBoxLayout(self.global_stats_widget)

        title_label = QLabel(self.tr("Statistiques Détaillées"))
        title_label.setObjectName("statisticsDashboardTitle")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        global_stats_page_layout.addWidget(title_label)

        global_stats_group = QGroupBox(self.tr("Statistiques Globales"))
        global_stats_group.setObjectName("globalStatsGroup")
        global_stats_layout = QFormLayout(global_stats_group)
        global_stats_layout.setLabelAlignment(Qt.AlignRight)
        global_stats_layout.setSpacing(10)
        self.stats_labels = {
            "total_clients": QLabel("0"), "active_clients": QLabel("0"),
            "total_projects": QLabel("0"), "active_projects": QLabel("0"),
            "total_products": QLabel("0"),
            "total_sales_proforma": QLabel("0"),
            "new_clients_last_month": QLabel("0"),
            "new_clients_last_quarter": QLabel("0"),
            "total_clients_trend": QLabel(""),
            "active_clients_trend": QLabel(""), # Added for active clients trend label
            "total_sales_proforma_trend": QLabel("") # Added for sales trend label
        }

        total_clients_layout = QHBoxLayout()
        total_clients_layout.addWidget(self.stats_labels["total_clients"])
        total_clients_layout.addSpacing(10)
        self.stats_labels["total_clients_trend"].setObjectName("trendLabel")
        total_clients_layout.addWidget(self.stats_labels["total_clients_trend"])
        total_clients_layout.addStretch()
        global_stats_layout.addRow(self.tr("Nombre total de clients:"), total_clients_layout)

        active_clients_layout = QHBoxLayout()
        active_clients_layout.addWidget(self.stats_labels["active_clients"])
        active_clients_layout.addSpacing(10)
        self.stats_labels["active_clients_trend"].setObjectName("trendLabel")
        active_clients_layout.addWidget(self.stats_labels["active_clients_trend"])
        active_clients_layout.addStretch()
        global_stats_layout.addRow(self.tr("Nombre de clients actifs:"), active_clients_layout)

        global_stats_layout.addRow(self.tr("Nombre total de projets:"), self.stats_labels["total_projects"])
        global_stats_layout.addRow(self.tr("Nombre de projets actifs:"), self.stats_labels["active_projects"])
        global_stats_layout.addRow(self.tr("Nombre total de produits (BDD):"), self.stats_labels["total_products"])

        total_sales_proforma_layout = QHBoxLayout()
        total_sales_proforma_layout.addWidget(self.stats_labels["total_sales_proforma"])
        total_sales_proforma_layout.addSpacing(10)
        self.stats_labels["total_sales_proforma_trend"].setObjectName("trendLabel")
        total_sales_proforma_layout.addWidget(self.stats_labels["total_sales_proforma_trend"])
        total_sales_proforma_layout.addStretch()
        global_stats_layout.addRow(self.tr("Total Ventes (Proforma):"), total_sales_proforma_layout)

        global_stats_layout.addRow(self.tr("Nouveaux Clients (Mois Dernier):"), self.stats_labels["new_clients_last_month"])
        global_stats_layout.addRow(self.tr("Nouveaux Clients (Trimestre Dernier):"), self.stats_labels["new_clients_last_quarter"])

        date_filter_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.dateChanged.connect(self.refresh_all_dashboard_content)
        self.end_date_edit.dateChanged.connect(self.refresh_all_dashboard_content)
        date_filter_layout.addWidget(QLabel("De:"))
        date_filter_layout.addWidget(self.start_date_edit)
        date_filter_layout.addWidget(QLabel("à:"))
        date_filter_layout.addWidget(self.end_date_edit)

        global_stats_layout.addRow(self.tr("Période:"), date_filter_layout)

        save_load_layout = QHBoxLayout()
        self.view_name_input = QLineEdit()
        self.view_name_input.setPlaceholderText(self.tr("Nom de la vue"))
        save_load_layout.addWidget(self.view_name_input)
        self.save_view_button = QPushButton(self.tr("Sauvegarder la vue"))
        save_load_layout.addWidget(self.save_view_button)
        self.load_view_combo = QComboBox()
        save_load_layout.addWidget(self.load_view_combo)
        self.save_view_button.clicked.connect(self.save_view)
        self.load_view_combo.currentIndexChanged.connect(self.load_view)
        global_stats_layout.addRow(self.tr("Vues:"), save_load_layout)


        global_stats_page_layout.addWidget(global_stats_group)

    def get_current_view_config(self):
        return {
            "start_date": self.start_date_edit.date().toString(Qt.ISODate),
            "end_date": self.end_date_edit.date().toString(Qt.ISODate),
        }

    def save_view(self):
        view_name = self.view_name_input.text()
        if not view_name:
            QMessageBox.warning(self, "Nom manquant", "Veuillez entrer un nom pour la vue.")
            return

        config = self.get_current_view_config()

        # This would be a call to a new CRUD function
        # For now, we'll just log it
        logging.info(f"Saving view '{view_name}' with config: {config}")
        self.populate_views_combo()

    def load_view(self, index):
        if index == 0:
            return

        view_name = self.load_view_combo.itemText(index)

        # This would be a call to a new CRUD function
        # For now, we'll just log it and use a dummy config
        logging.info(f"Loading view '{view_name}'")
        config = {
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }

        self.start_date_edit.setDate(QDate.fromString(config["start_date"], Qt.ISODate))
        self.end_date_edit.setDate(QDate.fromString(config["end_date"], Qt.ISODate))
        self.refresh_all_dashboard_content()

    def populate_views_combo(self):
        self.load_view_combo.clear()
        self.load_view_combo.addItem("Sélectionner une vue...")
        # This would be a call to a new CRUD function
        # For now, we'll just add a dummy item
        self.load_view_combo.addItem("Vue Annuelle 2023")

        health_score_group = QGroupBox(self.tr("Indice de Santé Commerciale"))
        health_score_group.setObjectName("healthScoreGroup")
        health_score_layout = QVBoxLayout(health_score_group)
        self.health_score_value_label = QLabel("0 %")
        self.health_score_value_label.setAlignment(Qt.AlignCenter)
        health_score_value_font = QFont()
        health_score_value_font.setPointSize(14)
        health_score_value_font.setBold(True)
        self.health_score_value_label.setFont(health_score_value_font)
        self.health_score_value_label.setObjectName("healthScoreValueLabel")
        self.health_score_progress_bar = QProgressBar()
        self.health_score_progress_bar.setRange(0, 100); self.health_score_progress_bar.setValue(0)
        self.health_score_progress_bar.setTextVisible(False)
        self.health_score_progress_bar.setObjectName("healthScoreProgressBar")
        health_score_layout.addWidget(self.health_score_value_label)
        health_score_layout.addWidget(self.health_score_progress_bar)
        global_stats_page_layout.addWidget(health_score_group)

        self.segmentation_tabs = QTabWidget()
        self.segmentation_tabs.setObjectName("segmentationTabs")
        self._setup_segmentation_tab_ui_internal()
        global_stats_page_layout.addWidget(self.segmentation_tabs)

        self.global_stats_widget.setLayout(global_stats_page_layout)
        self.stats_stack.addWidget(self.global_stats_widget)

        # --- Client Details Widget ---
        self.client_details_widget = QWidget()
        self.client_details_widget.setObjectName("clientDetailsWidget")
        client_details_page_layout = QVBoxLayout(self.client_details_widget)

        client_details_title = QLabel(self.tr("Détails du Client"))
        client_details_title.setObjectName("clientDetailsTitleLabel")
        title_font_details = QFont()
        title_font_details.setPointSize(14)
        title_font_details.setBold(True)
        client_details_title.setFont(title_font_details)
        client_details_title.setAlignment(Qt.AlignCenter)
        client_details_page_layout.addWidget(client_details_title)

        self.client_details_layout = QFormLayout()
        self.client_details_layout.setObjectName("clientDetailsFormLayout")
        self.client_details_layout.setLabelAlignment(Qt.AlignRight)
        self.client_details_layout.setSpacing(8)
        client_details_page_layout.addLayout(self.client_details_layout)

        client_details_page_layout.addStretch(1)

        self.back_to_global_stats_button = QPushButton(self.tr("Retour aux Statistiques Globales"))
        self.back_to_global_stats_button.setObjectName("backToGlobalButton")
        self.back_to_global_stats_button.setIcon(QIcon.fromTheme("go-previous", QIcon(":/icons/arrow-left-circle.svg")))
        self.back_to_global_stats_button.clicked.connect(self._show_global_stats_view)
        client_details_page_layout.addWidget(self.back_to_global_stats_button)

        self.client_details_widget.setLayout(client_details_page_layout)
        self.stats_stack.addWidget(self.client_details_widget)

        # Country Stats Display Widget
        self.country_stats_display_widget = CountryStatsDisplayWidget(self)
        self.stats_stack.addWidget(self.country_stats_display_widget)
        self.country_stats_display_widget.back_to_global_requested.connect(self._show_global_stats_view)
        self.country_stats_display_widget.add_client_to_country_requested.connect(self.request_add_client_for_country)
        self.request_add_client_for_country.connect(self._handle_add_client_for_country)

        # Status Client List Widget
        self.status_client_list_widget = StatusClientListWidget(self)
        self.stats_stack.addWidget(self.status_client_list_widget)
        self.status_client_list_widget.back_to_global_requested.connect(self._show_global_stats_view)
        self.status_client_list_widget.view_client_detail_requested.connect(self.request_view_client_details.emit)

        self.stats_stack.setCurrentWidget(self.global_stats_widget)

    def _show_global_stats_view(self):
        self.stats_stack.setCurrentWidget(self.global_stats_widget)
        self.update_map() # Refresh map to show global view when returning

    def _handle_add_client_for_country(self, country_name):
        dialog = AddNewClientDialog(parent=self, initial_country_name=country_name)
        if dialog.exec_() == AddNewClientDialog.Accepted:
            client_data = dialog.get_data()
            controller = ClientController()
            try:
                controller.add_new_client(client_data)
                QMessageBox.information(self, self.tr("Client Ajouté"), self.tr("Le nouveau client a été ajouté avec succès."))
                self.refresh_all_dashboard_content()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur lors de l'ajout du client: {0}").format(str(e)))

    def _show_country_stats_view(self, country_name: str):
        logging.info(f"Fetching and showing stats for country: {country_name}")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        country_obj = None
        try:
            country_obj = get_country_by_name(country_name)
            if not country_obj:
                logging.error(f"Country '{country_name}' not found in DB.")
                self._show_global_stats_view()
                if hasattr(self, 'parent') and callable(self.parent) and hasattr(self.parent(), 'notify'):
                     self.parent().notify(self.tr("Erreur Données"), self.tr("Pays '{0}' non trouvé.").format(country_name), "ERROR")
                return

            country_id = country_obj['country_id']
            client_count = clients_crud_instance.get_client_count_by_country_id(country_id=country_id, include_deleted=False)
            project_count = get_active_project_count_by_country_id(country_id=country_id)

            db_session_proforma = get_db_connection()
            sales_value = 0.0
            try:
                sales_value = get_total_proforma_sales_for_country_id(db_session_proforma, country_id=country_id)
            finally:
                if db_session_proforma: db_session_proforma.close()

            self.country_stats_display_widget.update_display(country_name, client_count, project_count, sales_value)
            self.stats_stack.setCurrentWidget(self.country_stats_display_widget)
            self.update_map(focus_country_iso_a2=country_obj.get('iso_a2_code')) # Use iso_a2_code from DB


        except Exception as e:
            logging.error(f"Error in _show_country_stats_view for {country_name}: {e}", exc_info=True)
            self._show_global_stats_view()
            if hasattr(self, 'parent') and callable(self.parent) and hasattr(self.parent(), 'notify'):
                self.parent().notify(self.tr("Erreur"), self.tr("Impossible de charger les statistiques pour {0}.").format(country_name), "ERROR")
        finally:
            QApplication.restoreOverrideCursor()


    @pyqtSlot(str, str)
    def _display_client_details_in_panel(self, client_id_str, client_name_str):
        logging.info(f"Displaying details for client: {client_name_str} (ID: {client_id_str}) in panel.")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            while self.client_details_layout.rowCount() > 0:
                self.client_details_layout.removeRow(0)

            client_data = clients_crud_instance.get_client_by_id(client_id_str, include_deleted=True, include_details=True)
            if not client_data:
                self.client_details_layout.addRow(QLabel(self.tr("Erreur:")), QLabel(self.tr("Client non trouvé.")))
                self.stats_stack.setCurrentWidget(self.client_details_widget)
                return

            country_name = client_data.get('country', self.tr("N/A")) # Assumes get_client_by_id now returns country name
            city_name = client_data.get('city', self.tr("N/A")) # Assumes get_client_by_id now returns city name
            status_name = client_data.get('status', self.tr("N/A")) # Assumes get_client_by_id now returns status name

            created_at_val = client_data.get('created_at')
            created_at_display = self.tr("N/A")
            if created_at_val:
                try:
                    if isinstance(created_at_val, str):
                        dt_obj = datetime.fromisoformat(created_at_val.replace('Z', '+00:00'))
                    else:
                        dt_obj = created_at_val
                    created_at_display = dt_obj.strftime('%d %b %Y, %H:%M')
                except ValueError:
                    logging.warning(f"Could not parse date: {created_at_val}")
                    created_at_display = str(created_at_val)

            details_to_display = {
                self.tr("Nom Client:"): client_data.get('client_name', self.tr("N/A")),
                self.tr("Société:"): client_data.get('company_name') or self.tr("N/A"),
                self.tr("Pays:"): country_name,
                self.tr("Ville:"): city_name,
                self.tr("Statut:"): status_name,
                self.tr("Email:"): client_data.get('email') or self.tr("N/A"),
                self.tr("Téléphone:"): client_data.get('phone') or self.tr("N/A"),
                self.tr("Date Création:"): created_at_display,
                self.tr("Ident. Projet:"): client_data.get('project_identifier') or self.tr("N/A"),
                self.tr("Besoin Principal:"): client_data.get('primary_need_description') or self.tr("N/A")
            }

            for label_text, value_text in details_to_display.items():
                key_label = QLabel(f"<b>{label_text}</b>")
                value_label = QLabel(str(value_text))
                value_label.setWordWrap(True)
                value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                self.client_details_layout.addRow(key_label, value_label)

            self.stats_stack.setCurrentWidget(self.client_details_widget)

        except Exception as e:
            logging.error(f"Error fetching/displaying client details for ID {client_id_str}: {e}", exc_info=True)
            self.client_details_layout.addRow(QLabel(self.tr("Erreur:")), QLabel(self.tr("Impossible de charger les détails du client.")))
        finally:
            QApplication.restoreOverrideCursor()


    def refresh_statistics_data(self):
        logging.info("Refreshing statistics data panel...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.update_global_stats()
            self.update_business_health_score()
            self.update_customer_segmentation_views()
        finally:
            QApplication.restoreOverrideCursor()
        logging.info("Statistics data panel refresh complete.")

    def _generate_map_html_worker(self, focus_country_iso_a2):
        geojson_path = os.path.join(APP_ROOT_DIR, "resources", "assets", "world_countries.geojson")
        if not os.path.exists(geojson_path):
            return None, self.tr("Les données géographiques de la carte (GeoJSON) sont introuvables.")

        clients_by_country_counts = get_client_counts_by_country()
        all_clients_for_main_map_popups = clients_crud_instance.get_all_clients_with_details(include_deleted=False)

        db_session = get_db_connection()
        try:
            from db.cruds.application_settings_crud import get_setting
            scope = get_setting('geographic_scope', 'international', conn=db_session)
            last_lat = float(get_setting('map_last_lat', '20', conn=db_session))
            last_lng = float(get_setting('map_last_lng', '0', conn=db_session))
            last_zoom = int(get_setting('map_last_zoom', '2', conn=db_session))
        finally:
            if db_session:
                db_session.close()

        map_html_content = generate_folium_map_html(
            geojson_path=geojson_path,
            clients_by_country_counts=clients_by_country_counts,
            all_clients_details_for_popups=all_clients_for_main_map_popups,
            app_translator_func=self.tr,
            map_interaction_handler_name="pyMapConnector",
            focused_country_iso_a2=focus_country_iso_a2,
            scope=scope,
            initial_location=[last_lat, last_lng],
            initial_zoom=last_zoom
        )
        return map_html_content, None

    def _on_map_html_generated(self, result):
        map_html_content, error_message = result
        if error_message:
            self._set_map_error_html(error_message)
        elif map_html_content:
            if self.map_view:
                self.map_view.setHtml(map_html_content)
            else:
                logging.error("self.map_view is None. Cannot set HTML for the map.")
        else:
            self._set_map_error_html(self.tr("La génération du contenu HTML de la carte a échoué."))

    def update_map(self, focus_country_iso_a2=None):
        logging.info(f"update_map called. Focus country ISO A2: {focus_country_iso_a2}")
        worker = GlobalStatsWorker(self._generate_map_html_worker, focus_country_iso_a2)
        worker.signals.result.connect(self._on_map_html_generated)
        worker.signals.error.connect(lambda err: self._set_map_error_html(str(err[0])))
        self.threadpool.start(worker)


    def _set_map_error_html(self, message: str):
        logging.info(f"_set_map_error_html called. self.map_view is: {self.map_view}. Message: {message}")
        if self.map_view:
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; color: #333; }}
                    .error-container {{ text-align: center; padding: 25px; border: 1px solid #ffccc7; background-color: #fff2f0; color: #d93025; border-radius: 8px; max-width: 90%; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error-icon {{ font-size: 40px; margin-bottom: 15px; color: #d93025; }}
                    h3 {{ margin-top: 0; color: #d93025; font-size: 1.6em; font-weight: 600;}}
                    p {{ font-size: 1.1em; margin-bottom: 25px; }}
                    button {{
                        padding: 12px 25px;
                        font-size: 1.05em;
                        font-weight: 500;
                        color: white;
                        background-color: #1a73e8; /* Google Blue */
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        transition: background-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }}
                    button:hover {{ background-color: #1765c7; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }}
                    button:active {{ background-color: #1452a3; }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-icon">⚠️</div>
                    <h3>{self.tr("Erreur d'Affichage de la Carte")}</h3>
                    <p>{message}</p>
                    <button onclick="if(window.pyMapConnector && typeof window.pyMapConnector.requestMapRefresh === 'function') {{ window.pyMapConnector.requestMapRefresh(); }} else {{ alert('{self.tr("Le mécanisme de rafraîchissement n\\'est pas encore pleinement disponible.")}'); }}">{self.tr("Réessayer de Charger la Carte")}</button>
                </div>
            </body>
            </html>
            """
            self.map_view.setHtml(error_html)
            logging.info(f"Displayed error HTML in map_view: {message}")
        else:
            logging.error("StatisticsDashboard: self.map_view is None. Cannot display error message in map_view.")


    def _fetch_global_stats(self):
        # This function runs in a separate thread
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        current_total_clients = get_total_clients_count()
        current_active_clients = get_active_clients_count()
        total_projects = get_total_projects_count()
        active_projects = get_active_projects_count()
        total_products = get_total_products_count()
        sales_in_period = self.get_total_sales_from_proforma(start_date, end_date)

        return {
            "total_clients": current_total_clients,
            "active_clients": current_active_clients,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_products": total_products,
            "sales_in_period": sales_in_period,
        }

    def _update_global_stats_labels(self, stats):
        self.stats_labels["total_clients"].setText(f"<b>{stats['total_clients']}</b>")
        self.update_total_clients_trend(stats['total_clients'])
        self.stats_labels["active_clients"].setText(f"<b>{stats['active_clients']}</b>")
        self.update_active_clients_trend(stats['active_clients'])
        self.stats_labels["total_projects"].setText(f"<b>{stats['total_projects']}</b>")
        self.stats_labels["active_projects"].setText(f"<b>{stats['active_projects']}</b>")
        self.stats_labels["total_products"].setText(f"<b>{stats['total_products']}</b>")
        self.stats_labels["total_sales_proforma"].setText("<b>€ {:,.2f}</b>".format(stats['sales_in_period']))
        self.update_total_sales_proforma_trend(stats['sales_in_period'])

        self.update_client_acquisition_stats()

    def update_global_stats(self):
        worker = GlobalStatsWorker(self._fetch_global_stats)
        worker.signals.result.connect(self._update_global_stats_labels)
        self.threadpool.start(worker)


    def get_total_sales_from_proforma(self, start_date, end_date) -> float:
        db_session = None
        try:
            start_iso = start_date.toString(Qt.ISODate) + "T00:00:00.000000Z"
            end_iso = end_date.toString(Qt.ISODate) + "T23:59:59.999999Z"
            db_session = get_db_connection()
            total_sales = get_total_sales_amount_for_period(db_session, start_iso, end_iso)
            return total_sales
        except Exception as e:
            logging.error(f"Error calculating total sales from proforma for period: {e}", exc_info=True)
            return 0.0
        finally:
            if db_session:
                try:
                    db_session.close()
                except Exception as e_close:
                    logging.error(f"Error closing db_session in get_total_sales_from_proforma: {e_close}", exc_info=True)


    def update_total_clients_trend(self, current_total_clients: int):
        pass


    def update_active_clients_trend(self, current_active_clients: int):
        pass

    def update_total_sales_proforma_trend(self, current_month_sales: float):
        pass

    def _calculate_trend_display(self, current_value, previous_value, is_currency=False):
        """Helper to calculate trend text and style."""
        trend_text = ""
        style = "color: #555; font-style: italic; font-size: 9pt;"
        if previous_value is not None and previous_value > 0:
            percentage_change = ((current_value - previous_value) / previous_value) * 100
            arrow = "→"
            if percentage_change > 0.5:
                arrow = "↗"
                style = "color: #28a745; font-weight: bold; font-size: 9pt;"
            elif percentage_change < -0.5:
                arrow = "↘"
                style = "color: #dc3545; font-weight: bold; font-size: 9pt;"

            if is_currency:
                trend_text = f"{arrow} {percentage_change:+.1f}% (€ {current_value - previous_value:+.2f})"
            else:
                trend_text = f"{arrow} {percentage_change:+.1f}% ({current_value - previous_value:+.0f})"
        elif current_value > 0 and (previous_value is None or previous_value == 0) :
            arrow = "↗"
            style = "color: #28a745; font-weight: bold; font-size: 9pt;"
            trend_text = f"{arrow} {self.tr('Nouveau')}" if not is_currency else f"{arrow} € {current_value:.2f}"
        else:
            trend_text = "→" if not is_currency else "→ € 0.00"
        return trend_text, style


    def update_client_acquisition_stats(self):
        pass


    def update_business_health_score(self):
        try:
            total_clients_count = get_total_clients_count()
            active_clients_count = get_active_clients_count()
            health_score = (active_clients_count / total_clients_count) * 100 if total_clients_count and total_clients_count > 0 else 0
            self.health_score_value_label.setText(f"{health_score:.0f} %")
            self.health_score_progress_bar.setValue(int(health_score))

            if health_score >= 75: self.health_score_progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
            elif health_score >= 50: self.health_score_progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")
            else: self.health_score_progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")
        except Exception as e:
            logging.error(f"Error updating business health score: {e}", exc_info=True)
            self.health_score_value_label.setText(self.tr("Erreur"))
            self.health_score_progress_bar.setValue(0)
            self.health_score_progress_bar.setStyleSheet("")


    def _setup_segmentation_tab_ui_internal(self):
        self.segmentation_tables = {}
        self.segmentation_chart_pages = {}

        tab_configs = [
            ("country", self.tr("Par Pays"), [self.tr("Pays"), self.tr("Nombre de Clients")], "table"),
            ("city", self.tr("Par Ville"), [self.tr("Pays"), self.tr("Ville"), self.tr("Nombre de Clients")], "table"),
            ("status", self.tr("Par Statut"), [], "chart"),
            ("category", self.tr("Par Catégorie"), [self.tr("Catégorie"), self.tr("Nombre de Clients")], "table"),
            ("product_popularity", self.tr("Par Popularité Produit"), [self.tr("Nom Produit"), self.tr("Nombre d'Utilisations")], "table")
        ]

        for key, title, headers, tab_type in tab_configs:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            tab_widget.setObjectName(f"segmentationTab_{key}")

            export_button = QPushButton(self.tr("Exporter"))
            export_button.setIcon(QIcon(":/icons/download.svg"))
            export_button.clicked.connect(lambda _, k=key: self.export_segmentation_data(k))
            tab_layout.addWidget(export_button, 0, Qt.AlignRight)

            if tab_type == "table":
                table_widget = QTableWidget()
                table_widget.setObjectName(f"segmentationTable_{key}")
                table_widget.setColumnCount(len(headers))
                table_widget.setHorizontalHeaderLabels(headers)
                table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
                table_widget.setSelectionBehavior(QTableWidget.SelectRows)
                table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table_widget.setSortingEnabled(True)
                table_widget.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #e9ecef; padding: 4px; border: 1px solid #dee2e6; font-weight: bold; }")
                table_widget.verticalHeader().setVisible(False)
                table_widget.setAlternatingRowColors(True)
                tab_layout.addWidget(table_widget)
                self.segmentation_tables[key] = table_widget
            elif tab_type == "chart":
                self.segmentation_chart_pages[key] = tab_widget

            self.segmentation_tabs.addTab(tab_widget, title)
        logging.debug(f"segmentation_chart_pages initialized: {self.segmentation_chart_pages}")
        logging.debug(f"segmentation_tables initialized: {self.segmentation_tables}")


    def _populate_table(self, table_key, data_fetch_func, column_keys):
        table = self.segmentation_tables.get(table_key)
        if not table:
            logging.warning(f"Table with key '{table_key}' not found in segmentation_tables.")
            return

        table.setSortingEnabled(False)
        table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            data_rows = data_fetch_func()
            if data_rows is None: data_rows = []

            if not data_rows:
                table.setRowCount(1)
                no_data_item = QTableWidgetItem(self.tr("Aucune donnée disponible."))
                no_data_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(0,0, no_data_item)
                if table.columnCount() > 0:
                    table.setSpan(0,0, 1, table.columnCount())
                return

            table.setRowCount(len(data_rows))
            for row_idx, row_data in enumerate(data_rows):
                for col_idx, col_key in enumerate(column_keys):
                    item_value = row_data.get(col_key, "")
                    table_item = QTableWidgetItem(str(item_value))
                    if col_key in ['client_count', 'usage_count'] and isinstance(item_value, (int, float)):
                        table_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row_idx, col_idx, table_item)
        except Exception as e:
            logging.error(f"Error populating table {table_key}: {e}", exc_info=True)
            table.setRowCount(1)
            error_item = QTableWidgetItem(self.tr("Erreur de chargement des données."))
            error_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0,0, error_item)
            if table.columnCount() > 0:
                 table.setSpan(0,0, 1, table.columnCount())
        finally:
            table.setSortingEnabled(True)
            QApplication.restoreOverrideCursor()


    def _on_status_chart_slice_picked(self, event):
        logging.debug(f"Pie chart slice picked. Event: {event}, Artist: {event.artist}")
        if not hasattr(self, 'last_pie_chart_labels') or not self.last_pie_chart_labels:
            logging.warning("_on_status_chart_slice_picked: last_pie_chart_labels not available.")
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ax_patches = event.artist.axes.patches
            wedge_index = ax_patches.index(event.artist)

            if 0 <= wedge_index < len(self.last_pie_chart_labels):
                status_name = self.last_pie_chart_labels[wedge_index]
                logging.info(f"Clicked on status: {status_name} (index: {wedge_index})")

                status_obj = get_status_setting_by_name(status_name, 'Client')
                if not status_obj:
                    logging.error(f"Status '{status_name}' not found in DB for type 'Client'.")
                    if hasattr(self, 'parent') and callable(self.parent) and hasattr(self.parent(), 'notify'):
                        self.parent().notify(self.tr("Erreur Données"), self.tr("Détails du statut '{0}' non trouvés.").format(status_name), "ERROR")
                    return

                status_id = status_obj['status_id']
                clients = clients_crud_instance.get_clients_by_status_id(status_id=status_id, include_deleted=False)
                self.status_client_list_widget.update_display(status_name, clients)
                self.stats_stack.setCurrentWidget(self.status_client_list_widget)
            else:
                logging.warning(f"Picked wedge index {wedge_index} out of bounds for labels (len: {len(self.last_pie_chart_labels)}).")
        except ValueError:
            logging.warning("Picked artist not found in axes patches. Cannot determine status.")
        except Exception as e:
            logging.error(f"Error handling pie chart pick event: {e}", exc_info=True)
        finally:
            QApplication.restoreOverrideCursor()



    def _update_status_segmentation_chart(self):
        logging.info("Updating status segmentation chart...")
        page_widget = self.segmentation_chart_pages.get("status")
        if page_widget is None:
            logging.error("Page widget for 'status' chart not found.")
            return

        chart_layout = page_widget.layout()
        if chart_layout is None:
            logging.error("Chart layout for 'status' is None. Re-creating.")
            chart_layout = QVBoxLayout(page_widget)
            page_widget.setLayout(chart_layout)

        while chart_layout.count():
            item = chart_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            status_data = get_client_segmentation_by_status()
            if not status_data:
                no_data_label = QLabel(self.tr("Aucune donnée de statut client disponible."))
                no_data_label.setAlignment(Qt.AlignCenter)
                chart_layout.addWidget(no_data_label)
                return

            # Filter out statuses with 0 clients before creating labels and sizes
            filtered_status_data = [item for item in status_data if item.get('client_count', 0) > 0]

            if not filtered_status_data:
                no_data_label = QLabel(self.tr("Aucun client trouvé pour les statuts existants."))
                no_data_label.setAlignment(Qt.AlignCenter)
                chart_layout.addWidget(no_data_label)
                return

            labels = [item.get('status_name', 'N/A') for item in filtered_status_data]
            sizes = [item.get('client_count', 0) for item in filtered_status_data]


            plt.style.use('seaborn-v0_8-pastel')
            fig = Figure(figsize=(5.5, 4.5), dpi=90)
            fig.patch.set_alpha(0)
            ax = fig.add_subplot(111)
            ax.patch.set_alpha(0)

            wedges, texts, autotexts = ax.pie(
                sizes,
                autopct=lambda p: '{:.1f}%\n({:.0f})'.format(p, p * sum(sizes) / 100.0),
                startangle=90,
                pctdistance=0.80,
                wedgeprops=dict(width=0.35, edgecolor='w')
            )
            ax.axis('equal')

            if not sizes:
                return

            for text_obj in texts + autotexts:
                text_obj.set_fontsize(8)

            for wedge in wedges:
                wedge.set_picker(True)
                # wedge.set_pickradius(5) # AttributeError: 'Wedge' object has no attribute 'set_pickradius'. Did you mean: 'set_radius'?
                # Picking is usually enabled by set_picker(True). Radius affects the wedge size.
                # If the intent was to make wedges easier to click, set_picker(True) is the main part.
                # If a visual change of radius was intended, set_radius() would be used, but pickradius is not standard.
                # For now, let's assume set_picker(True) is sufficient for clickability.
                # If a hover effect or similar was intended by pickradius, that's a more complex change.

            self.last_pie_chart_labels = list(labels)

            if len(labels) <= 7:
                 ax.legend(wedges, labels, title=self.tr("Statuts"), loc="center left", bbox_to_anchor=(1.05, 0.5), prop={'size': 7})
                 fig.subplots_adjust(right=0.75)
            else:
                 fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)


            if hasattr(self, 'status_chart_canvas') and self.status_chart_canvas:
                if hasattr(self, '_pick_event_cid') and self._pick_event_cid is not None:
                    try: self.status_chart_canvas.mpl_disconnect(self._pick_event_cid)
                    except: pass

            self.status_chart_canvas = FigureCanvas(fig)
            self.status_chart_canvas.setObjectName("statusPieChartCanvas")
            self._pick_event_cid = self.status_chart_canvas.mpl_connect('pick_event', self._on_status_chart_slice_picked)

            chart_layout.addWidget(self.status_chart_canvas)
            self.status_chart_canvas.draw_idle()
            logging.info("Status segmentation chart updated.")

        except Exception as e:
            logging.error(f"Error updating status segmentation chart: {e}", exc_info=True)
            error_label = QLabel(self.tr("Erreur génération graphique des statuts."))
            error_label.setAlignment(Qt.AlignCenter)
            chart_layout.addWidget(error_label)
        finally:
            QApplication.restoreOverrideCursor()


    def update_customer_segmentation_views(self):
        for key, args in {
            "country": (get_client_counts_by_country, ["country_name", "client_count"]),
            "city": (get_client_segmentation_by_city, ["country_name", "city_name", "client_count"]),
            "category": (get_client_segmentation_by_category, ["category", "client_count"]),
            "product_popularity": (get_product_usage_counts, ["product_name", "usage_count"]),
        }.items():
            worker = GlobalStatsWorker(self._populate_table, key, args[0], args[1])
            self.threadpool.start(worker)
        self._update_status_segmentation_chart()

    def export_segmentation_data(self, key):
        if key in self.segmentation_tables:
            self.export_table_to_csv(self.segmentation_tables[key])
        elif key in self.segmentation_chart_pages:
            self.export_chart_to_png(key)

    def export_table_to_csv(self, table_widget):
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le fichier CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    headers = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]
                    writer.writerow(headers)
                    for row in range(table_widget.rowCount()):
                        row_data = [table_widget.item(row, column).text() for column in range(table_widget.columnCount())]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Exportation réussie", "Le tableau a été exporté en CSV avec succès.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'exportation", f"Une erreur est survenue lors de l'exportation du tableau : {e}")

    def export_chart_to_png(self, key):
        if key == "status":
            if hasattr(self, 'status_chart_canvas'):
                path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le graphique", "", "PNG Files (*.png)")
                if path:
                    try:
                        self.status_chart_canvas.figure.savefig(path)
                        QMessageBox.information(self, "Exportation réussie", "Le graphique a été exporté en PNG avec succès.")
                    except Exception as e:
                        QMessageBox.critical(self, "Erreur d'exportation", f"Une erreur est survenue lors de l'exportation du graphique : {e}")

        for key, args in {
            "country": (get_client_counts_by_country, ["country_name", "client_count"]),
            "city": (get_client_segmentation_by_city, ["country_name", "city_name", "client_count"]),
            "category": (get_client_segmentation_by_category, ["category", "client_count"]),
            "product_popularity": (get_product_usage_counts, ["product_name", "usage_count"]),
        }.items():
            worker = GlobalStatsWorker(self._populate_table, key, args[0], args[1])
            self.threadpool.start(worker)


class StatisticsSummaryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatisticsSummaryWidget")
        self._init_ui()
        self.update_summary_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        title_label = QLabel(self.tr("Aperçu Rapide"))
        title_label.setObjectName("summaryTitleLabel")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        stats_group = QGroupBox(self.tr("Statistiques Clés"))
        stats_group.setObjectName("summaryStatsGroup")
        stats_layout = QFormLayout(stats_group)
        stats_layout.setLabelAlignment(Qt.AlignLeft)
        stats_layout.setSpacing(7)
        stats_layout.setContentsMargins(8, 10, 8, 8)

        self.summary_labels = {
            "total_clients": QLabel("0"),
            "active_projects": QLabel("0"),
            "total_sales_current_month": QLabel("€ 0.00")
        }
        for key, label_widget in self.summary_labels.items():
            label_widget.setObjectName(f"summaryLabel_{key}")
            label_font = label_widget.font()
            label_font.setBold(True)
            label_widget.setFont(label_font)
            label_widget.setAlignment(Qt.AlignRight)


        stats_layout.addRow(self.tr("Clients Totaux:"), self.summary_labels["total_clients"])
        stats_layout.addRow(self.tr("Projets Actifs:"), self.summary_labels["active_projects"])
        stats_layout.addRow(self.tr("Ventes (Mois Actuel):"), self.summary_labels["total_sales_current_month"])

        layout.addWidget(stats_group)
        layout.addStretch(1)

        self.setLayout(layout)

    def update_summary_stats(self):
        logging.info("StatisticsSummaryWidget: Updating summary stats...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            total_clients = get_total_clients_count()
            self.summary_labels["total_clients"].setText(str(total_clients))

            active_projects = get_active_projects_count()
            self.summary_labels["active_projects"].setText(str(active_projects))

            sales_current_month_val = 0.0
            db_session = None
            try:
                today = datetime.utcnow().date()
                start_of_current_month = today.replace(day=1)
                end_of_current_month = (today.replace(day=1) + relativedelta(months=1)) - relativedelta(days=1)
                start_iso = start_of_current_month.strftime('%Y-%m-%dT00:00:00.000000Z')
                end_iso = end_of_current_month.strftime('%Y-%m-%dT23:59:59.999999Z')
                db_session = get_db_connection()
                sales_current_month_val = get_total_sales_amount_for_period(db_session, start_iso, end_iso)
            except Exception as e_sales:
                logging.error(f"StatisticsSummaryWidget: Error fetching current month sales: {e_sales}", exc_info=True)
            finally:
                if db_session:
                    try: db_session.close()
                    except: pass

            self.summary_labels["total_sales_current_month"].setText("€ {:,.2f}".format(sales_current_month_val))
            logging.info("StatisticsSummaryWidget: Summary stats updated.")

        except Exception as e:
            logging.error(f"StatisticsSummaryWidget: Error updating summary stats: {e}", exc_info=True)
            for key in self.summary_labels:
                self.summary_labels[key].setText(self.tr("<i>Erreur</i>"))
        finally:
            QApplication.restoreOverrideCursor()


    def refresh_data(self):
        self.update_summary_stats()


class StatusClientListWidget(QWidget):
    back_to_global_requested = pyqtSignal()
    view_client_detail_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusClientListWidget")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.title_label = QLabel(self.tr("Clients par Statut"))
        self.title_label.setObjectName("statusClientListTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        self.clients_table = QTableWidget()
        self.clients_table.setObjectName("statusClientsTable")
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels([
            self.tr("Nom Client"), self.tr("Société"), self.tr("Pays"), self.tr("Ville")
        ])
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setSelectionMode(QTableWidget.SingleSelection)
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #e9ecef; padding: 4px; border: 1px solid #dee2e6; font-weight: bold; }")
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.clients_table.doubleClicked.connect(self._on_table_double_clicked)
        main_layout.addWidget(self.clients_table)

        buttons_layout = QHBoxLayout()
        self.view_client_button = QPushButton(self.tr("Voir Fiche Client"))
        self.view_client_button.setObjectName("viewClientButton")
        self.view_client_button.setIcon(QIcon(":/icons/eye.svg"))
        self.view_client_button.setEnabled(False)
        self.view_client_button.clicked.connect(self._emit_view_client_detail_signal)
        buttons_layout.addWidget(self.view_client_button)

        buttons_layout.addStretch()

        self.back_button = QPushButton(self.tr("Retour aux Stats Globales"))
        self.back_button.setObjectName("backToGlobalButton")
        self.back_button.setIcon(QIcon(":/icons/arrow-left-circle.svg"))
        self.back_button.clicked.connect(self.back_to_global_requested.emit)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def update_display(self, status_name: str, clients: list[dict]):
        self.title_label.setText(self.tr("Clients - Statut: <b>{0}</b>").format(status_name))

        self.clients_table.setRowCount(0)
        self.clients_table.setSortingEnabled(False)

        if not clients:
            logging.info(f"StatusClientListWidget: No clients to display for status '{status_name}'.")
            self.clients_table.setRowCount(1)
            no_data_item = QTableWidgetItem(self.tr("Aucun client trouvé pour ce statut."))
            no_data_item.setTextAlignment(Qt.AlignCenter)
            self.clients_table.setItem(0, 0, no_data_item)
            if self.clients_table.columnCount() > 0:
                self.clients_table.setSpan(0, 0, 1, self.clients_table.columnCount())
            self.view_client_button.setEnabled(False)
            return

        self.clients_table.setRowCount(len(clients))
        for row, client_data in enumerate(clients):
            name_item = QTableWidgetItem(client_data.get("client_name", "N/A"))
            name_item.setData(Qt.UserRole, client_data.get("client_id"))
            self.clients_table.setItem(row, 0, name_item)
            self.clients_table.setItem(row, 1, QTableWidgetItem(client_data.get("company_name") or "N/A"))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client_data.get("country", "N/A")))
            self.clients_table.setItem(row, 3, QTableWidgetItem(client_data.get("city", "N/A")))

        self.clients_table.setSortingEnabled(True)
        self.view_client_button.setEnabled(False)
        logging.info(f"StatusClientListWidget updated for status '{status_name}' with {len(clients)} clients.")

    def _on_table_selection_changed(self):
        if self.clients_table.rowCount() == 1 and self.clients_table.item(0,0) and \
           self.clients_table.item(0,0).text() == self.tr("Aucun client trouvé pour ce statut."):
            self.view_client_button.setEnabled(False)
        else:
            self.view_client_button.setEnabled(len(self.clients_table.selectedItems()) > 0)


    def _emit_view_client_detail_signal(self):
        selected_items = self.clients_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            client_id_item = self.clients_table.item(selected_row, 0)
            if client_id_item:
                client_id = client_id_item.data(Qt.UserRole)
                if client_id:
                    self.view_client_detail_requested.emit(str(client_id))
                else: logging.warning("No client_id in selected row's UserRole.")
            else: logging.warning("First item in selected row is None.")

    def _on_table_double_clicked(self, index):
        client_id_item = self.clients_table.item(index.row(), 0)
        if client_id_item:
            client_id = client_id_item.data(Qt.UserRole)
            if client_id: self.view_client_detail_requested.emit(str(client_id))
            else: logging.warning("No client_id in double-clicked row's UserRole.")
        else: logging.warning("First item in double-clicked row is None.")


class CountryStatsDisplayWidget(QWidget):
    back_to_global_requested = pyqtSignal()
    add_client_to_country_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CountryStatsDisplayWidget")
        self.current_country_name = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.title_label = QLabel(self.tr("Statistiques par Pays"))
        self.title_label.setObjectName("countryStatsTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        stats_group = QGroupBox(self.tr("Détails"))
        stats_group.setObjectName("countryStatsGroup")
        form_layout = QFormLayout(stats_group)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(10, 12, 10, 10)


        self.client_count_label = QLabel("N/A")
        self.project_count_label = QLabel("N/A")
        self.sales_value_label = QLabel("N/A")

        value_font = QFont()
        value_font.setBold(True)
        self.client_count_label.setFont(value_font)
        self.project_count_label.setFont(value_font)
        self.sales_value_label.setFont(value_font)

        self.client_count_label.setObjectName("countryStatLabelClientCount")
        self.project_count_label.setObjectName("countryStatLabelProjectCount")
        self.sales_value_label.setObjectName("countryStatLabelSalesValue")


        form_layout.addRow(self.tr("Clients Totaux:"), self.client_count_label)
        form_layout.addRow(self.tr("Projets Actifs:"), self.project_count_label)
        form_layout.addRow(self.tr("Ventes Proforma Totales:"), self.sales_value_label)

        main_layout.addWidget(stats_group)

        buttons_layout = QHBoxLayout()
        self.add_client_button = QPushButton(self.tr("Ajouter Client à ce Pays"))
        self.add_client_button.setObjectName("addClientToCountryButton")
        self.add_client_button.setIcon(QIcon(":/icons/user-add.svg"))
        self.add_client_button.clicked.connect(self._emit_add_client_signal)
        buttons_layout.addWidget(self.add_client_button)

        buttons_layout.addStretch()

        self.back_button = QPushButton(self.tr("Retour aux Stats Globales"))
        self.back_button.setObjectName("backToGlobalButton")
        self.back_button.setIcon(QIcon(":/icons/arrow-left-circle.svg"))
        self.back_button.clicked.connect(self.back_to_global_requested)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def update_display(self, country_name: str, client_count: int, project_count: int, sales_value: float):
        self.current_country_name = country_name
        self.title_label.setText(self.tr("Statistiques pour: <b>{0}</b>").format(country_name))
        self.client_count_label.setText(str(client_count))
        self.project_count_label.setText(str(project_count))
        self.sales_value_label.setText("€ {:,.2f}".format(sales_value))
        logging.info(f"CountryStatsDisplayWidget updated for {country_name}.")

    def _emit_add_client_signal(self):
        if self.current_country_name:
            self.add_client_to_country_requested.emit(self.current_country_name)
        else:
            logging.warning("CountryStatsDisplayWidget: _emit_add_client_signal called but current_country_name is not set.")