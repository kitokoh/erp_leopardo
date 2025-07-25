import sys
from PyQt5.QtWidgets import QApplication
from face_app import FaceWindow # Assurez-vous que face_app.py est dans le même dossier

def main():
    app = QApplication(sys.argv)
    face_window = FaceWindow()
    face_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
