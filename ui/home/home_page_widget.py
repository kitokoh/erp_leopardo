# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLabel,
    QSizePolicy, QScrollArea, QStackedWidget, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize, QFile, QTextStream
from PyQt5.QtGui import QFont, QIcon, QMovie, QColor

import os
import random

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
        main_v_layout.setContentsMargins(0,0,0,0)
        main_v_layout.setSpacing(0)

        # --- Message de bienvenue (Supprimé) ---

        # --- Section Centrale: GIF (gauche) et Boutons (droite) ---
        center_h_layout = QHBoxLayout()
        center_h_layout.setContentsMargins(10, 10, 10, 10)
        center_h_layout.setSpacing(15)


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

        center_h_layout.addWidget(gif_label, 1) # GIF on the left, stretch factor 1

        # Button Grid in the Center
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
            # {"name": self.tr("Module X"), "object_name": "btnModuleX", "icon": ":/icons/placeholder_icon.svg", "slot": self.go_to_settings} # Example, can be removed
        ]
        row, col = 0, 0
        num_columns = 4 # Changed from 3 to 4 to ensure max 3 rows for 11 buttons (4-4-3)


        for i, module_data in enumerate(self.modules):
            button = QPushButton(module_data["name"])
            button.setObjectName(module_data["object_name"])
            if module_data["icon"] and QIcon.hasThemeIcon(module_data["icon"]): # Check if icon exists
                button.setIcon(QIcon(module_data["icon"]))
            else: # Fallback icon
                button.setIcon(QIcon(":/icons/placeholder_icon.svg"))
            button.setIconSize(QSize(32, 32))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(module_data["slot"])
            grid_layout.addWidget(button, row, col)
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

        grid_layout.setRowStretch(row + 1, 1) # Ensure remaining rows/cols don't take extra space
        grid_layout.setColumnStretch(num_columns, 1)

        button_container_widget.setLayout(grid_layout)
        button_scroll_area.setWidget(button_container_widget)
        center_h_layout.addWidget(button_scroll_area, 2) # Buttons in center, stretch factor 2

        # Right Sidebar for Statistics Summary
        self.right_sidebar_container = QFrame() # Use QFrame for potential styling (e.g., border)
        self.right_sidebar_container.setObjectName("homePageRightSidebar")
        self.right_sidebar_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # self.right_sidebar_container.setFixedWidth(250) # Example fixed width, adjust as needed
        self.right_sidebar_layout = QVBoxLayout(self.right_sidebar_container)
        self.right_sidebar_layout.setContentsMargins(5,5,5,5)
        self.right_sidebar_container.setLayout(self.right_sidebar_layout)
        self.right_sidebar_container.setVisible(False) # Initially hidden until content is set
        center_h_layout.addWidget(self.right_sidebar_container, 1) # Summary on right, stretch factor 1

        main_v_layout.addLayout(center_h_layout)

        # Bottom Area for Map and Promotional Sections
        bottom_h_layout = QHBoxLayout()
        bottom_h_layout.setContentsMargins(10, 5, 10, 10) # Added some margins
        bottom_h_layout.setSpacing(10) # Added spacing between sections

        # Left Promotional Area
        self.left_promo_area = QFrame()
        self.left_promo_area.setObjectName("leftPromoArea")
        self.left_promo_area.setFrameShape(QFrame.StyledPanel) # Example styling
        # self.left_promo_area.setFixedWidth(200) # Example fixed width, adjust as needed
        self.left_promo_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_promo_layout = QVBoxLayout(self.left_promo_area)
        left_promo_label = QLabel(self.tr("Espace Promo Gauche"))
        left_promo_label.setAlignment(Qt.AlignCenter)
        left_promo_layout.addWidget(left_promo_label)
        self.left_promo_area.setLayout(left_promo_layout)

        # Center Map Area
        self.bottom_content_area = QStackedWidget()
        self.bottom_content_area.setObjectName("homePageBottomContentArea")
        self.bottom_content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Right Promotional Area
        self.right_promo_area = QFrame()
        self.right_promo_area.setObjectName("rightPromoArea")
        self.right_promo_area.setFrameShape(QFrame.StyledPanel) # Example styling
        # self.right_promo_area.setFixedWidth(200) # Example fixed width, adjust as needed
        self.right_promo_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_promo_layout = QVBoxLayout(self.right_promo_area)
        right_promo_label = QLabel(self.tr("Espace Promo Droit"))
        right_promo_label.setAlignment(Qt.AlignCenter)
        right_promo_layout.addWidget(right_promo_label)
        self.right_promo_area.setLayout(right_promo_layout)

        bottom_h_layout.addWidget(self.left_promo_area, 1) # Stretch factor 1 for left promo
        bottom_h_layout.addWidget(self.bottom_content_area, 3) # Stretch factor 3 for map (larger)
        bottom_h_layout.addWidget(self.right_promo_area, 1) # Stretch factor 1 for right promo

        main_v_layout.addLayout(bottom_h_layout, 1) # Add the horizontal layout to the main vertical layout

        self.setLayout(main_v_layout)

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
