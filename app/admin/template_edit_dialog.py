# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QDialogButtonBox, QMessageBox, QCheckBox, QLabel,
    QFileDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Importer les constantes et CRUD nécessaires
from app.utils.app_constants import SUPPORTED_LANGUAGES
from app.db.cruds import template_categories_crud, clients_crud # Pour lister les clients

class TemplateEditDialog(QDialog):
    def __init__(self, template_data: dict = None, app_root_dir: str = None, config: object = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.template_data = template_data # None pour mode ajout, données pour mode édition
        self.app_root_dir = app_root_dir
        self.config = config
        self.selected_file_path = None # Pour stocker le chemin du fichier uploadé

        if self.template_data:
            self.setWindowTitle(self.tr("Modifier Modèle de Document"))
        else:
            self.setWindowTitle(self.tr("Ajouter Nouveau Modèle de Document"))

        self.setMinimumWidth(600)
        self._setup_ui()
        self._populate_combos()

        if self.template_data:
            self._populate_form_for_edit()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.template_name_edit = QLineEdit()
        form_layout.addRow(self.tr("Nom du Modèle *:"), self.template_name_edit)

        self.template_type_combo = QComboBox()
        # Types communs, pourraient être chargés dynamiquement ou depuis constantes
        # Pour l'instant, quelques exemples. DOCUMENT_TYPE_PROFORMA_HTML etc. sont dans app_constants
        # from utils.app_constants import DOCUMENT_TYPE_PROFORMA_HTML, DOCUMENT_TYPE_PACKING_LIST_PDF # etc.
        # self.template_type_combo.addItem(DOCUMENT_TYPE_PROFORMA_HTML, DOCUMENT_TYPE_PROFORMA_HTML)
        # self.template_type_combo.addItem(DOCUMENT_TYPE_PACKING_LIST_PDF, DOCUMENT_TYPE_PACKING_LIST_PDF)
        self.template_type_combo.addItem("HTML_PROFORMA", "HTML_PROFORMA") # Exemple
        self.template_type_combo.addItem("HTML_PACKING_LIST", "HTML_PACKING_LIST") # Exemple
        self.template_type_combo.addItem("EMAIL_WELCOME", "EMAIL_WELCOME") # Exemple
        self.template_type_combo.addItem("DOCUMENT_EXCEL", "DOCUMENT_EXCEL")
        self.template_type_combo.addItem("DOCUMENT_WORD", "DOCUMENT_WORD")
        self.template_type_combo.setEditable(True) # Permettre d'entrer de nouveaux types
        form_layout.addRow(self.tr("Type de Modèle *:"), self.template_type_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(60)
        form_layout.addRow(self.tr("Description:"), self.description_edit)

        self.language_combo = QComboBox()
        form_layout.addRow(self.tr("Langue *:"), self.language_combo)

        self.category_combo = QComboBox()
        form_layout.addRow(self.tr("Catégorie:"), self.category_combo)

        self.client_id_combo = QComboBox() # Pourrait être une recherche plus tard
        form_layout.addRow(self.tr("Client Spécifique (optionnel):"), self.client_id_combo)

        self.version_edit = QLineEdit()
        form_layout.addRow(self.tr("Version:"), self.version_edit)

        self.is_default_checkbox = QCheckBox(self.tr("Marquer comme défaut pour ce type/langue/client"))
        form_layout.addRow(self.is_default_checkbox)

        # Section Fichier
        file_layout = QHBoxLayout()
        self.base_file_name_edit = QLineEdit()
        self.base_file_name_edit.setPlaceholderText(self.tr("Ex: proforma_tpl.html (si non stocké en DB)"))
        self.base_file_name_edit.setReadOnly(True) # Lecture seule si on uploade dans raw_template_file_data
        file_layout.addWidget(self.base_file_name_edit)

        self.browse_button = QPushButton(self.tr("Parcourir..."))
        self.browse_button.clicked.connect(self._on_browse_file)
        file_layout.addWidget(self.browse_button)
        form_layout.addRow(self.tr("Fichier de Base / Upload:"), file_layout)
        self.selected_file_label = QLabel(self.tr("Aucun nouveau fichier sélectionné."))
        form_layout.addRow(self.selected_file_label)

        form_layout.addRow(QLabel(self.tr("Contenu Brut (pour templates en DB, ex: HTML, Texte):")))
        self.raw_content_edit = QTextEdit()
        self.raw_content_edit.setPlaceholderText(self.tr("Coller le contenu HTML/Texte ici, ou il sera lu depuis le fichier uploadé si applicable."))
        self.raw_content_edit.setAcceptRichText(False)
        self.raw_content_edit.setFixedHeight(150)
        form_layout.addWidget(self.raw_content_edit) # Ajouter directement au form_layout pour qu'il prenne toute la largeur

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText(self.tr("Sauvegarder"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))
        self.button_box.accepted.connect(self._on_accept_data)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _populate_combos(self):
        # Langues
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(self.tr(lang_name) + f" ({lang_code})", lang_code)
        self.language_combo.setCurrentIndex(self.language_combo.findData("fr")) # Défaut Français

        # Catégories
        self.category_combo.addItem(self.tr("Aucune catégorie"), None)
        try:
            categories = template_categories_crud.get_all_template_categories()
            if categories:
                for cat in categories:
                    self.category_combo.addItem(cat.get('category_name'), cat.get('category_id'))
        except Exception as e:
            self.logger.error(f"Erreur chargement catégories de modèles: {e}")

        # Clients (pour templates spécifiques)
        self.client_id_combo.addItem(self.tr("Global (aucun client)"), None)
        try:
            # Lister quelques clients - pour une vraie app, une recherche serait mieux
            # clients = clients_crud.get_all_clients_simplified(limit=100) # Supposons une telle fonction
            # if clients:
            #     for client in clients:
            #         self.client_id_combo.addItem(f"{client.get('name', client.get('client_id'))}", client.get('client_id'))
            pass # Pour l'instant, laisser vide ou ajouter manuellement si besoin pour test
        except Exception as e:
            self.logger.error(f"Erreur chargement clients pour filtre modèles: {e}")


    def _populate_form_for_edit(self):
        self.template_name_edit.setText(self.template_data.get('template_name', ''))

        type_idx = self.template_type_combo.findData(self.template_data.get('template_type'))
        if type_idx >=0: self.template_type_combo.setCurrentIndex(type_idx)
        else: self.template_type_combo.setCurrentText(self.template_data.get('template_type', ''))

        self.description_edit.setPlainText(self.template_data.get('description', ''))

        lang_idx = self.language_combo.findData(self.template_data.get('language_code'))
        if lang_idx >=0: self.language_combo.setCurrentIndex(lang_idx)

        cat_idx = self.category_combo.findData(self.template_data.get('category_id'))
        if cat_idx >=0: self.category_combo.setCurrentIndex(cat_idx)

        client_idx = self.client_id_combo.findData(self.template_data.get('client_id'))
        if client_idx >=0: self.client_id_combo.setCurrentIndex(client_idx)
        elif self.template_data.get('client_id'): # Si client_id existe mais pas dans la liste
            self.client_id_combo.addItem(f"Client ID: {self.template_data.get('client_id')}", self.template_data.get('client_id'))
            self.client_id_combo.setCurrentIndex(self.client_id_combo.findData(self.template_data.get('client_id')))


        self.version_edit.setText(self.template_data.get('version', '1.0'))
        self.is_default_checkbox.setChecked(bool(self.template_data.get('is_default_for_type_lang')))

        self.base_file_name_edit.setText(self.template_data.get('base_file_name', ''))

        raw_content = self.template_data.get('raw_template_file_data')
        if isinstance(raw_content, bytes):
            try:
                self.raw_content_edit.setPlainText(raw_content.decode('utf-8'))
            except UnicodeDecodeError:
                self.raw_content_edit.setPlainText(self.tr("Erreur: Contenu binaire non décodable en UTF-8."))
        elif isinstance(raw_content, str): # Devrait être bytes mais par sécurité
             self.raw_content_edit.setPlainText(raw_content)


    def _on_browse_file(self):
        # Pour l'instant, nous supportons principalement HTML pour raw_template_file_data
        # Pour XLSX/DOCX, on stockerait le nom du fichier et il serait géré sur le serveur.
        # Ici, on se concentre sur la lecture du contenu pour les types texte/html.
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(self.tr("Modèles HTML (*.html *.htm);;Modèles Texte (*.txt);;Tous les fichiers (*.*)"))
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec_():
            filenames = file_dialog.selectedFiles()
            if filenames:
                self.selected_file_path = filenames[0]
                self.selected_file_label.setText(os.path.basename(self.selected_file_path))
                self.base_file_name_edit.setText(os.path.basename(self.selected_file_path)) # Mettre à jour aussi

                # Tenter de lire le contenu si c'est un type texte/html pour pré-remplir raw_content_edit
                # Cela dépendra du type de template sélectionné.
                # Pour cette phase, on lit toujours si c'est un fichier texte.
                try:
                    if self.selected_file_path.lower().endswith(('.html', '.htm', '.txt')):
                        with open(self.selected_file_path, 'r', encoding='utf-8') as f:
                            self.raw_content_edit.setPlainText(f.read())
                    else:
                        # Pour les autres types, on ne pré-remplit pas raw_content_edit
                        # mais on garde selected_file_path pour que la logique de sauvegarde puisse
                        # copier le fichier sur le serveur (hors de portée de l'agent pour l'instant)
                        # ou stocker le BLOB si c'est décidé.
                        # Pour cette phase, si ce n'est pas HTML/TXT, raw_content_edit ne sera pas peuplé par browse.
                        self.raw_content_edit.setPlainText(self.tr("[Contenu du fichier binaire non affiché ici. Il sera uploadé.]"))
                except Exception as e:
                    self.logger.error(f"Erreur lecture fichier sélectionné {self.selected_file_path}: {e}")
                    QMessageBox.warning(self, self.tr("Erreur Fichier"), self.tr("Impossible de lire le contenu du fichier."))
                    self.selected_file_label.setText(self.tr("Fichier sélectionné (erreur lecture)."))


    def _on_accept_data(self):
        # Validation
        if not self.template_name_edit.text().strip():
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le nom du modèle est obligatoire."))
            return
        if not self.template_type_combo.currentText().strip(): # Si éditable et vide
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le type de modèle est obligatoire."))
            return
        if not self.language_combo.currentData(): # Assure qu'une langue est sélectionnée
             QMessageBox.warning(self, self.tr("Validation"), self.tr("La langue du modèle est obligatoire."))
             return

        # Si raw_content_edit est vide et selected_file_path est None et base_file_name_edit est vide (pour édition)
        # il faut au moins une source de contenu.
        is_editing = bool(self.template_data)
        current_base_file = self.base_file_name_edit.text().strip()
        current_raw_content = self.raw_content_edit.toPlainText().strip()

        if not current_raw_content and not self.selected_file_path and not (is_editing and current_base_file):
             QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez fournir un contenu (via upload ou texte brut) ou un nom de fichier de base pour le modèle."))
             return

        self.accept()

    def get_data(self) -> dict:
        data = {
            "template_name": self.template_name_edit.text().strip(),
            "template_type": self.template_type_combo.currentText().strip(), # Si éditable
            "description": self.description_edit.toPlainText().strip(),
            "language_code": self.language_combo.currentData(),
            "category_id": self.category_combo.currentData(),
            "client_id": self.client_id_combo.currentData(), # Peut être None
            "version": self.version_edit.text().strip() or "1.0",
            "is_default_for_type_lang": self.is_default_checkbox.isChecked(),
            "base_file_name": self.base_file_name_edit.text().strip() or None, # Sera mis à jour si upload
            "raw_template_file_data": None, # Sera peuplé par la logique appelante si upload
            "content_definition": None, # Pourrait être un JSON pour certains types, à gérer
            # Champs spécifiques email/page de garde (non gérés dans cette UI de base)
            "email_subject_template": None,
            "email_variables_info": None,
            "cover_page_config_json": None,
            "document_mapping_config_json": None
        }

        # Si un nouveau fichier a été sélectionné, il prime.
        if self.selected_file_path:
            data["base_file_name"] = os.path.basename(self.selected_file_path)
            # La logique d'appel lira le contenu de self.selected_file_path pour raw_template_file_data
            # si le type de template est HTML/Texte.
            # Pour cette phase, on suppose que si selected_file_path est défini, le contenu sera lu
            # par la fonction appelante (TemplateManagementWidget).
            # Alternative: lire ici et stocker dans un attribut.
            if self.selected_file_path.lower().endswith(('.html', '.htm', '.txt')):
                 try:
                    with open(self.selected_file_path, 'rb') as f: # Lire en binaire
                        data["raw_template_file_data"] = f.read()
                 except Exception as e:
                    self.logger.error(f"Erreur re-lecture fichier {self.selected_file_path} dans get_data: {e}")
                    # Laisser raw_template_file_data à None, une erreur sera levée par l'appelant si besoin
            else:
                # Pour les fichiers non-texte (XLSX, DOCX), on ne stocke pas raw_template_file_data
                # On se fie au base_file_name et le fichier doit être sur le serveur.
                # L'upload réel de ces fichiers est plus complexe.
                data["raw_template_file_data"] = None # Explicitement
                self.logger.info(f"Fichier non-texte '{data['base_file_name']}' sélectionné. Contenu non stocké en DB.")


        elif self.raw_content_edit.toPlainText().strip(): # Si pas de nouveau fichier mais du contenu brut
            data["raw_template_file_data"] = self.raw_content_edit.toPlainText().strip().encode('utf-8')
            # Si raw_content est édité, base_file_name pourrait être vidé ou gardé pour info
            # data["base_file_name"] = None # Optionnel: si contenu brut prime, vider base_file_name

        # Si on est en mode édition et qu'aucun nouveau fichier n'a été sélectionné et que raw_content_edit est vide,
        # mais qu'il y avait un raw_content initial, il faut le préserver.
        # Cependant, si l'utilisateur a vidé raw_content_edit, on considère qu'il veut le vider.
        # La logique actuelle est : nouveau fichier > contenu de raw_content_edit > rien.
        # Si on édite et qu'on ne touche ni à l'upload ni à raw_content_edit, et que base_file_name existe,
        # on suppose que le template reste basé sur ce fichier sur le serveur.
        # Si raw_template_file_data était initialement chargé depuis la DB, et que l'utilisateur ne l'a pas vidé,
        # et n'a pas uploadé de nouveau fichier, il faut le conserver.
        if self.template_data and not self.selected_file_path and not data["raw_template_file_data"] and self.template_data.get('raw_template_file_data'):
            # Si l'utilisateur n'a pas fourni de nouveau contenu (ni fichier, ni texte brut modifié)
            # et qu'il y avait un contenu brut initial, on le garde.
            # Attention: si l'utilisateur a activement vidé raw_content_edit, on doit respecter cela.
            # La logique ci-dessus le fait déjà : si raw_content_edit est vide, data["raw_template_file_data"] sera None.
            # Ce qu'il faut, c'est que si on ne veut pas changer le contenu, on ne touche à rien.
            # Le plus simple est que `update_template` dans le CRUD ne mette à jour `raw_template_file_data` que s'il est explicitement fourni.
            # Pour get_data(), on retourne ce qui est dans l'UI.
            pass


        return data

    def tr(self, text, disambiguation=None, n=-1):
        # Simple fallback tr method
        from PyQt5.QtWidgets import QApplication
        return QApplication.translate("TemplateEditDialog", text, disambiguation, n)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test mode ajout
    # add_dialog = TemplateEditDialog(app_root_dir=os.getcwd(), config=None)
    # if add_dialog.exec_() == QDialog.Accepted:
    #     print("Données Ajout:", add_dialog.get_data())

    # Test mode édition
    sample_edit_data = {
        "template_id": 1,
        "template_name": "Test Proforma FR",
        "template_type": "HTML_PROFORMA",
        "description": "Un template de test.",
        "language_code": "fr",
        "category_id": 1, # Supposer qu'une catégorie avec ID 1 existe
        "client_id": None,
        "version": "1.1",
        "is_default_for_type_lang": True,
        "base_file_name": "proforma_test_fr.html",
        "raw_template_file_data": b"<h1>Hello {{name}}</h1>" # bytes
    }
    edit_dialog = TemplateEditDialog(template_data=sample_edit_data, app_root_dir=os.getcwd(), config=None)
    if edit_dialog.exec_() == QDialog.Accepted:
        print("Données Modifiées:", edit_dialog.get_data())

    sys.exit(app.exec_())
