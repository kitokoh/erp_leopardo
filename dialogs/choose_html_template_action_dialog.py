# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QCheckBox, QDialogButtonBox, QSizePolicy, QWidget, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon

# Constantes pour les actions (pourraient être dans un fichier de constantes partagé)
ACTION_COPY_RAW = "copy_raw"
ACTION_GENERATE_DIRECT = "generate_direct"

class ChooseHtmlTemplateActionDialog(QDialog):
    def __init__(self, template_name: str, client_name: str, parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.client_name = client_name
        self._chosen_action = None
        self._dont_ask_again = False

        self.setWindowTitle(self.tr("Options d'Ajout de Modèle HTML"))
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Message principal
        icon_label = QLabel()
        # Vous pouvez utiliser une icône standard si disponible, par exemple :
        # icon = self.style().standardIcon(QStyle.SP_MessageBoxQuestion)
        # icon_label.setPixmap(icon.pixmap(32, 32)) # Ajuster la taille
        # Pour l'instant, pas d'icône pour simplifier

        message_text = self.tr(
            "Comment souhaitez-vous ajouter le modèle HTML '{0}' pour le client '{1}' ?"
        ).format(self.template_name, self.client_name)
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)

        header_layout = QHBoxLayout()
        # header_layout.addWidget(icon_label) # Si icône utilisée
        header_layout.addWidget(message_label)
        main_layout.addLayout(header_layout)

        # Groupe de boutons radio pour les options
        self.options_group = QButtonGroup(self)

        self.radio_copy_raw = QRadioButton(self.tr("Copier le modèle HTML brut dans le dossier client"))
        copy_raw_help = self.tr("Ceci ajoutera une version modifiable du modèle aux documents du client. Vous pourrez ensuite générer la version finale (PDF/HTML rempli) à partir de cette copie.")
        self.radio_copy_raw.setToolTip(copy_raw_help)
        # QLabel pour l'aide sous le radio (plus visible que tooltip)
        copy_raw_help_label = QLabel(f"<small>{copy_raw_help}</small>")
        copy_raw_help_label.setWordWrap(True)
        copy_raw_layout = QVBoxLayout()
        copy_raw_layout.setContentsMargins(20, 0, 0, 0) # Indentation pour le texte d'aide
        copy_raw_layout.addWidget(self.radio_copy_raw)
        copy_raw_layout.addWidget(copy_raw_help_label)
        main_layout.addLayout(copy_raw_layout)
        self.options_group.addButton(self.radio_copy_raw)


        self.radio_generate_direct = QRadioButton(self.tr("Générer directement le document final (PDF/HTML rempli)"))
        generate_direct_help = self.tr("Ceci utilisera les données actuelles du client pour remplir le modèle et produire immédiatement le document final.")
        self.radio_generate_direct.setToolTip(generate_direct_help)
        generate_direct_help_label = QLabel(f"<small>{generate_direct_help}</small>")
        generate_direct_help_label.setWordWrap(True)
        generate_direct_layout = QVBoxLayout()
        generate_direct_layout.setContentsMargins(20, 0, 0, 0)
        generate_direct_layout.addWidget(self.radio_generate_direct)
        generate_direct_layout.addWidget(generate_direct_help_label)
        main_layout.addLayout(generate_direct_layout)
        self.options_group.addButton(self.radio_generate_direct)

        main_layout.addSpacing(10)

        # Case à cocher pour la persistance
        self.checkbox_memoriser_choix = QCheckBox(self.tr("Se souvenir de mon choix et ne plus me demander"))
        main_layout.addWidget(self.checkbox_memoriser_choix)

        # Boutons d'action
        self.button_box = QDialogButtonBox()
        self.ok_button = self.button_box.addButton(QDialogButtonBox.Ok)
        self.ok_button.setText(self.tr("OK"))
        self.cancel_button = self.button_box.addButton(QDialogButtonBox.Cancel)
        self.cancel_button.setText(self.tr("Annuler"))

        self.ok_button.setEnabled(False) # Désactivé jusqu'à ce qu'un choix soit fait

        main_layout.addWidget(self.button_box)

        # Connexions
        self.options_group.buttonClicked.connect(self._on_option_selected)
        self.button_box.accepted.connect(self.accept_dialog)
        self.button_box.rejected.connect(self.reject)

        self.setMinimumWidth(500) # Ajuster selon le contenu

    @pyqtSlot()
    def _on_option_selected(self):
        self.ok_button.setEnabled(True)

    def set_default_choice(self, action: str):
        if action == ACTION_COPY_RAW:
            self.radio_copy_raw.setChecked(True)
        elif action == ACTION_GENERATE_DIRECT:
            self.radio_generate_direct.setChecked(True)
        else: # Par défaut, ou si action inconnue, choisir la génération directe
            self.radio_generate_direct.setChecked(True)
        self._on_option_selected() # Pour s'assurer que le bouton OK est activé

    def set_initial_dont_ask_again(self, checked: bool):
        self.checkbox_memoriser_choix.setChecked(checked)

    def accept_dialog(self):
        if self.radio_copy_raw.isChecked():
            self._chosen_action = ACTION_COPY_RAW
        elif self.radio_generate_direct.isChecked():
            self._chosen_action = ACTION_GENERATE_DIRECT
        else:
            # Ne devrait pas arriver si le bouton OK est géré correctement
            self.reject() # Ou afficher un message
            return

        self._dont_ask_again = self.checkbox_memoriser_choix.isChecked()
        self.accept()

    def get_chosen_action(self) -> str | None:
        return self._chosen_action

    def get_dont_ask_again_preference(self) -> bool:
        return self._dont_ask_again

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    # Pour le test, simuler les constantes si elles ne sont pas importables directement
    # ACTION_COPY_RAW = "copy_raw"
    # ACTION_GENERATE_DIRECT = "generate_direct"

    app = QApplication(sys.argv)
    dialog = ChooseHtmlTemplateActionDialog("Facture Proforma XYZ", "Client Test SARL")
    dialog.set_default_choice(ACTION_GENERATE_DIRECT) # Test du préréglage
    if dialog.exec_() == QDialog.Accepted:
        print(f"Action choisie: {dialog.get_chosen_action()}")
        print(f"Mémoriser choix: {dialog.get_dont_ask_again_preference()}")
    else:
        print("Dialogue annulé")
    sys.exit(app.exec_())
