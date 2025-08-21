# -*- coding: utf-8 -*-
import os
import shutil
import logging # Added for logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QLabel,
    QListWidget, QListWidgetItem, QComboBox, QGroupBox, QWidget, QApplication, QTextEdit
)
from PyQt5.QtGui import QIcon, QColor, QDesktopServices
from PyQt5.QtCore import Qt, QUrl, QSettings # Ajout de QSettings

import app.db as db_manager
from app.db.cruds.template_categories_crud import get_all_template_categories
from app.views.gui.widgets.html_editor import HtmlEditor
from app.utils import populate_docx_template
import app.icons_rc
from PyQt5.QtWidgets import QFormLayout

# Importer la nouvelle boîte de dialogue de choix et les constantes d'action
from .choose_html_template_action_dialog import ChooseHtmlTemplateActionDialog, ACTION_COPY_RAW, ACTION_GENERATE_DIRECT

# Constantes pour QSettings (pourraient être dans un fichier de constantes partagé)
HTML_TEMPLATE_DEFAULT_ACTION_KEY = "HtmlTemplate/defaultAction"
HTML_TEMPLATE_DONT_ASK_AGAIN_KEY = "HtmlTemplate/dontAskAgain"


# List of template types to be excluded from the "Generate via model" dialog (typically email templates)
# This list should be maintained to match the template_type values used for email templates in the database.
EMAIL_TEMPLATE_TYPES_TO_EXCLUDE = [
    "EMAIL_WELCOME", "EMAIL_RESET_PASSWORD", "EMAIL_NEWSLETTER_SUBSCRIPTION",
    "EMAIL_FOLLOW_UP", "EMAIL_HOLIDAY_CHRISTMAS", "EMAIL_HOLIDAY_NEWYEAR",
    "EMAIL_SAV_TICKET_OPENED", "EMAIL_SAV_TICKET_RESOLVED",
    "GENERIC_EMAIL_MESSAGE", "NEWSLETTER_BASE"
    # Add any other specific email template types used in your system
]

class CreateDocumentDialog(QDialog):
    # Maps internal type keys to user-friendly names and template_type filters
    DOCUMENT_TYPE_MAPPING = {
        "DEVIS": {"name": "Devis", "template_type_filter": "DEVIS_HTML"},
        "PROFORMA": {"name": "Facture Proforma", "template_type_filter": "PROFORMA_INVOICE_HTML"},
        "ORDER_FORM": {"name": "Bon de Commande", "template_type_filter": "ORDER_FORM_HTML"},
        "DELIVERY_NOTE": {"name": "Note de Livraison", "template_type_filter": "PACKING_LIST_HTML"},
        "SALES_CONTRACT": {"name": "Contrat de Vente", "template_type_filter": "SALES_CONTRACT_HTML"},
        "TECHNICAL_SPECIFICATIONS": {"name": "Spécifications Techniques", "template_type_filter": "TECHNICAL_SPECIFICATIONS_HTML"},
        "WARRANTY_DOCUMENT": {"name": "Document de Garantie", "template_type_filter": "WARRANTY_DOCUMENT_HTML"},
        "COVER_PAGE": {"name": "Page de Garde", "template_type_filter": "COVER_PAGE_HTML"},
        "PRODUCT_IMAGES": {"name": "Images Produits", "template_type_filter": "PRODUCT_IMAGES_HTML"},
        "CONTACT_PAGE": {"name": "Page Contact", "template_type_filter": "CONTACT_PAGE_HTML"},
        # Excel types
        "PROFORMA_EXCEL": {"name": "Facture Proforma (Excel)", "template_type_filter": "PROFORMA_EXCEL"},
        "PACKING_LIST_EXCEL": {"name": "Liste de Colisage (Excel)", "template_type_filter": "PACKING_LIST_EXCEL"},
        "SALES_CONTRACT_EXCEL": {"name": "Contrat de Vente (Excel)", "template_type_filter": "SALES_CONTRACT_EXCEL"},
        "TECHNICAL_SPECIFICATIONS_EXCEL": {"name": "Spécifications Techniques (Excel)", "template_type_filter": "TECHNICAL_SPECIFICATIONS_EXCEL"},
    }

    def __init__(self, client_info, config, app_root_dir, current_user_id, parent=None, template_data=None, old_document_id_to_version=None, order_identifier=None): # Ajout app_root_dir
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        # self.app_root_dir = config.get("app_root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Déjà présent, mais on reçoit app_root_dir
        self.app_root_dir = app_root_dir # S'assurer que app_root_dir est bien passé et stocké
        self.current_user_id = current_user_id
        self.pre_selected_template_id = template_data.get('template_id') if template_data else None
        self.old_document_id_to_version = old_document_id_to_version
        self.order_identifier = order_identifier

        self._action_performed = None # Pour stocker l'action réalisée (copy_raw ou generate_direct)

        self.setWindowTitle(self.tr("Générer Document(s) Client via Modèle"))
        if self.old_document_id_to_version:
            self.setWindowTitle(self.tr("Créer une Nouvelle Version du Document"))
        self.setMinimumSize(600, 400) # Peut-être ajuster si les filtres prennent plus de place
        self._init_ui()
        if self.pre_selected_template_id:
            self._select_and_load_pre_selected_template()

    def get_action_performed(self): # Nouvelle méthode pour DocumentsTab
        return self._action_performed

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Filters layout
        filters_group_box = QGroupBox(self.tr("Filtres"))
        filters_layout = QHBoxLayout(filters_group_box) # Use QHBoxLayout for horizontal alignment

        self.doc_type_combo = QComboBox()
        self.language_combo = QComboBox()

        doc_type_label = QLabel(self.tr("Type:"))
        filters_layout.addWidget(doc_type_label)
        filters_layout.addWidget(self.doc_type_combo)
        filters_layout.addSpacing(15) # Add some space between filter groups

        language_label = QLabel(self.tr("Langue:"))
        filters_layout.addWidget(language_label)
        filters_layout.addWidget(self.language_combo)
        filters_layout.addStretch(1) # Push filters to the left

        main_layout.addWidget(filters_group_box)

        # Template List
        self.template_list_widget = QListWidget()
        self.template_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        main_layout.addWidget(QLabel(self.tr("Modèles Disponibles (sélectionnez un ou plusieurs):")))
        main_layout.addWidget(self.template_list_widget, 1) # Give list widget stretch factor

        # Footer Notes Input
        footer_notes_group = QGroupBox(self.tr("Notes de Bas de Page (Optionnel)"))
        footer_notes_layout = QVBoxLayout(footer_notes_group)
        self.footer_notes_edit = QTextEdit()
        self.footer_notes_edit.setPlaceholderText(self.tr("Entrez ici les notes de bas de page personnalisées. Laissez vide pour utiliser les notes par défaut de la langue."))
        self.footer_notes_edit.setFixedHeight(80) # Adjust height as needed
        footer_notes_layout.addWidget(self.footer_notes_edit)
        main_layout.addWidget(footer_notes_group)

        self._load_document_types_and_languages() # Populates combos

        # Connect signals for filtering the template list
        self.doc_type_combo.currentIndexChanged.connect(self._filter_and_load_templates_for_selection)
        self.language_combo.currentIndexChanged.connect(self._filter_and_load_templates_for_selection)

        self._filter_and_load_templates_for_selection() # Initial load

        # Buttons
        button_layout = QHBoxLayout()
        self.view_folder_button = QPushButton("📁 " + self.tr("Voir Dossier Client"))
        self.view_folder_button.clicked.connect(self._handle_view_client_folder)
        button_layout.addWidget(self.view_folder_button)
        button_layout.addStretch(1)

        # Renommer le bouton pour refléter qu'il initie une action, pas seulement la génération
        self.action_button = QPushButton("✅ " + self.tr("Valider Sélection"))
        self.action_button.setObjectName("primaryButton")
        self.action_button.clicked.connect(self._handle_template_selection_action) # Nouvelle méthode de handler
        button_layout.addWidget(self.action_button)

        main_layout.addLayout(button_layout)

        dialog_button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        dialog_button_box.rejected.connect(self.reject)
        main_layout.addWidget(dialog_button_box)

    def _load_document_types_and_languages(self):
        # Populate Document Types
        self.doc_type_combo.blockSignals(True)
        self.doc_type_combo.clear()
        self.doc_type_combo.addItem(self.tr("Tous Types"), "ALL")
        for key, info in self.DOCUMENT_TYPE_MAPPING.items():
            self.doc_type_combo.addItem(self.tr(info["name"]), info["template_type_filter"])
        self.doc_type_combo.blockSignals(False)

        # Populate Languages
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItem(self.tr("Toutes Langues"), "ALL")

        client_languages = self.client_info.get('selected_languages', [])
        if isinstance(client_languages, str):
            client_languages = [lang.strip() for lang in client_languages.split(',') if lang.strip()]

        system_languages = ["fr", "en", "ar", "tr", "pt", "ru"] # Ou depuis config
        effective_langs_for_combo = sorted(list(set(client_languages + system_languages)))

        for lang_code in effective_langs_for_combo:
            self.language_combo.addItem(lang_code.upper(), lang_code)

        if not effective_langs_for_combo and self.language_combo.count() <= 1:
            self.language_combo.addItem("FR", "fr")
        self.language_combo.blockSignals(False)

    def _filter_and_load_templates_for_selection(self):
        self.template_list_widget.clear()
        selected_type_filter = self.doc_type_combo.currentData()
        selected_lang_filter = self.language_combo.currentData()

        filter_params = {'apply_visibility_filter': True}
        if selected_type_filter and selected_type_filter != "ALL":
            filter_params['template_type_filter_list'] = [selected_type_filter]
        if selected_lang_filter and selected_lang_filter != "ALL":
            filter_params['language_code_filter'] = selected_lang_filter

        client_id = self.client_info.get('client_id')
        client_specific_templates = []
        if client_id:
            client_filter_params = filter_params.copy()
            client_filter_params['client_id_filter'] = client_id
            client_specific_templates = db_manager.get_all_templates(**client_filter_params) or []

        global_filter_params = filter_params.copy()
        global_filter_params['client_id_filter'] = None
        global_templates = db_manager.get_all_templates(**global_filter_params) or []

        displayed_template_ids = set()
        for template in client_specific_templates:
            item_text = f"{template.get('template_name')} ({template.get('language_code')}) - Client"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, template.get('template_id'))
            self.template_list_widget.addItem(list_item)
            displayed_template_ids.add(template.get('template_id'))
            if self.pre_selected_template_id and template.get('template_id') == self.pre_selected_template_id:
                list_item.setSelected(True)

        for template in global_templates:
            if template.get('template_id') not in displayed_template_ids:
                item_text = f"{template.get('template_name')} ({template.get('language_code')}) - Global"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, template.get('template_id'))
                self.template_list_widget.addItem(list_item)
                if self.pre_selected_template_id and template.get('template_id') == self.pre_selected_template_id:
                    list_item.setSelected(True)

        if self.template_list_widget.count() == 0:
            self.template_list_widget.addItem(self.tr("Aucun modèle ne correspond aux filtres."))

    def _select_and_load_pre_selected_template(self):
        if not self.pre_selected_template_id: return
        template_details = db_manager.get_template_by_id(self.pre_selected_template_id)
        if not template_details: return

        lang_code_to_select = template_details.get('language_code')
        if lang_code_to_select:
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == lang_code_to_select:
                    self.language_combo.setCurrentIndex(i); break

        template_actual_type = template_details.get('template_type')
        if template_actual_type:
            for i in range(self.doc_type_combo.count()):
                if self.doc_type_combo.itemData(i) == template_actual_type:
                    self.doc_type_combo.setCurrentIndex(i); break
        self._filter_and_load_templates_for_selection()

    def _get_selected_template_ids_and_lang_for_direct_generation(self): # Renommée pour clarté
        selected_items = self.template_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner au moins un modèle."))
            return None, None

        template_ids = [item.data(Qt.UserRole) for item in selected_items]
        language_code_from_combo = self.language_combo.currentData()
        if language_code_from_combo == "ALL":
            language_code_from_combo = None # Le modèle utilisera sa propre langue
        return template_ids, language_code_from_combo

    def _handle_template_selection_action(self): # Nouvelle méthode principale
        selected_items = self.template_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner au moins un modèle."))
            return

        if len(selected_items) == 1:
            template_id = selected_items[0].data(Qt.UserRole)
            template_details = db_manager.get_template_by_id(template_id)

            if template_details and template_details.get('template_type', '').endswith('_HTML'):
                self._process_single_html_template_with_choice(template_details)
                return # Le traitement est géré par la méthode ci-dessus

        # Pour sélection multiple, ou templates non-HTML, ou si le choix HTML n'a pas abouti à une action
        # (par exemple, dialogue de choix annulé mais on veut quand même essayer de générer les autres),
        # on procède à la génération directe.
        self._perform_direct_generation_for_selected()


    def _process_single_html_template_with_choice(self, template_details: dict):
        settings = QSettings(self.config.get("organization_name", "MaSociete"), self.config.get("application_name", "MonApp"))
        dont_ask_again = settings.value(HTML_TEMPLATE_DONT_ASK_AGAIN_KEY, False, type=bool)
        default_action = settings.value(HTML_TEMPLATE_DEFAULT_ACTION_KEY, ACTION_GENERATE_DIRECT) # Default à generate_direct

        chosen_action = None

        if dont_ask_again:
            chosen_action = default_action
            logging.info(f"Préférence mémorisée trouvée : {chosen_action}, Ne plus demander : {dont_ask_again}")
        else:
            logging.info(f"Affichage du dialogue de choix. Préférence actuelle (pour pré-sélection) : {default_action}")
            choice_dialog = ChooseHtmlTemplateActionDialog(
                template_name=template_details.get('template_name'),
                client_name=self.client_info.get('client_name', self.client_info.get('company_name')),
                parent=self
            )
            choice_dialog.set_default_choice(default_action)
            if choice_dialog.exec_() == QDialog.Accepted:
                chosen_action = choice_dialog.get_chosen_action()
                do_not_ask_again_preference = choice_dialog.get_dont_ask_again_preference()
                logging.info(f"Dialogue de choix accepté. Action: {chosen_action}, Mémoriser: {do_not_ask_again_preference}")

                if do_not_ask_again_preference:
                    settings.setValue(HTML_TEMPLATE_DEFAULT_ACTION_KEY, chosen_action)
                    settings.setValue(HTML_TEMPLATE_DONT_ASK_AGAIN_KEY, True)
                else:
                    # Sauvegarder le dernier choix comme défaut pour la prochaine fois, mais Ne Plus Demander reste False
                    settings.setValue(HTML_TEMPLATE_DEFAULT_ACTION_KEY, chosen_action)
                    settings.setValue(HTML_TEMPLATE_DONT_ASK_AGAIN_KEY, False)
            else:
                logging.info("Dialogue de choix annulé par l'utilisateur.")
                self.reject() # L'utilisateur a annulé le dialogue de choix
                return

        if chosen_action == ACTION_COPY_RAW:
            self._action_performed = ACTION_COPY_RAW
            success = self._perform_copy_raw_template(template_details) # Implémenté à l'étape 4
            if success:
                self.accept()
            else:
                self.reject() # Erreur gérée dans _perform_copy_raw_template

        elif chosen_action == ACTION_GENERATE_DIRECT:
            self._action_performed = ACTION_GENERATE_DIRECT
            current_lang_filter = self.language_combo.currentData()
            language_code_for_generation = current_lang_filter if current_lang_filter != "ALL" else template_details.get('language_code')

            generated_file_path = self._generate_document_from_template_id(template_details.get('template_id'), language_code_for_generation)
            if generated_file_path and os.path.exists(generated_file_path):
                # QMessageBox.information(self, self.tr("Document Généré"), self.tr("Le document a été généré avec succès."))
                # L'ouverture du fichier est gérée par le dialogue parent si nécessaire
                self.accept()
            # Les erreurs sont gérées dans _generate_document_from_template_id ou par l'appelant
            # else: self.reject() # Si échec, _generate_document_from_template_id devrait notifier
        else:
            logging.info("Aucune action choisie ou dialogue annulé avant la sélection d'action.")
            self.reject() # Pas d'action choisie ou dialogue annulé

    def _perform_direct_generation_for_selected(self):
        template_ids, language_context = self._get_selected_template_ids_and_lang_for_direct_generation()
        if not template_ids:
            return # Message d'erreur déjà affiché par _get_selected_template_ids_and_lang

        generated_paths = []
        generated_count = 0
        for template_id in template_ids:
            template_details = db_manager.get_template_by_id(template_id)
            if not template_details:
                logging.warning(f"Template ID {template_id} non trouvé lors de la génération directe. Ignoré.")
                continue

            # Si c'est un template HTML et qu'on est dans ce flux (ex: sélection multiple),
            # on ne présente pas le choix "copie brute", on génère directement.
            actual_generation_language = language_context if language_context else template_details.get('language_code')
            if not actual_generation_language:
                QMessageBox.warning(self, self.tr("Erreur Langue"), self.tr(f"Impossible de déterminer la langue pour le modèle {template_details.get('template_name')}. Document ignoré."))
                continue

            generated_file_path = self._generate_document_from_template_id(template_id, actual_generation_language)
            if generated_file_path and os.path.exists(generated_file_path):
                generated_paths.append(generated_file_path)
                generated_count += 1
            elif generated_file_path: # Généré mais non trouvé (erreur)
                 QMessageBox.warning(self, self.tr("Erreur Fichier Partiel"), self.tr("Le fichier pour '{0}' semble avoir été généré mais est introuvable.").format(template_details.get('template_name')))

        if generated_count > 0:
            self._action_performed = ACTION_GENERATE_DIRECT # Marquer l'action
            if len(generated_paths) == 1 and generated_count == 1 : # Si un seul doc a été généré avec succès
                 # Pas de message ici, DocumentsTab s'en chargera peut-être, ou ouverture directe
                 pass # L'ouverture est mieux gérée par le parent
            else:
                QMessageBox.information(self, self.tr("Documents Générés"),
                                        self.tr("{0} document(s) ont été générés avec succès.").format(generated_count))
            self.accept()
        elif template_ids and generated_count == 0: # Tentative mais tout a échoué
            QMessageBox.warning(self, self.tr("Échec Génération"), self.tr("Aucun document n'a pu être généré avec succès."))
            self.reject()
        else: # Pas de templates sélectionnés ou autre cas non géré
            self.reject()


    def _handle_view_client_folder(self):
        client_base_folder = self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path")
        if client_base_folder:
            # Assurer que le chemin est absolu si stocké relativement à app_root_dir
            if not os.path.isabs(client_base_folder) and self.app_root_dir:
                client_base_folder = os.path.join(self.app_root_dir, client_base_folder)

            if os.path.isdir(client_base_folder):
                try:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(client_base_folder))
                except Exception as e:
                    logging.error(f"Error opening client folder {client_base_folder}: {e}", exc_info=True)
                    QMessageBox.warning(self, self.tr("Erreur Ouverture Dossier"), self.tr("Impossible d'ouvrir le dossier client : {0}").format(str(e)))
            else:
                QMessageBox.warning(self, self.tr("Dossier Invalide"), self.tr("Le dossier client '{0}' est invalide ou inaccessible.").format(client_base_folder))
        else:
            QMessageBox.warning(self, self.tr("Dossier Introuvable"), self.tr("Le dossier de base du client n'est pas configuré."))


    def _generate_document_from_template_id(self, template_id, language_code_for_generation):
        """
        Generates a document using a specific template_id.
        language_code_for_generation specifies the language context for data fetching and notes.
        The template itself has an inherent language.
        """
        logging.info(f"Attempting to generate document from template_id='{template_id}', lang_context='{language_code_for_generation}' for client_id='{self.client_info.get('client_id')}'")

        chosen_template = db_manager.get_template_by_id(template_id)
        if not chosen_template:
            QMessageBox.critical(self, self.tr("Erreur Modèle"), self.tr("Modèle avec ID '{0}' introuvable.").format(template_id))
            return None

        template_base_filename = chosen_template.get('base_file_name')
        template_inherent_language = chosen_template.get('language_code') # Langue du fichier modèle
        template_actual_type = chosen_template.get('template_type')
        template_display_name_for_output = chosen_template.get('template_name', 'Document')

        # Déterminer le chemin absolu du fichier modèle source
        # Cela suppose que config.get("templates_dir") est relatif à self.app_root_dir ou absolu
        # Si self.config.get("templates_dir") est déjà un chemin absolu, os.path.join fonctionnera correctement.
        # Si c'est un chemin relatif, il sera joint à self.app_root_dir.
        # Il faut s'assurer que self.config.get("templates_dir") est bien défini.
        # Par défaut, si "templates_dir" n'est pas dans config, on utilise un sous-dossier "templates" de app_root_dir.
        # Mais pour les modèles de base, ils sont souvent dans "resources/templates".
        # Le plus sûr est de se baser sur la structure connue où les templates sont dans "resources/templates"
        # à la racine du projet (app_root_dir).

        if not self.app_root_dir or not os.path.isdir(self.app_root_dir):
             QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le dossier racine de l'application n'est pas correctement configuré."))
             return None

        # Chemin vers le dossier des templates de base, par exemple "resources/templates"
        # Adapter ce chemin si la structure est différente.
        base_templates_folder = os.path.join(self.app_root_dir, "resources", "templates")
        template_file_on_disk_abs = os.path.join(base_templates_folder, template_inherent_language, template_base_filename)

        if not os.path.exists(template_file_on_disk_abs):
             # Tentative avec un chemin alternatif (si pas de sous-dossier langue pour certains types)
             template_file_on_disk_abs_alt = os.path.join(base_templates_folder, template_base_filename)
             if os.path.exists(template_file_on_disk_abs_alt):
                 template_file_on_disk_abs = template_file_on_disk_abs_alt
             else:
                QMessageBox.warning(self, self.tr("Fichier Modèle Introuvable"),
                                    self.tr("Le fichier modèle '{0}' (lang: {1}) est introuvable dans '{2}' ou '{3}'.")
                                    .format(template_base_filename, template_inherent_language,
                                            os.path.join(base_templates_folder, template_inherent_language),
                                            base_templates_folder))
                return None

        # Prepare Context Data
        default_company_obj = db_manager.get_default_company()
        default_company_id = default_company_obj['company_id'] if default_company_obj else None
        if not default_company_id:
            QMessageBox.warning(self, self.tr("Config Erreur"), self.tr("Société par défaut non définie. Certaines informations pourraient manquer."))
            # On peut continuer mais le document sera incomplet

        client_id_for_context = self.client_info.get('client_id')
        # project_id_for_context_arg = self.client_info.get('project_id') # project_id est sur self.client_info
        # self.order_identifier est l'identifiant de la commande actuelle pour ce dialogue

        document_type_for_notes_fetch = template_actual_type
        additional_context_for_gen = {
            'document_type': template_actual_type, # Type du template source
            'current_document_type_for_notes': document_type_for_notes_fetch,
            'footer_notes': self.footer_notes_edit.toPlainText().strip(),
            'order_id': self.order_identifier # Passer l'order_identifier au contexte
        }

        # Le project_id peut être lié à la commande (order_identifier) ou au client.
        # Il faut une logique pour déterminer le bon project_id pour le contexte.
        # Pour l'instant, utilisons self.order_identifier si présent, sinon le project_id du client_info.
        project_id_for_context = None
        if self.order_identifier:
            # Essayer de trouver le project_id associé à cette commande
            # Ceci nécessiterait une fonction comme get_project_id_for_order(order_identifier)
            # Pour l'instant, on suppose que le project_id du client est pertinent
            # ou que le contexte peut le gérer via order_identifier.
             pass # Le contexte builder utilisera order_id pour trouver le projet associé si nécessaire.
        # else: project_id_for_context = self.client_info.get('project_id') # Pas standard sur client_info

        document_context = db_manager.get_document_context_data(
            client_id=client_id_for_context,
            company_id=default_company_id,
            target_language_code=language_code_for_generation,
            project_id=project_id_for_context, # Peut être None
            order_id=self.order_identifier, # Transmettre l'order_id
            document_type=template_actual_type, # Type du template source
            additional_context=additional_context_for_gen,
            app_root_dir=self.app_root_dir
        )
        if not document_context: # Ou si le contexte est minimal à cause d'erreurs
            logging.warning(f"Contexte documentaire incomplet ou non généré pour template {template_id}.")
            # On pourrait afficher un message d'erreur plus spécifique ici.
            # QMessageBox.warning(self, self.tr("Erreur Contexte"), self.tr("Impossible de générer toutes les données pour le document."))
            # Pour l'instant, on continue, le document sera généré avec les données disponibles.
            if document_context is None: document_context = {} # Assurer que c'est un dict

        # Determine Output Filename and Path
        client_base_folder_relative = self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path")
        if not client_base_folder_relative:
            QMessageBox.critical(self, self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré."))
            return None

        client_base_folder_absolute = os.path.join(self.app_root_dir, client_base_folder_relative)
        if not os.path.isdir(client_base_folder_absolute):
            try:
                os.makedirs(client_base_folder_absolute, exist_ok=True)
            except OSError as e_mkdir_base:
                QMessageBox.critical(self, self.tr("Erreur Dossier Client"), self.tr("Impossible de créer le dossier de base du client '{0}':\n{1}").format(client_base_folder_absolute, e_mkdir_base))
                return None
        
        doc_type_name_for_folder = template_display_name_for_output.replace(" ", "_").replace("/", "_")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_ext = os.path.splitext(template_base_filename)[1].lower() # s'assurer qu'il est en minuscule

        client_name_for_file = "".join(c if c.isalnum() else "_" for c in self.client_info.get('client_name', 'Client'))
        output_filename_base = f"{client_name_for_file}_{doc_type_name_for_folder}_{language_code_for_generation}_{timestamp_str}"
        output_filename = f"{output_filename_base}{original_ext}"

        # Structure de dossier: client_base/order_id_safe (si commande)/langue/nom_type_template/fichier
        target_doc_folder_final_level = os.path.join(language_code_for_generation, doc_type_name_for_folder)
        if self.order_identifier:
            safe_order_subfolder = self.order_identifier.replace(':', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
            target_doc_folder_final_level = os.path.join(safe_order_subfolder, target_doc_folder_final_level)

        target_doc_folder_abs = os.path.join(client_base_folder_absolute, target_doc_folder_final_level)
        os.makedirs(target_doc_folder_abs, exist_ok=True)
        output_file_path_abs = os.path.join(target_doc_folder_abs, output_filename)

        # Generation Logic
        generation_success = False
        final_generated_file_path = output_file_path_abs
        final_output_filename = output_filename
        final_document_type_for_db = template_actual_type # Type du template source initialement

        try:
            shutil.copy(template_file_on_disk_abs, output_file_path_abs) # Copie initiale

            if template_actual_type.endswith('_HTML') or original_ext == '.html':
                with open(output_file_path_abs, 'r', encoding='utf-8') as f: html_content_str = f.read()
                populated_html = HtmlEditor.populate_html_content(html_content_str, document_context)
                with open(output_file_path_abs, 'w', encoding='utf-8') as f: f.write(populated_html)
                generation_success = True # HTML peuplé avec succès

                # Tentative de conversion en PDF
                from utils.html_to_pdf_util import convert_html_to_pdf, WeasyPrintError
                pdf_output_filename_base = f"{output_filename_base}.pdf" # Nom de fichier si PDF
                pdf_output_path_abs = os.path.join(target_doc_folder_abs, pdf_output_filename_base)

                # base_url pour WeasyPrint : dossier du template original
                base_url_for_pdf_conversion = QUrl.fromLocalFile(os.path.dirname(template_file_on_disk_abs)).toString()

                try:
                    pdf_bytes = convert_html_to_pdf(populated_html, base_url=base_url_for_pdf_conversion)
                    if pdf_bytes:
                        with open(pdf_output_path_abs, 'wb') as f_pdf: f_pdf.write(pdf_bytes)
                        logging.info(f"Conversion HTML en PDF réussie : {pdf_output_path_abs}")
                        final_generated_file_path = pdf_output_path_abs
                        final_output_filename = pdf_output_filename_base
                        final_document_type_for_db = template_actual_type.replace("_HTML", "_PDF") if "_HTML" in template_actual_type else f"{template_actual_type}_PDF"
                        try: # Optionnel : supprimer le HTML peuplé intermédiaire
                            os.remove(output_file_path_abs)
                        except OSError: pass
                    else: # convert_html_to_pdf a retourné None (par exemple, contenu HTML vide après peuplement)
                        logging.warning(f"convert_html_to_pdf a retourné None pour {output_filename}. Le HTML peuplé sera conservé.")
                        # generation_success est déjà True (HTML peuplé sauvegardé)
                except WeasyPrintError as e_w_pdf:
                    logging.error(f"Échec conversion PDF pour {output_filename}: {e_w_pdf}. Le HTML peuplé sera conservé.")
                    QMessageBox.warning(self, self.tr("Erreur Conversion PDF"),
                                        self.tr("La conversion du HTML en PDF a échoué pour '{0}'. Le fichier HTML peuplé a été sauvegardé.\nErreur: {1}")
                                        .format(output_filename, str(e_w_pdf)))
                    # generation_success est déjà True (HTML peuplé sauvegardé)

            elif original_ext == '.docx': # Pour les templates Word
                populate_docx_template(output_file_path_abs, document_context) # Assurez-vous que cette fonction existe et est correcte
                generation_success = True
            elif original_ext == '.xlsx': # Pour les templates Excel
                # La population Excel est plus complexe et peut nécessiter une bibliothèque comme openpyxl.
                # Pour l'instant, on se contente de copier le template. Une logique de peuplement pourrait être ajoutée.
                logging.info(f"Template Excel '{template_display_name_for_output}' copié. Le peuplement n'est pas implémenté.")
                generation_success = True # Copie réussie
            else:
                logging.info(f"Type de template '{template_actual_type}' (ext: {original_ext}) non géré spécifiquement pour le peuplement. Fichier copié tel quel.")
                generation_success = True # Copie réussie

        except Exception as e_gen:
            logging.error(f"Erreur durant la génération du document pour {final_output_filename} (template ID {template_id}): {e_gen}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Génération"), self.tr("Erreur lors de la génération de '{0}':\n{1}").format(final_output_filename, str(e_gen)))
            return None

        if not generation_success: return None

        # Enregistrement en base de données
        # Le chemin relatif est par rapport à client_base_folder_absolute
        relative_path_for_db = os.path.relpath(final_generated_file_path, client_base_folder_absolute)

        doc_db_data = {
            'client_id': client_id_for_context,
            # 'project_id': project_id_for_context, # Le contexte builder peut avoir trouvé un project_id via order_id
            'project_id': document_context.get("order", {}).get("project_id") if self.order_identifier else document_context.get("project", {}).get("id"),
            'order_identifier': self.order_identifier if self.order_identifier else document_context.get('order', {}).get('reference'),
            'document_name': final_output_filename, # Ou un nom plus descriptif, par ex. template_display_name_for_output
            'file_name_on_disk': final_output_filename,
            'file_path_relative': relative_path_for_db,
            'document_type_generated': final_document_type_for_db,
            'source_template_id': template_id,
            'user_id': self.current_user_id,
            'language_code': language_code_for_generation, # Langue du document généré
            'version_tag': "1.0" # Version initiale
        }

        # Logique pour nouvelle version si old_document_id_to_version est fourni
        new_doc_id = None
        try:
            if self.old_document_id_to_version:
                logging.info(f"Création d'une nouvelle version pour l'ancien document ID: {self.old_document_id_to_version}")
                new_doc_id = db_manager.client_documents_crud.create_new_document_version(
                    old_document_id=self.old_document_id_to_version,
                    new_document_data=doc_db_data
                )
            else:
                new_doc_id = db_manager.client_documents_crud.add_client_document(doc_db_data)

            if new_doc_id:
                logging.info(f"Document '{final_output_filename}' (DB ID: {new_doc_id}) traité pour client {client_id_for_context}")
                return final_generated_file_path # Retourner le chemin absolu du fichier généré
            else:
                QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Document généré mais échec de l'enregistrement en base de données."))
                if os.path.exists(final_generated_file_path):
                    try: os.remove(final_generated_file_path)
                    except OSError: logging.warning(f"Impossible de nettoyer {final_generated_file_path} après échec DB.")
                return None
        except Exception as e_db_add:
            logging.error(f"Erreur ajout/versionnement document en DB {final_output_filename}: {e_db_add}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Erreur lors de l'enregistrement du document en DB:\n{0}").format(str(e_db_add)))
            if os.path.exists(final_generated_file_path):
                try: os.remove(final_generated_file_path)
                except OSError: logging.warning(f"Impossible de nettoyer {final_generated_file_path} après échec DB.")
            return None

    def _perform_copy_raw_template(self, template_details: dict) -> bool:
        """
        Copie le contenu d'un modèle HTML brut dans le dossier du client
        et enregistre une entrée dans la base de données.
        """
        try:
            template_id = template_details.get('template_id')
            template_base_filename = template_details.get('base_file_name')
            template_language_code = template_details.get('language_code')
            template_name_for_output = template_details.get('template_name', 'Copied_Template')

            html_content_bytes = template_details.get('raw_template_file_data')
            html_content_str = None

            if isinstance(html_content_bytes, bytes):
                try: html_content_str = html_content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    QMessageBox.critical(self, self.tr("Erreur Encodage Modèle"), self.tr("Le contenu du modèle HTML source (ID: {0}) n'est pas en UTF-8 valide.").format(template_id))
                    return False
            elif isinstance(html_content_bytes, str): html_content_str = html_content_bytes

            if not html_content_str:
                if not self.app_root_dir or not os.path.isdir(self.app_root_dir):
                    QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le dossier racine de l'application n'est pas configuré. Impossible de trouver le modèle source."))
                    return False

                base_templates_folder = os.path.join(self.app_root_dir, "resources", "templates")
                source_template_path = os.path.join(base_templates_folder, template_language_code, template_base_filename)

                if not os.path.exists(source_template_path):
                    source_template_path_alt = os.path.join(base_templates_folder, template_base_filename)
                    if os.path.exists(source_template_path_alt): source_template_path = source_template_path_alt
                    else:
                        QMessageBox.critical(self, self.tr("Fichier Modèle Introuvable"), self.tr("Le fichier modèle source '{0}' (lang: {1}) est introuvable.").format(template_base_filename, template_language_code))
                        return False
                try:
                    with open(source_template_path, 'r', encoding='utf-8') as f_source: html_content_str = f_source.read()
                except IOError as e_io:
                    QMessageBox.critical(self, self.tr("Erreur Lecture Modèle"), self.tr("Impossible de lire le fichier modèle source '{0}':\n{1}").format(source_template_path, e_io))
                    return False

            if not html_content_str:
                QMessageBox.critical(self, self.tr("Contenu Modèle Vide"), self.tr("Le contenu du modèle HTML source (ID: {0}) est vide.").format(template_id))
                return False

            client_relative_base_path = self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path")
            if not client_relative_base_path:
                QMessageBox.critical(self, self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré."))
                return False

            client_abs_base_path = os.path.join(self.app_root_dir, client_relative_base_path)

            target_subfolder_name = "Modeles_HTML_Modifiables"
            target_folder_final_level = os.path.join(template_language_code, target_subfolder_name)

            order_identifier_for_path = self.order_identifier
            safe_order_subfolder = None
            if order_identifier_for_path:
                safe_order_subfolder = order_identifier_for_path.replace(':', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
                target_folder_final_level = os.path.join(safe_order_subfolder, target_folder_final_level)

            target_dir_abs = os.path.join(client_abs_base_path, target_folder_final_level)
            os.makedirs(target_dir_abs, exist_ok=True)

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_template_name_for_file = "".join(c if c.isalnum() else "_" for c in template_name_for_output)
            client_name_for_file = "".join(c if c.isalnum() else "_" for c in self.client_info.get('client_name', 'Client'))

            dest_filename = f"{client_name_for_file}_{safe_template_name_for_file}_{template_language_code}_{timestamp_str}_editable.html"
            target_file_path_abs = os.path.join(target_dir_abs, dest_filename)

            try:
                with open(target_file_path_abs, 'w', encoding='utf-8') as f_dest: f_dest.write(html_content_str)
            except IOError as e_io_write:
                QMessageBox.critical(self, self.tr("Erreur Écriture Fichier"), self.tr("Impossible de sauvegarder le modèle HTML brut:\n{0}").format(e_io_write))
                return False

            file_path_relative_to_client_base = os.path.relpath(target_file_path_abs, client_abs_base_path)

            doc_db_data = {
                "client_id": self.client_info.get("client_id"),
                "document_name": f"{template_name_for_output} (Copie Brute)",
                "file_name_on_disk": dest_filename,
                "file_path_relative": file_path_relative_to_client_base,
                "document_type_generated": "EDITABLE_HTML",
                "language_code": template_language_code,
                "source_template_id": template_id,
                "order_identifier": order_identifier_for_path,
                "user_id": self.current_user_id,
                "notes": f"Modèle HTML brut '{template_name_for_output}' (ID: {template_id}) copié.",
                "version_tag": "1.0_raw"
            }

            new_doc_id = db_manager.client_documents_crud.add_client_document(doc_db_data)
            if not new_doc_id:
                QMessageBox.critical(self, self.tr("Erreur Base de Données"), self.tr("Échec de l'enregistrement du modèle HTML brut copié en DB."))
                try: os.remove(target_file_path_abs)
                except OSError: logging.warning(f"Impossible de supprimer {target_file_path_abs} après échec DB.")
                return False

            logging.info(f"Modèle HTML brut '{dest_filename}' (DB ID: {new_doc_id}) copié pour client {self.client_info.get('client_id')}")
            return True

        except Exception as e:
            logging.error(f"Erreur inattendue dans _perform_copy_raw_template: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur inattendue lors de la copie du modèle HTML brut:\n{0}").format(e))
            return False


    # Remove old methods related to template list display
    def has_multiple_purchase_events(self): return False
    def load_templates(self): pass
    def create_documents(self): pass
