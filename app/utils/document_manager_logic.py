# -*- coding: utf-8 -*-
import os
import shutil
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox, QDialog

from app.views.client_management.client_controller import ClientController
from app.db.cruds.misc.locations_crud import get_country_by_id, get_city_by_id
from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name, get_status_setting_by_id
from app.db.cruds.clients import clients_crud
from app.db.cruds.projects import projects_crud
from app.db.cruds.misc import activity_logs_crud
from app.views.gui.dialogs.edit_client_dialog import EditClientDialog
from .app_utils import sanitize_foldername
import logging

# Note: This entire file's functions are helpers for DocumentManager (main_window.py).
# They are not session-managed themselves but expect a db_session to be passed in
# from the calling method in DocumentManager.

def handle_create_client_execution(doc_manager, db_session, client_data_dict=None):
    # This function is complex and calls other controllers/dialogs.
    # The session passed here should be used for direct DB calls within this function's scope.
    # Sub-dialogs or controllers called from here should manage their own sessions.
    client_controller = ClientController() # This controller will manage its own sessions.

    if not client_data_dict:
        QMessageBox.critical(doc_manager, "Erreur", "Données client non fournies.")
        return

    # ... (validation logic remains the same) ...

    # --- Client Creation via Controller ---
    # The controller handles its own session management, so we don't pass the session here.
    created_client_info = client_controller.create_client(client_data_dict)

    if not created_client_info or not created_client_info.get("client_id"):
        # ... (error handling) ...
        return

    actual_new_client_id = created_client_info.get("client_id")
    # ... (folder creation logic) ...
    try:
        # ...
        clients_crud.update_client(db_session, actual_new_client_id, {'default_base_folder_path': base_folder_full_path})
        # ...
    except Exception as e:
        # Rollback would require a session, but the client was created in a separate session
        # by the controller. This highlights a need for a more transactional approach in the future.
        # For now, we log the error.
        logging.error(f"Failed to update client folder path, but client {actual_new_client_id} was already created.")

    # --- Project and Task Creation ---
    try:
        project_status = get_status_setting_by_name(db_session, "Planning", "Project")
        project_data = { 'client_id': actual_new_client_id, 'status_id': project_status.get('status_id') if project_status else None, ... }
        new_project_id = projects_crud.add_project(db_session, project_data)
        if new_project_id:
            # ...
            task_status = get_status_setting_by_name(db_session, "To Do", "Task")
            # ... loop and add tasks ...
            # projects_crud.add_task(db_session, task_data)
            # ...
    except Exception as e:
        logging.error(f"Error creating project/tasks for client {actual_new_client_id}: {e}", exc_info=True)

    # --- Final UI update ---
    # ...
    # This part should also use the passed-in session for augmenting data
    country_obj = get_country_by_id(db_session, ...)
    city_obj = get_city_by_id(db_session, ...)
    status_obj = get_status_setting_by_id(db_session, ...)
    # ...

def load_and_display_clients(doc_manager, db_session, filters: dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False):
    doc_manager.clients_data_map.clear()
    doc_manager.client_list_widget.clear()
    try:
        all_clients_dicts = clients_crud.get_all_clients_with_details(
            db_session, filters=filters, limit=limit, offset=offset, include_deleted=include_deleted
        )
        for client_data in all_clients_dicts:
            country_name = "N/A"
            if client_data.get('country_id'):
                country_obj = get_country_by_id(db_session, client_data['country_id'])
                if country_obj: country_name = country_obj['country_name']

            # ... (similar logic for city and status) ...

            adapted_client_dict = { ... } # build dict
            doc_manager.clients_data_map[adapted_client_dict["client_id"]] = adapted_client_dict
            doc_manager.add_client_to_list_widget(adapted_client_dict)
    except Exception as e:
        QMessageBox.critical(doc_manager, "Erreur DB", f"Erreur de chargement des clients:\n{e}")

def perform_old_clients_check(doc_manager, db_session):
    try:
        reminder_days = doc_manager.config.get("default_reminder_days", 30)
        status_archived = get_status_setting_by_name(db_session, 'Archivé', 'Client')
        # ...
        all_clients = clients_crud.get_all_clients(db_session, include_deleted=False)
        # ... (rest of the logic) ...
        if reply == QMessageBox.Yes:
            for c_info in old_clients_to_notify:
                archive_client_status(doc_manager, db_session, c_info['client_id']) # Pass session
    except Exception as e:
        logging.error(f"Erreur vérification clients anciens: {e}", exc_info=True)

def handle_open_edit_client_dialog(doc_manager, db_session, client_id):
    # ...
    dialog = EditClientDialog(...)
    if dialog.exec_() == QDialog.Accepted:
        # ...
        update_result = clients_crud.update_client(db_session, client_id, data_for_db_update)
        # ...
    # ...

def archive_client_status(doc_manager, db_session, client_id):
    try:
        status_archived_obj = get_status_setting_by_name(db_session, 'Archivé', 'Client')
        # ...
        update_result = clients_crud.update_client(db_session, client_id, update_data)
        # ...
        activity_logs_crud.add_activity_log(db_session, log_data)
        # ...
    except Exception as e:
        # ... (error handling)

def permanently_delete_client(doc_manager, db_session, client_id):
    # ...
    if reply == QMessageBox.Yes:
        try:
            # Note: This function in CRUD should handle all related deletions (cascade)
            # or they must be handled here explicitly within the same session.
            delete_result = clients_crud.hard_delete_client(db_session, client_id)
            if delete_result['success']:
                # ... (UI updates) ...
            else:
                # ... (error handling) ...
        except Exception as e:
            # ...

def create_final_invoice_and_update_db(db_session, client_id: str, ...):
    # This function is now also expected to be called with a session
    # ...
    try:
        client_data = clients_crud.get_client_by_id(db_session, client_id)
        # ...
        new_client_doc_id = client_documents_crud.add_client_document(db_session, client_doc_data)
        # ...
        new_invoice_id = invoices_crud.add_invoice(db_session, invoice_table_data)
        # ...
        return True, new_invoice_id, new_client_doc_id
    except Exception as e:
        # ...
        return False, None, None

# filter_and_display_clients does not need a session as it operates on the in-memory doc_manager.clients_data_map
def filter_and_display_clients(doc_manager):
    # ... (no changes needed)
    pass
