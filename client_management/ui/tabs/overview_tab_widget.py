# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class OverviewTabWidget(QWidget):
    def __init__(self, client_info, parent_client_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.parent_client_widget = parent_client_widget # To call methods like _handle_overview_new_order

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self._setup_ui()

from PyQt5.QtGui import QIcon # Added import
import db # Assuming db_manager is aliased as db in the original context
from datetime import datetime # Added import

class OverviewTabWidget(QWidget):
    def __init__(self, client_info, parent_client_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.parent_client_widget = parent_client_widget

        # Direct access to tr method from parent_client_widget if needed, or pass translator
        self.tr = self.parent_client_widget.tr if hasattr(self.parent_client_widget, 'tr') else lambda x: x

        self.layout = QVBoxLayout(self) # Main layout for this tab
        self.layout.setAlignment(Qt.AlignTop)
        self._setup_ui()
        self.refresh_overview_data() # Initial data load

    def _setup_ui(self):
        # ---- Client Header Section for Overview Tab ----
        header_group = QGroupBox(self.tr("Informations Clés du Client"))
        header_group.setObjectName("overviewHeaderGroup")
        header_form_layout = QFormLayout(header_group)

        self.overview_client_name_label = QLabel(f"<b>{self.client_info.get('client_name', 'N/A')}</b>")
        self.overview_client_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header_form_layout.addRow(self.tr("Nom du Client:"), self.overview_client_name_label)

        self.overview_company_name_label = QLabel(self.client_info.get('company_name', 'N/A') or self.tr("N/A"))
        self.overview_company_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header_form_layout.addRow(self.tr("Société:"), self.overview_company_name_label)

        self.overview_category_label = QLabel(self.client_info.get('category', 'N/A'))
        self.overview_category_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header_form_layout.addRow(self.tr("Catégorie:"), self.overview_category_label)

        self.overview_status_label = QLabel(self.client_info.get('status', 'N/A'))
        self.overview_status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # Status color will be applied in _update_header_labels
        header_form_layout.addRow(self.tr("Statut Client:"), self.overview_status_label)

        self.layout.addWidget(header_group)

        # ---- Key Metrics Section for Overview Tab ----
        metrics_group = QGroupBox(self.tr("Indicateurs Clés"))
        metrics_group.setObjectName("overviewMetricsGroup")
        metrics_form_layout = QFormLayout(metrics_group)

        self.overview_active_projects_label = QLabel(self.tr("Chargement..."))
        metrics_form_layout.addRow(self.tr("Projets Actifs:"), self.overview_active_projects_label)

        self.overview_open_orders_label = QLabel(self.tr("Chargement..."))
        metrics_form_layout.addRow(self.tr("Commandes Ouvertes:"), self.overview_open_orders_label)

        self.overview_last_activity_label = QLabel(self.tr("N/A")) # Will be populated by _update_header_labels
        metrics_form_layout.addRow(self.tr("Dernière Mise à Jour Client:"), self.overview_last_activity_label)

        self.layout.addWidget(metrics_group)

        # ---- Quick Actions Section for Overview Tab ----
        quick_actions_group = QGroupBox(self.tr("Actions Rapides"))
        quick_actions_group.setObjectName("overviewQuickActionsGroup")
        quick_actions_layout = QHBoxLayout(quick_actions_group)

        self.overview_new_order_btn = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Nouvelle Commande"))
        self.overview_new_order_btn.clicked.connect(self.parent_client_widget._handle_overview_new_order)
        quick_actions_layout.addWidget(self.overview_new_order_btn)

        self.overview_new_project_btn = QPushButton(QIcon(":/icons/folder-add.svg"), self.tr("Nouveau Projet"))
        self.overview_new_project_btn.clicked.connect(self.parent_client_widget._handle_overview_new_project)
        quick_actions_layout.addWidget(self.overview_new_project_btn)

        self.overview_add_contact_btn = QPushButton(QIcon(":/icons/user-plus.svg"), self.tr("Ajouter Contact"))
        self.overview_add_contact_btn.clicked.connect(self.parent_client_widget.add_contact)
        quick_actions_layout.addWidget(self.overview_add_contact_btn)

        self.overview_generate_doc_btn = QPushButton(QIcon(":/icons/file-plus.svg"), self.tr("Générer Document"))
        self.overview_generate_doc_btn.clicked.connect(self.parent_client_widget._handle_overview_generate_document)
        quick_actions_layout.addWidget(self.overview_generate_doc_btn)

        quick_actions_layout.addStretch()
        self.layout.addWidget(quick_actions_group)

        # ---- Open Projects Snippet Section ----
        self.overview_projects_group = QGroupBox(self.tr("Projets Récents/Actifs"))
        self.overview_projects_group.setObjectName("overviewProjectsGroup")
        self.overview_projects_layout = QVBoxLayout(self.overview_projects_group)
        self.overview_projects_layout.setSpacing(5)
        self.overview_no_projects_label = QLabel(self.tr("Aucun projet actif à afficher."))
        self.overview_no_projects_label.setAlignment(Qt.AlignCenter)
        self.overview_projects_layout.addWidget(self.overview_no_projects_label)
        self.layout.addWidget(self.overview_projects_group)

        # ---- Recent Orders Snippet Section ----
        self.overview_orders_group = QGroupBox(self.tr("Commandes Récentes/Ouvertes"))
        self.overview_orders_group.setObjectName("overviewOrdersGroup")
        self.overview_orders_layout = QVBoxLayout(self.overview_orders_group)
        self.overview_orders_layout.setSpacing(5)
        self.overview_no_orders_label = QLabel(self.tr("Aucune commande récente/ouverte à afficher."))
        self.overview_no_orders_label.setAlignment(Qt.AlignCenter)
        self.overview_orders_layout.addWidget(self.overview_no_orders_label)
        self.layout.addWidget(self.overview_orders_group)

        # ---- Recent Activity Snippet Section ----
        self.overview_activity_group = QGroupBox(self.tr("Activité Récente"))
        self.overview_activity_group.setObjectName("overviewActivityGroup")
        self.overview_activity_layout = QVBoxLayout(self.overview_activity_group)
        self.overview_activity_layout.setSpacing(3)
        self.overview_no_activity_label = QLabel(self.tr("Aucune activité récente à afficher pour ce client."))
        self.overview_no_activity_label.setAlignment(Qt.AlignCenter)
        self.overview_activity_layout.addWidget(self.overview_no_activity_label)
        self.layout.addWidget(self.overview_activity_group)

    def update_client_info(self, new_client_info):
        """Updates the internal client_info and refreshes the display."""
        self.client_info = new_client_info
        self.refresh_overview_data()

    def _update_header_labels(self):
        """Updates the header labels with current client_info."""
        if not hasattr(self, 'overview_client_name_label'): return

        self.overview_client_name_label.setText(f"<b>{self.client_info.get('client_name', 'N/A')}</b>")
        self.overview_company_name_label.setText(self.client_info.get('company_name', 'N/A') or self.tr("N/A"))
        self.overview_category_label.setText(self.client_info.get('category', 'N/A'))

        status_text = self.client_info.get('status', 'N/A')
        self.overview_status_label.setText(status_text)
        status_id = self.client_info.get('status_id')
        status_color = "black"
        if status_id:
            # Assuming db_manager is accessible via parent_client_widget or passed differently
            status_setting = self.parent_client_widget.db_manager.get_status_setting_by_id(status_id)
            if status_setting and status_setting.get('color_hex'):
                status_color = status_setting.get('color_hex')
        self.overview_status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")

        last_update_raw = self.client_info.get('updated_at', self.client_info.get('creation_date', ''))
        last_update_display = self.tr("N/A")
        if last_update_raw:
            try:
                dt_obj = datetime.fromisoformat(last_update_raw.replace('Z', '+00:00'))
                last_update_display = dt_obj.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                last_update_display = last_update_raw
        if hasattr(self, 'overview_last_activity_label'):
            self.overview_last_activity_label.setText(last_update_display)

    def _load_metrics_and_snippets(self):
        """Loads key metrics and populates snippet sections."""
        client_id = self.client_info.get("client_id")
        if not client_id:
            self.overview_active_projects_label.setText(self.tr("N/A"))
            self.overview_open_orders_label.setText(self.tr("N/A"))
            # Clear snippets
            self._clear_layout(self.overview_projects_layout, self.overview_no_projects_label)
            self._clear_layout(self.overview_orders_layout, self.overview_no_orders_label)
            self._clear_layout(self.overview_activity_layout, self.overview_no_activity_label)
            self.overview_no_projects_label.setVisible(True)
            self.overview_no_orders_label.setVisible(True)
            self.overview_no_activity_label.setVisible(True)
            return

        # Access db_manager and projects_crud via parent_client_widget
        db_m = self.parent_client_widget.db_manager
        proj_crud = self.parent_client_widget.projects_crud # Assuming projects_crud is an attribute of ClientWidget

        # Active Projects Count
        try:
            all_projects = proj_crud.get_projects_by_client_id(client_id)
            active_project_count = 0
            if all_projects:
                project_statuses_settings = db_m.get_all_status_settings(type_filter='Project')
                active_status_ids = {s['status_id'] for s in project_statuses_settings if not s.get('is_completion_status') and not s.get('is_archival_status')}
                for project in all_projects:
                    if project.get('status_id') in active_status_ids:
                        active_project_count += 1
            self.overview_active_projects_label.setText(str(active_project_count))
        except Exception as e:
            # Consider logging via parent_client_widget's logger if it has one
            print(f"Error loading active projects for overview: {e}") # Simplified logging
            self.overview_active_projects_label.setText(self.tr("Erreur"))

        # Open Orders Count
        try:
            all_commandes = db_m.get_commandes_for_client(client_id)
            open_order_count = 0
            if all_commandes:
                commande_statuses_settings = db_m.get_all_status_settings(type_filter='Commande')
                open_status_ids = {s['status_id'] for s in commande_statuses_settings if not s.get('is_completion_status') and not s.get('is_archival_status')}
                for commande in all_commandes:
                    if commande.get('status_commande_id') in open_status_ids:
                        open_order_count += 1
            self.overview_open_orders_label.setText(str(open_order_count))
        except Exception as e:
            print(f"Error loading open orders for overview: {e}")
            self.overview_open_orders_label.setText(self.tr("Erreur"))

        self._populate_projects_snippet(client_id, proj_crud, db_m)
        self._populate_orders_snippet(client_id, db_m)
        self._populate_activity_snippet(client_id, db_m)


    def _clear_layout(self, layout, placeholder_label=None):
        """Clears all widgets from a layout, optionally keeping a placeholder."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget and widget != placeholder_label:
                widget.setParent(None)
                widget.deleteLater()
        if placeholder_label: # Ensure placeholder is visible after clearing
            placeholder_label.setVisible(True)
            if layout.indexOf(placeholder_label) == -1: # Add if not already there (e.g. first clear)
                 layout.addWidget(placeholder_label)


    def _populate_projects_snippet(self, client_id, proj_crud, db_m):
        self._clear_layout(self.overview_projects_layout, self.overview_no_projects_label)
        try:
            all_projects = proj_crud.get_projects_by_client_id(client_id)
            active_projects_list = []
            if all_projects:
                project_statuses_settings = db_m.get_all_status_settings(type_filter='Project')
                active_status_ids = {s['status_id'] for s in project_statuses_settings if not s.get('is_completion_status') and not s.get('is_archival_status')}
                for project in all_projects:
                    if project.get('status_id') in active_status_ids:
                        # Resolve status name and color
                        status_name = self.tr("Inconnu")
                        status_color = "grey"
                        for s_set in project_statuses_settings:
                            if s_set['status_id'] == project.get('status_id'):
                                status_name = s_set.get('status_name', status_name)
                                status_color = s_set.get('color_hex', status_color)
                                break
                        project['status_name_resolved'] = status_name
                        project['status_color_resolved'] = status_color
                        active_projects_list.append(project)

            active_projects_list.sort(key=lambda p: p.get('created_at', ''), reverse=True)
            projects_to_display = active_projects_list[:3]

            if projects_to_display:
                self.overview_no_projects_label.setVisible(False)
                for project_data in projects_to_display:
                    # ... (Create project_widget as in ClientWidget._load_overview_metrics)
                    # Connect name_label.linkActivated to self._handle_project_snippet_clicked
                    # Example for one widget:
                    project_widget = QWidget()
                    project_layout = QHBoxLayout(project_widget)
                    project_layout.setContentsMargins(0,0,0,0)
                    name_label = QLabel(f"<a href='{project_data.get('project_id')}'>{project_data.get('project_name', self.tr('Projet Sans Nom'))}</a>")
                    name_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                    name_label.linkActivated.connect(lambda link, p_id=project_data.get('project_id'): self._handle_project_snippet_clicked(p_id))
                    # ... add status_label, deadline_display_label to project_layout ...
                    status_label = QLabel(project_data.get('status_name_resolved', self.tr('Statut Inconnu')))
                    status_label.setStyleSheet(f"color: {project_data.get('status_color_resolved', 'grey')}; font-weight: bold; padding: 2px 5px; background-color: #f0f0f0; border-radius: 3px;")
                    project_layout.addWidget(name_label, 1)
                    project_layout.addWidget(status_label)
                    # ... (add more details like deadline)
                    project_layout.addStretch(0)
                    self.overview_projects_layout.addWidget(project_widget)
            else:
                self.overview_no_projects_label.setVisible(True)
        except Exception as e:
            print(f"Error populating projects snippet: {e}")
            self.overview_no_projects_label.setText(self.tr("Erreur chargement projets."))
            self.overview_no_projects_label.setVisible(True)

    def _populate_orders_snippet(self, client_id, db_m):
        self._clear_layout(self.overview_orders_layout, self.overview_no_orders_label)
        # ... (Similar logic to ClientWidget._load_overview_metrics for orders)
        # Connect ref_label.linkActivated to self._handle_order_snippet_clicked
        # ...
        pass # Placeholder for brevity

    def _populate_activity_snippet(self, client_id, db_m):
        self._clear_layout(self.overview_activity_layout, self.overview_no_activity_label)
        # ... (Similar logic to ClientWidget._load_overview_metrics for activity)
        # ...
        pass # Placeholder for brevity

    def _handle_project_snippet_clicked(self, project_id):
        # This will call a method on parent_client_widget to handle the navigation
        self.parent_client_widget._handle_project_snippet_clicked(project_id)

    def _handle_order_snippet_clicked(self, commande_id):
        # This will call a method on parent_client_widget to handle the navigation
        self.parent_client_widget._handle_order_snippet_clicked(commande_id)

    def refresh_overview_data(self):
        """Refreshes all dynamic content in the overview tab."""
        self._update_header_labels()
        self._load_metrics_and_snippets()
