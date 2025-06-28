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
    def __init__(self, parent=None):
        super().__init__(parent)
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
        center_h_layout.setContentsMargins(10, 10, 10, 10) # Marges pour cette section (ajouté top margin)

        center_h_layout.setSpacing(15)

        # Colonne Gauche: GIF
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
            # Tentative de redimensionnement du QMovie lui-même avant de l'assigner
            # ou de contrôler la taille du QLabel.
            # Pour un contrôle proportionnel, on peut écouter le signal resized du QLabel parent.
            # Pour l'instant, fixons une taille pour la prévisibilité.
            # self.movie.setScaledSize(QSize(350, 300)) # Ajustez au besoin
            gif_label.setFixedSize(QSize(350, 300)) # Donner une taille fixe au QLabel
            gif_label.setScaledContents(True) # S'assurer que le contenu du QMovie s'adapte au QLabel

            self.movie.start()
            gif_label.setAlignment(Qt.AlignCenter)

        else:
            gif_label.setText(self.tr("GIF '{0}' non trouvé.").format(chosen_gif_name))
            gif_label.setStyleSheet("color: red;")
            gif_label.setAlignment(Qt.AlignCenter)

        center_h_layout.addWidget(gif_label, 1)


        # Colonne Droite: Boutons de modules
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

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
            {"name": self.tr("Module X"), "object_name": "btnModuleX", "icon": ":/icons/placeholder_icon.svg", "slot": self.go_to_settings}
        ]
        row, col = 0, 0
        num_columns = 4


        for i, module_data in enumerate(self.modules):
            button = QPushButton(module_data["name"])
            button.setObjectName(module_data["object_name"])
            if module_data["icon"] and QIcon.hasThemeIcon(module_data["icon"]):
                button.setIcon(QIcon(module_data["icon"]))
                button.setIconSize(QSize(32, 32)) # Taille d'icône réduite pour boutons plus petits

            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12) # Ombre un peu moins étendue
            shadow.setXOffset(1)    # Offset plus subtil
            shadow.setYOffset(2)    # Offset plus subtil
            shadow.setColor(QColor(0, 0, 0, 80)) # Ombre plus légère
            button.setGraphicsEffect(shadow)

            button.clicked.connect(module_data["slot"])
            grid_layout.addWidget(button, row, col)
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

        grid_layout.setRowStretch(row + 1, 1)
        grid_layout.setColumnStretch(num_columns, 1)

        button_container_widget.setLayout(grid_layout)
        scroll_area.setWidget(button_container_widget)
        center_h_layout.addWidget(scroll_area, 2)

        main_v_layout.addLayout(center_h_layout)

        self.bottom_content_area = QStackedWidget()
        self.bottom_content_area.setObjectName("homePageBottomContentArea")
        self.bottom_content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_v_layout.addWidget(self.bottom_content_area, 1)


        self.setLayout(main_v_layout)

    def set_bottom_widget(self, widget_to_display):
        while self.bottom_content_area.count() > 0:
            self.bottom_content_area.removeWidget(self.bottom_content_area.widget(0))

        if widget_to_display:
            self.bottom_content_area.addWidget(widget_to_display)
            self.bottom_content_area.setCurrentWidget(widget_to_display)
            self.bottom_content_area.setVisible(True)
        else:
            self.bottom_content_area.setVisible(False)


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
        if hasattr(self.parent(), 'get_statistics_widget_instance'):
            stats_widget = self.parent().get_statistics_widget_instance()
            if stats_widget:
                self.set_bottom_widget(stats_widget)
            else:
                 if hasattr(self.parent(), 'show_statistics_view'):
                    self.parent().show_statistics_view()
        elif hasattr(self.parent(), 'show_statistics_view'):
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

        def show_documents_view(self): print("Mock: Navigating to Documents View")
        def show_project_management_view(self): print("Mock: Navigating to Project Management")
        def show_statistics_view(self):
            print("Mock: Navigating to Statistics (Fallback - full page)")
            temp_stats_page = QLabel("PAGE STATS COMPLÈTE (FALLBACK)")
            temp_stats_page.setAlignment(Qt.AlignCenter)
            temp_stats_page.setStyleSheet("background-color: yellow; font-size: 22px;")

            while self.main_layout.count():
                 item = self.main_layout.takeAt(0)
                 widget = item.widget()
                 if widget:
                     widget.deleteLater()
            self.main_layout.addWidget(temp_stats_page)


        def show_product_management_page(self): print("Mock: Navigating to Product Management")
        def show_partner_management_view(self): print("Mock: Navigating to Partner Management")
        def show_inventory_browser_view(self): print("Mock: Navigating to Inventory Management")
        def show_recruitment_view(self): print("Mock: Navigating to Recruitment")
        def show_experience_module_view(self): print("Mock: Navigating to Experience Management")
        def show_botpress_integration_view(self): print("Mock: Navigating to Botpress Integration")
        def show_camera_management_view(self): print("Mock: Navigating to Camera Management")
        def show_settings_page(self): print("Mock: Navigating to Settings Page")

    main_win = MockMainWindow()
    main_win.show()
    sys.exit(app.exec_())
