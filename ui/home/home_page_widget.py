# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLabel,
    QSizePolicy, QScrollArea, QStackedWidget, QFrame, QGraphicsDropShadowEffect,
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize, QFile, QTextStream, QPropertyAnimation, QEasingCurve, QRect, QEvent
from PyQt5.QtGui import QFont, QIcon, QMovie, QColor

import os
import random

from .promo_content_manager import PromoContentManager
from .promo_widgets import PromoSectionWidget
from .quick_stats_widget import QuickStatsWidget # Import the new widget



from .quick_stats_widget import QuickStatsWidget # Import the new widget
from .module_card_widget import ModuleCardWidget # Ajout de l'import
from statistics.map_widget import HomePageMapWidget
from client_management.add_new_client_dialog import AddNewClientDialog
from client_management.client_controller import ClientController
from db.cruds import clients_crud, projects_crud, products_crud
from db.cruds import recruitment_job_openings_crud, recruitment_candidates_crud


class HomePageWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window # Store reference to DocumentManager
        self.setObjectName("HomePageWidget")
        self.animations_enabled = True # Option to toggle animations

        # Initialize fictional data source for QuickStatsWidget
        self.fictional_data_source = {
            "clients_actifs": 150,
            "projets_en_cours": 20,
            "taches_ouvertes": 12,
            "nouveaux_documents_mois": 75,
            "tickets_support_actifs": 5
        }

        # Fictional searchable items for global search simulation
        self.searchable_items = [
            "Rapport Annuel 2023.pdf", "Client: ACME Corp", "Projet: Phoenix",
            "Note: Réunion Marketing Q3", "Produit: X1000", "Facture #INV-2024-001",
            "Client: Stark Industries", "Devis #QT-2024-015", "Contact: Jane Doe",
            "Produit: Y200 Super", "Tâche: Finaliser la présentation client"
        ]

        self.module_cards_list = []

        self._init_ui()
        self._load_styles()

    def _load_styles(self):
        style_sheet_path = os.path.join(os.path.dirname(__file__), "home_page_style.qss")
        if os.path.exists(style_sheet_path):
            file = QFile(style_sheet_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                self.setStyleSheet(stream.readAll())
                file.close()
            else:
                print(f"Warning: Could not open stylesheet file: {style_sheet_path}")
        else:
            print(f"Warning: Stylesheet file not found: {style_sheet_path}")


    def _init_ui(self):
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(10)

        self.modules = [
            {"name": self.tr("Gestion Documents Client"), "object_name": "btnClientDocuments", "icon": ":/icons/modern/folder-docs.svg", "slot": self.go_to_documents},
            {"name": self.tr("Gestion de Projet"), "object_name": "btnProjectManagement", "icon": ":/icons/dashboard.svg", "slot": self.go_to_project_management},
            {"name": self.tr("Statistiques"), "object_name": "btnStatistics", "icon": ":/icons/bar-chart.svg", "slot": self.go_to_statistics},
            {"name": self.tr("Gestion des Produits"), "object_name": "btnProductManagement", "icon": ":/icons/book.svg", "slot": self.go_to_product_management},
            {"name": self.tr("Gestion des Partenaires"), "object_name": "btnPartnerManagement", "icon": ":/icons/team.svg", "slot": self.go_to_partner_management},
            {"name": self.tr("Gestion Stock Atelier"), "object_name": "btnInventoryManagement", "icon": ":/icons/book.svg", "slot": self.go_to_inventory_management},
            {"name": self.tr("Recrutement"), "object_name": "btnRecruitment", "icon": ":/icons/users.svg", "slot": self.go_to_recruitment},
            {"name": self.tr("Gestion des Connaissances"), "object_name": "btnExperienceManagement", "icon": ":/icons/book.svg", "slot": self.go_to_experience_management},
            {"name": self.tr("Intégration Botpress"), "object_name": "btnBotpressIntegration", "icon": ":/icons/placeholder_icon.svg", "slot": self.go_to_botpress_integration},
            {"name": self.tr("Gestion Caméras"), "object_name": "btnCameraManagement", "icon": ":/icons/video.svg", "slot": self.go_to_camera_management},
            {"name": self.tr("Paramètres"), "object_name": "btnSettings", "icon": ":/icons/modern/settings.svg", "slot": self.go_to_settings},
        ]

        self.promo_manager = PromoContentManager()

        # Le GIF est maintenant initialisé ici pour être passé aux méthodes de layout
        self.gif_label = QLabel()
        self.gif_label.setObjectName("homePageGifLabel")
        available_gifs = ["1.gif", "2.gif", "3.gif"]
        chosen_gif_name = random.choice(available_gifs)
        gif_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "gifshome", chosen_gif_name)
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.gif_label.setMovie(self.movie)
            self.gif_label.setScaledContents(True)
            self.movie.start()
            self.gif_label.setAlignment(Qt.AlignCenter)
        else:
            self.gif_label.setText(self.tr("GIF non trouvé"))

        # La carte est maintenant un widget de la classe, pour être déplacée facilement
        self.map_widget_container = QFrame() # Conteneur pour la carte
        self.map_widget_container.setObjectName("homePageMapContainer")

        top_layout = self._setup_top_layout()
        bottom_layout = self._setup_bottom_layout()

        main_v_layout.addLayout(top_layout, 1)
        main_v_layout.addWidget(bottom_layout, 2)

        self.setLayout(main_v_layout)
        self._load_all_module_card_stats()

    def _get_stats_for_module(self, module_id: str) -> list[dict]:
        """
        Récupère les données statistiques pour un module donné.
        Pour l'instant, retourne des données factices.
        Devra être connecté aux vrais services/CRUDs plus tard.
        """
        # logging.debug(f"HomePageWidget: Récupération des stats pour le module_id: {module_id}")

        # Note: Les imports suivants sont supposés être faits en haut du fichier
        # from db import db_manager
        # from db.cruds.clients_crud import get_active_clients_count
        # from project_management.cruds import get_active_projects_count, get_overdue_tasks_count
        # etc. pour les autres modules.

        # Pour cette simulation, nous allons appeler des fonctions placeholder qui existent dans ce fichier.
        try:
            if module_id == "btnClientDocuments":
                active_clients = clients_crud.get_active_clients_count()
                # Assumons une fonction pour les documents récents, sinon mettons une valeur statique
                docs_recents = 12 # Placeholder, car la fonction n'existe pas
                return [
                    {'value': str(active_clients), 'label': self.tr('Clients Actifs')},
                    {'value': str(docs_recents), 'label': self.tr('Docs Récents')}
                ]
            elif module_id == "btnProjectManagement":
                active_projects = projects_crud.get_active_projects_count()
                overdue_tasks = projects_crud.get_overdue_tasks_count()
                return [
                    {'value': str(active_projects), 'label': self.tr('Projets en Cours'), 'color': '#28A745'},
                    {'value': str(overdue_tasks), 'label': self.tr('Tâches en Retard'), 'color': '#DC3545' if overdue_tasks > 0 else '#28A745'}
                ]
            elif module_id == "btnProductManagement":
                total_products = products_crud.get_total_products_count()
                return [
                    {'value': str(total_products), 'label': self.tr('Produits Actifs')}
                ]
            elif module_id == "btnRecruitment":
                open_positions = len(recruitment_job_openings_crud.get_all_job_openings())
                new_candidates = len(recruitment_candidates_crud.get_all_candidates())
                return [
                    {'value': str(open_positions), 'label': self.tr('Postes Ouverts')},
                    {'value': str(new_candidates), 'label': self.tr('Nouv. Candidatures')}
                ]
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques pour {module_id}: {e}")
        return []


    def _load_all_module_card_stats(self):
        """Charge et affiche les statistiques pour toutes les cartes de module."""
        if not hasattr(self, 'module_cards_list'):
            logging.warning("HomePageWidget: module_cards_list non trouvée, impossible de charger les stats.")
            return

        for card in self.module_cards_list:
            if isinstance(card, ModuleCardWidget): # S'assurer que c'est bien une ModuleCardWidget
                stats_data = self._get_stats_for_module(card.module_id)
                card.update_stats(stats_data)
            else:
                logging.warning(f"HomePageWidget: Item dans module_cards_list n'est pas une ModuleCardWidget: {type(card)}")


    def _handle_search_query(self):
        query = self.search_input.text()
        if not query.strip():
            # Optional: Show a message if search query is empty, or just do nothing
            # QMessageBox.information(self, self.tr("Recherche"), self.tr("Veuillez entrer un terme de recherche."))
            return

        # Perform a simple case-insensitive search on self.searchable_items
        lower_query = query.lower()
        results = [item for item in self.searchable_items if lower_query in item.lower()]

        if results:
            results_text = self.tr("Résultats trouvés ({0}):\n\n").format(len(results)) + "\n".join(results)
            QMessageBox.information(self, self.tr("Résultats de la Recherche"), results_text)
        else:
            QMessageBox.information(self, self.tr("Résultats de la Recherche"), self.tr("Aucun résultat trouvé pour '{0}'.").format(query))

    def eventFilter(self, obj, event):
        # Check if the object is a QPushButton and if it's one of our module buttons
        # (which have the event filter installed and will have animation attributes added)
        if isinstance(obj, QPushButton) and obj.property("isModuleButton") == True: # Added a custom property check
            if not self.animations_enabled: # Check if animations are globally enabled
                return super().eventFilter(obj, event)

            base_icon_size = QSize(32, 32) # Original icon size
            enlarged_icon_size = QSize(40, 40) # Enlarged icon size for hover

            if event.type() == QEvent.Enter:
                # Define animations if not already defined for this button
                # We store them on the button itself to avoid recreating them
                if not hasattr(obj, 'enter_icon_animation'):
                    obj.enter_icon_animation = QPropertyAnimation(obj, b"iconSize")
                    obj.enter_icon_animation.setDuration(150)
                    obj.enter_icon_animation.setEndValue(enlarged_icon_size)
                    obj.enter_icon_animation.setEasingCurve(QEasingCurve.InOutQuad)

                    obj.leave_icon_animation = QPropertyAnimation(obj, b"iconSize")
                    obj.leave_icon_animation.setDuration(150)
                    obj.leave_icon_animation.setEndValue(base_icon_size)
                    obj.leave_icon_animation.setEasingCurve(QEasingCurve.InOutQuad)

                # Start enter animation
                obj.leave_icon_animation.stop()
                obj.enter_icon_animation.setStartValue(obj.iconSize()) # Start from current icon size
                obj.enter_icon_animation.start()
                return True # Event handled

            elif event.type() == QEvent.Leave:
                # Start leave animation (only if animations were initialized)
                if hasattr(obj, 'leave_icon_animation'):
                    obj.enter_icon_animation.stop()
                    obj.leave_icon_animation.setStartValue(obj.iconSize()) # Start from current icon size
                    obj.leave_icon_animation.start()

                return True # Event handled

        return super().eventFilter(obj, event)

    def _setup_top_layout(self):
        """Crée le layout du haut avec la carte et la sidebar de statistiques."""
        top_h_layout = QHBoxLayout()
        top_h_layout.setContentsMargins(10, 10, 10, 10)
        top_h_layout.setSpacing(15)

        # La carte prend la place principale
        top_h_layout.addWidget(self.map_widget_container, 3) # Stretch factor 3

        # Right Sidebar pour les aperçus rapides
        self.right_sidebar_container = QFrame()
        self.right_sidebar_container.setObjectName("homePageRightSidebar")
        self.right_sidebar_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.right_sidebar_layout = QVBoxLayout(self.right_sidebar_container)
        self.right_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.right_sidebar_container.setLayout(self.right_sidebar_layout)

        self.quick_stats = QuickStatsWidget(self)
        self.quick_stats.refresh_requested.connect(self._refresh_quick_stats_data)
        self.set_right_sidebar_widget(self.quick_stats)
        self._refresh_quick_stats_data()

        # Ajout de la barre de recherche sous les statistiques rapides
        search_layout = self._setup_search_layout()
        self.right_sidebar_layout.addLayout(search_layout)

        top_h_layout.addWidget(self.right_sidebar_container, 1) # Stretch factor 1

        return top_h_layout


    def _refresh_quick_stats_data(self):
        """Generates simulated data and updates the QuickStatsWidget."""
        if not hasattr(self, 'quick_stats') or not self.quick_stats:
            return

        # Update fictional data source with some evolution
        self.fictional_data_source["clients_actifs"] = max(100, self.fictional_data_source["clients_actifs"] + random.randint(-2, 3))
        self.fictional_data_source["projets_en_cours"] = max(5, self.fictional_data_source["projets_en_cours"] + random.randint(-1, 2))

        # If projects increase, tasks might increase or decrease (some get done, new ones appear)
        if self.fictional_data_source["projets_en_cours"] > 20:
             self.fictional_data_source["taches_ouvertes"] = max(0, self.fictional_data_source["taches_ouvertes"] + random.randint(-2, 3))
        else:
             self.fictional_data_source["taches_ouvertes"] = max(0, self.fictional_data_source["taches_ouvertes"] + random.randint(-1, 1))

        self.fictional_data_source["nouveaux_documents_mois"] = max(10, self.fictional_data_source["nouveaux_documents_mois"] + random.randint(-5, 10))
        self.fictional_data_source["tickets_support_actifs"] = max(0, self.fictional_data_source["tickets_support_actifs"] + random.randint(-1, 1))

        # Prepare data for the widget
        display_data = [
            {"label": self.tr("Clients Actifs:"), "value": str(self.fictional_data_source["clients_actifs"])},
            {"label": self.tr("Projets en Cours:"), "value": str(self.fictional_data_source["projets_en_cours"])},
            {"label": self.tr("Tâches Ouvertes:"), "value": str(self.fictional_data_source["taches_ouvertes"])},
            {"label": self.tr("Nouveaux Documents (Mois):"), "value": str(self.fictional_data_source["nouveaux_documents_mois"])},
            {"label": self.tr("Tickets Support Actifs:"), "value": str(self.fictional_data_source["tickets_support_actifs"])}
        ]
        self.quick_stats.update_stats(display_data)



    def _setup_search_layout(self):
        """Crée le layout pour la barre de recherche."""
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(10, 5, 10, 5)
        search_layout.setSpacing(5)
        search_layout.setAlignment(Qt.AlignCenter) # Centrer la barre

        self.search_input = QLineEdit()
        self.search_input.setObjectName("homePageSearchInput")
        self.search_input.setPlaceholderText(self.tr("Rechercher..."))
        self.search_input.returnPressed.connect(self._handle_search_query)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton()
        self.search_button.setObjectName("homePageSearchButton")
        search_icon = QIcon.fromTheme("search", QIcon(":/icons/search.svg"))
        if not search_icon.isNull():
            self.search_button.setIcon(search_icon)
        else:
            self.search_button.setText("🔍")
        self.search_button.setToolTip(self.tr("Lancer la recherche"))
        self.search_button.clicked.connect(self._handle_search_query)
        search_layout.addWidget(self.search_button)

        return search_layout

    def _setup_bottom_layout(self):
        """Crée le layout du bas avec la grille de boutons."""
        bottom_h_layout = QHBoxLayout()
        bottom_h_layout.setContentsMargins(10, 5, 10, 10)
        bottom_h_layout.setSpacing(10)

        # Promo Content Manager - self.promo_manager needs to be accessible
        # self.promo_manager is initialized in _init_ui or constructor

        # Left Promotional Area
        self.left_promo_widget = PromoSectionWidget() # self.left_promo_widget needs to be accessible
        self.left_promo_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_message = self.promo_manager.get_random_message()
        if left_message:
            self.left_promo_widget.set_content(
                left_message.get("title", ""),
                left_message.get("body", ""),
                left_message.get("category", "generic")
            )
        else:
            self.left_promo_widget.set_content(self.tr("Info"), self.tr("Aucun message promotionnel disponible."), "generic")
        self.left_promo_widget.clicked.connect(lambda: self.update_promo_widget_content(self.left_promo_widget))

        # Center Map Area / Bottom Content Area
        self.bottom_content_area = QStackedWidget() # self.bottom_content_area needs to be accessible
        self.bottom_content_area.setObjectName("homePageBottomContentArea")
        self.bottom_content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.home_map_widget = HomePageMapWidget(app_translator_func=self.tr)
        self.bottom_content_area.addWidget(self.home_map_widget)
        if hasattr(self.home_map_widget.interaction_handler, 'country_clicked_signal'):
            self.home_map_widget.interaction_handler.country_clicked_signal.connect(self._handle_add_client_for_country)

        # Right Promotional Area
        self.right_promo_widget = PromoSectionWidget() # self.right_promo_widget needs to be accessible
        self.right_promo_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_message = self.promo_manager.get_random_message()
        if self.promo_manager.messages and len(self.promo_manager.messages) > 1:
            current_left_title = self.left_promo_widget.title_label.text() # Need a way to get original title if prefixed
            current_left_body = self.left_promo_widget.body_label.text()
            # This comparison might be tricky if titles are prefixed.
            # For simplicity, we assume left_message holds the original chosen message.
            while right_message == left_message:
                right_message = self.promo_manager.get_random_message()

        if right_message:
            self.right_promo_widget.set_content(
                right_message.get("title", ""),
                right_message.get("body", ""),
                right_message.get("category", "generic")
            )

        else:
            for card_ref in self.module_cards_list:
                if card_ref: card_ref.deleteLater()
            self.module_cards_list.clear()

        button_scroll_area = QScrollArea()
        button_scroll_area.setWidgetResizable(True)
        button_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        button_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        button_scroll_area.setObjectName("homePageButtonScrollArea")

        button_container_widget = QWidget()
        grid_layout = QGridLayout(button_container_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        if self.modules:
            # Afficher uniquement la première carte, plus grande
            module_data = self.modules[0]
            accent_color_key = module_data["object_name"].replace("btn", "").lower()
            card = ModuleCardWidget(
                module_id=module_data["object_name"],
                title=module_data["name"],
                icon_path=module_data["icon"],
                tooltip=module_data["name"],
                navigation_slot=module_data["slot"],
                accent_color_key=accent_color_key
            )
            if module_data["slot"]:
                card.cardClicked.connect(module_data["slot"])
            self.module_cards_list.append(card)
            grid_layout.addWidget(card, 0, 0)

        button_container_widget.setLayout(grid_layout)
        button_scroll_area.setWidget(button_container_widget)
        return button_scroll_area

    def update_promo_widget_content(self, promo_widget_instance):
        """Fetches a new random message and updates the given PromoSectionWidget."""
        message = self.promo_manager.get_random_message()
        if message:
            # Simple logic to try not to show the exact same message immediately
            # Compare with the raw data of the currently displayed message
            current_message_data = promo_widget_instance.current_message_data
            if current_message_data and \
               message.get("title") == current_message_data.get("title") and \
               message.get("body") == current_message_data.get("body") and \
               len(self.promo_manager.messages) > 1:

                new_message = message # Initialize new_message to the current message
                # Try to get a different message
                attempts = 0
                max_attempts = len(self.promo_manager.messages) * 2 # Avoid infinite loop if all messages are same (unlikely)
                while new_message == message and attempts < max_attempts:
                    new_message = self.promo_manager.get_random_message()
                    attempts += 1
                message = new_message # This could be None if get_random_message returns None

            if message: # Ensure message is not None before trying to access its content
                promo_widget_instance.set_content(
                    message.get("title", ""),
                    message.get("body", ""),
                    message.get("category", "generic")
                )
            else: # Fallback if no message could be retrieved or all are duplicates of None
                promo_widget_instance.set_content(
                    self.tr("Info"),
                    self.tr("Contenu non disponible pour le moment."),
                    "generic"
                )
        else: # Original message was None
            promo_widget_instance.set_content(
                self.tr("Info"),
                self.tr("Contenu non disponible pour le moment."),
                "generic"
            )


    def set_map_widget(self, map_widget):
        """Place le widget de la carte dans le conteneur prévu."""
        if hasattr(self, 'map_widget_container'):
            # Vider le conteneur au cas où
            while self.map_widget_container.layout() and self.map_widget_container.layout().count():
                item = self.map_widget_container.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Mettre en place un layout si ce n'est pas déjà fait
            if not self.map_widget_container.layout():
                layout = QVBoxLayout(self.map_widget_container)
                layout.setContentsMargins(0,0,0,0)
                self.map_widget_container.setLayout(layout)

            # Ajouter le nouveau widget de carte
            if map_widget:
                self.map_widget_container.layout().addWidget(map_widget)
                self.map_widget_container.setVisible(True)
            else:
                self.map_widget_container.setVisible(False)

    def set_bottom_widget(self, widget_to_display):
        # Cette méthode est maintenant utilisée pour placer la carte.
        self.set_map_widget(widget_to_display)

    def set_right_sidebar_widget(self, widget_to_display):
        # Clear existing widgets from the right sidebar layout
        while self.right_sidebar_layout.count() > 0:
            item = self.right_sidebar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if widget_to_display:
            self.right_sidebar_layout.addWidget(widget_to_display)
            self.right_sidebar_container.setVisible(True)
        else:
            self.right_sidebar_container.setVisible(False)

    @pyqtSlot()
    def go_to_documents(self):
        if hasattr(self.main_window, 'show_documents_view'):
            self.main_window.show_documents_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_documents_view.")

    @pyqtSlot()
    def go_to_project_management(self):
        if hasattr(self.main_window, 'show_project_management_view'):
            self.main_window.show_project_management_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_project_management_view.")

    @pyqtSlot()
    def go_to_statistics(self):
        # This button should navigate to the main statistics view, not embed it here.
        if hasattr(self.main_window, 'show_statistics_view'):
            self.main_window.show_statistics_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_statistics_view.")

    @pyqtSlot()
    def go_to_product_management(self):
        if hasattr(self.main_window, 'show_product_management_page'):
            self.main_window.show_product_management_page()
        else:
            print(f"HomePageWidget: main_window does NOT have show_product_management_page.")

    @pyqtSlot()
    def go_to_partner_management(self):
        if hasattr(self.main_window, 'show_partner_management_view'):
            self.main_window.show_partner_management_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_partner_management_view.")

    @pyqtSlot()
    def go_to_inventory_management(self):
        if hasattr(self.main_window, 'show_inventory_browser_view'):
            self.main_window.show_inventory_browser_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_inventory_browser_view.")

    @pyqtSlot()
    def go_to_recruitment(self):
        if hasattr(self.main_window, 'show_recruitment_view'):
            self.main_window.show_recruitment_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_recruitment_view.")

    @pyqtSlot()
    def go_to_experience_management(self):
        if hasattr(self.main_window, 'show_experience_module_view'):
            self.main_window.show_experience_module_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_experience_module_view.")

    @pyqtSlot()
    def go_to_botpress_integration(self):
        if hasattr(self.main_window, 'show_botpress_integration_view'):
            self.main_window.show_botpress_integration_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_botpress_integration_view.")

    @pyqtSlot()
    def go_to_camera_management(self):
        if hasattr(self.main_window, 'show_camera_management_view'):
            self.main_window.show_camera_management_view()
        else:
            print(f"HomePageWidget: main_window does NOT have show_camera_management_view.")

    @pyqtSlot()
    def go_to_settings(self):
        if hasattr(self.main_window, 'show_settings_page'):
            self.main_window.show_settings_page()
        else:
            print(f"HomePageWidget: main_window does NOT have show_settings_page.")

    def _handle_add_client_for_country(self, country_name):
        dialog = AddNewClientDialog(parent=self, initial_country_name=country_name)
        if dialog.exec_() == AddNewClientDialog.Accepted:
            client_data = dialog.get_data()
            controller = ClientController()
            try:
                controller.add_new_client(client_data)
                QMessageBox.information(self, self.tr("Client Ajouté"), self.tr("Le nouveau client a été ajouté avec succès."))
                self.home_map_widget.refresh_map()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur lors de l'ajout du client: {0}").format(str(e)))



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys


    try:
        import icons_rc
    except ImportError:
        print("Warning: icons_rc.py not found. Icons might not display in direct test.")

    app = QApplication(sys.argv)
    class MockMainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Mock Main Window for HomePageWidget Test")
            self.main_layout = QVBoxLayout(self)


            self.statistics_dashboard_instance = QLabel("Contenu de la Page Statistiques (Mock)")
            self.statistics_dashboard_instance.setAlignment(Qt.AlignCenter)
            self.statistics_dashboard_instance.setStyleSheet("background-color: lightgreen; font-size: 18px;")

            self.home_page = HomePageWidget(self)
            self.main_layout.addWidget(self.home_page)
            self.resize(1200, 800)

        def get_statistics_widget_instance(self):
            return self.statistics_dashboard_instance

        def show_documents_view(self): print("MockMainWindow: show_documents_view called")
        def show_project_management_view(self): print("MockMainWindow: show_project_management_view called")

        def show_statistics_view(self):
            print("MockMainWindow: show_statistics_view called (Full Page Navigation Fallback)")

            temp_stats_page = QLabel("PAGE STATS COMPLÈTE (FALLBACK)")
            temp_stats_page.setAlignment(Qt.AlignCenter)
            temp_stats_page.setStyleSheet("background-color: yellow; font-size: 22px;")

            current_central_widget = self.main_layout.itemAt(0).widget() # Assuming HomePageWidget is the first
            if current_central_widget:
                current_central_widget.setVisible(False) # Hide HomePageWidget

            # This is a very basic way to simulate page change in mock;
            # in real app, QStackedWidget handles this.
            # For simplicity, just add and show, previous one is hidden.
            # If there was another page showing, it should be hidden too.
            # This mock doesn't handle complex stack, just one level.
            if hasattr(self, "_current_mock_page") and self._current_mock_page:
                self._current_mock_page.setVisible(False)
                self._current_mock_page.deleteLater()

            self.main_layout.addWidget(temp_stats_page)
            self._current_mock_page = temp_stats_page
            self._current_mock_page.setVisible(True)


        def show_product_management_page(self): print("MockMainWindow: show_product_management_page called")
        def show_partner_management_view(self): print("MockMainWindow: show_partner_management_view called")
        def show_inventory_browser_view(self): print("MockMainWindow: show_inventory_browser_view called")
        def show_recruitment_view(self): print("MockMainWindow: show_recruitment_view called")
        def show_experience_module_view(self): print("MockMainWindow: show_experience_module_view called")
        def show_botpress_integration_view(self): print("MockMainWindow: show_botpress_integration_view called")
        def show_camera_management_view(self): print("MockMainWindow: show_camera_management_view called")
        def show_settings_page(self): print("MockMainWindow: show_settings_page called")


    main_win = MockMainWindow()
    main_win.show()
    sys.exit(app.exec_())
