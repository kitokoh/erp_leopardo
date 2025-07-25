import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

class ModernApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 400, 300)

        # Set a modern, dark theme
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        button_style = """
            QPushButton {
                background-color: #3f87f5;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #3672cf;
            }
            QPushButton:pressed {
                background-color: #2a5a9e;
            }
        """

        marketing_button = QPushButton("Marketing Automation")
        marketing_button.setStyleSheet(button_style)
        marketing_button.clicked.connect(self.open_marketing_app)
        layout.addWidget(marketing_button)

        crm_button = QPushButton("CRM")
        crm_button.setStyleSheet(button_style)
        crm_button.clicked.connect(self.open_crm_app)
        layout.addWidget(crm_button)

    def open_marketing_app(self):
        try:
            # Note: This assumes the script is run from the root directory
            subprocess.Popen(["python3", "marketing_automation/main.py"])
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "Could not find the Marketing Automation application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def open_crm_app(self):
        try:
            # Note: This assumes the script is run from the root directory
            subprocess.Popen(["python3", "crm/main.py"])
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "Could not find the CRM application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernApp()
    window.show()
    sys.exit(app.exec_())
