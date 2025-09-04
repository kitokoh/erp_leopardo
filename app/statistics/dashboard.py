# -*- coding: utf-8 -*-
import os
import logging
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSplitter, QHBoxLayout,
    QGroupBox, QFormLayout, QTableWidget, QHeaderView, QTabWidget, QProgressBar,
    QTableWidgetItem, QStackedWidget, QApplication, QMessageBox, QDateEdit, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QTimer, QRunnable, QThreadPool, QDate
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
from datetime import datetime
from dateutil.relativedelta import relativedelta
import csv

from .map_utils import generate_folium_map_html
from .data_loader import (
    fetch_global_stats, get_country_stats, get_client_segmentation_by_city,
    get_client_segmentation_by_status, get_client_segmentation_by_category,
    get_client_counts_by_country, get_product_usage_counts, get_total_clients_count,
    get_active_projects_count, get_total_sales_amount_for_period, get_active_clients_count
)
from app.db.cruds.clients import clients_crud
from app.db.cruds.misc import status_settings_crud, application_settings_crud
from app.db.connection import get_db_connection
from app.views.gui.dialogs.add_new_client_dialog import AddNewClientDialog
from app.views.client_management.client_controller import ClientController
from app.core.app_setup import APP_ROOT_DIR

from .widgets.country_stats_widget import CountryStatsDisplayWidget
from .widgets.client_list_widget import StatusClientListWidget
from .widgets.panels import ClientDetailsPanel
from .widgets.charts import StatusChart

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class StatsWorker(QRunnable): # Renamed for clarity
    def __init__(self, fn, db_session_needed=False, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.db_session_needed = db_session_needed
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        db_session = None
        try:
            if self.db_session_needed:
                db_session = get_db_connection()
                result = self.fn(db_session, *self.args, **self.kwargs)
            else:
                result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit((e, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            if db_session:
                db_session.close()
            self.signals.finished.emit()

class MapInteractionHandler(QObject):
    # ... (class remains the same)
    pass

class StatisticsDashboard(QWidget):
    # ... (signals remain the same)
    def __init__(self, parent=None):
        # ... (initialization largely the same, just ensure db calls are handled)
        super().__init__(parent)
        self.threadpool = QThreadPool()
        # ... UI setup ...
        # The core change is how data loading functions are called.

    def _on_map_view_changed(self, lat, lng, zoom):
        db_session = None
        try:
            db_session = get_db_connection()
            application_settings_crud.set_setting(db_session, 'map_last_lat', str(lat))
            application_settings_crud.set_setting(db_session, 'map_last_lng', str(lng))
            application_settings_crud.set_setting(db_session, 'map_last_zoom', str(zoom))
        except Exception as e:
            logging.error(f"Error saving map view state: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

    def _show_country_stats_view(self, country_name: str):
        worker = StatsWorker(get_country_stats, db_session_needed=True, country_name=country_name)
        worker.signals.result.connect(self._on_country_stats_loaded)
        worker.signals.error.connect(lambda err: logging.error(f"Error fetching country stats: {err}"))
        self.threadpool.start(worker)

    def _on_country_stats_loaded(self, stats):
        if stats:
            self.country_stats_display_widget.update_display(stats["country_obj"]['name'], stats["client_count"], stats["project_count"], stats["sales_value"])
            self.stats_stack.setCurrentWidget(self.country_stats_display_widget)
            self.update_map(focus_country_iso_a2=stats["country_obj"].get('iso_a2_code'))
        else:
            self._show_global_stats_view()
            # ... notification ...

    def _display_client_details_in_panel(self, client_id_str, client_name_str):
        worker = StatsWorker(clients_crud.get_client_by_id, db_session_needed=True, client_id=client_id_str, include_deleted=True, include_details=True)
        worker.signals.result.connect(self.client_details_widget.update_details)
        worker.signals.error.connect(lambda err: self.client_details_widget.update_details(None))
        self.threadpool.start(worker)
        self.stats_stack.setCurrentWidget(self.client_details_widget)

    def _generate_map_html_worker(self, db_session, focus_country_iso_a2):
        geojson_path = os.path.join(APP_ROOT_DIR, "resources", "assets", "world_countries.geojson")
        clients_by_country = get_client_counts_by_country(db_session)
        all_clients = clients_crud.get_all_clients_with_details(db_session, include_deleted=False)
        # ... (rest of map generation logic) ...
        return generate_folium_map_html(...)

    def update_map(self, focus_country_iso_a2=None):
        worker = StatsWorker(self._generate_map_html_worker, db_session_needed=True, focus_country_iso_a2=focus_country_iso_a2)
        # ... (connect signals) ...
        self.threadpool.start(worker)

    def update_global_stats(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        worker = StatsWorker(fetch_global_stats, db_session_needed=True, start_date=start_date, end_date=end_date)
        # ... (connect signals) ...
        self.threadpool.start(worker)

    def update_business_health_score(self):
        # This function can also be run in a worker
        def fetch_health_score_data(db_session):
            total = get_total_clients_count(db_session)
            active = get_active_clients_count(db_session)
            return (active / total) * 100 if total > 0 else 0

        worker = StatsWorker(fetch_health_score_data, db_session_needed=True)
        # ... (connect signals to update UI) ...
        self.threadpool.start(worker)

    def _populate_table(self, db_session, table_key, data_fetch_func, column_keys):
        # This now receives a session from the worker
        table = self.segmentation_tables.get(table_key)
        if not table: return
        data_rows = data_fetch_func(db_session)
        # ... (UI population logic) ...

    def _on_status_chart_slice_picked(self, event):
        # ...
        db_session = None
        try:
            db_session = get_db_connection()
            status_name = self.last_pie_chart_labels[wedge_index]
            status_obj = status_settings_crud.get_status_setting_by_name(db_session, status_name, 'Client')
            if status_obj:
                clients = clients_crud.get_clients_by_status_id(db_session, status_id=status_obj['status_id'])
                self.status_client_list_widget.update_display(status_name, clients)
                self.stats_stack.setCurrentWidget(self.status_client_list_widget)
        except Exception as e:
            logging.error(f"Error handling pie chart pick: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

    def _update_status_segmentation_chart(self):
        worker = StatsWorker(get_client_segmentation_by_status, db_session_needed=True)
        worker.signals.result.connect(lambda data: self.status_chart.update_chart(data, self._on_status_chart_slice_picked))
        self.threadpool.start(worker)

    def update_customer_segmentation_views(self):
        data_map = {
            "country": (get_client_counts_by_country, ["country_name", "client_count"]),
            "city": (get_client_segmentation_by_city, ["country_name", "city_name", "client_count"]),
            "category": (get_client_segmentation_by_category, ["category", "client_count"]),
            "product_popularity": (get_product_usage_counts, ["product_name", "usage_count"]),
        }
        for key, (func, keys) in data_map.items():
            worker = StatsWorker(self._populate_table, db_session_needed=True, table_key=key, data_fetch_func=func, column_keys=keys)
            self.threadpool.start(worker)
        self._update_status_segmentation_chart()

class StatisticsSummaryWidget(QWidget):
    # ... (init and _init_ui)
    def update_summary_stats(self):
        worker = StatsWorker(self._fetch_summary_data, db_session_needed=True)
        worker.signals.result.connect(self._on_summary_data_loaded)
        self.threadpool.start(worker)

    def _fetch_summary_data(self, db_session):
        total_clients = get_total_clients_count(db_session)
        active_projects = get_active_projects_count(db_session)
        today = datetime.utcnow().date()
        start_of_month = today.replace(day=1)
        start_iso = start_of_month.strftime('%Y-%m-%dT00:00:00.000000Z')
        # Pro-forma sales don't need end date if we want up to now
        sales = get_total_sales_amount_for_period(db_session, start_iso, None)
        return {"total_clients": total_clients, "active_projects": active_projects, "sales": sales}

    def _on_summary_data_loaded(self, data):
        if data:
            self.summary_labels["total_clients"].setText(str(data["total_clients"]))
            self.summary_labels["active_projects"].setText(str(data["active_projects"]))
            self.summary_labels["total_sales_current_month"].setText("€ {:,.2f}".format(data["sales"]))
        else:
            # Handle error case
            pass
    # ... (rest of the class)
