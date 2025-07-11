# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolButton, QButtonGroup, QLabel, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon
import functools # Ajouté pour partial

class SidebarNavigationWidget(QWidget):
    """
    Widget de la barre latérale de navigation principale.
    Gère l'affichage des modules sous forme de boutons (icône seule ou icône + texte)
    et permet de basculer entre un état déployé et rétracté.
    """
    moduleSelected = pyqtSignal(str)  # Émet l'ID du module sélectionné
    expansionToggled = pyqtSignal(bool) # Émet le nouvel état d'expansion (True si déployé)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarNavigationWidget")

        self.is_expanded = True  # Par défaut, la sidebar est déployée
        self.module_buttons = [] # Liste pour stocker les QToolButtons des modules
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True) # Un seul bouton peut être coché à la fois

        self._init_ui()
        self.set_expanded_state(self.is_expanded, animate=False) # Appliquer l'état initial

    def _init_ui(self):
        """Initialise l'interface utilisateur du widget."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Optionnel: Placeholder pour le logo
        # self.logo_label = QLabel("Logo App")
        # self.logo_label.setObjectName("sidebarAppLogo")
        # self.logo_label.setAlignment(Qt.AlignCenter)
        # self.logo_label.setFixedHeight(50) # Ajuster selon la taille du logo
        # self.main_layout.addWidget(self.logo_label)

        # Layout pour les boutons de module
        self.buttons_container_widget = QWidget() # Conteneur pour permettre le défilement si nécessaire plus tard
        self.buttons_layout = QVBoxLayout(self.buttons_container_widget)
        self.buttons_layout.setContentsMargins(5, 5, 5, 5) # Marges autour des boutons
        self.buttons_layout.setSpacing(4) # Espacement entre les boutons
        self.buttons_layout.setAlignment(Qt.AlignTop) # Aligner les boutons en haut

        self.main_layout.addWidget(self.buttons_container_widget, 1) # Le 1 permet au container de prendre l'espace dispo

        # Bouton de bascule (toggle) pour déployer/rétracter
        self.toggle_button = QToolButton(self)
        self.toggle_button.setObjectName("sidebarToggleButton")
        self.toggle_button.setCheckable(False)
        self.toggle_button.clicked.connect(self.toggle_expansion)
        self.toggle_button.setFixedHeight(35)
        self.toggle_button.setIconSize(QSize(18, 18))

        self.main_layout.addWidget(self.toggle_button)

        # Définir une politique de taille initiale
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def set_modules(self, modules_config: list[dict]):
        """
        Efface les boutons existants et crée de nouveaux boutons de module
        basés sur la configuration fournie.
        """
        # Effacer les anciens boutons
        for button in self.module_buttons:
            self.button_group.removeButton(button)
            button.deleteLater()
        self.module_buttons.clear()

        # Créer et ajouter les nouveaux boutons
        for config in modules_config:
            module_id = config.get('id', 'unknown_module')
            button = QToolButton(self)
            button.setObjectName(f"sidebarButton_{module_id}")
            button.setText(config.get('name', 'Sans Nom'))
            button.setToolTip(config.get('tooltip', config.get('name', '')))

            icon_path = config.get('icon_path')
            if icon_path:
                button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(22, 22)) # Taille d'icône par défaut, peut être ajustée

            button.setCheckable(True)
            button.setFixedHeight(45) # Hauteur fixe pour chaque bouton
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Stocker l'ID du module dans le bouton pour le retrouver facilement
            button.setProperty("module_id", module_id)

            button.clicked.connect(functools.partial(self._on_module_button_clicked, module_id))

            self.buttons_layout.addWidget(button)
            self.module_buttons.append(button)
            self.button_group.addButton(button)

        self._update_button_styles() # Appliquer le style initial (icône seule / texte + icône)

    def toggle_expansion(self):
        """Bascule l'état déployé/rétracté de la sidebar."""
        self.set_expanded_state(not self.is_expanded)
        self.expansionToggled.emit(self.is_expanded)

    def _update_button_styles(self):
        """Met à jour le style des boutons de module (icône seule ou icône+texte)."""
        # Cette méthode sera étoffée lorsque les boutons de module seront implémentés.
        # Pour l'instant, elle s'assure que les styles sont rafraîchis.
        style_to_set = Qt.ToolButtonTextBesideIcon if self.is_expanded else Qt.ToolButtonIconOnly
        for button in self.module_buttons:
            button.setToolButtonStyle(style_to_set)

        # Rafraîchir le style pour appliquer les changements de propriété dynamique
        self.style().unpolish(self)
        self.style().polish(self)

    def set_expanded_state(self, is_expanded: bool, animate: bool = False):
        """
        Définit l'état d'expansion de la sidebar et met à jour l'UI.
        """
        self.is_expanded = is_expanded

        # Mettre à jour la propriété dynamique pour QSS
        self.setProperty("expanded", self.is_expanded)

        if self.is_expanded:
            self.setFixedWidth(220) # Largeur typique déployée (ajuster si nécessaire)
            self.toggle_button.setIcon(QIcon(":/icons/arrow-left-circle.svg")) # Using available icon
            self.toggle_button.setToolTip(self.tr("Rétracter la barre latérale"))
        else:
            self.setFixedWidth(60)  # Largeur typique rétractée (ajuster si nécessaire)
            self.toggle_button.setIcon(QIcon(":/icons/chevron-right.svg"))
            self.toggle_button.setToolTip(self.tr("Déployer la barre latérale"))

        self._update_button_styles() # Mettre à jour le style des boutons de module

    def _on_module_button_clicked(self, module_id: str):
        """Slot interne pour gérer les clics sur les boutons de module."""
        logging.debug(f"Sidebar button clicked for module_id: {module_id}")
        self.moduleSelected.emit(module_id)
        # Le QButtonGroup s'occupe de cocher le bouton cliqué et décocher les autres.

    def set_active_module(self, module_id: str):
        """Coche le bouton correspondant au module_id actif."""
        for button in self.module_buttons:
            if button.property("module_id") == module_id:
                if not button.isChecked(): # Coche seulement si ce n'est pas déjà le cas pour éviter boucle de signaux
                    button.setChecked(True)
                break
        else:
            logging.warning(f"SidebarNavigationWidget: No button found for module_id '{module_id}' to set active.")

if __name__ == '__main__':
    # Pour des tests basiques du widget seul
    from PyQt5.QtWidgets import QApplication
    import sys
    # Assurez-vous que icons_rc est importé si vous testez avec des icônes du qrc
    # import icons_rc

    app = QApplication(sys.argv)

    # Création d'une instance de SidebarNavigationWidget
    sidebar = SidebarNavigationWidget()

    # Exemple de configuration de modules pour le test
    # test_modules = [
    #     {'id': 'home', 'name': 'Accueil', 'icon_path': ':/icons/home.svg', 'tooltip': 'Page d\'accueil'},
    #     {'id': 'documents', 'name': 'Documents', 'icon_path': ':/icons/folder.svg', 'tooltip': 'Gestion des documents'},
    #     {'id': 'settings', 'name': 'Paramètres', 'icon_path': ':/icons/settings.svg', 'tooltip': 'Configuration de l\'application'}
    # ]
    # sidebar.set_modules(test_modules) # Sera implémenté plus tard

    sidebar.setWindowTitle("Test SidebarNavigationWidget")
    sidebar.set_expanded_state(True) # Test état déployé
    # sidebar.setFixedWidth(220) # Largeur typique déployée
    sidebar.show()

    # Pour tester l'état rétracté :
    # sidebar_collapsed = SidebarNavigationWidget()
    # sidebar_collapsed.set_modules(test_modules)
    # sidebar_collapsed.setWindowTitle("Test Sidebar Collapsed")
    # sidebar_collapsed.set_expanded_state(False)
    # sidebar_collapsed.setFixedWidth(60) # Largeur typique rétractée
    # sidebar_collapsed.show()

    sys.exit(app.exec_())
