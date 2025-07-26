import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize

class SpartanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Leopard")
        self.setGeometry(100, 100, 600, 400)

        # A clean, minimalist palette
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#f0f0f0"))
        self.setPalette(palette)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(40)
        main_layout.setAlignment(Qt.AlignCenter)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)

        # Button styles
        button_style = """
            QPushButton {{
                background-color: #ffffff;
                color: #333333;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 15px;
                padding: 20px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                border-color: #3f87f5;
                color: #3f87f5;
            }}
            QPushButton:pressed {{
                background-color: #e8e8e8;
            }}
        """

        # Shadow effect for buttons
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 60))

        marketing_button = QPushButton("Marketing")
        marketing_button.setStyleSheet(button_style)
        marketing_button.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=10, xOffset=2, yOffset=2))
        marketing_button.clicked.connect(self.open_marketing_app)
        button_layout.addWidget(marketing_button)

        crm_button = QPushButton("CRM")
        crm_button.setStyleSheet(button_style)
        crm_button.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=10, xOffset=2, yOffset=2))
        crm_button.clicked.connect(self.open_crm_app)
        button_layout.addWidget(crm_button)

        erp_button = QPushButton("ERP")
        erp_button.setStyleSheet(button_style)
        erp_button.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=10, xOffset=2, yOffset=2))
        erp_button.clicked.connect(self.open_erp_app)
        button_layout.addWidget(erp_button)

        main_layout.addLayout(button_layout)

    def open_marketing_app(self):
        QMessageBox.information(self, "Marketing Automation", "This feature is not yet implemented.")

    def open_crm_app(self):
        self._open_app("cleCRM/main.py", "CRM")

    def open_erp_app(self):
        QMessageBox.information(self, "ERP", "This feature is not yet implemented.")

    def _open_app(self, script_path, app_name):
        try:
            subprocess.Popen(["python3", script_path])
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", f"Could not find the {app_name} application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while opening {app_name}: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpartanApp()
    window.show()
    sys.exit(app.exec_())
