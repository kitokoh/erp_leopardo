# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTabWidget, QAbstractItemView, QHeaderView, QMessageBox, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
# Dialogs will be accessed via self.section_widget.main_widget
# from ..dialogs import AssignPersonnelDialog, AssignTransporterDialog, AssignFreightForwarderDialog, AssignMoneyTransferAgentDialog
# from carrier_email_dialog import CarrierEmailDialog
import db.cruds.projects_crud as projects_crud
import db.cruds.client_order_money_transfer_agents_crud as coma_crud


class ClientAssignmentsInternalTab(QWidget):
    def __init__(self, client_info, section_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.section_widget = section_widget # Parent ClientInfoSection
        self.main_widget = section_widget.main_widget # Grandparent ClientMainWidget

        self.default_company_id = self.main_widget.default_company_id
        self.AssignPersonnelDialog = self.main_widget.AssignPersonnelDialog
        self.AssignTransporterDialog = self.main_widget.AssignTransporterDialog
        self.AssignFreightForwarderDialog = self.main_widget.AssignFreightForwarderDialog
        self.AssignMoneyTransferAgentDialog = self.main_widget.AssignMoneyTransferAgentDialog
        self.CarrierEmailDialog = self.main_widget.CarrierEmailDialog
        self.SendEmailDialog = self.main_widget.SendEmailDialog
        self.config = self.main_widget.config


        self._setup_ui()
        self.load_all_assignments()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.assignments_sub_tabs = QTabWidget()
        layout.addWidget(self.assignments_sub_tabs)

        self._setup_vendors_personnel_sub_tab()
        self._setup_technicians_sub_tab()
        self._setup_transporters_sub_tab()
        self._setup_forwarders_sub_tab()
        self._setup_mta_sub_tab()

        # Connect signals for button states
        self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
        self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
        self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
        self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)
        self.mta_project_selector_combo.currentIndexChanged.connect(self.handle_mta_project_selection_changed)
        self.assigned_mta_table.itemSelectionChanged.connect(self.update_mta_buttons_state)

    def _setup_vendors_personnel_sub_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.assigned_vendors_table = QTableWidget(); self.assigned_vendors_table.setColumnCount(4)
        self.assigned_vendors_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
        self.assigned_vendors_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_vendors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_vendors_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.assigned_vendors_table)
        buttons_layout = QHBoxLayout()
        self.add_assigned_vendor_btn = QPushButton(self.tr("Ajouter Vendeur/Personnel")); self.add_assigned_vendor_btn.clicked.connect(self.handle_add_assigned_vendor)
        self.remove_assigned_vendor_btn = QPushButton(self.tr("Retirer Vendeur/Personnel")); self.remove_assigned_vendor_btn.clicked.connect(self.handle_remove_assigned_vendor)
        buttons_layout.addWidget(self.add_assigned_vendor_btn); buttons_layout.addWidget(self.remove_assigned_vendor_btn)
        layout.addLayout(buttons_layout)
        self.assignments_sub_tabs.addTab(widget, self.tr("Vendeurs & Personnel"))

    def _setup_technicians_sub_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.assigned_technicians_table = QTableWidget(); self.assigned_technicians_table.setColumnCount(4)
        self.assigned_technicians_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
        # ... (set table properties)
        layout.addWidget(self.assigned_technicians_table)
        buttons_layout = QHBoxLayout()
        self.add_assigned_technician_btn = QPushButton(self.tr("Ajouter Technicien")); self.add_assigned_technician_btn.clicked.connect(self.handle_add_assigned_technician)
        self.remove_assigned_technician_btn = QPushButton(self.tr("Retirer Technicien")); self.remove_assigned_technician_btn.clicked.connect(self.handle_remove_assigned_technician)
        buttons_layout.addWidget(self.add_assigned_technician_btn); buttons_layout.addWidget(self.remove_assigned_technician_btn)
        layout.addLayout(buttons_layout)
        self.assignments_sub_tabs.addTab(widget, self.tr("Techniciens"))

    def _setup_transporters_sub_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.assigned_transporters_table = QTableWidget(); self.assigned_transporters_table.setColumnCount(6)
        self.assigned_transporters_table.setHorizontalHeaderLabels([self.tr("Nom Transporteur"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Détails Transport"), self.tr("Coût Estimé"), self.tr("Actions")])
        # ... (set table properties)
        layout.addWidget(self.assigned_transporters_table)
        buttons_layout = QHBoxLayout()
        self.add_assigned_transporter_btn = QPushButton(self.tr("Ajouter Transporteur")); self.add_assigned_transporter_btn.clicked.connect(self.handle_add_assigned_transporter)
        self.remove_assigned_transporter_btn = QPushButton(self.tr("Retirer Transporteur")); self.remove_assigned_transporter_btn.clicked.connect(self.handle_remove_assigned_transporter)
        buttons_layout.addWidget(self.add_assigned_transporter_btn); buttons_layout.addWidget(self.remove_assigned_transporter_btn)
        layout.addLayout(buttons_layout)
        self.assignments_sub_tabs.addTab(widget, self.tr("Transporteurs"))

    def _setup_forwarders_sub_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.assigned_forwarders_table = QTableWidget(); self.assigned_forwarders_table.setColumnCount(5)
        self.assigned_forwarders_table.setHorizontalHeaderLabels([self.tr("Nom Transitaire"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Description Tâche"), self.tr("Coût Estimé")])
        # ... (set table properties)
        layout.addWidget(self.assigned_forwarders_table)
        buttons_layout = QHBoxLayout()
        self.add_assigned_forwarder_btn = QPushButton(self.tr("Ajouter Transitaire")); self.add_assigned_forwarder_btn.clicked.connect(self.handle_add_assigned_forwarder)
        self.remove_assigned_forwarder_btn = QPushButton(self.tr("Retirer Transitaire")); self.remove_assigned_forwarder_btn.clicked.connect(self.handle_remove_assigned_forwarder)
        buttons_layout.addWidget(self.add_assigned_forwarder_btn); buttons_layout.addWidget(self.remove_assigned_forwarder_btn)
        layout.addLayout(buttons_layout)
        self.assignments_sub_tabs.addTab(widget, self.tr("Transitaires"))

    def _setup_mta_sub_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        project_selector_layout = QHBoxLayout()
        project_selector_layout.addWidget(QLabel(self.tr("Sélectionner Commande/Projet:")))
        self.mta_project_selector_combo = QComboBox()
        project_selector_layout.addWidget(self.mta_project_selector_combo)
        layout.addLayout(project_selector_layout)
        self.assigned_mta_table = QTableWidget(); self.assigned_mta_table.setColumnCount(8)
        self.assigned_mta_table.setHorizontalHeaderLabels([
            self.tr("Nom Agent"), self.tr("Type"), self.tr("Email"), self.tr("Téléphone"),
            self.tr("Détails Affectation"), self.tr("Frais Estimés"), self.tr("Statut Email"), self.tr("Actions")])
        # ... (set table properties)
        self.assigned_mta_table.setMinimumHeight(150)
        layout.addWidget(self.assigned_mta_table)
        buttons_layout = QHBoxLayout()
        self.add_assigned_mta_btn = QPushButton(self.tr("Assigner Agent de Transfert")); self.add_assigned_mta_btn.clicked.connect(self.handle_add_assigned_mta)
        self.remove_assigned_mta_btn = QPushButton(self.tr("Retirer Agent de Transfert")); self.remove_assigned_mta_btn.clicked.connect(self.handle_remove_assigned_mta)
        buttons_layout.addWidget(self.add_assigned_mta_btn); buttons_layout.addWidget(self.remove_assigned_mta_btn)
        layout.addLayout(buttons_layout)
        self.assignments_sub_tabs.addTab(widget, self.tr("Agents de Transfert d'Argent"))

        self.load_projects_for_mta_combo() # Initial population
        self.add_assigned_mta_btn.setEnabled(False) # Initial state
        self.remove_assigned_mta_btn.setEnabled(False)


    def load_all_assignments(self):
        self.load_assigned_vendors_personnel()
        self.load_assigned_technicians()
        self.load_assigned_transporters()
        self.load_assigned_freight_forwarders()
        self.handle_mta_project_selection_changed() # This will load MTA if a project is selected

    # Methods for Vendors/Personnel (example, others similar)
    def load_assigned_vendors_personnel(self):
        self.assigned_vendors_table.setRowCount(0)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter=None) or []
            for row, item_data in enumerate(assigned_list):
                self.assigned_vendors_table.insertRow(row)
                name_item = QTableWidgetItem(item_data.get('personnel_name'))
                name_item.setData(Qt.UserRole, item_data.get('assignment_id'))
                self.assigned_vendors_table.setItem(row, 0, name_item)
                self.assigned_vendors_table.setItem(row, 1, QTableWidgetItem(item_data.get('role_in_project')))
                self.assigned_vendors_table.setItem(row, 2, QTableWidgetItem(item_data.get('personnel_email')))
                self.assigned_vendors_table.setItem(row, 3, QTableWidgetItem(item_data.get('personnel_phone')))
        except Exception as e:
            logging.error(f"Error loading vendors/personnel: {e}", exc_info=True)
        self.update_assigned_vendors_buttons_state()

    def handle_add_assigned_vendor(self):
        if not self.default_company_id or not self.AssignPersonnelDialog: return
        dialog = self.AssignPersonnelDialog(client_id=self.client_info['client_id'], role_filter=None, company_id=self.default_company_id, parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_assigned_vendors_personnel()

    def handle_remove_assigned_vendor(self):
        selected = self.assigned_vendors_table.selectedItems()
        if not selected: return
        assignment_id = selected[0].data(Qt.UserRole)
        if assignment_id is None: return
        if QMessageBox.question(self, self.tr("Confirmer"), self.tr("Retirer ce membre?"), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if db_manager.unassign_personnel_from_client(assignment_id): self.load_assigned_vendors_personnel()
            else: QMessageBox.warning(self, self.tr("Erreur"), self.tr("Échec retrait."))

    def update_assigned_vendors_buttons_state(self):
        self.remove_assigned_vendor_btn.setEnabled(bool(self.assigned_vendors_table.selectedItems()))

    # Implement similar load_*, handle_add_*, handle_remove_*, update_*_buttons_state for other assignment types
    def load_assigned_technicians(self):
        self.assigned_technicians_table.setRowCount(0)
        # ... similar to load_assigned_vendors_personnel but with role_filter="Technicien" or similar
        self.update_assigned_technicians_buttons_state()
    def handle_add_assigned_technician(self): pass
    def handle_remove_assigned_technician(self): pass
    def update_assigned_technicians_buttons_state(self):
         if hasattr(self, 'remove_assigned_technician_btn'):
            self.remove_assigned_technician_btn.setEnabled(bool(self.assigned_technicians_table.selectedItems()))

    def load_assigned_transporters(self):
        self.assigned_transporters_table.setRowCount(0)
        # ...
        self.update_assigned_transporters_buttons_state()
    def handle_add_assigned_transporter(self): pass
    def handle_remove_assigned_transporter(self): pass
    def update_assigned_transporters_buttons_state(self):
        if hasattr(self, 'remove_assigned_transporter_btn'):
            self.remove_assigned_transporter_btn.setEnabled(bool(self.assigned_transporters_table.selectedItems()))

    def load_assigned_freight_forwarders(self):
        self.assigned_forwarders_table.setRowCount(0)
        # ...
        self.update_assigned_forwarders_buttons_state()
    def handle_add_assigned_forwarder(self): pass
    def handle_remove_assigned_forwarder(self): pass
    def update_assigned_forwarders_buttons_state(self):
        if hasattr(self, 'remove_assigned_forwarder_btn'):
            self.remove_assigned_forwarder_btn.setEnabled(bool(self.assigned_forwarders_table.selectedItems()))

    # MTA Methods
    def load_projects_for_mta_combo(self):
        self.mta_project_selector_combo.blockSignals(True)
        self.mta_project_selector_combo.clear()
        self.mta_project_selector_combo.addItem(self.tr("--- Sélectionner Commande/Projet ---"), None)
        client_id = self.client_info.get('client_id')
        if not client_id: self.mta_project_selector_combo.blockSignals(False); return
        try:
            projects = projects_crud.get_projects_by_client_id(client_id=client_id) or []
            for p in projects: self.mta_project_selector_combo.addItem(p.get('project_name'), p.get('project_id'))
        except Exception as e: logging.error(f"Error loading projects for MTA: {e}", exc_info=True)
        finally: self.mta_project_selector_combo.blockSignals(False); self.handle_mta_project_selection_changed()

    def handle_mta_project_selection_changed(self):
        project_id = self.mta_project_selector_combo.currentData()
        self.add_assigned_mta_btn.setEnabled(bool(project_id))
        if project_id: self.load_assigned_money_transfer_agents()
        else: self.assigned_mta_table.setRowCount(0); self.remove_assigned_mta_btn.setEnabled(False)

    def load_assigned_money_transfer_agents(self):
        self.assigned_mta_table.setRowCount(0)
        project_id = self.mta_project_selector_combo.currentData()
        client_id = self.client_info.get('client_id')
        if not project_id or not client_id: self.update_mta_buttons_state(); return
        try:
            agents = coma_crud.get_assigned_agents_for_client_order(client_id, project_id) or []
            for row, agent in enumerate(agents):
                self.assigned_mta_table.insertRow(row)
                # ... populate row ...
        except Exception as e: logging.error(f"Error loading MTAs: {e}", exc_info=True)
        self.update_mta_buttons_state()

    def handle_add_assigned_mta(self): pass
    def handle_remove_assigned_mta(self): pass
    def handle_email_money_transfer_agent(self, assignment_id, agent_email): pass
    def update_mta_buttons_state(self):
        if hasattr(self, 'remove_assigned_mta_btn'):
            self.remove_assigned_mta_btn.setEnabled(bool(self.assigned_mta_table.selectedItems()))

    def tr(self, text, disambiguation=None, n=-1):
        if hasattr(self.main_widget, 'tr'):
            return self.main_widget.tr(text, disambiguation, n)
        from PyQt5.QtWidgets import QApplication
        return QApplication.translate("ClientAssignmentsInternalTab", text, disambiguation, n)
