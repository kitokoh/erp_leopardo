import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont

class CrmApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRM")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()
        label = QLabel("Welcome to the CRM App!")
        label.setFont(QFont("Arial", 16))
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CrmApp()
    window.show()
    sys.exit(app.exec_())
