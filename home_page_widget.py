# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QSizePolicy,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

class HomePageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomePageWidget")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Welcome Message
        welcome_label = QLabel(self.tr("Bienvenue à votre Gestionnaire d'Application"))
        welcome_font = QFont()
        welcome_font.setPointSize(28) # Increased size
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #333; margin-bottom: 20px;")
        main_layout.addWidget(welcome_label)

        # Scroll Area for module buttons
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;") # Ensure content widget is transparent
        scroll_area.setWidget(content_widget)

        grid_layout = QGridLayout(content_widget)
        grid_layout.setContentsMargins(20, 10, 20, 10) # Adjusted margins for content within scroll
        grid_layout.setSpacing(20) # Increased spacing

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

        button_style_sheet = """
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                font-weight: bold;
                color: #333333;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #aaaaaa;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """

        row, col = 0, 0
        # Determine number of columns (e.g., 3 for wider screens, 2 for narrower)
        # This is a static example; dynamic resizing would be more complex.
        num_columns = 3

        for i, module in enumerate(self.modules):
            button = QPushButton(module["name"])
            button.setObjectName(module["object_name"])
            # Icons would be set here if `icons_rc.py` was updated
            # from PyQt5.QtGui import QIcon
            # if QIcon.hasThemeIcon(module["icon"]): # Check if icon exists
            #     button.setIcon(QIcon(module["icon"]))
            #     button.setIconSize(Qt.QSize(32,32)) # Example size

            button.setMinimumHeight(100) # Make buttons taller for card-like appearance
            button.setMinimumWidth(180)  # Set a minimum width for buttons
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Allow buttons to expand
            button.setStyleSheet(button_style_sheet)
            button.clicked.connect(module["slot"])

            grid_layout.addWidget(button, row, col)

            col += 1
            if col >= num_columns:
                col = 0
                row += 1

        # Add stretch to the bottom and right of the grid if not full
        # This helps keep cards aligned to top-left if the grid isn't full.
        grid_layout.setRowStretch(row + 1, 1)
        grid_layout.setColumnStretch(num_columns, 1)

        main_layout.addWidget(scroll_area)

    # Placeholder slots for navigation - these will call parent methods
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
    # Need to import icons_rc for testing if icons are used directly in this test
    # import icons_rc

    app = QApplication(sys.argv)
    # This is a basic test, so parent methods won't work without a mock parent
    class MockMainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Mock Main Window")
            layout = QVBoxLayout(self)
            self.home_page = HomePageWidget(self)
            layout.addWidget(self.home_page)
            self.resize(800, 600)

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
