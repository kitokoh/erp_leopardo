# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QApplication, QLabel, QLineEdit,
    QComboBox, QCheckBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QLocale # Added QLocale

from db.cruds.products.products_crud import products_crud_instance as products_crud
from .global_product_edit_dialog import GlobalProductEditDialog # Use the new dedicated dialog
from auth.permissions import has_permission, P_MANAGE_GLOBAL_PRODUCTS, P_VIEW_GLOBAL_PRODUCTS

# Placeholder for actual SUPPORTED_LANGUAGES definition or import
try:
    from client_management.tabs.documents_tab import SUPPORTED_LANGUAGES
except ImportError:
    logging.warning("ManageGlobalProductsDialog: Could not import SUPPORTED_LANGUAGES, using fallback.")
    SUPPORTED_LANGUAGES = {"en": "English", "fr": "Français", "es": "Español", "ar": "العربية"}


class ManageGlobalProductsDialog(QDialog):
    def __init__(self, current_user_info: dict, config: object, notification_manager: object, parent=None): # Removed product_dialog_class
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.config = config
        self.notification_manager = notification_manager
        # self.ProductDialog is no longer needed as we use GlobalProductEditDialog

        self.setWindowTitle(self.tr("Gestion du Catalogue Global des Produits"))
        self.setMinimumSize(900, 600)

        # Attempt to inherit stylesheet from parent if possible
        # This is a common pattern but might need parent to expose 'style_sheet_content'
        if parent and hasattr(parent, 'style_sheet_content'):
            self.setStyleSheet(parent.style_sheet_content)
        elif parent and hasattr(parent, 'styleSheet'): # Fallback to parent's direct stylesheet
             self.setStyleSheet(parent.styleSheet())


        self._setup_ui()
        self._populate_language_filter() # Populate languages dynamically
        self.load_global_products()
        self._apply_permissions()

    def tr(self, text, disambiguation=None, n=-1):
        return QApplication.translate("ManageGlobalProductsDialog", text, disambiguation, n)

    def _populate_language_filter(self):
        self.lang_filter_combo.clear()
        self.lang_filter_combo.addItem(self.tr("Toutes langues"), None)
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            self.lang_filter_combo.addItem(self.tr(lang_name), lang_code)


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Filter Bar
        filter_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Rechercher par nom ou code..."))
        self.search_input.textChanged.connect(self.load_global_products)
        filter_bar_layout.addWidget(QLabel(self.tr("Recherche:")))
        filter_bar_layout.addWidget(self.search_input)

        self.lang_filter_combo = QComboBox()
        # Items populated by _populate_language_filter
        self.lang_filter_combo.currentTextChanged.connect(self.load_global_products)
        filter_bar_layout.addWidget(QLabel(self.tr("Langue:")))
        filter_bar_layout.addWidget(self.lang_filter_combo)

        self.active_filter_combo = QComboBox()
        self.active_filter_combo.addItem(self.tr("Tous (Statut)"), None) # Changed default label
        self.active_filter_combo.addItem(self.tr("Actif Uniquement"), "active")
        self.active_filter_combo.addItem(self.tr("Inactif Uniquement"), "inactive")
        self.active_filter_combo.currentTextChanged.connect(self.load_global_products)
        filter_bar_layout.addWidget(QLabel(self.tr("Statut:")))
        filter_bar_layout.addWidget(self.active_filter_combo)

        self.include_deleted_checkbox = QCheckBox(self.tr("Inclure Supprimés (Soft-Delete)"))
        self.include_deleted_checkbox.stateChanged.connect(self.load_global_products)
        filter_bar_layout.addWidget(self.include_deleted_checkbox)

        main_layout.addLayout(filter_bar_layout)

        # Table
        self.products_table = QTableWidget()
        self.products_table.setObjectName("globalProductsTable")
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Code Produit"), self.tr("Nom Produit"),
            self.tr("Catégorie"), self.tr("Langue"), self.tr("Prix Base"), self.tr("Actif")
        ])
        header_style = """
            QHeaderView::section {
                background-color: #334155; color: white; padding: 6px;
                border: 1px solid #4A5568; font-weight: bold; font-size: 9pt;
            }
        """
        self.products_table.horizontalHeader().setStyleSheet(header_style)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.products_table.setSortingEnabled(True)

        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.products_table.itemSelectionChanged.connect(self._update_action_buttons_state)
        self.products_table.doubleClicked.connect(self.handle_edit_product_on_doubleclick) # Edit on double click
        main_layout.addWidget(self.products_table)

        # Action Buttons
        action_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Ajouter Produit Global"))
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.handle_add_product)
        action_buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton(QIcon(":/icons/edit-2.svg"), self.tr("Modifier Produit Global"))
        self.edit_button.setObjectName("actionButton")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self.handle_edit_product)
        action_buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton(QIcon(":/icons/trash-2.svg"), self.tr("Supprimer Produit Global"))
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.handle_delete_product)
        action_buttons_layout.addWidget(self.delete_button)

        action_buttons_layout.addStretch()

        self.refresh_button = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser"))
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.load_global_products)
        action_buttons_layout.addWidget(self.refresh_button)

        action_buttons_layout.addStretch(1) # Add stretch before equivalency button

        self.equivalency_button = QPushButton(QIcon.fromTheme("transform-move"), self.tr("Gérer les Équivalences")) # Using a generic theme icon
        self.equivalency_button.setObjectName("actionButton") # Or "secondaryButton"
        self.equivalency_button.setToolTip(self.tr("Ouvrir le dialogue de gestion des équivalences de produits"))
        self.equivalency_button.clicked.connect(self.handle_manage_equivalencies)
        action_buttons_layout.addWidget(self.equivalency_button)


        main_layout.addLayout(action_buttons_layout)

        # Bottom Bar (Close)
        bottom_bar_layout = QHBoxLayout()
        bottom_bar_layout.addStretch()
        self.close_button = QPushButton(self.tr("Fermer"))
        self.close_button.setObjectName("secondaryButton") # Or just a default button
        self.close_button.clicked.connect(self.accept) # Accept will close the dialog
        bottom_bar_layout.addWidget(self.close_button)
        main_layout.addLayout(bottom_bar_layout)

    def _apply_permissions(self):
        can_manage = has_permission(self.current_user_info.get('role_name'), P_MANAGE_GLOBAL_PRODUCTS)
        can_view = has_permission(self.current_user_info.get('role_name'), P_VIEW_GLOBAL_PRODUCTS) or can_manage

        self.add_button.setEnabled(can_manage)
        # Visibility of the whole dialog should be checked by the caller before opening.
        # Here we just enable/disable controls based on specific management permission.
        if not can_manage: # If cannot manage, edit/delete definitely disabled
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        # If can_manage is true, _update_action_buttons_state will handle enabling based on selection.

        # If user cannot even view, perhaps the table should be hidden or show a message
        # But typically, if they can open the dialog, they have view permission.
        # This dialog is for "managing", so P_MANAGE_GLOBAL_PRODUCTS is the primary gate.
        # If a separate "view global catalog" screen existed, it would use P_VIEW_GLOBAL_PRODUCTS.


    def _update_action_buttons_state(self):
        selected_items = self.products_table.selectedItems()
        has_selection = bool(selected_items)
        can_manage = has_permission(self.current_user_info.get('role_name'), P_MANAGE_GLOBAL_PRODUCTS)

        self.edit_button.setEnabled(has_selection and can_manage)
        self.delete_button.setEnabled(has_selection and can_manage)

    def load_global_products(self):
        self.products_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        filters = {}
        search_term = self.search_input.text().strip()
        if search_term:
            filters['product_name'] = search_term
            # For combined search, products_crud.get_all_products would need modification
            # or use a specific filter key like 'search_term' that it handles.
            # Current products_crud uses 'product_name' for LIKE on name, and 'product_code_like' for code.
            # To search both, we might need to call it twice or modify the CRUD.
            # For simplicity now, it searches product_name. User can search code by using product_code_like filter if UI exposed it.

        selected_lang = self.lang_filter_combo.currentData()
        if selected_lang:
            filters['language_code'] = selected_lang

        active_status_filter = self.active_filter_combo.currentData()
        active_only_param = None
        if active_status_filter == "active":
            active_only_param = True
        elif active_status_filter == "inactive":
            active_only_param = False

        include_deleted = self.include_deleted_checkbox.isChecked()

        try:
            all_prods = products_crud.get_all_products(
                filters=filters,
                include_deleted=include_deleted,
                active_only=active_only_param
            )

            self.products_table.setRowCount(len(all_prods))
            for row, prod_data in enumerate(all_prods):
                prod_id = prod_data.get('product_id')

                id_item = QTableWidgetItem(str(prod_id))
                id_item.setData(Qt.UserRole, prod_id)
                self.products_table.setItem(row, 0, id_item)

                self.products_table.setItem(row, 1, QTableWidgetItem(prod_data.get('product_code', '')))
                self.products_table.setItem(row, 2, QTableWidgetItem(prod_data.get('product_name', '')))
                self.products_table.setItem(row, 3, QTableWidgetItem(prod_data.get('category', '')))
                self.products_table.setItem(row, 4, QTableWidgetItem(prod_data.get('language_code', '')))

                locale = QLocale()
                base_price = prod_data.get('base_unit_price', 0.0)
                price_str = locale.toString(float(base_price), 'f', 2)
                # Assuming currency is EUR for now, or it should be part of product_data
                price_item = QTableWidgetItem(price_str + " €")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(row, 5, price_item)

                active_text = self.tr("Oui") if prod_data.get('is_active') else self.tr("Non")
                if prod_data.get('is_deleted'):
                    active_text += self.tr(" (Supprimé)")
                active_item = QTableWidgetItem(active_text)
                active_item.setTextAlignment(Qt.AlignCenter)

                if prod_data.get('is_deleted'):
                    for col_idx in range(self.products_table.columnCount()):
                        cell_item = self.products_table.item(row, col_idx) or QTableWidgetItem()
                        # Apply strikethrough or gray out for deleted items
                        font = cell_item.font()
                        font.setStrikeOut(True)
                        cell_item.setFont(font)
                        cell_item.setForeground(Qt.gray)
                        if not self.products_table.item(row, col_idx): self.products_table.setItem(row, col_idx, cell_item)
                elif not prod_data.get('is_active'):
                     for col_idx in range(self.products_table.columnCount()):
                        cell_item = self.products_table.item(row, col_idx) or QTableWidgetItem()
                        cell_item.setForeground(Qt.darkGray)
                        if not self.products_table.item(row, col_idx): self.products_table.setItem(row, col_idx, cell_item)
                self.products_table.setItem(row, 6, active_item)

        except Exception as e:
            logging.error(f"Error loading global products: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), str(e))
        finally:
            QApplication.restoreOverrideCursor()
            self._update_action_buttons_state()

    def handle_edit_product_on_doubleclick(self, model_index):
        if not has_permission(self.current_user_info.get('role_name'), P_MANAGE_GLOBAL_PRODUCTS):
            return # Do nothing if no permission
        self.handle_edit_product()


    def handle_add_product(self):
        dialog = GlobalProductEditDialog(current_user_info=self.current_user_info, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_product_data = dialog.get_product_data()
            # created_by_user_id is already added in GlobalProductEditDialog.get_product_data()
            result = products_crud.add_product(new_product_data)
            if result.get('success'):
                if self.notification_manager:
                    self.notification_manager.show_notification(self.tr("Succès"), self.tr("Produit global ajouté avec succès."), 'success')
                self.load_global_products()
            else:
                QMessageBox.critical(self, self.tr("Erreur d'Ajout"), self.tr("Impossible d'ajouter le produit global: {0}").format(result.get('error')))


    def handle_edit_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un produit à modifier."))
            return

        product_id_item = self.products_table.item(selected_rows[0].row(), 0)
        if not product_id_item: return # Should not happen

        product_id = product_id_item.data(Qt.UserRole)
        if not product_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du produit non trouvé pour la ligne sélectionnée."))
            return

        product_data_to_edit = products_crud.get_product_by_id(product_id, include_deleted=True)
        if not product_data_to_edit:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Données du produit non trouvées pour l'ID {0}.").format(product_id))
            return

        dialog = GlobalProductEditDialog(product_data=product_data_to_edit, current_user_info=self.current_user_info, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_product_data()
            # updated_by_user_id is already added in GlobalProductEditDialog.get_product_data()
            result = products_crud.update_product(product_id, updated_data)
            if result.get('success') and result.get('updated_count', 0) > 0:
                if self.notification_manager:
                    self.notification_manager.show_notification(self.tr("Succès"), self.tr("Produit global mis à jour avec succès."), 'success')
                self.load_global_products()
            elif result.get('success') and result.get('updated_count', 0) == 0:
                if self.notification_manager:
                    self.notification_manager.show_notification(self.tr("Information"), self.tr("Aucune modification détectée pour le produit."), 'info')
            else:
                QMessageBox.critical(self, self.tr("Erreur de Mise à Jour"), self.tr("Impossible de mettre à jour le produit: {0}").format(result.get('error')))


    def handle_delete_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un produit à supprimer."))
            return

        product_id_item = self.products_table.item(selected_rows[0].row(), 0)
        product_name_item = self.products_table.item(selected_rows[0].row(), 2) # Name column

        if not product_id_item or not product_name_item: return

        product_id = product_id_item.data(Qt.UserRole)
        product_name = product_name_item.text()

        if not product_id: return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer (soft delete) le produit global '{0}' (ID: {1})?\n"
                                             "Cela le marquera comme supprimé et inactif.").format(product_name, product_id),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            result = products_crud.delete_product(product_id) # delete_product performs soft delete
            if result.get('success'):
                if self.notification_manager:
                    self.notification_manager.show_notification(self.tr("Supprimé"), self.tr("Produit '{0}' marqué comme supprimé.").format(product_name), 'success')
                self.load_global_products()
            else:
                QMessageBox.critical(self, self.tr("Erreur de Suppression"), self.tr("Impossible de supprimer le produit: {0}").format(result.get('error')))

    def handle_manage_equivalencies(self):
        source_product_id_to_pass = None
        selected_rows = self.products_table.selectionModel().selectedRows()
        if selected_rows:
            # La colonne 0 contient l'ID du produit stocké avec setData(Qt.UserRole)
            # et aussi affiché comme texte.
            product_id_item = self.products_table.item(selected_rows[0].row(), 0)
            if product_id_item:
                source_product_id_to_pass = product_id_item.data(Qt.UserRole)
                if source_product_id_to_pass is None: # Fallback si UserRole n'est pas l'ID mais le texte
                    try:
                        source_product_id_to_pass = int(product_id_item.text())
                    except ValueError:
                         logging.warning("Could not parse product_id from table cell text in ManageGlobalProductsDialog.")
                         source_product_id_to_pass = None # Assurer qu'il est None si invalide

        # Import ProductEquivalencyDialog here to avoid circular dependencies at module level if any
        try:
            from gui.dialogs.product_equivalency_dialog import ProductEquivalencyDialog
            # Passer source_product_id_to_pass au constructeur
            eq_dialog = ProductEquivalencyDialog(source_product_id=source_product_id_to_pass, parent=self)
            eq_dialog.exec_() # Show as a modal dialog
            # No specific action after close for now, but could refresh product list if equivalencies impact display
        except ImportError:
            logging.error("Failed to import ProductEquivalencyDialog.")
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le module de gestion des équivalences est introuvable."))
        except Exception as e:
            logging.error(f"Error opening ProductEquivalencyDialog: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), str(e))

if __name__ == '__main__':
    app = QApplication([])

    mock_user_info = {'user_id': 'test_user', 'role_name': 'Administrator'}
    mock_config = type('MockConfig', (), {})() # Simplified mock config
    mock_notifications = type('MockNotifications', (), {
        'show_notification': staticmethod(lambda title, msg, type: print(f"NOTIF ({type}): {title} - {msg}"))
    })()

    # For testing, ensure P_MANAGE_GLOBAL_PRODUCTS is handled by has_permission
    # This might require mocking has_permission or ensuring 'Administrator' role has it in a test DB setup.
    # from auth.permissions import P_MANAGE_GLOBAL_PRODUCTS as P_MGP # Ensure it's importable
    # For this snippet, we assume it's correctly checked.

    dialog = ManageGlobalProductsDialog(mock_user_info, mock_config, mock_notifications, parent=None)
    dialog.exec_()

    # app.exec_() # Not needed if dialog.exec_() is blocking
