# -*- coding: utf-8 -*-
import os
import shutil
import sqlite3 # Should be checked if still needed directly, db_manager should handle most
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox, QDialog, QInputDialog # QInputDialog was used in add_new_country/city, not directly in moved methods but good to keep context
# from PyQt5.QtCore import QStandardPaths # Removed as not used by these functions

# -*- coding: utf-8 -*-
import os
import shutil
import sqlite3 # Should be checked if still needed directly, db_manager should handle most
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox, QDialog, QInputDialog # QInputDialog was used in add_new_country/city, not directly in moved methods but good to keep context
# from PyQt5.QtCore import QStandardPaths # Removed as not used by these functions

# Import necessary functions directly from their new CRUD module locations
from client_management.client_controller import ClientController # Added
from controllers.contact_controller import ContactController # Added
from db.cruds.locations_crud import get_country_by_id, get_city_by_id # These are fine as locations_crud is not refactored to class yet
from db.cruds.status_settings_crud import get_status_setting_by_name, get_status_setting_by_id # Fine
from db.cruds.clients_crud import clients_crud_instance # Import the instance
from db.cruds.projects_crud import add_project, get_project_by_id, delete_project # Fine
from db.cruds.tasks_crud import add_task # Fine
from db.cruds.contacts_crud import get_contact_by_email, add_contact, update_contact, link_contact_to_client, get_contacts_for_client, update_client_contact_link # Fine
from db.cruds.products_crud import get_product_by_name, add_product, products_crud_instance

from db.cruds.client_project_products_crud import add_product_to_client_or_project, get_products_for_client_or_project

import logging # For logging errors or info
# Confirm import of products_crud_instance at module load time
if 'products_crud_instance' in globals():
    logging.info(f"DM_LOGIC: products_crud_instance successfully imported at module level: {products_crud_instance}")
else:
    logging.error("DM_LOGIC: products_crud_instance is NOT DEFINED at module level after import line!")


# Import dialogs that are used within the moved logic
# Assuming these dialogs are in a 'dialogs.py' or similar accessible location.
# If they are defined in main.py and not moved yet, this will cause an issue.
# For this step, we assume they are accessible.
from dialogs import (
    ContactDialog, ProductDialog, CreateDocumentDialog, EditClientDialog
)
# If ClientWidget is used by any logic here (e.g. for refreshing tabs), it would also need to be importable.
# from client_widget import ClientWidget # Not directly used in the functions being moved, but DocumentManager uses it.

import logging # For logging errors or info

def handle_create_client_execution(doc_manager, client_data_dict=None):
    client_controller = ClientController() # Instantiate controller

    if not client_data_dict:
        # This path should ideally not be taken if AddNewClientDialog is always used
        QMessageBox.critical(doc_manager, "Erreur", "Données client non fournies.")
        return

    # Basic validation of data from dialog (raw names)
    client_name_val = client_data_dict.get("client_name", "").strip()
    country_name_for_folder = client_data_dict.get("country_name", "").strip() # Used for folder name
    project_identifier_val = client_data_dict.get("project_identifier", "").strip()

    if not client_name_val or not country_name_for_folder or not project_identifier_val:
        QMessageBox.warning(doc_manager, doc_manager.tr("Champs Requis"), doc_manager.tr("Nom client, Pays et ID Projet sont obligatoires."))
        doc_manager.notify(title=doc_manager.tr("Champs Requis Manquants"),
                           message=doc_manager.tr("Nom client, Pays et ID Projet sont obligatoires pour la création."),
                           type='WARNING')
        return

    # --- Client Creation via Controller ---
    client_data_dict_for_controller = client_data_dict.copy()
    client_data_dict_for_controller['created_by_user_id'] = doc_manager.current_user_id

    created_client_info = client_controller.create_client(client_data_dict_for_controller)

    actual_new_client_id = None
    new_project_id_central_db = None # Define for later use in error handling

    if not created_client_info or not created_client_info.get("client_id"):
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"),
                             doc_manager.tr("Impossible de créer le client via le contrôleur."))
        # Add None check for created_client_info before calling .get()
        if created_client_info is None:
            print("Error: Client creation failed, created_client_info is None.") # Or use actual logging
            doc_manager.notify(title=doc_manager.tr("Erreur Création Client"),
                               message=doc_manager.tr("Le contrôleur n'a pas pu créer le client. Réponse nulle."),
                               type='ERROR')
            return # Or handle appropriately otherwise

        doc_manager.notify(title=doc_manager.tr("Erreur Création Client"),
                           message=created_client_info.get("error", doc_manager.tr("Le contrôleur n'a pas pu créer le client.")),
                           type='ERROR')
        return

    actual_new_client_id = created_client_info.get("client_id")
    country_id_val = created_client_info.get("country_id") # Resolved by controller
    city_id_val = created_client_info.get("city_id")       # Resolved by controller

    # --- Folder Creation ---
    folder_name_str = f"{client_name_val}_{country_name_for_folder}_{project_identifier_val}".replace(" ", "_").replace("/", "-")
    base_folder_full_path = os.path.join(doc_manager.config["clients_dir"], folder_name_str)

    # Note: project_identifier uniqueness should ideally be handled by client_controller.create_client
    # If it returns successfully, we assume project_identifier is unique.
    # The folder path uniqueness is a separate check.
    if os.path.exists(base_folder_full_path):
        QMessageBox.warning(doc_manager, doc_manager.tr("Dossier Existant"),
                            doc_manager.tr("Un dossier client avec un chemin similaire existe déjà: {0}. Le client a été créé en DB, mais le dossier n'est pas unique.").format(base_folder_full_path))
        doc_manager.notify(title=doc_manager.tr("Dossier Client Existant"),
                           message=doc_manager.tr("Un dossier client avec le chemin '{0}' existe déjà. Le client ID {1} a été créé en DB mais le dossier n'est pas unique.").format(base_folder_full_path, actual_new_client_id),
                           type='WARNING')
        # Client exists in DB. We might want to update it with this path, or allow user to change, or rollback.
        # For now, proceed and update client with this path, assuming user might consolidate.
        # This behavior might need refinement based on product requirements.

    try:
        os.makedirs(base_folder_full_path, exist_ok=True)
        # Update client record with the base_folder_full_path
        if actual_new_client_id: # Ensure client ID is valid
            clients_crud_instance.update_client(actual_new_client_id, {'default_base_folder_path': base_folder_full_path})
            created_client_info['default_base_folder_path'] = base_folder_full_path # Keep our local copy updated

        # Create language subfolders
        # Ensure selected_languages is a string from controller, then split.
        selected_langs_str = created_client_info.get("languages", "fr") # 'languages' is the key from controller
        selected_langs_list = selected_langs_str.split(',') if isinstance(selected_langs_str, str) else ["fr"]


        for lang_code in selected_langs_list:
            os.makedirs(os.path.join(base_folder_full_path, lang_code.strip()), exist_ok=True)

    except OSError as e_os:
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Dossier"), doc_manager.tr("Erreur de création du dossier client:\n{0}").format(str(e_os)))
        doc_manager.notify(title=doc_manager.tr("Erreur Création Dossier"), message=doc_manager.tr("Erreur de création du dossier pour le client '{0}'.").format(client_name_val), type='ERROR')
        if actual_new_client_id:
            clients_crud_instance.delete_client(actual_new_client_id) # Rollback client creation
            doc_manager.notify(title=doc_manager.tr("Rollback DB"), message=doc_manager.tr("Entrée client (ID: {0}) annulée suite à l'erreur de dossier.").format(actual_new_client_id), type='INFO')
        return # Stop further execution

    # --- Project and Task Creation (remains largely the same, using actual_new_client_id) ---
    try:
        project_status_planning_obj = get_status_setting_by_name("Planning", "Project")
        project_status_id_for_pm = project_status_planning_obj['status_id'] if project_status_planning_obj else None

        if not project_status_id_for_pm:
            QMessageBox.warning(doc_manager, doc_manager.tr("Erreur Configuration Projet"),
                                doc_manager.tr("Statut de projet par défaut 'Planning' non trouvé. Le projet ne sera pas créé avec un statut initial."))
            doc_manager.notify(title=doc_manager.tr("Erreur Configuration Projet"),
                               message=doc_manager.tr("Statut projet par défaut 'Planning' non trouvé."),
                               type='WARNING')

        project_data_for_db = {
            'client_id': actual_new_client_id,
            'project_name': f"Projet pour {created_client_info.get('client_name', client_name_val)}", # Use name from controller if available
            'description': f"Projet pour client: {created_client_info.get('client_name', client_name_val)}. Besoin initial: {created_client_info.get('primary_need_description', '')}",
            'start_date': datetime.now().strftime("%Y-%m-%d"),
            'deadline_date': (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            'budget': created_client_info.get('price', 0.0), # Price from controller (likely 0 or default)
            'status_id': project_status_id_for_pm,
            'priority': 1
        }
        logging.info(f"Attempting to create project for client {actual_new_client_id} with data: {project_data_for_db}")
        new_project_id_central_db = add_project(project_data_for_db)

        if new_project_id_central_db:
            QMessageBox.information(doc_manager, doc_manager.tr("Projet Créé (Central DB)"),
                                    doc_manager.tr("Un projet associé a été créé pour {0}.").format(created_client_info.get('client_name', client_name_val)))

            task_status_todo_obj = get_status_setting_by_name("To Do", "Task")
            task_status_id_for_todo = task_status_todo_obj['status_id'] if task_status_todo_obj else None

            if not task_status_id_for_todo:
                QMessageBox.warning(doc_manager, doc_manager.tr("Erreur Configuration Tâche"),
                                    doc_manager.tr("Statut de tâche par défaut 'To Do' non trouvé."))

            standard_tasks = [
                {"name": "Initial Client Consultation & Needs Assessment", "description": "Understand client requirements, objectives, target markets, and budget.", "priority_val": 2, "deadline_days": 3},
                {"name": "Market Research & Analysis", "description": "Research target international markets, including competition, regulations, and cultural nuances.", "priority_val": 1, "deadline_days": 7},
                {"name": "Post-Sales Follow-up & Support", "description": "Follow up with the client after delivery.", "priority_val": 1, "deadline_days": 60}
            ]

            for task_item in standard_tasks:
                task_deadline = (datetime.now() + timedelta(days=task_item["deadline_days"])).strftime("%Y-%m-%d")
                task_data_for_db = {
                    'project_id': new_project_id_central_db,
                    'task_name': task_item["name"],
                    'description': task_item["description"],
                    'status_id': task_status_id_for_todo,
                    'priority': task_item["priority_val"],
                    'due_date': task_deadline
                }
                logging.info(f"Attempting to add task for project {new_project_id_central_db} with data: {task_data_for_db}")
                add_task(task_data_for_db)
            QMessageBox.information(doc_manager, doc_manager.tr("Tâches Créées (Central DB)"),
                                    doc_manager.tr("Des tâches standard ont été ajoutées au projet pour {0}.").format(created_client_info.get('client_name', client_name_val)))
        else:
            logging.error(f"Failed to create project for client {actual_new_client_id}. Data attempted: {project_data_for_db}")
            QMessageBox.warning(doc_manager, doc_manager.tr("Erreur DB Projet"),
                                doc_manager.tr("Le client a été créé, mais la création du projet associé a échoué."))
            doc_manager.notify(title=doc_manager.tr("Erreur Création Projet Associé"),
                               message=doc_manager.tr("Client créé (ID: {0}), mais échec de la création du projet associé.").format(actual_new_client_id),
                               type='WARNING')

        # --- Update UI Map Data (ui_map_data) ---
        client_dict_from_controller = created_client_info # Use the data from controller

        ui_map_data = None
        if client_dict_from_controller:
            # Fetch names for IDs obtained from controller
            country_obj = get_country_by_id(client_dict_from_controller.get('country_id')) if client_dict_from_controller.get('country_id') else None
            city_obj = get_city_by_id(client_dict_from_controller.get('city_id')) if client_dict_from_controller.get('city_id') else None
            # Status should be part of created_client_info if controller sets it, or fetch if controller returns status_id
            status_id_from_controller = client_dict_from_controller.get('client_status_id') # Key used in controller
            status_obj = get_status_setting_by_id(status_id_from_controller) if status_id_from_controller else None

            sel_langs_str_ui = client_dict_from_controller.get('languages', 'fr') # Key used in controller
            sel_langs_list_ui = sel_langs_str_ui.split(',') if isinstance(sel_langs_str_ui, str) else ['fr']

            ui_map_data = {
                "client_id": client_dict_from_controller.get('client_id'),
                "client_name": client_dict_from_controller.get('client_name'),
                "company_name": client_dict_from_controller.get('company_name'),
                "need": client_dict_from_controller.get('primary_need_description'),
                "country": country_obj['country_name'] if country_obj else client_data_dict.get("country_name", "N/A"), # Fallback to original input if needed
                "country_id": client_dict_from_controller.get('country_id'),
                "city": city_obj['city_name'] if city_obj else client_data_dict.get("city_name", "N/A"), # Fallback to original input if needed
                "city_id": client_dict_from_controller.get('city_id'),
                "project_identifier": client_dict_from_controller.get('project_identifier'),
                "base_folder_path": client_dict_from_controller.get('default_base_folder_path'), # Updated earlier
                "selected_languages": sel_langs_list_ui,
                "price": client_dict_from_controller.get('price', 0), # Price from controller
                "notes": client_dict_from_controller.get('notes', ''), # Notes from controller
                "status": status_obj['status_name'] if status_obj else "N/A",
                "status_id": status_id_from_controller,
                "creation_date": client_dict_from_controller.get('created_at','').split("T")[0] if client_dict_from_controller.get('created_at') else datetime.now().strftime("%Y-%m-%d"),
                "category": client_dict_from_controller.get('category', 'Standard') # Category from controller
            }
            doc_manager.clients_data_map[actual_new_client_id] = ui_map_data
            doc_manager.add_client_to_list_widget(ui_map_data)

        if ui_map_data:
            # --- BEGIN AUTO PROFORMA GENERATION ---
            try:
                logging.info(f"Starting automatic Proforma generation for new client ID: {actual_new_client_id}")

                # 1. Determine Proforma Language
                selected_langs_str = created_client_info.get("languages", "fr")
                proforma_language_codes = [lang.strip() for lang in selected_langs_str.split(',') if lang.strip()]

                if not proforma_language_codes:
                    default_lang_from_config = doc_manager.config.get("default_document_language", "fr")
                    proforma_language_codes = [default_lang_from_config]
                    logging.info(f"No specific languages selected for client {actual_new_client_id}, defaulting Proforma to: {proforma_language_codes[0]}")

                target_proforma_lang = proforma_language_codes[0]
                logging.info(f"Target language for automatic Proforma: {target_proforma_lang}")

                # 2. Fetch Default Proforma Template
                from db.cruds import templates_crud
                default_proforma_template = templates_crud.get_template_by_type_lang_default(
                    template_type="HTML_PROFORMA",
                    language_code=target_proforma_lang,
                    client_id=None
                )

                if not default_proforma_template:
                    logging.error(f"No default Proforma template found for language '{target_proforma_lang}'. Skipping auto-generation.")
                    doc_manager.notify(title=doc_manager.tr("Modèle Proforma Manquant"),
                                       message=doc_manager.tr("Aucun modèle Proforma par défaut trouvé pour la langue '{0}'. La génération automatique est annulée.").format(target_proforma_lang),
                                       type='WARNING')
                    raise Exception(f"Default Proforma template not found for {target_proforma_lang}")

                template_base_filename = default_proforma_template.get('base_file_name')
                template_inherent_language = default_proforma_template.get('language_code')

                template_file_on_disk_abs = os.path.join(
                    doc_manager.config.get("templates_dir", "templates"),
                    template_inherent_language,
                    template_base_filename
                )

                if not os.path.exists(template_file_on_disk_abs):
                    logging.error(f"Default Proforma template file not found on disk: {template_file_on_disk_abs}")
                    doc_manager.notify(title=doc_manager.tr("Fichier Modèle Introuvable"),
                                       message=doc_manager.tr("Fichier modèle Proforma '{0}' introuvable pour la langue '{1}'. Génération auto annulée.").format(template_base_filename, target_proforma_lang),
                                       type='ERROR')
                    raise Exception(f"Default Proforma template file not found: {template_file_on_disk_abs}")

                # 3. Determine Company ID (Default Company)
                from db.cruds import companies_crud
                default_company = companies_crud.get_default_company()
                if not default_company or not default_company.get("company_id"):
                    logging.error("No default company configured. Cannot generate Proforma.")
                    doc_manager.notify(title=doc_manager.tr("Erreur Configuration Société"),
                                       message=doc_manager.tr("Aucune société par défaut n'est configurée. La génération automatique de Proforma est annulée."),
                                       type='ERROR')
                    raise Exception("Default company not configured.")

                auto_proforma_company_id = default_company.get("company_id")

                # 4. Generate Proforma PDF
                client_info_for_pdf_gen = created_client_info.copy()
                client_info_for_pdf_gen['base_folder_path'] = base_folder_full_path

                from utils import generate_pdf_for_document

                proforma_doc_title_base = default_proforma_template.get('template_name', 'Facture_Proforma')
                proforma_specific_additional_context = {
                    'document_title': f"{proforma_doc_title_base} - {client_info_for_pdf_gen.get('client_name', 'Client')}",
                    'proforma_id': f"PF-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }

                generated_pdf_path = generate_pdf_for_document(
                    source_file_path=template_file_on_disk_abs,
                    client_info=client_info_for_pdf_gen,
                    app_root_dir=doc_manager.app_root_dir,
                    parent_widget=doc_manager,
                    target_language_code=target_proforma_lang,
                    project_id=new_project_id_central_db,
                    additional_context=proforma_specific_additional_context,
                document_type_for_context=default_proforma_template.get('template_type'),
                allow_empty_products=True # Allow empty products for auto-generated Proforma
                )
            logging.info(f"Called generate_pdf_for_document for AUTO PROFORMA. File: {template_base_filename}, Lang: {target_proforma_lang}, allow_empty_products=True. Result path: {generated_pdf_path}") # NEW LOG

                if not generated_pdf_path or not os.path.exists(generated_pdf_path):
                    logging.error(f"Automatic Proforma PDF generation failed for client {actual_new_client_id}.")
                    raise Exception("Automatic Proforma PDF generation failed.")

                logging.info(f"Automatic Proforma PDF generated successfully: {generated_pdf_path}")

                # 5. Save Document Record to ClientDocuments
                from db.cruds import client_documents_crud
                relative_pdf_path_for_db = os.path.relpath(generated_pdf_path, base_folder_full_path)

                auto_proforma_doc_data = {
                    'client_id': actual_new_client_id,
                    'project_id': new_project_id_central_db,
                    'order_identifier': proforma_specific_additional_context.get('proforma_id'),
                    'document_name': os.path.basename(generated_pdf_path),
                    'file_name_on_disk': os.path.basename(generated_pdf_path),
                    'file_path_relative': relative_pdf_path_for_db,
                    'document_type_generated': "PROFORMA_PDF",
                    'source_template_id': default_proforma_template.get('template_id'),
                    'user_id': doc_manager.current_user_id,
                    'language_code': target_proforma_lang,
                    'version_tag': "1.0"
                }

                new_client_doc_db_id = client_documents_crud.add_client_document(auto_proforma_doc_data)

                if not new_client_doc_db_id:
                    logging.error(f"Failed to save auto-generated Proforma to ClientDocuments for client {actual_new_client_id}.")
                    if os.path.exists(generated_pdf_path):
                        try: os.remove(generated_pdf_path)
                        except OSError: logging.error(f"Failed to cleanup generated PDF: {generated_pdf_path}")
                    doc_manager.notify(title=doc_manager.tr("Erreur DB Document"),
                                       message=doc_manager.tr("Proforma PDF généré mais échec de l'enregistrement en base de données."),
                                       type='ERROR')
                    raise Exception("Failed to save auto-generated Proforma to ClientDocuments.")

                logging.info(f"Auto-generated Proforma (Doc ID: {new_client_doc_db_id}) saved to ClientDocuments for client {actual_new_client_id}.")
                doc_manager.notify(title=doc_manager.tr("Proforma Automatique Créée"),
                                   message=doc_manager.tr("Une facture Proforma a été automatiquement générée et ajoutée pour le client en langue '{0}'.").format(target_proforma_lang),
                                   type='SUCCESS')

            except Exception as e_auto_proforma:
                logging.error(f"Error during automatic Proforma generation for client {actual_new_client_id}: {e_auto_proforma}", exc_info=True)
                doc_manager.notify(title=doc_manager.tr("Échec Proforma Auto"),
                                   message=doc_manager.tr("La génération automatique de la Proforma a échoué. Raison: {0}").format(str(e_auto_proforma)),
                                   type='WARNING')
            # --- END AUTO PROFORMA GENERATION ---

            contact_controller = ContactController(current_user_id=doc_manager.current_user_id) # Pass user_id

            # Check if this is the first contact for the client
            existing_contacts = get_contacts_for_client(actual_new_client_id, limit=1)
            is_first_contact = not existing_contacts

            contact_dialog = ContactDialog(client_id=actual_new_client_id,
                                           parent=doc_manager,
                                           is_first_contact=is_first_contact,
                                           current_user_id=doc_manager.current_user_id) # Pass current_user_id
            if contact_dialog.exec_() == QDialog.Accepted:
                contact_form_data = contact_dialog.get_data()

                logging.info(f"Attempting to process contact for client {actual_new_client_id} using ContactController. Form data: {contact_form_data}")

                # Use the ContactController here
                contact_id_linked, link_id = contact_controller.get_or_create_contact_and_link(
                    client_id=actual_new_client_id,
                    contact_form_data=contact_form_data
                )

                if contact_id_linked:
                    logging.info(f"Contact processed successfully for client {actual_new_client_id}. Contact ID: {contact_id_linked}, Link ID: {link_id}")
                    # Optionally, notify user of contact success, though ContactDialog itself might do this.
                    # For consistency, a simple log here is fine, or a notification via doc_manager.notify if desired.
                    # Example: doc_manager.notify(title=doc_manager.tr("Contact Traité"), message=doc_manager.tr("Le contact a été traité avec succès pour le nouveau client."), type='SUCCESS')
                else:
                    logging.error(f"Failed to process contact for client {actual_new_client_id} using ContactController.")
                    QMessageBox.warning(doc_manager,
                                        doc_manager.tr("Erreur Contact"),
                                        doc_manager.tr("Le traitement du contact a échoué. Veuillez vérifier les informations du contact ou consulter les logs pour plus de détails."))
            else:
                logging.info(f"ContactDialog was cancelled for client {actual_new_client_id}.")

            # ProductDialog and subsequent price calculation
            product_dialog = ProductDialog(client_id=actual_new_client_id, app_root_dir=doc_manager.app_root_dir, parent=doc_manager)
            if product_dialog.exec_() == QDialog.Accepted:
                products_list_data = product_dialog.get_data()

                # Check if products_crud_instance is defined before using it in the loop
                if 'products_crud_instance' not in globals() or globals()['products_crud_instance'] is None:
                    logging.error("DM_LOGIC: products_crud_instance is NOT available in handle_create_client_execution before product loop. This should have been caught at module load.")
                    QMessageBox.critical(doc_manager, "Erreur Critique Module Produit", "Le module de gestion des produits n'est pas correctement initialisé.")
                    # Optionally, return or raise an exception to prevent further processing
                    # For now, we'll let it proceed and potentially hit NameErrors if it's truly not defined,
                    # but the module-level log should have caught this.
                else:
                    logging.info(f"DM_LOGIC: products_crud_instance IS available in handle_create_client_execution: {globals()['products_crud_instance']}")


                for product_item_data in products_list_data:
                    logging.info(f"Processing product item from dialog: {product_item_data}")
                    global_product_id_to_link = None
                    current_base_unit_price = None # Used to determine if override is needed

                    try:
                        # products_crud_instance is now checked before the loop.
                        # If it was None, an error message was shown.
                        # If execution reaches here and it's still None (e.g. due to some very complex issue),
                        # the NameError will occur as before, but the logs should give clues.


                        # Step 1: Determine the global_product_id
                        dialog_provided_global_product_id = product_item_data.get('product_id') # From selected existing product
                        product_code_from_dialog = product_item_data.get('product_code', "").strip()

                        if dialog_provided_global_product_id is not None:
                            logging.info(f"Using existing global product_id from dialog: {dialog_provided_global_product_id}")
                            global_product_id_to_link = dialog_provided_global_product_id
                            existing_global_product_details = products_crud_instance.get_product_by_id(global_product_id_to_link)
                            if existing_global_product_details:
                                current_base_unit_price = existing_global_product_details.get('base_unit_price')
                        else:
                            if not product_code_from_dialog:
                                logging.warning(f"Product code (SKU) missing for product '{product_item_data.get('name')}'.")
                                QMessageBox.warning(doc_manager, doc_manager.tr("Code Produit Requis"),
                                                     doc_manager.tr("Le code produit (SKU) est requis pour le produit '{0}'. Ce produit ne sera pas ajouté.").format(product_item_data.get('name')))
                                continue
                            existing_product_by_code = products_crud_instance.get_product_by_code(product_code_from_dialog)
                            if existing_product_by_code:
                                global_product_id_to_link = existing_product_by_code['product_id']
                                current_base_unit_price = existing_product_by_code.get('base_unit_price')
                                logging.debug(f"Helper: Found existing global product by code. ID: {global_product_id_to_link}")
                            else:
                                logging.info(f"Helper: Product with code '{product_code_from_dialog}' not found. Creating new global product.")
                                new_global_product_data = {
                                    'product_name': product_item_data['name'], 'product_code': product_code_from_dialog,
                                    'description': product_item_data['description'], 'base_unit_price': product_item_data['unit_price'],
                                    'language_code': product_item_data.get('language_code', 'fr'), 'category': product_item_data.get('category', ''),
                                    'unit_of_measure': product_item_data.get('unit_of_measure', 'unit'), 'weight': product_item_data.get('weight'),
                                    'dimensions': product_item_data.get('dimensions'), 'is_active': True,
                                    'created_by_user_id': doc_manager.current_user_id
                                }
                                add_result = products_crud_instance.add_product(new_global_product_data)
                                if add_result and add_result.get('success'):
                                    global_product_id_to_link = add_result.get('id')
                                    current_base_unit_price = new_global_product_data['base_unit_price']
                                    logging.info(f"DM_LOGIC: New global product '{new_global_product_data['product_name']}' created with ID: {global_product_id_to_link}") # Enhanced log
                                else:
                                    error_detail = add_result.get('error', 'Unknown error') if add_result else 'Unknown error'
                                    logging.error(f"DM_LOGIC: Failed to add new global product '{product_item_data.get('name')}' (Code: {product_code_from_dialog}). Error: {error_detail}")
                                    QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Création Produit Global"),
                                                         doc_manager.tr("Impossible de créer le produit global '{0}' (Code: {1}). Erreur: {2}").format(product_item_data['name'], product_code_from_dialog, error_detail))
                                    return False # Indicate failure for this item

                        if global_product_id_to_link:
                            unit_price_from_dialog = product_item_data['unit_price']
                            unit_price_override_val = None
                            if current_base_unit_price is None or unit_price_from_dialog != current_base_unit_price:
                                unit_price_override_val = unit_price_from_dialog
                            link_data = {
                                'client_id': actual_new_client_id, 'project_id': None,
                                'product_id': global_product_id_to_link, 'quantity': product_item_data['quantity'],
                                'unit_price_override': unit_price_override_val,
                                'added_by_user_id': doc_manager.current_user_id
                            }
                            logging.debug(f"Helper: Attempting to link product_id {global_product_id_to_link} to client {actual_new_client_id} with data: {link_data}")
                            cpp_id = add_product_to_client_or_project(link_data)
                            if cpp_id:
                                logging.info(f"Helper: Successfully linked product '{product_item_data.get('name')}' to client. Link ID: {cpp_id}")
                                return True # Indicate success for this item
                            else:
                                logging.error(f"Helper: Failed to link product '{product_item_data.get('name')}' (Global ID: {global_product_id_to_link}) to client {actual_new_client_id}.")
                                QMessageBox.warning(doc_manager, doc_manager.tr("Erreur Liaison Produit"),
                                                    doc_manager.tr("Impossible de lier le produit '{0}' au client.").format(product_item_data['name']))
                                return False # Indicate failure for this item
                        else:
                            logging.error(f"Helper: Global product ID to link is None for item '{product_item_data.get('name')}'. Cannot link.")
                            QMessageBox.warning(doc_manager, doc_manager.tr("Erreur Interne Produit"),
                                                doc_manager.tr("ID de produit global non déterminé pour '{0}'. Liaison annulée.").format(product_item_data.get('name')))
                            return False # Indicate failure for this item
                    except Exception as e_product_save: # This broad exception catch should ideally be within the helper
                        logging.error(f"Unexpected error processing product '{product_item_data.get('name', 'Inconnu')}': {type(e_product_save).__name__} - {e_product_save}", exc_info=True)
                        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Sauvegarde Produit"),
                                             doc_manager.tr("Une erreur est survenue lors de la sauvegarde du produit '{0}': {1}").format(product_item_data.get('name', 'Inconnu'), str(e_product_save)))
                        return False # Indicate failure for this item

                # Update client's total price based on successfully saved products
                linked_products_after_save = get_products_for_client_or_project(client_id=actual_new_client_id, project_id=None)
                calculated_total_sum_after_save = sum(p.get('total_price_calculated', 0.0) for p in linked_products_after_save if p.get('total_price_calculated') is not None)
                logging.info(f"Updating client {actual_new_client_id} price to {calculated_total_sum_after_save} after ProductDialog acceptance.")
                clients_crud_instance.update_client(actual_new_client_id, {'price': calculated_total_sum_after_save})
                if actual_new_client_id in doc_manager.clients_data_map:
                    doc_manager.clients_data_map[actual_new_client_id]['price'] = calculated_total_sum_after_save
                if ui_map_data: ui_map_data['price'] = calculated_total_sum_after_save # Ensure ui_map_data for CreateDocumentDialog is fresh

                # Proceed to CreateDocumentDialog
                logging.info(f"Attempting to show CreateDocumentDialog for client ID {actual_new_client_id}.")
                create_document_dialog = CreateDocumentDialog(
                    client_info=ui_map_data, config=doc_manager.config,
                    current_user_id=doc_manager.current_user_id, parent=doc_manager
                )
                if create_document_dialog.exec_() == QDialog.Accepted:
                    logging.info("CreateDocumentDialog accepted.")
                else:
                    logging.info("CreateDocumentDialog cancelled.")
            else: # ProductDialog was cancelled
                logging.info("ProductDialog cancelled by user.")
                # Update client's total price based on any products linked PRIOR to this cancelled dialog
                linked_products_after_cancel = get_products_for_client_or_project(client_id=actual_new_client_id, project_id=None)
                calculated_total_sum_after_cancel = sum(p.get('total_price_calculated', 0.0) for p in linked_products_after_cancel if p.get('total_price_calculated') is not None)
                logging.info(f"Updating client {actual_new_client_id} price to {calculated_total_sum_after_cancel} after ProductDialog cancellation.")
                clients_crud_instance.update_client(actual_new_client_id, {'price': calculated_total_sum_after_cancel})
                if actual_new_client_id in doc_manager.clients_data_map:
                    doc_manager.clients_data_map[actual_new_client_id]['price'] = calculated_total_sum_after_cancel
                # CreateDocumentDialog is SKIPPED as per Test Case 3




#         else: # ui_map_data was not populated (should not happen if controller succeeded)
#              QMessageBox.warning(doc_manager, doc_manager.tr("Erreur Données Client"), doc_manager.tr("Les données du client (ui_map_data) ne sont pas disponibles pour la séquence de dialogue."))
# # --- After contact_dialog.exec_() block ---
        else: # ContactDialog was cancelled
            logging.info("ContactDialog cancelled by user.")
            # Ensure client's price is initialized/updated even if workflow is exited early
            # (e.g., to 0 if no products were ever associated with this new client)
            clients_crud_instance.update_client(actual_new_client_id, {'price': 0.0})
            if actual_new_client_id in doc_manager.clients_data_map:
                doc_manager.clients_data_map[actual_new_client_id]['price'] = 0.0
            if ui_map_data: ui_map_data['price'] = 0.0


# --- Final notifications and UI updates (outside the main if ui_map_data block, but relies on its outcomes) ---

        doc_manager.notify(title=doc_manager.tr("Client Créé"),
                           message=doc_manager.tr("Le client '{0}' (ID: {1}) a été créé avec succès.").format(created_client_info.get('client_name', client_name_val), actual_new_client_id),
                           type='SUCCESS')
        doc_manager.open_client_tab_by_id(actual_new_client_id)
        doc_manager.stats_widget.update_stats()

    except sqlite3.IntegrityError as e_sqlite_integrity: # This might be caught by controller now
        logging.error(f"Database integrity error: {client_name_val}", exc_info=True)
        error_msg_detail = str(e_sqlite_integrity).lower()
        user_message = doc_manager.tr("Erreur de base de données.")
        if "unique constraint failed: clients.project_identifier" in error_msg_detail: # Should be caught by controller
            user_message = doc_manager.tr("L'ID de Projet '{0}' existe déjà.").format(project_identifier_val)
        elif "unique constraint failed: clients.default_base_folder_path" in error_msg_detail: # Path created from user input
             user_message = doc_manager.tr("Un client avec un nom ou un chemin de dossier résultant similaire existe déjà.")
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur de Données"), user_message)
        doc_manager.notify(title=doc_manager.tr("Erreur Données Client"), message=user_message, type='ERROR')
        # If client was created by controller but project/task fails here, client still exists.
        # Consider if rollback is needed for controller-created client if subsequent steps fail.
        # For now, if controller created client, it remains.
    except Exception as e_general:
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Inattendue"), doc_manager.tr("Une erreur s'est produite:\n{0}").format(str(e_general)))
        doc_manager.notify(title=doc_manager.tr("Erreur Inattendue Création"), message=doc_manager.tr("Erreur inattendue."), type='ERROR')
        # Rollback for project/tasks if created
        if new_project_id_central_db and get_project_by_id(new_project_id_central_db):
            delete_project(new_project_id_central_db)
        # Client created by controller remains unless explicitly rolled back.
        # This part needs careful consideration of transactional behavior.
        # If client was created (actual_new_client_id is not None), but this later part fails,
        # the client exists in DB, but project/tasks might not.
        # The original code had some rollback logic for client if os.makedirs failed after client creation.
        # That specific OSError is handled above with rollback. This is for other exceptions.


def load_and_display_clients(doc_manager, filters: dict = None, limit: int = None, offset: int = 0, include_deleted: bool = False):
    """
    Loads client data from the database and displays it in the UI.
    Now accepts filters, pagination, and include_deleted parameters.
    """
    doc_manager.clients_data_map.clear()
    doc_manager.client_list_widget.clear()
    try:
        # Use get_all_clients_with_details for richer data for UI map
        # The 'filters' dict here is for the CRUD method, not the UI search term yet.
        # UI search term will be applied on top of this loaded data or by refining the filters dict.
        all_clients_dicts = clients_crud_instance.get_all_clients_with_details(
            filters=filters,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted
        )
        # get_all_clients_with_details already sorts by client_name
        # if all_clients_dicts is None: all_clients_dicts = [] # Already returns list
        # all_clients_dicts.sort(key=lambda c: c.get('client_name', '')) # Sorting done by CRUD

        for client_data in all_clients_dicts:
            country_name = "N/A"
            if client_data.get('country_id'):
                country_obj = get_country_by_id(client_data['country_id'])
                if country_obj: country_name = country_obj['country_name']
            city_name = "N/A"
            if client_data.get('city_id'):
                city_obj = get_city_by_id(client_data['city_id'])
                if city_obj: city_name = city_obj['city_name']
            status_name = "N/A"
            status_id_val = client_data.get('status_id')
            if status_id_val:
                status_obj = get_status_setting_by_id(status_id_val)
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
            doc_manager.add_client_to_list_widget(adapted_client_dict) # add_client_to_list_widget is a method of DocumentManager
    except Exception as e:
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"), doc_manager.tr("Erreur de chargement des clients:\n{0}").format(str(e)))

def filter_and_display_clients(doc_manager):
    search_term = doc_manager.search_input_field.text().lower()
    selected_status_id = doc_manager.status_filter_combo.currentData()

    doc_manager.client_list_widget.clear()
    for client_id_key, client_data_val in doc_manager.clients_data_map.items():
        if selected_status_id is not None:
            if client_data_val.get("status_id") != selected_status_id:
                continue
        if search_term and not (search_term in client_data_val.get("client_name","").lower() or \
                               search_term in client_data_val.get("project_identifier","").lower() or \
                               search_term in client_data_val.get("company_name","").lower()):
            continue
        doc_manager.add_client_to_list_widget(client_data_val) # add_client_to_list_widget is a method of DocumentManager

def perform_old_clients_check(doc_manager):
    try:
        reminder_days_val = doc_manager.config.get("default_reminder_days", 30)
        s_archived_obj = get_status_setting_by_name('Archivé', 'Client')
        s_archived_id = s_archived_obj['status_id'] if s_archived_obj else -1
        s_complete_obj = get_status_setting_by_name('Complété', 'Client')
        s_complete_id = s_complete_obj['status_id'] if s_complete_obj else -2

        # Get all non-deleted clients for this check by default
        all_clients = clients_crud_instance.get_all_clients(include_deleted=False)
        # if all_clients is None: all_clients = [] # get_all_clients returns list
        old_clients_to_notify = []
        cutoff_date = datetime.now() - timedelta(days=reminder_days_val)

        for client in all_clients:
            if client.get('status_id') not in [s_archived_id, s_complete_id]:
                creation_date_str = client.get('created_at')
                if creation_date_str:
                    try:
                        if 'T' in creation_date_str and '.' in creation_date_str:
                            client_creation_date = datetime.fromisoformat(creation_date_str.split('.')[0])
                        elif 'T' in creation_date_str:
                             client_creation_date = datetime.fromisoformat(creation_date_str.replace('Z', ''))
                        else:
                            client_creation_date = datetime.strptime(creation_date_str, "%Y-%m-%d")
                        if client_creation_date <= cutoff_date:
                            old_clients_to_notify.append({
                                'client_id': client.get('client_id'),
                                'client_name': client.get('client_name'),
                                'creation_date_str': client_creation_date.strftime("%Y-%m-%d")
                            })
                    except ValueError as ve:
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
                    archive_client_status(doc_manager, c_info['client_id']) # Call the refactored function
    except Exception as e:
        logging.error(f"Erreur vérification clients anciens: {str(e)}")

def handle_open_edit_client_dialog(doc_manager, client_id):
    current_client_data = doc_manager.clients_data_map.get(client_id)
    if not current_client_data:
        QMessageBox.warning(doc_manager, doc_manager.tr("Erreur"), doc_manager.tr("Client non trouvé."))
        doc_manager.notify(title=doc_manager.tr("Client Introuvable"),
                           message=doc_manager.tr("Les données du client (ID: {0}) n'ont pas pu être chargées pour modification.").format(client_id),
                           type='ERROR')
        return

    dialog = EditClientDialog(current_client_data, doc_manager.config, doc_manager) # Pass doc_manager as parent
    if dialog.exec_() == QDialog.Accepted:
        updated_form_data = dialog.get_data()
        data_for_db_update = {
            'client_name': updated_form_data.get('client_name'), 'company_name': updated_form_data.get('company_name'),
            'primary_need_description': updated_form_data.get('primary_need_description'), 'project_identifier': updated_form_data.get('project_identifier'),
            'country_id': updated_form_data.get('country_id'), 'city_id': updated_form_data.get('city_id'),
            'selected_languages': updated_form_data.get('selected_languages'), 'status_id': updated_form_data.get('status_id'),
            'notes': updated_form_data.get('notes'), 'category': updated_form_data.get('category')
        }
        # Use clients_crud_instance.update_client
        update_result = clients_crud_instance.update_client(client_id, data_for_db_update)
        if update_result['success']:
            # load_and_display_clients needs to be called with current filters/pagination
            # This might require main_window to handle the refresh.
            # For now, assume a simple refresh.
            doc_manager.load_clients_from_db_slot() # Call the slot in main_window for full refresh logic
            # The following lines might be redundant if load_clients_from_db_slot updates clients_data_map
            # and refreshes tabs correctly.
            # load_and_display_clients(doc_manager) # Refresh map and list widget
            updated_client_data_for_tab = doc_manager.clients_data_map.get(client_id) # Get fresh data after load_and_display_clients
            client_name_for_notify = updated_client_data_for_tab.get('client_name', str(client_id)) if updated_client_data_for_tab else str(client_id)
            doc_manager.notify(title=doc_manager.tr("Client Mis à Jour"),
                               message=doc_manager.tr("Les informations du client '{0}' ont été mises à jour.").format(client_name_for_notify),
                               type='SUCCESS')
            tab_refreshed = False
            for i in range(doc_manager.client_tabs_widget.count()):
                tab_widget = doc_manager.client_tabs_widget.widget(i)
                if hasattr(tab_widget, 'client_info') and tab_widget.client_info.get("client_id") == client_id:
                    if hasattr(tab_widget, 'refresh_display'):
                        if updated_client_data_for_tab: # Ensure it's not None
                            tab_widget.refresh_display(updated_client_data_for_tab)
                            doc_manager.client_tabs_widget.setTabText(i, updated_client_data_for_tab.get('client_name', 'Client'))
                            tab_refreshed = True
                    break
            doc_manager.stats_widget.update_stats()
        else:
            QMessageBox.warning(doc_manager, doc_manager.tr("Erreur"), doc_manager.tr("Échec de la mise à jour du client."))
            doc_manager.notify(title=doc_manager.tr("Erreur Mise à Jour Client"),
                               message=doc_manager.tr("Impossible de mettre à jour les informations du client ID: {0}.").format(client_id),
                               type='ERROR')

def archive_client_status(doc_manager, client_id):
    if client_id not in doc_manager.clients_data_map: return
    try:
        status_archived_obj = get_status_setting_by_name('Archivé', 'Client')
        if not status_archived_obj:
            QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Configuration"),
                                 doc_manager.tr("Statut 'Archivé' non trouvé. Veuillez configurer les statuts."))
            doc_manager.notify(title=doc_manager.tr("Erreur Configuration Statut"),
                               message=doc_manager.tr("Statut 'Archivé' non trouvé. Impossible d'archiver."),
                               type='ERROR')
            return
        archived_status_id = status_archived_obj['status_id']
        client_name_for_notify = doc_manager.clients_data_map[client_id].get('client_name', str(client_id))

        # Update client to archived status and also set soft delete flags
        update_data = {
            'status_id': archived_status_id,
            'is_deleted': True, # Explicitly mark as soft-deleted
            'deleted_at': datetime.utcnow().isoformat() + "Z"
        }
        update_result = clients_crud_instance.update_client(client_id, update_data)

        if update_result['success'] and update_result.get('updated_count', 0) > 0:
            # Update local map, though a full refresh might be better
            if client_id in doc_manager.clients_data_map:
                doc_manager.clients_data_map[client_id]["status"] = status_archived_obj['status_name'] # "Archivé"
                doc_manager.clients_data_map[client_id]["status_id"] = archived_status_id
                doc_manager.clients_data_map[client_id]["is_deleted"] = True # Reflect soft delete in map

            # Refresh display considering current filters (especially include_deleted)
            doc_manager.filter_client_list_display_slot() # Use the main_window slot
            # load_and_display_clients(doc_manager) # Or call with current filters
            filter_and_display_clients(doc_manager) # Refresh list display
            for i in range(doc_manager.client_tabs_widget.count()):
                tab_w = doc_manager.client_tabs_widget.widget(i)
                if hasattr(tab_w, 'client_info') and tab_w.client_info["client_id"] == client_id:
                    if hasattr(tab_w, 'status_combo'): # Check if ClientWidget has status_combo
                        tab_w.status_combo.setCurrentText("Archivé") # Update status combo in open tab
                    break
            doc_manager.stats_widget.update_stats()
            # QMessageBox.information(doc_manager, doc_manager.tr("Client Archivé"),
            #                         doc_manager.tr("Le client '{0}' a été archivé.").format(client_name_for_notify))
            doc_manager.notify(title=doc_manager.tr("Client Archivé"),
                               message=doc_manager.tr("Le client '{0}' a été archivé.").format(client_name_for_notify),
                               type='INFO')
        else:
            QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"),
                                 doc_manager.tr("Erreur d'archivage du client. Vérifiez les logs."))
            doc_manager.notify(title=doc_manager.tr("Erreur Archivage"),
                               message=doc_manager.tr("Erreur d'archivage du client '{0}'.").format(client_name_for_notify),
                               type='ERROR')
    except Exception as e:
        QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"), doc_manager.tr("Erreur d'archivage du client:\n{0}").format(str(e)))
        doc_manager.notify(title=doc_manager.tr("Erreur Archivage Inattendue"),
                           message=doc_manager.tr("Erreur inattendue lors de l'archivage du client '{0}'.").format(client_name_for_notify),
                           type='ERROR')

def permanently_delete_client(doc_manager, client_id):
    if client_id not in doc_manager.clients_data_map: return
    client_name_val = doc_manager.clients_data_map[client_id]['client_name']
    client_folder_path = doc_manager.clients_data_map[client_id]["base_folder_path"]

    reply = QMessageBox.question(
        doc_manager, doc_manager.tr("Confirmer Suppression"),
        doc_manager.tr("Supprimer '{0}'?\nCeci supprimera le client de la base de données et son dossier de fichiers (si possible).\nCette action est irréversible.").format(client_name_val),
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        try:
            # Use clients_crud_instance.delete_client for soft delete
            logging.info("INFO: permanently_delete_client now performs a SOFT delete due to CRUD changes. For hard delete, a new CRUD method is needed.")
            delete_result = clients_crud_instance.delete_client(client_id)

            if delete_result['success']:
                # Folder removal logic might be re-evaluated.
                # For soft delete, typically data isn't removed from filesystem immediately.
                # For now, keeping the rmtree logic but it's less common with soft delete.
                # Consider making folder archival a separate process or based on a longer-term policy.
                if os.path.exists(client_folder_path):
                    # shutil.rmtree(client_folder_path, ignore_errors=True) # Reconsider this line for soft delete
                    logging.warning(f"Client {client_id} soft-deleted. Folder {client_folder_path} was NOT removed as part of soft delete.")

                # Update UI: remove from active list (if not showing deleted), update map
                if client_id in doc_manager.clients_data_map:
                    # If not showing deleted items, remove from map. Otherwise, update its state.
                    # A full refresh via load_and_display_clients with current filters is better.
                    del doc_manager.clients_data_map[client_id] # Or mark as deleted if map handles it

                # Refresh display considering current filters (especially include_deleted)
                doc_manager.filter_client_list_display_slot() # Use the main_window slot
                # load_and_display_clients(doc_manager)
                for i in range(doc_manager.client_tabs_widget.count()):
                    if hasattr(doc_manager.client_tabs_widget.widget(i), 'client_info') and \
                       doc_manager.client_tabs_widget.widget(i).client_info["client_id"] == client_id:
                        doc_manager.close_client_tab(i); break # close_client_tab is a method of DocumentManager
                doc_manager.stats_widget.update_stats()
                # QMessageBox.information(doc_manager, doc_manager.tr("Client Supprimé"),
                #                         doc_manager.tr("Client '{0}' supprimé avec succès.").format(client_name_val))
                doc_manager.notify(title=doc_manager.tr("Client Supprimé"),
                                   message=doc_manager.tr("Client '{0}' supprimé avec succès.").format(client_name_val),
                                   type='SUCCESS')
            else:
                error_message = delete_result.get('error', doc_manager.tr("Erreur inconnue."))
                QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"),
                                     doc_manager.tr("Erreur lors de la suppression (soft) du client: {0}").format(error_message))
                doc_manager.notify(title=doc_manager.tr("Erreur Suppression (Soft)"),
                                   message=doc_manager.tr("Erreur de suppression (soft) du client '{0}': {1}").format(client_name_val, error_message),
                                   type='ERROR')
        except OSError as e_os: # This error is now less likely if rmtree is removed for soft delete
            QMessageBox.critical(doc_manager, doc_manager.tr("Erreur Dossier"),
                                 doc_manager.tr("Le client a été marqué comme supprimé, mais une erreur est survenue lors d'une opération sur son dossier:\n{0}").format(str(e_os)))
            doc_manager.notify(title=doc_manager.tr("Erreur Opération Dossier"),
                               message=doc_manager.tr("Client '{0}' marqué supprimé, mais erreur d'opération sur dossier.").format(client_name_val),
                               type='WARNING')
            # Refresh client list even if folder operation had issues
            if client_id in doc_manager.clients_data_map:
                 del doc_manager.clients_data_map[client_id] # Or mark deleted
            doc_manager.filter_client_list_display_slot()
            # load_and_display_clients(doc_manager)
            for i in range(doc_manager.client_tabs_widget.count()):
                if hasattr(doc_manager.client_tabs_widget.widget(i), 'client_info') and \
                   doc_manager.client_tabs_widget.widget(i).client_info["client_id"] == client_id:
                    doc_manager.close_client_tab(i); break
            doc_manager.stats_widget.update_stats()
        except Exception as e_db:
             QMessageBox.critical(doc_manager, doc_manager.tr("Erreur DB"),
                                  doc_manager.tr("Erreur lors de la suppression du client:\n{0}").format(str(e_db)))
             doc_manager.notify(title=doc_manager.tr("Erreur Suppression Inattendue"),
                                message=doc_manager.tr("Erreur inattendue lors de la suppression du client '{0}'.").format(client_name_val),
                                type='ERROR')

# --- Invoice Generation and DB Update Logic ---
# Assuming invoice_generation_logic.py is at the same level or in PYTHONPATH
from invoice_generation_logic import generate_final_invoice_pdf
from db.cruds import client_documents_crud, invoices_crud # clients_crud is already imported
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
    Generates a final invoice PDF, saves it, and creates corresponding entries
    in ClientDocuments and Invoices tables.

    Args:
        client_id: ID of the client.
        company_id: ID of the seller company.
        target_language_code: Language for the invoice.
        line_items: List of product/service line items.
        project_id: Optional project ID.
        additional_context_overrides: Optional dict to override context values.
        created_by_user_id: Optional ID of the user creating the document.

    Returns:
        Tuple: (success_status, new_invoice_table_id, new_client_document_id)
    """
    logging.info(f"Attempting to create final invoice for client {client_id}, project {project_id}")

    pdf_bytes, suggested_filename, full_context = generate_final_invoice_pdf(
        client_id=client_id,
        company_id=company_id,
        target_language_code=target_language_code,
        line_items=line_items,
        project_id=project_id,
        additional_context_overrides=additional_context_overrides
    )

    if pdf_bytes is None or full_context is None:
        logging.error(f"Failed to generate PDF bytes or context for client {client_id}.")
        return False, None, None

    # Determine Save Path & Save PDF
    try:
        client_data = clients_crud.get_client_by_id(client_id) # Assumes this returns a dict-like object
        if not client_data or not client_data.get('default_base_folder_path'):
            logging.error(f"Client data or base folder path not found for client_id: {client_id}")
            return False, None, None

        # Construct save directory: <client_base_folder>/<lang>/Invoices/
        # Ensure lang code is filesystem-friendly; it usually is (e.g., "en", "fr")
        save_directory = os.path.join(client_data['default_base_folder_path'], target_language_code, "Invoices")
        os.makedirs(save_directory, exist_ok=True)

        final_pdf_path = os.path.join(save_directory, suggested_filename)

        with open(final_pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        logging.info(f"Successfully saved final invoice PDF to: {final_pdf_path}")

    except IOError as e:
        logging.error(f"IOError saving PDF for client {client_id}: {e}", exc_info=True)
        return False, None, None
    except Exception as e: # Catch other potential errors from client_data fetching or os ops
        logging.error(f"Error during PDF saving prep for client {client_id}: {e}", exc_info=True)
        return False, None, None

    # Create ClientDocuments Entry
    new_client_doc_id = None
    try:
        # Ensure default_base_folder_path ends with a separator for clean relpath, or handle robustly
        base_path_for_rel = client_data['default_base_folder_path']
        if not base_path_for_rel.endswith(os.path.sep):
            base_path_for_rel += os.path.sep

        # Check if final_pdf_path is indeed under base_path_for_rel before making relpath
        # This is a basic check. os.path.commonpath can be more robust if paths are complex.
        if not final_pdf_path.startswith(base_path_for_rel):
            logging.error(f"Generated PDF path '{final_pdf_path}' is not under client base folder '{base_path_for_rel}'. Cannot determine relative path.")
            # Consider cleanup: os.remove(final_pdf_path)
            return False, None, None

        relative_pdf_path = os.path.relpath(final_pdf_path, base_path_for_rel)


        client_doc_data = {
            'document_id': str(uuid.uuid4()), # Generate a new UUID for the document
            'client_id': client_id,
            'project_id': project_id,
            'order_identifier': full_context.get("doc", {}).get("invoice_number"), # Use invoice number as order_identifier
            'document_name': suggested_filename,
            'file_name_on_disk': suggested_filename,
            'file_path_relative': relative_pdf_path,
            'document_type_generated': "FINAL_INVOICE", # Specific type for final invoices
            'source_template_id': None, # Not directly from a template record in DB in this flow
            'version_tag': "1.0",
            'notes': f"Final Invoice generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'created_by_user_id': created_by_user_id
        }
        new_client_doc_id_from_crud = client_documents_crud.add_client_document(client_doc_data)

        if not new_client_doc_id_from_crud: # add_client_document should return the ID string
            logging.error(f"Failed to create ClientDocuments entry for invoice {suggested_filename}, client {client_id}.")
            # Consider cleanup: os.remove(final_pdf_path)
            return False, None, None
        new_client_doc_id = client_doc_data['document_id'] # Use the UUID we generated
        logging.info(f"ClientDocuments entry created with ID: {new_client_doc_id} (CRUD returned: {new_client_doc_id_from_crud})")

    except Exception as e:
        logging.error(f"Error creating ClientDocuments entry for client {client_id}: {e}", exc_info=True)
        # Consider cleanup: os.remove(final_pdf_path) if it was saved
        return False, None, None

    # Create Invoices Table Entry
    new_invoice_table_id = None
    try:
        doc_ctx = full_context.get("doc", {})
        invoice_table_data = {
            'invoice_id': str(uuid.uuid4()), # Generate a new UUID for the invoice table primary key
            'client_id': client_id,
            'project_id': project_id,
            'document_id': new_client_doc_id, # Link to the ClientDocuments entry
            'invoice_number': doc_ctx.get("invoice_number"),
            'issue_date': doc_ctx.get("issue_date"),
            'due_date': doc_ctx.get("due_date"),
            'total_amount': doc_ctx.get("grand_total_amount_raw"), # Use raw numeric value
            'currency': doc_ctx.get("currency_symbol"), # Ensure this is just symbol or code as per DB
            'payment_status': 'unpaid', # Default for new final invoices
            'payment_date': None,
            'payment_method': None,
            'transaction_id': None,
            'notes': doc_ctx.get("notes", ""),
            # created_at, updated_at are usually handled by DB defaults in Invoices table
        }

        # Ensure currency is just the code/symbol, not amount + symbol
        if invoice_table_data['currency'] and ' ' in invoice_table_data['currency']: # e.g. "1,234.00 EUR"
             invoice_table_data['currency'] = invoice_table_data['currency'].split(' ')[-1]
        elif len(invoice_table_data.get('currency', '')) > 3 : # e.g. "EUR" is fine, but "Euro" might be too long if schema expects code
             # This logic depends on how currency_symbol is formatted by format_currency and what DB expects
             # For now, assume currency_symbol from context is just the code like "USD", "EUR"
             pass


        new_invoice_table_id_from_crud = invoices_crud.add_invoice(invoice_table_data)
        if not new_invoice_table_id_from_crud:
            logging.error(f"Failed to create Invoices table entry for invoice number {doc_ctx.get('invoice_number')}.")
            # Consider cleanup: os.remove(final_pdf_path) and client_documents_crud.delete_client_document(new_client_doc_id)
            return False, None, new_client_doc_id
        new_invoice_table_id = invoice_table_data['invoice_id'] # Use the UUID we generated
        logging.info(f"Invoices table entry created with ID: {new_invoice_table_id} (CRUD returned: {new_invoice_table_id_from_crud})")

    except Exception as e:
        logging.error(f"Error creating Invoices table entry for client {client_id}: {e}", exc_info=True)
        # Consider cleanup: os.remove(final_pdf_path) and client_documents_crud.delete_client_document(new_client_doc_id) if new_client_doc_id exists
        return False, None, new_client_doc_id

    logging.info(f"Successfully created final invoice, ClientDocument, and Invoice DB entry for client {client_id}. Invoice ID: {new_invoice_table_id}, Document ID: {new_client_doc_id}")
    return True, new_invoice_table_id, new_client_doc_id
