import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QLabel
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QRect, QPoint

class FaceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application Visage Interactive")
        self.setGeometry(100, 100, 500, 600) # Ajusté pour un visage plus allongé

        self.init_ui()

    def init_ui(self):
        # Fond de la fenêtre (couleur de peau approximative)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 224, 189)) # Couleur peau claire
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Style commun pour les boutons
        button_style_base = """
            QPushButton {{
                border: 2px solid #555;
                border-radius: {radius}px; /* Sera défini spécifiquement */
                background-color: {bg_color};
                color: white;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """

        # --- Yeux ---
        eye_radius = "25" # Pour des yeux ronds
        self.right_eye_button = QPushButton("Œil D", self)
        self.right_eye_button.setGeometry(100, 150, 50, 50)
        self.right_eye_button.setStyleSheet(
            button_style_base.format(radius=eye_radius, bg_color="#4A90E2", hover_color="#62A3F0", pressed_color="#3678C2") +
            "QPushButton { padding-bottom: 5px; }" # Ajustement pour le texte
        )
        self.right_eye_button.setToolTip("Ouvrir l'application principale")
        self.right_eye_button.clicked.connect(self.open_main_app)

        self.left_eye_button = QPushButton("Œil G", self)
        self.left_eye_button.setGeometry(350, 150, 50, 50) # Symétrie
        self.left_eye_button.setStyleSheet(
            button_style_base.format(radius=eye_radius, bg_color="#4A90E2", hover_color="#62A3F0", pressed_color="#3678C2") +
            "QPushButton { padding-bottom: 5px; }"
        )
        self.left_eye_button.setToolTip("Ouvrir application simulée (Œil Gauche)")
        self.left_eye_button.clicked.connect(lambda: self.show_simulated_app_message("Œil Gauche"))

        # --- Nez (deux narines comme boutons) ---
        nose_radius = "15"
        self.left_nostril_button = QPushButton("N.G", self)
        self.left_nostril_button.setGeometry(200, 280, 30, 40) # Narine plus verticale
        self.left_nostril_button.setStyleSheet(
            button_style_base.format(radius=nose_radius, bg_color="#E27D60", hover_color="#E8927A", pressed_color="#C96A50")
        )
        self.left_nostril_button.setToolTip("Action simulée (Narine Gauche)")
        self.left_nostril_button.clicked.connect(lambda: self.show_simulated_app_message("Narine Gauche"))

        self.right_nostril_button = QPushButton("N.D", self)
        self.right_nostril_button.setGeometry(270, 280, 30, 40) # Narine plus verticale
        self.right_nostril_button.setStyleSheet(
            button_style_base.format(radius=nose_radius, bg_color="#E27D60", hover_color="#E8927A", pressed_color="#C96A50")
        )
        self.right_nostril_button.setToolTip("Action simulée (Narine Droite)")
        self.right_nostril_button.clicked.connect(lambda: self.show_simulated_app_message("Narine Droite"))

        # --- Bouche ---
        mouth_radius = "20"
        self.mouth_button = QPushButton("Bouche", self)
        self.mouth_button.setGeometry(175, 380, 150, 40) # Bouche plus large
        self.mouth_button.setStyleSheet(
            button_style_base.format(radius=mouth_radius, bg_color="#C3423F", hover_color="#D45F5C", pressed_color="#A93A38")
        )
        self.mouth_button.setToolTip("Action simulée (Bouche)")
        self.mouth_button.clicked.connect(lambda: self.show_simulated_app_message("Bouche"))

        # --- Oreilles ---
        ear_radius = "20" # Oreilles semi-circulaires
        self.left_ear_button = QPushButton("Oreille G", self)
        self.left_ear_button.setGeometry(30, 200, 40, 80) # Oreille verticale
        self.left_ear_button.setStyleSheet(
            button_style_base.format(radius=ear_radius, bg_color="#A0522D", hover_color="#B86A40", pressed_color="#8A4725") +
            "QPushButton { border-top-right-radius: 0px; border-bottom-right-radius: 0px; }" # Côté plat vers le visage
        )
        self.left_ear_button.setToolTip("Action simulée (Oreille Gauche)")
        self.left_ear_button.clicked.connect(lambda: self.show_simulated_app_message("Oreille Gauche"))

        self.right_ear_button = QPushButton("Oreille D", self)
        self.right_ear_button.setGeometry(430, 200, 40, 80) # Oreille verticale
        self.right_ear_button.setStyleSheet(
            button_style_base.format(radius=ear_radius, bg_color="#A0522D", hover_color="#B86A40", pressed_color="#8A4725") +
            "QPushButton { border-top-left-radius: 0px; border-bottom-left-radius: 0px; }" # Côté plat vers le visage
        )
        self.right_ear_button.setToolTip("Action simulée (Oreille Droite)")
        self.right_ear_button.clicked.connect(lambda: self.show_simulated_app_message("Oreille Droite"))

        # Optionnel: Ajout de lunettes (simples lignes pour l'instant)
        # Pour des lunettes plus élaborées, QPainter serait mieux.
        # Ceci est un QLabel pour simuler la monture.
        self.glasses_label = QLabel(self)
        self.glasses_label.setGeometry(90, 140, 320, 70) # Englobe les yeux
        self.glasses_label.setStyleSheet("""
            QLabel {{
                border: 3px solid black;
                border-radius: 30px; /* Cadre arrondi */
                /* background-color: rgba(200, 200, 200, 0.3); Verres semi-transparents */
            }}
        """)
        # Barre centrale des lunettes
        self.glasses_bridge = QLabel(self)
        self.glasses_bridge.setGeometry(235, 160, 30, 10) # Entre les yeux
        self.glasses_bridge.setStyleSheet("QLabel { background-color: black; }")


    def open_main_app(self):
        try:
            # Assurez-vous que 'main.py' est dans le répertoire parent (racine du projet)
            # et que python3 est dans le PATH ou spécifiez le chemin complet vers l'interpréteur
            subprocess.Popen(["python3", "../main.py"]) # Modifié pour remonter d'un niveau
            QMessageBox.information(self, "Lancement", "Tentative de lancement de l'application principale...")
        except FileNotFoundError:
            QMessageBox.warning(self, "Erreur", "'main.py' non trouvé ou 'python3' n'est pas dans le PATH.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

    def show_simulated_app_message(self, part_name):
        QMessageBox.information(self, f"Simulation {part_name}", f"L'action pour '{part_name}' a été déclenchée !")

# Le code pour exécuter cette fenêtre sera dans visage/main.py
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     face_window = FaceWindow()
#     face_window.show()
#     sys.exit(app.exec_())
