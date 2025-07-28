import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QMessageBox, QHBoxLayout, QGraphicsDropShadowEffect, QLabel)
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QFontDatabase
from PyQt5.QtCore import Qt, QSize

class ModernUIMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Leopard")
        self.setGeometry(100, 100, 800, 600)

        # Adding a modern font
        QFontDatabase.addApplicationFont(":/fonts/Roboto-Regular.ttf")

        self.init_ui()

    def init_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Set a gradient background
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor("#2c3e50"))
        gradient.setColorAt(1.0, QColor("#34495e"))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        # Header
        header = QLabel("LEOPARD")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Roboto", 32, QFont.Bold))
        header.setStyleSheet("color: #ecf0f1; padding: 20px;")
        main_layout.addWidget(header)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(40)
        button_layout.setAlignment(Qt.AlignCenter)

        # Button styles
        button_style = """
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: #ecf0f1;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #ecf0f1;
                border-radius: 20px;
                padding: 25px;
                min-width: 150px;
                transition: all 0.3s ease;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #3498db;
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
        """

        # Shadow effect for buttons
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 100))

        # Create and add buttons
        marketing_button = QPushButton("Marketing")
        marketing_button.setStyleSheet(button_style)
        marketing_button.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=15, xOffset=5, yOffset=5, color=QColor(0,0,0,80)))
        marketing_button.clicked.connect(self.open_marketing_app)
        button_layout.addWidget(marketing_button)

        crm_button = QPushButton("CRM")
        crm_button.setStyleSheet(button_style)
        crm_button.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=15, xOffset=5, yOffset=5, color=QColor(0,0,0,80)))
        crm_button.clicked.connect(self.open_crm_app)
        button_layout.addWidget(crm_button)

        erp_button = QPushButton("ERP")
        erp_button.setStyleSheet(button_style)
        erp_button.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=15, xOffset=5, yOffset=5, color=QColor(0,0,0,80)))
        erp_button.clicked.connect(self.open_erp_app)
        button_layout.addWidget(erp_button)

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def open_marketing_app(self):
        QMessageBox.information(self, "Marketing", "This module is under development.")

    def open_crm_app(self):
        try:
            subprocess.Popen(["python3", "crm_main.py"])
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "Could not find the CRM application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def open_erp_app(self):
        QMessageBox.information(self, "ERP", "This module is under development.")

    def _open_app(self, script_path, app_name):
        try:
            subprocess.Popen(["python3", script_path])
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", f"Could not find the {app_name} application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while opening {app_name}: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # This is for the font to be loaded correctly
    # You would typically use a resource file (.qrc) for this
    # For now, we assume the font is in a 'fonts' directory
    # QFontDatabase.addApplicationFont("fonts/Roboto-Regular.ttf")
    window = ModernUIMain()
    window.show()
    sys.exit(app.exec_())
