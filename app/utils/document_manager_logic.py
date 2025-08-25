# -*- coding: utf-8 -*-
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox, QDialog, QInputDialog

from app.views.client_management.client_controller import ClientController
from app.controllers.contact_controller import ContactController
from app.db.cruds.misc.locations_crud import get_country_by_id, get_city_by_id
from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name, get_status_setting_by_id
from app.db.cruds.clients.clients_crud import clients_crud_instance
from app.db.cruds.projects.projects_crud import add_project, get_project_by_id, delete_project
from app.db.cruds.projects.tasks_crud import add_task
from app.db.cruds.misc.contacts_crud import get_contact_by_email, add_contact, update_contact, link_contact_to_client, get_contacts_for_client, update_client_contact_link
from app.db.cruds.products.products_crud import products_crud_instance
from app.db.cruds.clients.client_project_products_crud import add_product_to_client_or_project, get_products_for_client_or_project
from app.views.gui.dialogs import ContactDialog, ProductDialog, CreateDocumentDialog
from app.views.gui.dialogs.edit_client_dialog import EditClientDialog
from .app_utils import sanitize_foldername
import logging
from app.db.cruds.misc.activity_logs_crud import add_activity_log

def handle_create_client_execution(doc_manager, client_data_dict=None):
    if not client_data_dict:
        QMessageBox.critical(doc_manager, "Erreur", "Données client non fournies.")
        return

    client_name_val = client_data_dict.get("client_name", "").strip()
    country_name_for_folder = client_data_dict.get("country_name", "").strip()
    project_identifier_val = client_data_dict.get("project_identifier", "").strip()

    if not client_name_val or not country_name_for_folder or not project_identifier_val:
        QMessageBox.warning(doc_manager, doc_manager.tr("Champs Requis"), doc_manager.tr("Nom client, Pays et ID Projet sont obligatoires."))
        return

    db = None
    actual_new_client_id = None
    base_folder_full_path = None

    try:
        db = get_db_connection()
        client_controller = ClientController()
        contact_controller = ContactController(current_user_id=doc_manager.current_user_id)

        # --- Step 1: Create Client in DB ---
        client_data_dict_for_controller = client_data_dict.copy()
        client_data_dict_for_controller['created_by_user_id'] = doc_manager.current_user_id
        created_client_info = client_controller.create_client(db, client_data_dict_for_controller)

        if not created_client_info or not created_client_info.get("client_id"):
            error_msg = created_client_info.get("error", doc_manager.tr("Le contrôleur n'a pas pu créer le client."))
            raise Exception(error_msg)

        actual_new_client_id = created_client_info.get("client_id")
        logging.info(f"Client pre-committed to DB with ID: {actual_new_client_id}")

        # --- Step 2: Create Folder Structure ---
        client_name_sane = sanitize_foldername(client_name_val)
        country_name_sane = sanitize_foldername(country_name_for_folder)
        project_id_sane = sanitize_foldername(project_identifier_val)
        folder_name_str = f"{client_name_sane}_{country_name_sane}_{project_id_sane}"
        base_folder_full_path = os.path.join(doc_manager.config["clients_dir"], folder_name_str)

        if os.path.exists(base_folder_full_path):
             logging.warning(f"Client folder path {base_folder_full_path} already exists.")
             # Decide if this is a critical error or just a warning. For now, continue.

        os.makedirs(base_folder_full_path, exist_ok=True)
        clients_crud_instance.update_client(db, actual_new_client_id, {'default_base_folder_path': base_folder_full_path})
        created_client_info['default_base_folder_path'] = base_folder_full_path

        selected_langs_str = created_client_info.get("languages", "fr")
        selected_langs_list = selected_langs_str.split(',') if isinstance(selected_langs_str, str) else ["fr"]
        for lang_code in selected_langs_list:
            os.makedirs(os.path.join(base_folder_full_path, lang_code.strip()), exist_ok=True)

        # --- Step 3: Open Commande Dialog ---
        from app.views.gui.dialogs.commande_dialog import CommandeDialog
        commande_dialog = CommandeDialog(client_id=actual_new_client_id, current_user_id=doc_manager.current_user_id, parent=doc_manager)

        project_id_for_tasks = None
        if commande_dialog.exec_() == QDialog.Accepted:
            if hasattr(commande_dialog, 'get_created_project_id'):
                project_id_for_tasks = commande_dialog.get_created_project_id()
        else:
            logging.info(f"User cancelled initial CommandeDialog for client {actual_new_client_id}.")

        # --- Step 4: Create Default Project and Tasks if needed ---
        if not project_id_for_tasks:
            project_status_planning_obj = get_status_setting_by_name(db, "Planning", "Project")
            project_data_for_db_default = {
                'client_id': actual_new_client_id,
                'project_name': f"Projet Administratif pour {created_client_info.get('client_name', client_name_val)}",
                'description': f"Suivi administratif général pour client: {created_client_info.get('client_name', client_name_val)}.",
                'start_date': datetime.now().strftime("%Y-%m-%d"),
                'status_id': project_status_planning_obj['status_id'] if project_status_planning_obj else None, 'priority': 0
            }
            project_id_for_tasks = add_project(db, project_data_for_db_default)
            if not project_id_for_tasks:
                raise Exception("Failed to create default administrative project.")

        task_status_todo_obj = get_status_setting_by_name(db, "To Do", "Task")
        standard_tasks = [
            {"name": "Initial Client Consultation", "priority_val": 2, "deadline_days": 3},
            {"name": "Market Research", "priority_val": 1, "deadline_days": 7},
            {"name": "Post-Sales Follow-up", "priority_val": 1, "deadline_days": 60}
        ]
        for task_item in standard_tasks:
            task_data = {
                'project_id': project_id_for_tasks, 'task_name': task_item["name"],
                'description': task_item.get("description", ""), 'status_id': task_status_todo_obj['status_id'] if task_status_todo_obj else None,
                'priority': task_item["priority_val"], 'due_date': (datetime.now() + timedelta(days=task_item["deadline_days"])).strftime("%Y-%m-%d")
            }
            add_task(db, task_data)

        # --- Step 5: Handle Contact ---
        existing_contacts = get_contacts_for_client(db, actual_new_client_id, limit=1)
        contact_dialog = ContactDialog(parent=doc_manager, manage_link_fields=not existing_contacts)
        if contact_dialog.exec_() == QDialog.Accepted:
            contact_form_data = contact_dialog.get_contact_data()
            contact_controller.get_or_create_contact_and_link(db, client_id=actual_new_client_id, contact_form_data=contact_form_data)

        # --- Step 6: Commit Transaction ---
        db.commit()
        logging.info(f"Successfully committed all creation steps for client {actual_new_client_id}.")

    except Exception as e:
        if db: db.rollback()
        logging.error(f"Error during client creation transaction: {e}", exc_info=True)
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Création Client"), str(e))
        # Cleanup folder if client creation failed after folder was made
        if base_folder_full_path and os.path.exists(base_folder_full_path) and not actual_new_client_id:
            try:
                shutil.rmtree(base_folder_full_path)
                logging.info(f"Cleaned up created folder due to error: {base_folder_full_path}")
            except OSError as e_cleanup:
                logging.error(f"Failed to cleanup folder '{base_folder_full_path}': {e_cleanup}")
        return
    finally:
        if db:
            db.close()

    # --- Step 7: Post-Commit UI Updates ---
    if actual_new_client_id:
        doc_manager.notify(title=doc_manager.tr("Client Créé"),
                           message=doc_manager.tr("Le client '{0}' a été créé avec succès.").format(client_name_val),
                           type='SUCCESS')
        doc_manager.load_clients_from_db_slot() # Full refresh
        doc_manager.open_client_tab_by_id(actual_new_client_id)

        stats_dashboard = doc_manager.get_statistics_widget_instance()
        if stats_dashboard and hasattr(stats_dashboard, 'refresh_all_dashboard_content'):
            stats_dashboard.refresh_all_dashboard_content()


from sqlalchemy.orm import Session
from app.db.connection import get_db_connection

def load_and_display_clients(doc_manager, db: Session, filters: dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False):
    """
    Loads client data from the database and displays it in the UI.
    Now accepts a db session, filters, pagination, and include_deleted parameters.
    """
    doc_manager.clients_data_map.clear()
    doc_manager.client_list_widget.clear()
    try:
        all_clients_dicts = clients_crud_instance.get_all_clients_with_details(
            db=db,
            filters=filters,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted
        )

        for client_data in all_clients_dicts:
            country_name = "N/A"
            if client_data.get('country_id'):
                country_obj = get_country_by_id(db, client_data['country_id'])
                if country_obj: country_name = country_obj['country_name']
            city_name = "N/A"
            if client_data.get('city_id'):
                city_obj = get_city_by_id(db, client_data['city_id'])
                if city_obj: city_name = city_obj['city_name']
            status_name = "N/A"
            status_id_val = client_data.get('status_id')
            if status_id_val:
                status_obj = get_status_setting_by_id(db, status_id_val)
                if status_obj: status_name = status_obj['status_name']

            adapted_client_dict = {
                "client_id": client_data.get('client_id'), "client_name": client_data.get('client_name'),
                "company_name": client_data.get('company_name'), "need": client_data.get('primary_need_description'),
                "country": country_name, "country_id": client_data.get('country_id'),
                "city": city_name, "city_id": client_data.get('city_id'),
                "project_identifier": client_data.get('project_identifier'), "base_folder_path": client_data.get('default_base_folder_path'),
                "selected_languages": client_data.get('selected_languages', '').split(',') if client_data.get('selected_languages') else ['fr'],
                "price": client_data.get('price', 0), "notes": client_data.get('notes'),
                "status": status_name, "status_id": status_id_val,
                "creation_date": client_data.get('created_at', '').split('T')[0] if client_data.get('created_at') else "N/A",
                "category": client_data.get('category', 'Standard')
            }
            doc_manager.clients_data_map[adapted_client_dict["client_id"]] = adapted_client_dict
            doc_manager.add_client_to_list_widget(adapted_client_dict)
    except Exception as e:
        logging.error(f"Error loading and displaying clients: {e}", exc_info=True)
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"), doc_manager.tr("Erreur de chargement des clients:\n{0}").format(str(e)))

def filter_and_display_clients(doc_manager):
    search_term = doc_manager.search_input_field.text().lower()
    # Use the new attribute for selected status IDs, which is a list
    selected_status_ids = doc_manager.selected_status_ids_filter 

    doc_manager.client_list_widget.clear()
    for client_id_key, client_data_val in doc_manager.clients_data_map.items():
        # If selected_status_ids list is not empty, then filter by it.
        # An empty list means "All statuses" are effectively selected from the multi-select dialog.
        if selected_status_ids: # Check if the list is not empty
            client_status_id = client_data_val.get("status_id")
            if client_status_id not in selected_status_ids:
                continue
        
        # Keep the existing search term filter logic
        if search_term and not (search_term in client_data_val.get("client_name","").lower() or \
                               search_term in client_data_val.get("project_identifier","").lower() or \
                               search_term in client_data_val.get("company_name","").lower()):
            continue
        doc_manager.add_client_to_list_widget(client_data_val) # add_client_to_list_widget is a method of DocumentManager

def perform_old_clients_check(doc_manager):
    db = None
    try:
        db = get_db_connection()
        reminder_days_val = doc_manager.config.get("default_reminder_days", 30)
        s_archived_obj = get_status_setting_by_name(db, 'Archivé', 'Client')
        s_archived_id = s_archived_obj['status_id'] if s_archived_obj else -1
        s_complete_obj = get_status_setting_by_name(db, 'Complété', 'Client')
        s_complete_id = s_complete_obj['status_id'] if s_complete_obj else -2

        all_clients = clients_crud_instance.get_all_clients(db, include_deleted=False)
        old_clients_to_notify = []
        cutoff_date = datetime.now() - timedelta(days=reminder_days_val)

        for client in all_clients:
            if client.get('status_id') not in [s_archived_id, s_complete_id]:
                creation_date_str = client.get('created_at')
                if creation_date_str:
                    try:
                        # Robust parsing for different ISO formats
                        dt_str = str(creation_date_str).split('.')[0].replace('Z', '')
                        client_creation_date = datetime.fromisoformat(dt_str)

                        if client_creation_date <= cutoff_date:
                            old_clients_to_notify.append({
                                'client_id': client.get('client_id'),
                                'client_name': client.get('client_name'),
                                'creation_date_str': client_creation_date.strftime("%Y-%m-%d")
                            })
                    except (ValueError, TypeError) as ve:
                        logging.warning(f"Could not parse creation_date '{creation_date_str}' for client {client.get('client_id')}: {ve}")
                        continue
        if old_clients_to_notify:
            client_names_str = "\n".join([f"- {c['client_name']} (créé le {c['creation_date_str']})" for c in old_clients_to_notify])
            reply = QMessageBox.question(
                doc_manager, doc_manager.tr("Clients Anciens Actifs"),
                doc_manager.tr("Les clients suivants sont actifs depuis plus de {0} jours:\n{1}\n\nVoulez-vous les archiver?").format(reminder_days_val, client_names_str),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                for c_info in old_clients_to_notify:
                    archive_client_status(doc_manager, c_info['client_id'])
    except Exception as e:
        logging.error(f"Erreur vérification clients anciens: {type(e).__name__} - {str(e)}", exc_info=True)
    finally:
        if db:
            db.close()

def handle_open_edit_client_dialog(doc_manager, client_id):
    # This function is called from the UI, so it should manage its own session.
    db = None
    try:
        db = get_db_connection()
        # Fetch the most recent client data to populate the dialog
        current_client_data = clients_crud_instance.get_client_by_id(db, client_id, include_deleted=True)
        if not current_client_data:
            QMessageBox.warning(doc_manager, doc_manager.tr("Erreur"), doc_manager.tr("Client non trouvé."))
            doc_manager.notify(title=doc_manager.tr("Client Introuvable"),
                               message=doc_manager.tr("Les données du client (ID: {0}) n'ont pas pu être chargées pour modification.").format(client_id),
                               type='ERROR')
            return

        dialog = EditClientDialog(current_client_data, doc_manager.config, doc_manager)
        if dialog.exec_() == QDialog.Accepted:
            updated_form_data = dialog.get_data()
            data_for_db_update = {
                'client_name': updated_form_data.get('client_name'), 'company_name': updated_form_data.get('company_name'),
                'primary_need_description': updated_form_data.get('primary_need_description'), 'project_identifier': updated_form_data.get('project_identifier'),
                'country_id': updated_form_data.get('country_id'), 'city_id': updated_form_data.get('city_id'),
                'selected_languages': updated_form_data.get('selected_languages'), 'status_id': updated_form_data.get('status_id'),
                'notes': updated_form_data.get('notes'), 'category': updated_form_data.get('category')
            }
            update_result = clients_crud_instance.update_client(db, client_id, data_for_db_update)
            if update_result['success']:
                doc_manager.load_clients_from_db_slot() # This reloads the main list and map

                # After reloading, get the fresh data to notify and update tab
                updated_client_data_for_tab = doc_manager.clients_data_map.get(client_id)
                client_name_for_notify = updated_client_data_for_tab.get('client_name', str(client_id)) if updated_client_data_for_tab else str(client_id)
                doc_manager.notify(title=doc_manager.tr("Client Mis à Jour"),
                                   message=doc_manager.tr("Les informations du client '{0}' ont été mises à jour.").format(client_name_for_notify),
                                   type='SUCCESS')

                for i in range(doc_manager.client_tabs_widget.count()):
                    tab_widget = doc_manager.client_tabs_widget.widget(i)
                    if hasattr(tab_widget, 'client_info') and tab_widget.client_info.get("client_id") == client_id:
                        if hasattr(tab_widget, 'refresh_display') and updated_client_data_for_tab:
                            tab_widget.refresh_display(updated_client_data_for_tab)
                            doc_manager.client_tabs_widget.setTabText(i, updated_client_data_for_tab.get('client_name', 'Client'))
                        break

                # Refresh stats widget if it exists
                if hasattr(doc_manager, 'statistics_summary_widget_instance') and doc_manager.statistics_summary_widget_instance:
                    if hasattr(doc_manager.statistics_summary_widget_instance, 'update_stats'):
                        doc_manager.statistics_summary_widget_instance.update_stats()

            else:
                QMessageBox.warning(doc_manager, doc_manager.tr("Erreur"), doc_manager.tr("Échec de la mise à jour du client."))
                doc_manager.notify(title=doc_manager.tr("Erreur Mise à Jour Client"),
                                   message=doc_manager.tr("Impossible de mettre à jour les informations du client ID: {0}.").format(client_id),
                                   type='ERROR')
    except Exception as e:
        logging.error(f"Error during edit client dialog or update for client {client_id}: {e}", exc_info=True)
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Inattendue"), doc_manager.tr("Une erreur inattendue est survenue."))
    finally:
        if db:
            db.close()

def archive_client_status(doc_manager, client_id):
    if client_id not in doc_manager.clients_data_map: return

    client_name_for_notify = doc_manager.clients_data_map[client_id].get('client_name', str(client_id))
    db = None
    try:
        db = get_db_connection()
        status_archived_obj = get_status_setting_by_name(db, 'Archivé', 'Client')
        if not status_archived_obj:
            QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Configuration"),
                                 doc_manager.tr("Statut 'Archivé' non trouvé. Veuillez configurer les statuts."))
            return

        archived_status_id = status_archived_obj['status_id']

        update_data = {
            'status_id': archived_status_id,
            'is_deleted': True,
            'deleted_at': datetime.utcnow().isoformat() + "Z"
        }
        update_result = clients_crud_instance.update_client(db, client_id, update_data)

        if update_result.get('success'):
            log_data = {
                "user_id": doc_manager.current_user_id,
                "action_type": "CLIENT_ARCHIVED",
                "details": f"Client '{client_name_for_notify}' (ID: {client_id}) archivé.",
                "related_entity_type": "Client",
                "related_entity_id": client_id,
                "related_client_id": client_id
            }
            add_activity_log(db, log_data)

            # Commit changes before refreshing UI
            db.commit()

            # UI updates after successful DB operations
            doc_manager.load_clients_from_db_slot()

            # Close the tab for the archived client
            for i in range(doc_manager.client_tabs_widget.count()):
                tab_w = doc_manager.client_tabs_widget.widget(i)
                if hasattr(tab_w, 'client_info') and tab_w.client_info["client_id"] == client_id:
                    doc_manager.close_client_tab(i)
                    break

            if hasattr(doc_manager, 'statistics_summary_widget_instance') and doc_manager.statistics_summary_widget_instance:
                if hasattr(doc_manager.statistics_summary_widget_instance, 'update_stats'):
                    doc_manager.statistics_summary_widget_instance.update_stats()

            doc_manager.notify(title=doc_manager.tr("Client Archivé"),
                               message=doc_manager.tr("Le client '{0}' a été archivé.").format(client_name_for_notify),
                               type='INFO')
        else:
            db.rollback()
            error_msg = update_result.get('error', 'Unknown error')
            QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"),
                                 doc_manager.tr("Erreur d'archivage du client: {0}").format(error_msg))
    except Exception as e:
        if db: db.rollback()
        logging.error(f"Erreur inattendue lors de l'archivage du client '{client_name_for_notify}': {e}", exc_info=True)
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Inattendue"), doc_manager.tr("Erreur d'archivage du client:\n{0}").format(str(e)))
    finally:
        if db:
            db.close()

def permanently_delete_client(doc_manager, client_id):
    if client_id not in doc_manager.clients_data_map: return
    client_name_val = doc_manager.clients_data_map[client_id]['client_name']

    # The confirmation dialog text should reflect that this is a soft delete (archival)
    reply = QMessageBox.question(
        doc_manager, doc_manager.tr("Confirmer l'Archivage"),
        doc_manager.tr("Archiver '{0}'?\nCeci marquera le client comme supprimé et le cachera des listes par défaut. Le dossier du client ne sera PAS supprimé.\nCette action peut généralement être annulée.").format(client_name_val),
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    if reply == QMessageBox.No:
        return

    db = None
    try:
        db = get_db_connection()
        # The function clients_crud_instance.delete_client performs a soft delete.
        delete_result = clients_crud_instance.delete_client(db, client_id)

        if delete_result.get('success'):
            db.commit()
            logging.info(f"Client {client_id} marked as deleted (soft delete).")

            # Update UI
            doc_manager.load_clients_from_db_slot()

            # Close the tab for the archived client if it's open
            for i in range(doc_manager.client_tabs_widget.count()):
                tab_widget = doc_manager.client_tabs_widget.widget(i)
                if hasattr(tab_widget, 'client_info') and tab_widget.client_info.get("client_id") == client_id:
                    doc_manager.close_client_tab(i)
                    logging.info(f"Closed tab for archived client {client_id}.")
                    break

            if hasattr(doc_manager, 'statistics_summary_widget_instance') and doc_manager.statistics_summary_widget_instance:
                if hasattr(doc_manager.statistics_summary_widget_instance, 'update_stats'):
                    doc_manager.statistics_summary_widget_instance.update_stats()

            doc_manager.notify(title=doc_manager.tr("Client Archivé"),
                               message=doc_manager.tr("Le client '{0}' a été archivé avec succès.").format(client_name_val),
                               type='INFO')
        else:
            db.rollback()
            error_message = delete_result.get('error', doc_manager.tr("Erreur inconnue lors de l'archivage."))
            QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Archivage"),
                                 doc_manager.tr("Erreur lors de l'archivage du client: {0}").format(error_message))
    except Exception as e_archive:
        if db: db.rollback()
        logging.error(f"Erreur inattendue lors de l'archivage (soft delete) du client '{client_name_val}': {e_archive}", exc_info=True)
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Inattendue"),
                             doc_manager.tr("Une erreur inattendue est survenue lors de l'archivage du client:\n{0}").format(str(e_archive)))
    finally:
        if db:
            db.close()

# --- Invoice Generation and DB Update Logic ---
# Assuming invoice_generation_logic.py is at the same level or in PYTHONPATH
from .invoice_generation_logic import generate_final_invoice_pdf
from app.db.cruds.clients import client_documents_crud
from app.db.cruds.invoices import invoices_crud
import uuid # For ClientDocument ID if not generated by CRUD

def create_final_invoice_and_update_db(
    client_id: str,
    company_id: str,
    target_language_code: str,
    line_items: list,
    project_id: str = None,
    additional_context_overrides: dict = None,
    created_by_user_id: str = None
) -> tuple[bool, str | None, str | None]:
    """
    Generates a final invoice PDF and creates corresponding DB entries in a single transaction.
    """
    logging.info(f"Attempting to create final invoice for client {client_id}, project {project_id}")

    db = None
    final_pdf_path = None
    new_client_doc_id = None

    try:
        db = get_db_connection()

        # Step 1: Generate PDF bytes and context in memory. This part doesn't need the DB yet.
        pdf_bytes, suggested_filename, full_context = generate_final_invoice_pdf(
            db=db, # Pass db session to generator in case it needs it
            client_id=client_id,
            company_id=company_id,
            target_language_code=target_language_code,
            line_items=line_items,
            project_id=project_id,
            additional_context_overrides=additional_context_overrides
        )

        if pdf_bytes is None or full_context is None:
            raise Exception("Failed to generate PDF bytes or context.")

        # Step 2: Determine Save Path
        client_data = clients_crud_instance.get_client_by_id(db, client_id)
        if not client_data or not client_data.get('default_base_folder_path'):
            raise Exception(f"Client data or base folder path not found for client_id: {client_id}")

        save_directory = os.path.join(client_data['default_base_folder_path'], target_language_code, "Invoices")
        os.makedirs(save_directory, exist_ok=True)
        final_pdf_path = os.path.join(save_directory, suggested_filename)

        # Step 3: Create ClientDocuments Entry
        base_path_for_rel = client_data['default_base_folder_path']
        relative_pdf_path = os.path.relpath(final_pdf_path, base_path_for_rel)

        client_doc_data = {
            'client_id': client_id, 'project_id': project_id,
            'order_identifier': full_context.get("doc", {}).get("invoice_number"),
            'document_name': suggested_filename, 'file_name_on_disk': suggested_filename,
            'file_path_relative': relative_pdf_path, 'document_type_generated': "FINAL_INVOICE",
            'source_template_id': None, 'version_tag': "1.0",
            'notes': f"Final Invoice generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'created_by_user_id': created_by_user_id
        }
        new_client_doc_id = client_documents_crud.add_client_document(db, client_doc_data)
        if not new_client_doc_id:
            raise Exception("Failed to create ClientDocuments DB entry.")
        logging.info(f"ClientDocuments entry pre-committed with ID: {new_client_doc_id}")

        # Step 4: Create Invoices Table Entry
        doc_ctx = full_context.get("doc", {})
        invoice_table_data = {
            'client_id': client_id, 'project_id': project_id,
            'document_id': new_client_doc_id,
            'invoice_number': doc_ctx.get("invoice_number"), 'issue_date': doc_ctx.get("issue_date"),
            'due_date': doc_ctx.get("due_date"), 'total_amount': doc_ctx.get("grand_total_amount_raw"),
            'currency': doc_ctx.get("currency_symbol"), 'payment_status': 'unpaid',
            'notes': doc_ctx.get("notes", ""),
        }
        new_invoice_table_id = invoices_crud.add_invoice(db, invoice_table_data)
        if not new_invoice_table_id:
            raise Exception("Failed to create Invoices table DB entry.")
        logging.info(f"Invoices table entry pre-committed with ID: {new_invoice_table_id}")

        # Step 5: Write PDF to disk
        with open(final_pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        logging.info(f"Successfully wrote final invoice PDF to: {final_pdf_path}")

        # Step 6: Commit transaction
        db.commit()
        logging.info(f"Successfully committed invoice transaction for client {client_id}.")

        return True, new_invoice_table_id, new_client_doc_id

    except Exception as e:
        logging.error(f"Error in invoice creation transaction for client {client_id}: {e}", exc_info=True)
        if db:
            db.rollback()
        # Cleanup partial artifacts if they were created before the error
        if final_pdf_path and os.path.exists(final_pdf_path):
            try:
                os.remove(final_pdf_path)
                logging.info(f"Cleaned up partially created PDF file: {final_pdf_path}")
            except OSError as e_cleanup:
                logging.error(f"Failed to cleanup PDF file '{final_pdf_path}': {e_cleanup}")
        return False, None, new_client_doc_id # Return doc id if it was created, for potential manual cleanup
    finally:
        if db:
            db.close()
