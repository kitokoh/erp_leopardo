# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox, QLabel, QDialog, QTextBrowser
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from app.db.cruds.templates import templates_crud
from .template_edit_dialog import TemplateEditDialog # Ajout de l'import
# Supposer que APP_ROOT_DIR et config (pour templates_dir) sont accessibles
# via le parent ou une configuration globale.

class TemplateManagementWidget(QWidget):
    def __init__(self, app_root_dir: str, config: object, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.app_root_dir = app_root_dir
        self.config = config # Pour self.config.get("templates_dir", "templates")

        self.setWindowTitle(self.tr("Gestion des Modèles de Documents"))
        self.setMinimumSize(900, 600)
        self._setup_ui()
        self._connect_signals()
        self._populate_filters()
        self.load_templates()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Filtres
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(self.tr("Type de Modèle:")))
        self.type_filter_combo = QComboBox()
        filter_layout.addWidget(self.type_filter_combo)

        filter_layout.addWidget(QLabel(self.tr("Langue:")))
        self.lang_filter_combo = QComboBox()
        filter_layout.addWidget(self.lang_filter_combo)

        # TODO: Ajouter un filtre Client (Global/ID Client spécifique) si nécessaire dans une phase ultérieure.
        filter_layout.addStretch()
        self.refresh_button = QPushButton(QIcon.fromTheme("view-refresh"), self.tr("Actualiser"))
        filter_layout.addWidget(self.refresh_button)
        main_layout.addLayout(filter_layout)

        # Table des Modèles
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(8) # ID, Nom, Type, Langue, Fichier Base, Client ID, Défaut, Contenu en DB
        self.templates_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom du Modèle"), self.tr("Type"), self.tr("Langue"),
            self.tr("Fichier Base"), self.tr("Client Spécifique (ID)"),
            self.tr("Défaut (Type/Langue)"), self.tr("Contenu en DB")
        ])
        self.templates_table.setColumnHidden(0, True) # Cacher ID par défaut
        self.templates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.templates_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.templates_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.templates_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.templates_table)

        # Boutons d'action
        action_layout = QHBoxLayout()
        self.set_default_button = QPushButton(QIcon.fromTheme("emblem-default"), self.tr("Marquer comme Défaut"))
        self.set_default_button.setEnabled(False)
        action_layout.addWidget(self.set_default_button)

        self.view_content_button = QPushButton(QIcon.fromTheme("document-open"), self.tr("Voir Contenu"))
        self.view_content_button.setEnabled(False)
        action_layout.addWidget(self.view_content_button)

        action_layout.addStretch() # Garder un stretch avant les boutons d'action principaux

        self.add_template_button = QPushButton(QIcon.fromTheme("document-new"), self.tr("Ajouter Nouveau Template"))
        action_layout.addWidget(self.add_template_button)

        self.edit_template_button = QPushButton(QIcon.fromTheme("document-edit"), self.tr("Modifier Template"))
        self.edit_template_button.setEnabled(False)
        action_layout.addWidget(self.edit_template_button)

        self.delete_template_button = QPushButton(QIcon.fromTheme("edit-delete"), self.tr("Supprimer Template"))
        self.delete_template_button.setObjectName("dangerButton")
        self.delete_template_button.setEnabled(False)
        action_layout.addWidget(self.delete_template_button)

        main_layout.addLayout(action_layout)

    def _connect_signals(self):
        self.type_filter_combo.currentTextChanged.connect(self.load_templates)
        self.lang_filter_combo.currentTextChanged.connect(self.load_templates)
        self.refresh_button.clicked.connect(self.load_templates)
        self.templates_table.itemSelectionChanged.connect(self._update_action_button_states)

        self.set_default_button.clicked.connect(self._on_set_default_clicked)
        self.view_content_button.clicked.connect(self._on_view_content_clicked)

        self.add_template_button.clicked.connect(self._on_add_template_clicked)
        self.edit_template_button.clicked.connect(self._on_edit_template_clicked)
        self.delete_template_button.clicked.connect(self._on_delete_template_clicked)

    def _populate_filters(self):
        # Types
        self.type_filter_combo.addItem(self.tr("Tous Types"), None)
        try:
            types = templates_crud.get_distinct_template_types()
            for type_tuple in types:
                self.type_filter_combo.addItem(type_tuple[0], type_tuple[0])
        except Exception as e:
            self.logger.error(f"Erreur chargement types de modèles: {e}")

        # Langues
        self.lang_filter_combo.addItem(self.tr("Toutes Langues"), None)
        try:
            langs = templates_crud.get_distinct_template_languages()
            for lang_tuple in langs:
                self.lang_filter_combo.addItem(lang_tuple[0], lang_tuple[0]) # Assumant que SUPPORTED_LANGUAGES n'est pas utilisé ici pour les noms complets
        except Exception as e:
            self.logger.error(f"Erreur chargement langues des modèles: {e}")

    def load_templates(self):
        self.templates_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        selected_type = self.type_filter_combo.currentData()
        selected_lang = self.lang_filter_combo.currentData()

        try:
            # Pour la phase 1, pas de filtre client_id spécifique, on récupère tout (global et spécifique)
            templates = templates_crud.get_all_templates(
                template_type_filter=selected_type,
                language_code_filter=selected_lang,
                apply_visibility_filter=False # Voir tous les templates, même ceux masqués par défaut
            )

            self.templates_table.setRowCount(len(templates))
            for row, t_data in enumerate(templates):
                template_id = t_data.get('template_id')
                id_item = QTableWidgetItem(str(template_id))
                id_item.setData(Qt.UserRole, template_id) # Stocker l'ID
                self.templates_table.setItem(row, 0, id_item)
                self.templates_table.setItem(row, 1, QTableWidgetItem(t_data.get('template_name', '')))
                self.templates_table.setItem(row, 2, QTableWidgetItem(t_data.get('template_type', '')))
                self.templates_table.setItem(row, 3, QTableWidgetItem(t_data.get('language_code', '')))
                self.templates_table.setItem(row, 4, QTableWidgetItem(t_data.get('base_file_name', '')))
                self.templates_table.setItem(row, 5, QTableWidgetItem(t_data.get('client_id', self.tr('Global'))))

                is_default_text = self.tr("Oui") if t_data.get('is_default_for_type_lang') else self.tr("Non")
                self.templates_table.setItem(row, 6, QTableWidgetItem(is_default_text))

                has_db_content = self.tr("Oui") if t_data.get('raw_template_file_data') else self.tr("Non")
                self.templates_table.setItem(row, 7, QTableWidgetItem(has_db_content))

        except Exception as e:
            self.logger.error(f"Erreur chargement des modèles: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), str(e))
        finally:
            QApplication.restoreOverrideCursor()
            self._update_action_button_states()

    def _update_action_button_states(self):
        has_selection = bool(self.templates_table.selectedItems())
        self.set_default_button.setEnabled(has_selection)
        self.edit_template_button.setEnabled(has_selection)
        self.delete_template_button.setEnabled(has_selection)

        can_view_content = False
        if has_selection:
            selected_row = self.templates_table.currentRow()
            if selected_row >= 0: # S'assurer qu'une ligne est bien sélectionnée
                # Vérifier si la colonne 7 (Contenu en DB) est "Oui" ou si Fichier Base (col 4) a une valeur
                has_db_content_item = self.templates_table.item(selected_row, 7)
                base_file_item = self.templates_table.item(selected_row, 4)
                if (has_db_content_item and has_db_content_item.text() == self.tr("Oui")) or \
                   (base_file_item and base_file_item.text()):
                    can_view_content = True
        self.view_content_button.setEnabled(can_view_content)


    def _on_set_default_clicked(self):
        selected_rows = self.templates_table.selectionModel().selectedRows()
        if not selected_rows: return

        template_id = self.templates_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        template_name = self.templates_table.item(selected_rows[0].row(), 1).text()

        reply = QMessageBox.question(self, self.tr("Confirmer Défaut"),
                                     self.tr("Marquer '{0}' comme modèle par défaut pour son type et sa langue ?\nLes autres modèles similaires (même type/langue/client escpace) ne seront plus par défaut.").format(template_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success = templates_crud.set_default_template_by_id(template_id)
            if success:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Modèle marqué comme défaut."))
                self.load_templates() # Rafraîchir pour voir le changement
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de marquer le modèle comme défaut."))

    def _on_view_content_clicked(self):
        selected_rows = self.templates_table.selectionModel().selectedRows()
        if not selected_rows: return

        template_id = self.templates_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        template_data = templates_crud.get_template_by_id(template_id)

        if not template_data:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Modèle non trouvé."))
            return

        content_to_show = ""
        title = self.tr("Aperçu Contenu Modèle: {0}").format(template_data.get('template_name'))

        if template_data.get('raw_template_file_data'):
            try:
                # raw_template_file_data est un BLOB, essayons de le décoder en UTF-8
                content_to_show = template_data['raw_template_file_data'].decode('utf-8', errors='replace')
            except Exception as e:
                self.logger.error(f"Erreur décodage contenu DB du modèle {template_id}: {e}")
                content_to_show = self.tr("Erreur de décodage du contenu binaire.")
        elif template_data.get('base_file_name'):
            # Construire le chemin complet
            # templates_dir = self.config.get("templates_dir", "templates") # Assurez-vous que config est accessible
            templates_dir = getattr(self.config, "templates_dir", "templates") if hasattr(self.config, "templates_dir") else "templates"

            file_path = os.path.join(
                self.app_root_dir,
                templates_dir,
                template_data.get('language_code', ''),
                template_data.get('base_file_name')
            )
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_to_show = f.read()
                except Exception as e:
                    self.logger.error(f"Erreur lecture fichier modèle {file_path}: {e}")
                    content_to_show = self.tr("Impossible de lire le fichier modèle.")
            else:
                content_to_show = self.tr("Fichier modèle non trouvé sur le disque: {0}").format(file_path)
        else:
            content_to_show = self.tr("Aucun contenu ou fichier de base défini pour ce modèle.")

        # Afficher dans un dialogue simple avec QTextBrowser
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(700, 500)
        layout = QVBoxLayout(dialog)
        text_browser = QTextBrowser()
        text_browser.setPlainText(content_to_show) # setPlainText pour éviter le rendu HTML si c'est du code source
        layout.addWidget(text_browser)
        close_button = QPushButton(self.tr("Fermer"))
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.exec_()

    def _on_add_template_clicked(self):
        dialog = TemplateEditDialog(app_root_dir=self.app_root_dir, config=self.config, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()

            # created_by_user_id devrait être ajouté ici si current_user_info est disponible
            # Pour l'instant, on suppose qu'il est optionnel ou géré autrement.
            # data['created_by_user_id'] = self.current_user_info.get('user_id') # Si disponible

            # raw_template_file_data est déjà en bytes si lu depuis fichier dans get_data,
            # ou encodé en utf-8 si depuis QTextEdit.

            new_template_id = templates_crud.add_template(data)
            if new_template_id:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Nouveau modèle ajouté avec ID: {0}").format(new_template_id))
                self.load_templates()
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible d'ajouter le nouveau modèle."))


    def _on_edit_template_clicked(self):
        selected_rows = self.templates_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un modèle à modifier."))
            return

        template_id = self.templates_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        if not template_id:
            self.logger.error("Aucun ID de modèle trouvé pour la ligne sélectionnée.")
            return

        existing_template_data = templates_crud.get_template_by_id(template_id)
        if not existing_template_data:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Données du modèle non trouvées pour l'ID {0}.").format(template_id))
            return

        dialog = TemplateEditDialog(template_data=existing_template_data, app_root_dir=self.app_root_dir, config=self.config, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()

            # updated_by_user_id devrait être ajouté ici si current_user_info est disponible
            # updated_data['updated_by_user_id'] = self.current_user_info.get('user_id') # Si disponible

            success = templates_crud.update_template(template_id, updated_data)
            if success:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Modèle ID {0} mis à jour.").format(template_id))
                self.load_templates()
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de mettre à jour le modèle ID {0}.").format(template_id))

    def _on_delete_template_clicked(self):
        selected_rows = self.templates_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un modèle à supprimer."))
            return

        template_id = self.templates_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        template_name = self.templates_table.item(selected_rows[0].row(), 1).text()
        base_file_name = self.templates_table.item(selected_rows[0].row(), 4).text()


        if not template_id:
            self.logger.error("Aucun ID de modèle trouvé pour la suppression.")
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer le modèle '{0}' (ID: {1}) ?\n"
                                             "Ceci supprimera l'entrée de la base de données. "
                                             "Si un fichier de base ('{2}') est associé, il ne sera PAS supprimé du disque automatiquement.").format(template_name, template_id, base_file_name or "N/A"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Utiliser delete_template_and_get_file_info pour obtenir des infos si on veut informer sur le fichier
            # Pour l'instant, utilisons juste delete_template
            success = templates_crud.delete_template(template_id)
            if success:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Modèle '{0}' supprimé de la base de données.").format(template_name))
                self.load_templates()
                if base_file_name:
                    QMessageBox.information(self, self.tr("Information Fichier"),
                                            self.tr("Le fichier '{0}' associé à ce modèle (si stocké sur disque et non en DB) n'a pas été supprimé du serveur. Veuillez le faire manuellement si nécessaire.").format(base_file_name))
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de supprimer le modèle ID {0}.").format(template_id))


    def tr(self, text, disambiguation=None, n=-1):
        return QApplication.translate("TemplateManagementWidget", text, disambiguation, n)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    # Configuration minimale pour le test
    class MockConfig:
        templates_dir = "resources/templates" # Ajustez si nécessaire pour vos tests

    app = QApplication(sys.argv)
    # Assurez-vous que votre base de données est initialisée et accessible
    # from db import initialize_database
    # initialize_database()

    # Simuler app_root_dir, par exemple le répertoire parent du répertoire courant si ce script est dans admin/
    current_script_path = os.path.abspath(__file__)
    admin_dir = os.path.dirname(current_script_path)
    project_root_dir_for_test = os.path.dirname(admin_dir) # Remonter d'un niveau pour être à la racine du projet

    widget = TemplateManagementWidget(app_root_dir=project_root_dir_for_test, config=MockConfig())
    widget.show()
    sys.exit(app.exec_())
