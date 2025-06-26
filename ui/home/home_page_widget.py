# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLabel, 
    QSizePolicy, QScrollArea, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize, QFile, QTextStream
from PyQt5.QtGui import QFont, QIcon, QMovie
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
        main_v_layout.setContentsMargins(0,0,0,0) # Pas de marges pour le layout principal du widget
        main_v_layout.setSpacing(0)

        # --- Section Supérieure: Message de bienvenue ---
        welcome_label = QLabel(self.tr("Bienvenue à votre Gestionnaire d'Application"))
        welcome_label.setObjectName("homePageWelcomeLabel")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setWordWrap(True)
        # La police est définie dans home_page_style.qss, mais on peut la forcer ici aussi
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        welcome_label.setFont(font)
        # Ajout d'un QFrame pour le message de bienvenue pour permettre un padding via QSS si besoin
        welcome_frame = QFrame()
        welcome_frame_layout = QVBoxLayout(welcome_frame)
        welcome_frame_layout.addWidget(welcome_label)
        welcome_frame_layout.setContentsMargins(10, 15, 10, 15) # Padding pour le message
        main_v_layout.addWidget(welcome_frame)


        # --- Section Centrale: GIF (gauche) et Boutons (droite) ---
        center_h_layout = QHBoxLayout()
        center_h_layout.setContentsMargins(10, 0, 10, 10) # Marges pour cette section
        center_h_layout.setSpacing(15)

        # Colonne Gauche: GIF
        gif_label = QLabel()
        gif_label.setObjectName("homePageGifLabel")
        available_gifs = ["1.gif", "2.gif", "3.gif"]
        chosen_gif_name = random.choice(available_gifs)
        gif_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "gifshome", chosen_gif_name)
        if not os.path.exists(gif_path):
             gif_path_alt_base = os.path.join("resources", "gifshome") # Fallback pour exécution depuis racine
             if os.path.isdir(gif_path_alt_base): gif_path = os.path.join(gif_path_alt_base, chosen_gif_name)
             else: gif_path = chosen_gif_name 

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            gif_label.setMovie(self.movie)
            self.movie.setScaledSize(QSize(300,250)) # Taille indicative, à ajuster
            self.movie.start()
            gif_label.setAlignment(Qt.AlignCenter)
            gif_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) # Laisser le GIF dicter sa taille préférée
            # gif_label.setScaledContents(True) # Peut déformer si la taille du label est contrainte
        else:
            gif_label.setText(self.tr("GIF '{0}' non trouvé.").format(chosen_gif_name))
            gif_label.setStyleSheet("color: red;")
            gif_label.setAlignment(Qt.AlignCenter)
        
        center_h_layout.addWidget(gif_label, 1) # Stretch factor 1 pour le GIF

        # Colonne Droite: Boutons de modules
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")


        button_container_widget = QWidget() # Widget qui contiendra la grille
        button_container_widget.setObjectName("homePageButtonGridContainer")
        button_container_widget.setStyleSheet("background-color: transparent;") 
                                             
        grid_layout = QGridLayout(button_container_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5) # Marges légères autour de la grille
        grid_layout.setSpacing(10) # Espacement réduit entre boutons

        self.modules = [
            {"name": self.tr("Gestion Documents Client"), "object_name": "btnClientDocuments", "icon": ":/icons/modern/folder-docs.svg", "slot": self.go_to_documents},
            {"name": self.tr("Gestion de Projet"), "object_name": "btnProjectManagement", "icon": ":/icons/dashboard.svg", "slot": self.go_to_project_management},
            {"name": self.tr("Statistiques"), "object_name": "btnStatistics", "icon": ":/icons/bar-chart.svg", "slot": self.go_to_statistics},
            {"name": self.tr("Gestion des Produits"), "object_name": "btnProductManagement", "icon": ":/icons/book.svg", "slot": self.go_to_product_management},
            {"name": self.tr("Gestion des Partenaires"), "object_name": "btnPartnerManagement", "icon": ":/icons/team.svg", "slot": self.go_to_partner_management},
            {"name": self.tr("Gestion Stock Atelier"), "object_name": "btnInventoryManagement", "icon": ":/icons/book.svg", "slot": self.go_to_inventory_management},
            {"name": self.tr("Recrutement"), "object_name": "btnRecruitment", "icon": ":/icons/users.svg", "slot": self.go_to_recruitment},
            {"name": self.tr("Gestion des Connaissances"), "object_name": "btnExperienceManagement", "icon": ":/icons/book.svg", "slot": self.go_to_experience_management},
            # Potentiellement ajouter d'autres modules ici pour faire 3 lignes de 4
            {"name": self.tr("Intégration Botpress"), "object_name": "btnBotpressIntegration", "icon": ":/icons/placeholder_icon.svg", "slot": self.go_to_botpress_integration},
            {"name": self.tr("Gestion Caméras"), "object_name": "btnCameraManagement", "icon": ":/icons/video.svg", "slot": self.go_to_camera_management},
            {"name": self.tr("Paramètres"), "object_name": "btnSettings", "icon": ":/icons/modern/settings.svg", "slot": self.go_to_settings},
            {"name": self.tr("Module X"), "object_name": "btnModuleX", "icon": ":/icons/placeholder_icon.svg", "slot": self.go_to_settings} # Placeholder pour 12ème bouton
        ]
        row, col = 0, 0
        num_columns = 4 # 4 boutons par ligne

        for i, module_data in enumerate(self.modules):
            button = QPushButton(module_data["name"])
            button.setObjectName(module_data["object_name"])
            if module_data["icon"] and QIcon.hasThemeIcon(module_data["icon"]):
                button.setIcon(QIcon(module_data["icon"]))
                button.setIconSize(QSize(32, 32)) 
            
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        center_h_layout.addWidget(scroll_area, 2) # Stretch factor 2 pour la grille de boutons
        
        main_v_layout.addLayout(center_h_layout)

        # --- Section Inférieure: Contenu dynamique (ex: page Statistiques) ---
        self.bottom_content_area = QStackedWidget()
        self.bottom_content_area.setObjectName("homePageBottomContentArea")
        # La hauteur sera déterminée par son contenu ou un min-height dans QSS
        self.bottom_content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        main_v_layout.addWidget(self.bottom_content_area, 1) # Stretch factor 1, prendra l'espace restant

        self.setLayout(main_v_layout)

    def set_bottom_widget(self, widget_to_display):
        # S'assurer que le widget est correctement parenté si nécessaire par l'appelant
        # ou reparenter ici si le widget_to_display n'a pas déjà un parent approprié.
        # Pour QStackedWidget, il suffit d'ajouter et de définir comme courant.
        
        # Retirer les anciens widgets pour éviter les doublons
        while self.bottom_content_area.count() > 0:
            self.bottom_content_area.removeWidget(self.bottom_content_area.widget(0))
            
        if widget_to_display:
            self.bottom_content_area.addWidget(widget_to_display)
            self.bottom_content_area.setCurrentWidget(widget_to_display)
            self.bottom_content_area.setVisible(True)
        else:
            self.bottom_content_area.setVisible(False)


    # Slots de navigation... (inchangés)
    @pyqtSlot()
    def go_to_documents(self):
        if hasattr(self.parent(), 'show_documents_view'):
            self.parent().show_documents_view()
    # ... (autres slots go_to_X)

    @pyqtSlot()
    def go_to_project_management(self):
        if hasattr(self.parent(), 'show_project_management_view'):
            self.parent().show_project_management_view()

    @pyqtSlot()
    def go_to_statistics(self):
        # Au lieu de naviguer, on affiche la page des stats en bas
        if hasattr(self.parent(), 'get_statistics_widget_instance'): # Méthode à créer dans MainWindow
            stats_widget = self.parent().get_statistics_widget_instance()
            if stats_widget:
                self.set_bottom_widget(stats_widget)
            else: # Fallback: naviguer si l'instance n'est pas récupérable pour une raison X
                 if hasattr(self.parent(), 'show_statistics_view'):
                    self.parent().show_statistics_view()
        elif hasattr(self.parent(), 'show_statistics_view'): # Fallback si get_statistics_widget_instance n'existe pas
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
            self.main_layout = QVBoxLayout(self) # Changed to be accessible
            
            # Simuler les instances de modules que HomePageWidget pourrait vouloir afficher en bas
            self.statistics_dashboard_instance = QLabel("Contenu de la Page Statistiques (Mock)")
            self.statistics_dashboard_instance.setAlignment(Qt.AlignCenter)
            self.statistics_dashboard_instance.setStyleSheet("background-color: lightgreen; font-size: 18px;")

            self.home_page = HomePageWidget(self)
            self.main_layout.addWidget(self.home_page)
            self.resize(1200, 800)

        def get_statistics_widget_instance(self):
            # Retourne l'instance pour que HomePageWidget puisse l'afficher
            return self.statistics_dashboard_instance

        # Implémentation des méthodes show_X_view pour le mock
        def show_documents_view(self): print("Mock: Navigating to Documents View")
        def show_project_management_view(self): print("Mock: Navigating to Project Management")
        def show_statistics_view(self): 
            print("Mock: Navigating to Statistics (Fallback - full page)")
            # Pour simuler un changement de page complet si get_statistics_widget_instance n'est pas utilisé
            temp_stats_page = QLabel("PAGE STATS COMPLÈTE (FALLBACK)")
            temp_stats_page.setAlignment(Qt.AlignCenter)
            temp_stats_page.setStyleSheet("background-color: yellow; font-size: 22px;")
            
            # Nettoyer le layout et ajouter la nouvelle page (simulation simple)
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
