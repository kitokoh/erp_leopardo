# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QSizePolicy,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QIcon, QMovie
import os
import random # Added for random GIF selection

class HomePageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomePageWidget")
        self._init_ui()

    def _init_ui(self):
        main_v_layout = QVBoxLayout(self) # Layout principal vertical
        main_v_layout.setContentsMargins(20, 20, 20, 20)
        main_v_layout.setSpacing(20)

        # Welcome Message
        welcome_label = QLabel(self.tr("Bienvenue à votre Gestionnaire d'Application"))
        welcome_label.setObjectName("homePageWelcomeLabel")
        welcome_font = QFont()
        welcome_font.setPointSize(28)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        main_v_layout.addWidget(welcome_label)

        # GIF Area
        gif_label = QLabel()
        
        available_gifs = ["1.gif", "2.gif", "3.gif"]
        chosen_gif_name = random.choice(available_gifs)
        
        # Path construction for when this script is in ui/home/
        gif_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "gifshome", chosen_gif_name)

        if not os.path.exists(gif_path):
            # Fallback assuming script might be run from project root or resources is directly accessible
            gif_path_alt_base = os.path.join("resources", "gifshome")
            if os.path.isdir(gif_path_alt_base):
                 gif_path = os.path.join(gif_path_alt_base, chosen_gif_name)
            else: # Final fallback if resources/gifshome not found from typical locations
                 gif_path = chosen_gif_name # This will likely fail if not in current dir, but it's a last resort

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            gif_label.setMovie(self.movie)
            
            target_height = 200 
            # Ensure pixmap is valid before trying to get its dimensions
            if not self.movie.currentPixmap().isNull():
                scaled_width = int(target_height * self.movie.currentPixmap().width() / self.movie.currentPixmap().height())
                self.movie.setScaledSize(QSize(scaled_width, target_height))
            else:
                # Default/fallback size if pixmap is null (e.g. GIF not loaded yet or invalid)
                self.movie.setScaledSize(QSize(300, target_height))


            self.movie.start()
            gif_label.setAlignment(Qt.AlignCenter)
            main_v_layout.addWidget(gif_label)
        else:
            gif_placeholder_label = QLabel(self.tr("GIF non trouvé ({0}) dans :\n{1}\nVeuillez vérifier les chemins.").format(chosen_gif_name, gif_path))
            gif_placeholder_label.setAlignment(Qt.AlignCenter)
            gif_placeholder_label.setStyleSheet("color: red; font-style: italic;")
            main_v_layout.addWidget(gif_placeholder_label)

        # Scroll Area for module buttons
        scroll_area = QScrollArea() 
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; min-height: 300px; }")

        content_widget = QWidget()
        content_widget.setObjectName("homePageButtonGridContainer")
        content_widget.setStyleSheet("background-color: transparent;")
        
        grid_layout = QGridLayout() 
        grid_layout.setContentsMargins(10, 10, 10, 10) 
        grid_layout.setSpacing(20)

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
            {"name": self.tr("Paramètres"), "object_name": "btnSettings", "icon": ":/icons/modern/settings.svg", "slot": self.go_to_settings}
        ]

        row, col = 0, 0
        num_columns = 3

        for i, module in enumerate(self.modules):
            button = QPushButton(module["name"])
            button.setObjectName(module["object_name"])
            if module["icon"] and QIcon.hasThemeIcon(module["icon"]):
                button.setIcon(QIcon(module["icon"]))
                button.setIconSize(QSize(32,32)) 
            
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(module["slot"])
            grid_layout.addWidget(button, row, col)

            col += 1
            if col >= num_columns:
                col = 0
                row += 1
        
        content_widget.setLayout(grid_layout)
        scroll_area.setWidget(content_widget)
        main_v_layout.addWidget(scroll_area) 
        
        self.setLayout(main_v_layout)

    # Slots de navigation... (inchangés)
    @pyqtSlot()
    def go_to_documents(self):
        if hasattr(self.parent(), 'show_documents_view'):
            self.parent().show_documents_view()

    @pyqtSlot()
    def go_to_project_management(self):
        if hasattr(self.parent(), 'show_project_management_view'):
            self.parent().show_project_management_view()

    @pyqtSlot()
    def go_to_statistics(self):
        if hasattr(self.parent(), 'show_statistics_view'):
            self.parent().show_statistics_view()

    @pyqtSlot()
    def go_to_product_management(self):
        if hasattr(self.parent(), 'show_product_management_page'):
            self.parent().show_product_management_page()

    @pyqtSlot()
    def go_to_partner_management(self):
        if hasattr(self.parent(), 'show_partner_management_view'):
            self.parent().show_partner_management_view()

    @pyqtSlot()
    def go_to_inventory_management(self):
        if hasattr(self.parent(), 'show_inventory_browser_view'):
            self.parent().show_inventory_browser_view()

    @pyqtSlot()
    def go_to_recruitment(self):
        if hasattr(self.parent(), 'show_recruitment_view'):
            self.parent().show_recruitment_view()

    @pyqtSlot()
    def go_to_experience_management(self):
        if hasattr(self.parent(), 'show_experience_module_view'):
            self.parent().show_experience_module_view()

    @pyqtSlot()
    def go_to_botpress_integration(self):
        if hasattr(self.parent(), 'show_botpress_integration_view'):
            self.parent().show_botpress_integration_view()

    @pyqtSlot()
    def go_to_camera_management(self):
        if hasattr(self.parent(), 'show_camera_management_view'):
            self.parent().show_camera_management_view()

    @pyqtSlot()
    def go_to_settings(self):
        if hasattr(self.parent(), 'show_settings_page'):
            self.parent().show_settings_page()

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    # import icons_rc # Décommentez si vous testez ce fichier isolément et utilisez les ressources

    app = QApplication(sys.argv)
    class MockMainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Mock Main Window")
            layout = QVBoxLayout(self)
            # Simuler l'import depuis le nouveau chemin pour le test __main__
            # Ceci ne fonctionnera que si le script est exécuté depuis la racine du projet
            # et que ui/home est dans le PYTHONPATH.
            # Pour un test robuste, il faudrait ajuster sys.path ici.
            # from ui.home.home_page_widget import HomePageWidget 
            self.home_page = HomePageWidget(self) # Supposant que l'import global fonctionne
            layout.addWidget(self.home_page)
            self.resize(800, 900) 

        def show_documents_view(self): print("Navigating to Documents View")
        def show_project_management_view(self): print("Navigating to Project Management")
        def show_statistics_view(self): print("Navigating to Statistics")
        def show_product_management_page(self): print("Navigating to Product Management")
        def show_partner_management_view(self): print("Navigating to Partner Management")
        def show_inventory_browser_view(self): print("Navigating to Inventory Management")
        def show_recruitment_view(self): print("Navigating to Recruitment")
        def show_experience_module_view(self): print("Navigating to Experience Management")
        def show_botpress_integration_view(self): print("Navigating to Botpress Integration")
        def show_camera_management_view(self): print("Navigating to Camera Management")
        def show_settings_page(self): print("Navigating to Settings Page")

    main_win = MockMainWindow()
    main_win.show()
    sys.exit(app.exec_())
