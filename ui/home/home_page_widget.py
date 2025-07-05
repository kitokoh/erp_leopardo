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


class HomePageWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window # Store reference to DocumentManager
        self.setObjectName("HomePageWidget")
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
        main_v_layout.setContentsMargins(0,0,0,0) # Main layout itself has no outer margins
        main_v_layout.setSpacing(10) # Add some spacing between major horizontal sections

        # Define self.modules here so it's accessible by _setup_center_layout
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

        # Initialize Promo Content Manager here so it's accessible by _setup_bottom_layout
        self.promo_manager = PromoContentManager()

        # Setup layouts by calling helper methods
        center_layout = self._setup_center_layout()
        bottom_layout = self._setup_bottom_layout()

        main_v_layout.addLayout(center_layout)
        main_v_layout.addLayout(bottom_layout, 1) # Assign stretch factor to the bottom layout


        # Search Bar Layout (added at the top of main_v_layout)
        search_bar_layout = QHBoxLayout()
        search_bar_layout.setContentsMargins(10, 5, 10, 5) # Adjust margins as needed
        search_bar_layout.setSpacing(5)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("homePageSearchInput")
        self.search_input.setPlaceholderText(self.tr("Rechercher dans l'application..."))
        self.search_input.returnPressed.connect(self._handle_search_query)
        search_bar_layout.addWidget(self.search_input, 1) # Input takes most space

        self.search_button = QPushButton()
        self.search_button.setObjectName("homePageSearchButton")
        search_icon = QIcon.fromTheme("search", QIcon(":/icons/search.svg")) # Common theme icon name
        if not search_icon.isNull():
            self.search_button.setIcon(search_icon)
        else:
            self.search_button.setText("🔍") # Fallback emoji/text
        self.search_button.setToolTip(self.tr("Lancer la recherche"))
        self.search_button.clicked.connect(self._handle_search_query)
        # self.search_button.setFixedSize(QSize(30,30)) # Adjust size as needed
        search_bar_layout.addWidget(self.search_button)

        # Insert search bar at the top of the main layout
        main_v_layout.insertLayout(0, search_bar_layout)


        self.setLayout(main_v_layout)

    def _handle_search_query(self):
        query = self.search_input.text()
        if not query.strip():
            # Optional: Show a message if search query is empty, or just do nothing
            # QMessageBox.information(self, self.tr("Recherche"), self.tr("Veuillez entrer un terme de recherche."))
            return

        QMessageBox.information(
            self,
            self.tr("Recherche Globale (Simulation)"),
            self.tr("La fonctionnalité de recherche n'est pas encore implémentée.\n"
                    "Recherche demandée pour : '{0}'").format(query)
        )
        # In a real scenario, you would trigger the actual search logic here.

    def eventFilter(self, obj, event):
        # Check if the object is a QPushButton (our module buttons)
        if isinstance(obj, QPushButton) and hasattr(obj, 'animation_group'):
            if event.type() == QEvent.Enter:
                if not obj.original_geometry: # Initialize geometry on first relevant event
                    obj.original_geometry = obj.geometry()

                    # Define animations if not already defined
                    if not obj.animation_group:
                        original_rect = obj.original_geometry

                        # Enlarged rect (e.g., 10% bigger, centered)
                        new_width = int(original_rect.width() * 1.1)
                        new_height = int(original_rect.height() * 1.1)
                        new_x = original_rect.x() - (new_width - original_rect.width()) // 2
                        new_y = original_rect.y() - (new_height - original_rect.height()) // 2
                        enlarged_rect = QRect(new_x, new_y, new_width, new_height)

                        enter_anim = QPropertyAnimation(obj, b"geometry")
                        enter_anim.setDuration(150) # ms
                        enter_anim.setStartValue(original_rect)
                        enter_anim.setEndValue(enlarged_rect)
                        enter_anim.setEasingCurve(QEasingCurve.InOutQuad)

                        leave_anim = QPropertyAnimation(obj, b"geometry")
                        leave_anim.setDuration(150) # ms
                        leave_anim.setStartValue(enlarged_rect) # Will be current geometry
                        leave_anim.setEndValue(original_rect)
                        leave_anim.setEasingCurve(QEasingCurve.InOutQuad)

                        obj.animation_group = [enter_anim, leave_anim]

                # Start enter animation
                if obj.animation_group:
                    obj.animation_group[1].stop() # Stop leave animation if running
                    obj.animation_group[0].setStartValue(obj.geometry()) # Start from current geometry
                    obj.animation_group[0].start()
                return True # Event handled

            elif event.type() == QEvent.Leave:
                # Start leave animation
                if obj.animation_group and obj.original_geometry: # Ensure animations and original_geometry are set
                    obj.animation_group[0].stop() # Stop enter animation if running
                    obj.animation_group[1].setStartValue(obj.geometry()) # Start from current geometry
                    obj.animation_group[1].setEndValue(obj.original_geometry) # Ensure it returns to original
                    obj.animation_group[1].start()
                return True # Event handled

        return super().eventFilter(obj, event)

    def _setup_center_layout(self):
        """Creates and configures the central layout with GIF, buttons, and right sidebar."""
        center_h_layout = QHBoxLayout()
        center_h_layout.setContentsMargins(10, 10, 10, 10)
        center_h_layout.setSpacing(15)

        # GIF Label
        gif_label = QLabel()
        gif_label.setObjectName("homePageGifLabel")
        available_gifs = ["1.gif", "2.gif", "3.gif"]
        chosen_gif_name = random.choice(available_gifs)
        gif_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "gifshome", chosen_gif_name)
        if not os.path.exists(gif_path):
            gif_path_alt_base = os.path.join("resources", "gifshome")
            if os.path.isdir(gif_path_alt_base): gif_path = os.path.join(gif_path_alt_base, chosen_gif_name)
            else: gif_path = chosen_gif_name

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            gif_label.setMovie(self.movie)
            gif_label.setFixedSize(QSize(350, 300))
            gif_label.setScaledContents(True)
            self.movie.start()
            gif_label.setAlignment(Qt.AlignCenter)
        else:
            gif_label.setText(self.tr("GIF '{0}' non trouvé.").format(chosen_gif_name))
            gif_label.setStyleSheet("color: red;")
            gif_label.setAlignment(Qt.AlignCenter)
        center_h_layout.addWidget(gif_label, 1)

        # Button Grid
        button_scroll_area = QScrollArea()
        button_scroll_area.setWidgetResizable(True)
        button_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        button_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button_scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        button_container_widget = QWidget()
        button_container_widget.setObjectName("homePageButtonGridContainer")
        button_container_widget.setStyleSheet("background-color: transparent;")

        grid_layout = QGridLayout(button_container_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setSpacing(10)

        # self.modules is defined in _init_ui or constructor
        row, col = 0, 0
        num_columns = 4
        for i, module_data in enumerate(self.modules): # self.modules needs to be accessible
            button = QPushButton(module_data["name"])
            button.setObjectName(module_data["object_name"])
            if module_data["icon"] and QIcon.hasThemeIcon(module_data["icon"]):
                button.setIcon(QIcon(module_data["icon"]))
            else:
                button.setIcon(QIcon(":/icons/placeholder_icon.svg"))
            button.setIconSize(QSize(32, 32))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(module_data["slot"])

            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(2)
            shadow.setColor(QColor(0, 0, 0, 60))
            button.setGraphicsEffect(shadow)

            # Store animations and original geometry on the button object itself for easy access
            button.original_geometry = None # Will be set once shown
            button.animation_group = [] # To store enter/leave animations

            # Install event filter to handle Enter/Leave for animation
            button.installEventFilter(self)

            grid_layout.addWidget(button, row, col)
            col += 1
            if col >= num_columns:
                col = 0
                row += 1
        grid_layout.setRowStretch(row + 1, 1)
        grid_layout.setColumnStretch(num_columns, 1)
        button_container_widget.setLayout(grid_layout)
        button_scroll_area.setWidget(button_container_widget)
        center_h_layout.addWidget(button_scroll_area, 2)

        # Right Sidebar
        self.right_sidebar_container = QFrame()
        self.right_sidebar_container.setObjectName("homePageRightSidebar")
        self.right_sidebar_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.right_sidebar_layout = QVBoxLayout(self.right_sidebar_container)
        self.right_sidebar_layout.setContentsMargins(0,0,0,0)
        self.right_sidebar_container.setLayout(self.right_sidebar_layout)

        self.quick_stats = QuickStatsWidget(self)
        self.quick_stats.refresh_requested.connect(self._refresh_quick_stats_data)
        self.set_right_sidebar_widget(self.quick_stats)
        self._refresh_quick_stats_data() # Initial data load

        center_h_layout.addWidget(self.right_sidebar_container, 1)

        return center_h_layout

    def _refresh_quick_stats_data(self):
        """Generates simulated data and updates the QuickStatsWidget."""
        if not hasattr(self, 'quick_stats') or not self.quick_stats:
            return

        # Simulate fetching new data
        simulated_data = [
            {"label": self.tr("Clients Actifs:"), "value": str(random.randint(100, 200))},
            {"label": self.tr("Projets en Cours:"), "value": str(random.randint(10, 50))},
            {"label": self.tr("Tâches Ouvertes:"), "value": str(random.randint(5, 30))},
            {"label": self.tr("Nouveaux Documents (Mois):"), "value": str(random.randint(50, 150))},
            {"label": self.tr("Tickets Support Actifs:"), "value": str(random.randint(0,10))}
        ]
        self.quick_stats.update_stats(simulated_data)



    def _setup_bottom_layout(self):
        """Creates and configures the bottom layout with promotional widgets and content area."""
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
            self.right_promo_widget.set_content(self.tr("Avis"), self.tr("Consultez nos dernières mises à jour."), "generic")
        self.right_promo_widget.clicked.connect(lambda: self.update_promo_widget_content(self.right_promo_widget))

        bottom_h_layout.addWidget(self.left_promo_widget, 1)
        bottom_h_layout.addWidget(self.bottom_content_area, 3)
        bottom_h_layout.addWidget(self.right_promo_widget, 1)

        return bottom_h_layout

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


    def set_bottom_widget(self, widget_to_display):
        while self.bottom_content_area.count() > 0:
            widget = self.bottom_content_area.widget(0)
            self.bottom_content_area.removeWidget(widget)
            widget.deleteLater() # Important pour éviter les fuites de mémoire si les widgets ne sont pas réutilisés


        if widget_to_display:
            self.bottom_content_area.addWidget(widget_to_display)
            self.bottom_content_area.setCurrentWidget(widget_to_display)
            self.bottom_content_area.setVisible(True)
        else:
            self.bottom_content_area.setVisible(False)

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
