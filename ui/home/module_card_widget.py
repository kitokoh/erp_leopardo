# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtGui import QIcon, QMouseEvent, QFontMetrics, QColor
from PyQt5.QtCore import QFile

class ModuleCardWidget(QWidget):
    """
    Widget personnalisé pour afficher une "carte" de module sur la page d'accueil.
    Affiche une icône, un titre, et potentiellement des statistiques ou informations clés.
    La carte entière est cliquable.
    """
    cardClicked = pyqtSignal()

    def __init__(self, module_id: str, title: str, icon_path: str,
                 tooltip: str, navigation_slot: callable,
                 accent_color_key: str = None, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("moduleCard") # Pour le styling QSS global de la carte

        self.module_id = module_id
        self.card_title = title
        self.card_icon_path = icon_path
        self.card_tooltip = tooltip
        self.navigation_slot = navigation_slot # Le slot à appeler lors du clic
        self.accent_color_key = accent_color_key # Pour QSS : self.setProperty("moduleType", accent_color_key)

        if self.accent_color_key:
            self.setProperty("moduleType", self.accent_color_key)

        self._init_ui()
        self.setToolTip(self.card_tooltip)
        self.setCursor(Qt.PointingHandCursor) # Indiquer que c'est cliquable
        self._apply_shadow()

    def _apply_shadow(self):
        """Applique un effet d'ombre portée à la carte."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

    def _init_ui(self):
        """Initialise l'interface utilisateur de la carte."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15) # Padding interne global
        self.main_layout.setSpacing(10) # Espacement entre les sections (icône, titre, stats)

        # Section Icône
        self.icon_label = QLabel(self)
        self.icon_label.setObjectName("moduleIconLabel")
        if self.card_icon_path and QFile.exists(self.card_icon_path): # Check if icon exists before setting
            self.icon_label.setPixmap(QIcon(self.card_icon_path).pixmap(QSize(48, 48))) # Taille d'icône augmentée
        else:
            # Fallback or placeholder if icon not found
            self.icon_label.setPixmap(QIcon(":/icons/placeholder_icon.svg").pixmap(QSize(48,48)))
            logging.warning(f"ModuleCardWidget: Icon not found at {self.card_icon_path} for module {self.module_id}. Using placeholder.")

        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Prend la largeur, hauteur fixe
        self.icon_label.setFixedHeight(50) # Hauteur pour l'icône
        self.main_layout.addWidget(self.icon_label)

        # Section Titre
        self.title_label = QLabel(self.card_title)
        self.title_label.setObjectName("moduleTitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True) # Permettre le retour à la ligne pour les titres longs
        self.main_layout.addWidget(self.title_label)

        self.main_layout.addStretch(1) # Pousse les stats vers le bas si elles sont présentes

        # Section Statistiques (placeholders)
        self.stats_container = QWidget() # Conteneur pour les statistiques
        self.stats_container.setObjectName("statsContainer")
        self.stats_layout = QHBoxLayout(self.stats_container) # QHBoxLayout pour 2 stats côte à côte
        self.stats_layout.setContentsMargins(0, 5, 0, 0) # Un peu d'espace au-dessus des stats
        self.stats_layout.setSpacing(8)

        # Stat 1
        self.stat1_widget = QWidget()
        self.stat1_layout = QVBoxLayout(self.stat1_widget)
        self.stat1_layout.setContentsMargins(0,0,0,0)
        self.stat1_layout.setSpacing(0)
        self.stat1_value_label = QLabel("") # Sera rempli par update_stats
        self.stat1_value_label.setObjectName("statValueLabel")
        self.stat1_value_label.setAlignment(Qt.AlignCenter)
        self.stat1_text_label = QLabel("") # Sera rempli par update_stats
        self.stat1_text_label.setObjectName("statTextLabel")
        self.stat1_text_label.setAlignment(Qt.AlignCenter)
        self.stat1_layout.addWidget(self.stat1_value_label)
        self.stat1_layout.addWidget(self.stat1_text_label)
        self.stats_layout.addWidget(self.stat1_widget)
        self.stat1_widget.setVisible(False) # Caché par défaut

        # Stat 2 (optionnel)
        self.stat2_widget = QWidget()
        self.stat2_layout = QVBoxLayout(self.stat2_widget)
        self.stat2_layout.setContentsMargins(0,0,0,0)
        self.stat2_layout.setSpacing(0)
        self.stat2_value_label = QLabel("") # Sera rempli par update_stats
        self.stat2_value_label.setObjectName("statValueLabel") # Peut partager le même style
        self.stat2_value_label.setAlignment(Qt.AlignCenter)
        self.stat2_text_label = QLabel("") # Sera rempli par update_stats
        self.stat2_text_label.setObjectName("statTextLabel") # Peut partager le même style
        self.stat2_layout.addWidget(self.stat2_value_label)
        self.stat2_layout.addWidget(self.stat2_text_label)
        self.stats_layout.addWidget(self.stat2_widget)
        self.stat2_widget.setVisible(False) # Caché par défaut

        self.main_layout.addWidget(self.stats_container)
        self.stats_container.setVisible(False) # Le conteneur de stats est caché si pas de stats

        self.setLayout(self.main_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # Prend la largeur, hauteur préférée
        self.setMinimumHeight(160) # Hauteur minimale pour la carte

    def update_stats(self, stats_data: list[dict]):
        """
        Met à jour les labels de statistiques.
        stats_data: une liste de dictionnaires, ex: [{'value': '15', 'label': 'Projets Actifs', 'color': '#optional_color'}, ...]
                    Au maximum 2 statistiques seront affichées.
        """
        # Réinitialiser et cacher les stats par défaut
        self.stat1_value_label.setText("")
        self.stat1_text_label.setText("")
        self.stat1_widget.setVisible(False)

        self.stat2_value_label.setText("")
        self.stat2_text_label.setText("")
        self.stat2_widget.setVisible(False)

        self.stats_container.setVisible(False) # Cacher le conteneur si pas de stats

        if not stats_data:
            return

        has_visible_stats = False

        # Stat 1
        if len(stats_data) > 0 and stats_data[0]:
            stat1 = stats_data[0]
            self.stat1_value_label.setText(str(stat1.get('value', 'N/A'))) # Afficher N/A si valeur manquante
            self.stat1_text_label.setText(stat1.get('label', ''))

            # Appliquer la couleur si fournie
            stat1_color = stat1.get('color')
            if stat1_color:
                self.stat1_value_label.setStyleSheet(f"color: {stat1_color};")
            else:
                # Réinitialiser au style par défaut potentiellement défini dans QSS global ou par le parent
                self.stat1_value_label.setStyleSheet("")

            self.stat1_widget.setVisible(True)
            has_visible_stats = True

        # Stat 2
        if len(stats_data) > 1 and stats_data[1]:
            stat2 = stats_data[1]
            self.stat2_value_label.setText(str(stat2.get('value', 'N/A'))) # Afficher N/A si valeur manquante
            self.stat2_text_label.setText(stat2.get('label', ''))

            stat2_color = stat2.get('color')
            if stat2_color:
                self.stat2_value_label.setStyleSheet(f"color: {stat2_color};")
            else:
                self.stat2_value_label.setStyleSheet("")

            self.stat2_widget.setVisible(True)
            has_visible_stats = True

        if has_visible_stats:
            self.stats_container.setVisible(True)


    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.cardClicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event: QEvent):
        """Effet de survol à l'entrée de la souris."""
        if not hasattr(self, 'zoom_animation'):
            self.zoom_animation = QPropertyAnimation(self, b"geometry")
            self.zoom_animation.setDuration(150)
            self.zoom_animation.setEasingCurve(QEasingCurve.InOutQuad)

        start_rect = self.geometry()
        end_rect = start_rect.adjusted(-5, -5, 5, 5)

        self.zoom_animation.setStartValue(start_rect)
        self.zoom_animation.setEndValue(end_rect)
        self.zoom_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        """Effet de survol à la sortie de la souris."""
        if hasattr(self, 'zoom_animation'):
            start_rect = self.geometry()
            end_rect = start_rect.adjusted(5, 5, -5, -5)

            self.zoom_animation.setStartValue(start_rect)
            self.zoom_animation.setEndValue(end_rect)
            self.zoom_animation.start()
        super().leaveEvent(event)

# Nécessaire pour les tests si exécuté directement
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import os # Pour le logging
    logging.basicConfig(level=logging.DEBUG) # Pour voir les warnings d'icônes

    # Ajouter le chemin racine du projet pour que les imports relatifs fonctionnent
    # Ceci est spécifique au test direct de ce fichier.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Essayer d'importer icons_rc. Si ce n'est pas là où il faut, il y aura une erreur.
    # Pour un test direct, il faudrait que icons_rc.py soit accessible.
    try:
        import icons_rc
    except ImportError:
        logging.warning("icons_rc.py not found or not in PYTHONPATH. Icons from QRC might not load.")


    app = QApplication(sys.argv)

    # Fonction de navigation factice pour le test
    def test_nav_slot():
        print("ModuleCardWidget clicked! Navigation slot called.")

    # Créer une fenêtre pour contenir la carte
    test_window = QWidget()
    test_layout = QVBoxLayout(test_window)

    # Créer une instance de ModuleCardWidget pour le test
    # Utiliser un chemin d'icône valide depuis le qrc ou un fichier système pour tester l'affichage
    # Si icons_rc.py est bien généré et importé, ":/icons/home.svg" devrait fonctionner.
    # Sinon, utiliser un chemin absolu vers un SVG pour tester.
    icon_test_path = ":/icons/home.svg" # Assurez-vous que cette ressource existe et est compilée

    card1 = ModuleCardWidget(
        module_id="home_test",
        title="Accueil Principal",
        icon_path=icon_test_path,
        tooltip="Accéder à la page d'accueil principale",
        navigation_slot=test_nav_slot,
        accent_color_key="homeAccent" # Exemple de clé pour QSS
    )

    card2 = ModuleCardWidget(
        module_id="projects_test",
        title="Gestion de Projets Complexes et Longs", # Test avec titre long
        icon_path=":/icons/dashboard.svg", # Autre icône
        tooltip="Gérer tous les projets de l'entreprise",
        navigation_slot=test_nav_slot,
        accent_color_key="projectAccent"
    )
    # card2.update_stats([
    #     {'value': '25', 'label': 'Actifs'},
    #     {'value': '3', 'label': 'En Retard'}
    # ])


    test_layout.addWidget(card1)
    test_layout.addWidget(card2)
    test_window.setWindowTitle("Test ModuleCardWidget")
    test_window.resize(300, 400) # Donner assez de place pour voir les deux cartes
    test_window.show()

    sys.exit(app.exec_())

# Nécéssaire pour que self.tr fonctionne dans les tooltips lors d'un test direct
# Dans l'application réelle, DocumentManager ou QApplication s'en charge.
def tr(text):
    return QApplication.translate("ModuleCardWidget", text)
ModuleCardWidget.tr = tr
