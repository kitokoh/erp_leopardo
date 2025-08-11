# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QComboBox,
    QLineEdit, QDateEdit, QGroupBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDate
from datetime import datetime
# Placeholder for DB imports, will be added as needed
from app.db.cruds.invoices import commandes_crud
from app.db.cruds.misc.status_settings_crud import get_all_status_settings
from PyQt5.QtGui import QColor # For status color
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFormLayout


class CommandesDashboardWidget(QWidget):
    def __init__(self, parent=None, current_user_info=None, app_root_dir=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.app_root_dir = app_root_dir # Store app_root_dir
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle(self.tr("Tableau de Bord des Commandes"))
        self.setObjectName("commandesDashboardWidget") # For QSS styling if needed

        self.current_offset = 0
        self.limit_per_page = 25 # Example, can be made configurable

        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Titre
        title_label = QLabel(self.tr("Tableau de Bord des Commandes"))
        title_label.setObjectName("pageTitleLabel") # Use existing style if available
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Section Filtres
        filters_groupbox = QGroupBox(self.tr("Filtres"))
        filters_layout = QFormLayout(filters_groupbox) # Using QFormLayout for label-field pairs

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Réf. Commande, Nom Client..."))
        filters_layout.addRow(self.tr("Rechercher:"), self.search_input)

        self.status_filter_combo = QComboBox()
        filters_layout.addRow(self.tr("Statut:"), self.status_filter_combo)

        date_filter_layout = QHBoxLayout()
        self.date_from_edit = QDateEdit(QDate.currentDate().addMonths(-1)) # Default to one month ago
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDisplayFormat("yyyy-MM-dd")
        date_filter_layout.addWidget(QLabel(self.tr("De:")))
        date_filter_layout.addWidget(self.date_from_edit)
        date_filter_layout.addSpacing(10)
        self.date_to_edit = QDateEdit(QDate.currentDate())
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDisplayFormat("yyyy-MM-dd")
        date_filter_layout.addWidget(QLabel(self.tr("À:")))
        date_filter_layout.addWidget(self.date_to_edit)
        date_filter_layout.addStretch()
        filters_layout.addRow(date_filter_layout)

        filter_buttons_layout = QHBoxLayout()
        self.apply_filters_btn = QPushButton(self.tr("Appliquer Filtres"))
        # self.apply_filters_btn.setIcon(QIcon.fromTheme("system-search")) # Example icon
        # self.apply_filters_btn.clicked.connect(self._apply_filters_and_reload)
        filter_buttons_layout.addWidget(self.apply_filters_btn)

        self.apply_filters_btn = QPushButton(self.tr("Appliquer Filtres"))
        self.apply_filters_btn.setText("🔎") # Example icon
        self.apply_filters_btn.clicked.connect(self._apply_filters_and_reload)
        filter_buttons_layout.addWidget(self.apply_filters_btn)

        self.reset_filters_btn = QPushButton(self.tr("Réinitialiser Filtres"))
        self.reset_filters_btn.setText("🔄") # Example icon
        self.reset_filters_btn.clicked.connect(self._reset_filters_and_reload)
        filter_buttons_layout.addWidget(self.reset_filters_btn)
        filter_buttons_layout.addStretch()
        filters_layout.addRow(filter_buttons_layout)

        main_layout.addWidget(filters_groupbox)

        # Table des Commandes
        self.commandes_table = QTableWidget()
        self.commandes_table.setColumnCount(7) # Réf, Client, Date, Statut, Total, Projet, Actions
        self.commandes_table.setHorizontalHeaderLabels([
            self.tr("Référence"), self.tr("Client"), self.tr("Date Commande"),
            self.tr("Statut"), self.tr("Total TTC"), self.tr("Projet Associé"), self.tr("Actions")
        ])
        self.commandes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.commandes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.commandes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.commandes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.commandes_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.commandes_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.commandes_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.commandes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.commandes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.commandes_table.itemDoubleClicked.connect(self._handle_view_edit_commande) # Placeholder
        main_layout.addWidget(self.commandes_table)

        # KPIs Section (Placeholder - Simple version for now)
        kpi_layout = QHBoxLayout()
        self.total_commandes_label = QLabel(self.tr("Total Commandes Filtrées: N/A"))
        kpi_layout.addWidget(self.total_commandes_label)
        self.total_commandes_value_label = QLabel(self.tr("Valeur Totale Filtrée: N/A"))
        kpi_layout.addWidget(self.total_commandes_value_label)
        kpi_layout.addStretch()
        main_layout.addLayout(kpi_layout)

        # Pagination
        pagination_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton(self.tr("Précédent"))
        self.prev_page_btn.setText("⬅️")
        self.prev_page_btn.clicked.connect(self._prev_page)
        self.page_info_label = QLabel(self.tr("Page 1/1"))
        self.next_page_btn = QPushButton(self.tr("Suivant"))
        self.next_page_btn.setText("➡️")
        self.next_page_btn.clicked.connect(self._next_page)

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.next_page_btn)
        pagination_layout.addStretch()
        main_layout.addLayout(pagination_layout)

        self.setLayout(main_layout)
        self.logger.info("CommandesDashboardWidget UI setup complete.")

    def _populate_status_filter(self):
        self.status_filter_combo.blockSignals(True)
        self.status_filter_combo.clear()
        self.status_filter_combo.addItem(self.tr("Tous les Statuts"), None)
        try:
            statuses = get_all_status_settings(type_filter='Commande')
            if statuses:
                for status in sorted(statuses, key=lambda x: x.get('sort_order', 0)):
                    # Assuming icons are available in the theme
                    icon = QIcon.fromTheme(status.get('icon_name', 'document-properties'))
                    self.status_filter_combo.addItem(icon, status.get('status_name'), status.get('status_id'))
        except Exception as e:
            self.logger.error(f"Erreur chargement des statuts Commande: {e}", exc_info=True)
        finally:
            self.status_filter_combo.blockSignals(False)

    def _get_current_filters(self):
        filters = {}
        search_text = self.search_input.text().strip()
        if search_text:
            filters['search_term'] = search_text

        status_id = self.status_filter_combo.currentData()
        if status_id is not None: # Ensure we don't add a None filter if "Tous les Statuts" is selected
            filters['status_commande_id'] = status_id

        if self.date_from_edit.date().isValid() and not self.date_from_edit.date().isNull():
            filters['date_from'] = self.date_from_edit.date().toString("yyyy-MM-dd")

        if self.date_to_edit.date().isValid() and not self.date_to_edit.date().isNull():
            filters['date_to'] = self.date_to_edit.date().toString("yyyy-MM-dd")

        return filters

    def _apply_filters_and_reload(self):
        self.current_offset = 0 # Reset to first page when filters change
        self._load_commandes_data()

    def _reset_filters_and_reload(self):
        self.search_input.clear()
        self.status_filter_combo.setCurrentIndex(0) # "Tous les Statuts"
        # Reset dates to a sensible default or clear them
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-3)) # e.g., last 3 months
        self.date_to_edit.setDate(QDate.currentDate())
        self._apply_filters_and_reload()

    def _load_commandes_data(self):
        self.commandes_table.setRowCount(0)
        current_filters = self._get_current_filters()

        try:
            from app.db.cruds.invoices import commandes_crud # Corrected import
            total_commandes = commandes_crud.get_all_commandes_count(filters=current_filters)

            commandes_list = commandes_crud.get_all_commandes_with_details(
                filters=current_filters,
                limit=self.limit_per_page,
                offset=self.current_offset
            )
            if commandes_list is None: commandes_list = []

            self.total_commandes_label.setText(self.tr(f"Total Commandes Filtrées: {total_commandes}"))

            # Calculate total value from the *current page* of commandes for display simplicity
            # For a true "total value of filtered commandes", you'd sum across all pages (more complex query or fetch all)
            current_page_total_value = sum(cmd.get('total_ttc', 0.0) or 0.0 for cmd in commandes_list)
            self.total_commandes_value_label.setText(self.tr(f"Valeur Page Actuelle: {current_page_total_value:.2f} {commandes_list[0].get('currency', 'EUR') if commandes_list else 'EUR'}"))


            for row_idx, cmd_data in enumerate(commandes_list):
                self.commandes_table.insertRow(row_idx)

                ref_item = QTableWidgetItem(cmd_data.get("commande_reference", "N/A"))
                ref_item.setData(Qt.UserRole, cmd_data.get("commande_id"))
                self.commandes_table.setItem(row_idx, 0, ref_item)

                self.commandes_table.setItem(row_idx, 1, QTableWidgetItem(cmd_data.get("client_name", "N/A")))

                date_str = cmd_data.get("commande_date", "")
                date_formatted = datetime.fromisoformat(date_str.replace('Z','+00:00')).strftime('%Y-%m-%d %H:%M') if date_str else "N/A"
                self.commandes_table.setItem(row_idx, 2, QTableWidgetItem(date_formatted))

                status_item = QTableWidgetItem(cmd_data.get("status_commande_name", "N/A"))
                status_color_hex = cmd_data.get("status_commande_color")
                if status_color_hex:
                    try:
                        status_item.setForeground(QColor(status_color_hex))
                    except Exception as e_color: # Catch potential error if color_hex is invalid
                        self.logger.warning(f"Invalid status color '{status_color_hex}': {e_color}")
                self.commandes_table.setItem(row_idx, 3, status_item)

                total_ttc = cmd_data.get("total_ttc", 0.0) or 0.0
                currency = cmd_data.get("currency", "EUR")
                ttc_item = QTableWidgetItem(f"{total_ttc:.2f} {currency}")
                ttc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.commandes_table.setItem(row_idx, 4, ttc_item)

                self.commandes_table.setItem(row_idx, 5, QTableWidgetItem(cmd_data.get("project_name", self.tr("Aucun"))))

                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0,0,0,0); actions_layout.setSpacing(3)

                view_btn = QPushButton("✏️")
                view_btn.setToolTip(self.tr("Voir/Modifier Commande"))
                view_btn.clicked.connect(lambda ch, cid=cmd_data.get("commande_id"): self._handle_view_edit_commande(cid))
                actions_layout.addWidget(view_btn)

                client_id_for_action = cmd_data.get("client_id")
                client_btn = QPushButton("👤") # Fallback icon
                client_btn.setToolTip(self.tr("Aller à la Fiche Client"))
                client_btn.clicked.connect(lambda ch, cid=client_id_for_action: self._handle_go_to_client(cid))
                actions_layout.addWidget(client_btn)

                project_id_for_action = cmd_data.get("project_id")
                project_btn = QPushButton("📁") # Fallback icon
                project_btn.setToolTip(self.tr("Aller au Projet Associé"))
                if project_id_for_action:
                    project_btn.clicked.connect(lambda ch, pid=project_id_for_action: self._handle_go_to_project(pid))
                else:
                    project_btn.setEnabled(False)
                    project_btn.setToolTip(self.tr("Aucun projet directement associé à cette commande"))
                actions_layout.addWidget(project_btn)

                actions_layout.addStretch()
                self.commandes_table.setCellWidget(row_idx, 6, actions_widget)

            self._update_pagination_controls(total_commandes)

        except Exception as e:
            self.logger.error(f"Erreur chargement des données commandes: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Données", f"Impossible de charger les commandes: {e}")

    def _update_pagination_controls(self, total_items):
        current_page = (self.current_offset // self.limit_per_page) + 1
        total_pages = (total_items + self.limit_per_page - 1) // self.limit_per_page
        total_pages = max(1, total_pages) # Ensure total_pages is at least 1

        self.page_info_label.setText(self.tr(f"Page {current_page}/{total_pages} ({total_items} commandes)"))
        self.prev_page_btn.setEnabled(self.current_offset > 0)
        self.next_page_btn.setEnabled((self.current_offset + self.limit_per_page) < total_items)

    def _prev_page(self):
        if self.current_offset > 0:
            self.current_offset -= self.limit_per_page
            self._load_commandes_data()

    def _next_page(self):
        # Re-fetch total count based on current filters to ensure next button is correctly enabled/disabled
        current_filters = self._get_current_filters()
        from app.db.cruds.invoices import commandes_crud # Corrected import
        total_items = commandes_crud.get_all_commandes_count(filters=current_filters)

        if (self.current_offset + self.limit_per_page) < total_items:
            self.current_offset += self.limit_per_page
            self._load_commandes_data()
        else: # Should not happen if button is correctly disabled by _update_pagination_controls
            self.logger.info("Next page called but no more items.")


    def _handle_view_edit_commande(self, commande_id):
        if not commande_id: return
        self.logger.info(f"Request to view/edit commande ID: {commande_id}")
        try:
            from app.commande_management.commande_dialog import CommandeDialog

            # Determine app_root_dir. This is crucial if ProductDialog is called from CommandeDialog.
            app_root_dir_val = None
            parent_widget = self
            for _ in range(5): # Check up to 5 levels of parents
                if hasattr(parent_widget, 'app_root_dir'):
                    app_root_dir_val = parent_widget.app_root_dir
                    break
                if hasattr(parent_widget, 'parent') and callable(parent_widget.parent):
                    parent_widget = parent_widget.parent()
                    if parent_widget is None: break
                else: break

            if not app_root_dir_val: # Fallback if not found in parent chain
                 from app.app_setup import APP_ROOT_DIR as GLOBAL_APP_ROOT_DIR
                 app_root_dir_val = GLOBAL_APP_ROOT_DIR
                 self.logger.warning(f"app_root_dir not found in parent hierarchy for CommandesDashboard, using global APP_ROOT_DIR: {app_root_dir_val}")


            # Fetch client_id for the commande, as CommandeDialog constructor expects it.
            commande_data = commandes_crud.get_commande_by_id(commande_id) # This is a simplified version
            if not commande_data or not commande_data.get('client_id'):
                QMessageBox.critical(self, "Erreur", f"Impossible de récupérer l'ID client pour la commande {commande_id}.")
                return

            dialog = CommandeDialog(
                client_id=commande_data.get('client_id'),
                current_user_id=self.current_user_info.get('user_id') if self.current_user_info else None,
                commande_id_to_edit=commande_id,
                parent=self
            )
            # Pass app_root_dir to dialog if it needs it (e.g. if it instantiates ProductDialog)
            if hasattr(dialog, 'set_app_root_dir'): # Check if method exists
                dialog.set_app_root_dir(app_root_dir_val)
            elif hasattr(dialog, 'app_root_dir'): # Check if attribute exists
                dialog.app_root_dir = app_root_dir_val


            if dialog.exec_() == QDialog.Accepted:
                self._apply_filters_and_reload()
        except ImportError:
            self.logger.error("CommandeDialog could not be imported for editing.")
            QMessageBox.critical(self, "Erreur Module", "Impossible d'ouvrir le dialogue de commande.")
        except Exception as e:
            self.logger.error(f"Error opening CommandeDialog for edit: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la commande: {e}")


    def _load_initial_data(self):
        """Loads initial data like statuses for filters and the first set of commandes."""
        self.logger.info("Loading initial data for Commandes Dashboard...")
        self._populate_status_filter()
        self._apply_filters_and_reload() # Load initial commandes
        # pass # To be implemented

    def _handle_go_to_client(self, client_id):
        if not client_id:
            self.logger.warning("_handle_go_to_client called with no client_id.")
            return
        self.logger.info(f"Request to navigate to client ID: {client_id}")
        # Assuming parent is DocumentManager or can bubble up the request
        parent_navigator = self.parent()
        while parent_navigator:
            if hasattr(parent_navigator, 'open_client_tab_by_id'):
                parent_navigator.open_client_tab_by_id(client_id)
                # Also switch to the documents/client view stack if not already there
                if hasattr(parent_navigator, 'show_documents_view'):
                    parent_navigator.show_documents_view()
                return
            if hasattr(parent_navigator, 'parent') and callable(parent_navigator.parent):
                parent_navigator = parent_navigator.parent()
            else:
                break
        self.logger.error(f"Could not find a suitable parent method to navigate to client {client_id}.")
        QMessageBox.information(self, self.tr("Navigation"), self.tr("Impossible de naviguer vers la fiche client depuis ce contexte."))

    def _handle_go_to_project(self, project_id):
        if not project_id:
            self.logger.warning("_handle_go_to_project called with no project_id.")
            return
        self.logger.info(f"Request to navigate to project ID: {project_id}")
        # Assuming parent is DocumentManager or can bubble up the request
        parent_navigator = self.parent()
        while parent_navigator:
            if hasattr(parent_navigator, 'focus_on_project'): # DocumentManager should have this
                parent_navigator.focus_on_project(project_id) # This method will switch to PM Dashboard and focus
                return
            if hasattr(parent_navigator, 'parent') and callable(parent_navigator.parent):
                parent_navigator = parent_navigator.parent()
            else:
                break
        self.logger.error(f"Could not find a suitable parent method to navigate to project {project_id}.")
        QMessageBox.information(self, self.tr("Navigation"), self.tr("Impossible de naviguer vers le projet depuis ce contexte."))


    def tr(self, text):
        # Simple tr function for standalone testing, replace with proper context if integrated
        return QApplication.translate("CommandesDashboardWidget", text)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    # Mock user_info if your widget uses it
    mock_user = {"user_id": "test_user", "username": "Test User"}
    dashboard = CommandesDashboardWidget(current_user_info=mock_user)
    dashboard.show()
    sys.exit(app.exec_())
