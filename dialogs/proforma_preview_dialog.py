# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl # Added QUrl
from PyQt5.QtGui import QDesktopServices # Added QDesktopServices
import os # Added os for base_url

class ProformaPreviewDialog(QDialog):
    def __init__(self, html_content: str, base_template_path: str, parent=None):
        super().__init__(parent)
        self.html_content = html_content
        # base_url should be the directory of the template for relative paths (images, css)
        self.base_url = QUrl.fromLocalFile(os.path.dirname(base_template_path) + os.sep)

        self._setup_ui()
        self._populate_preview()

    def _setup_ui(self):
        self.setWindowTitle(self.tr("Aperçu de la Facture Proforma"))
        self.setMinimumSize(800, 600) # Taille minimale raisonnable

        layout = QVBoxLayout(self)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True) # Pour les liens externes si jamais il y en a
        # QTextBrowser peut avoir besoin d'un base_url pour les ressources relatives (images)
        # Ceci est géré via text_browser.setSource(url, QTextDocument.HtmlResource) ou en s'assurant que les chemins sont absolus/URLs dans le HTML.
        # Pour les images locales, il est préférable que le HTML utilise des URLs file:/// ou que le QTextBrowser connaisse le répertoire de base.
        layout.addWidget(self.text_browser)

        # Boutons
        self.button_box = QDialogButtonBox()
        self.generate_pdf_button = self.button_box.addButton(self.tr("Générer PDF"), QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton(self.tr("Annuler"), QDialogButtonBox.RejectRole)
        layout.addWidget(self.button_box)

        self.generate_pdf_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def _populate_preview(self):
        # Pour que QTextBrowser charge les images relatives correctement depuis le template HTML,
        # il faut lui indiquer le chemin de base.
        # Les URLs dans le HTML doivent être relatives à ce base_url ou absolues (file:/// ou http://).
        # self.html_content est déjà le HTML rendu. Si les images sont avec des chemins relatifs
        # au template original, le base_url doit être le dossier du template.
        self.text_browser.setHtml(self.html_content)
        self.text_browser.setSource(self.base_url, QTextBrowser.HtmlResource)


    # Helper pour traduction si ce dialogue est utilisé dans un contexte où self.tr() n'est pas hérité de QWidget
    def tr(self, text, disambiguation=None, n=-1):
        if hasattr(super(), 'tr'): # If parent is a QWidget with tr method
            return super().tr(text, disambiguation, n)
        # Fallback or default translation mechanism if needed
        from PyQt5.QtWidgets import QApplication # Late import
        return QApplication.translate("ProformaPreviewDialog", text, disambiguation, n)

if __name__ == '__main__':
    # Petit test pour ce dialogue
    from PyQt5.QtWidgets import QApplication
    import sys

    # Exemple de contenu HTML (avec une image locale relative pour tester base_url)
    # Supposons qu'il y ait une image "logo.png" dans un dossier "test_template_dir"
    # à côté de ce script de test, et un fichier "dummy_template.html" dans ce dossier.

    test_template_dir = "test_template_dir_preview"
    os.makedirs(test_template_dir, exist_ok=True)
    dummy_template_file = os.path.join(test_template_dir, "dummy_template.html")

    # Créer un fichier image dummy pour le test
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (100, 30), color = 'red')
        d = ImageDraw.Draw(img)
        d.text((10,10), "Logo", fill=(255,255,0))
        img.save(os.path.join(test_template_dir, "logo.png"))
        print(f"Dummy logo.png created in {test_template_dir}")
    except ImportError:
        print("Pillow (PIL) not installed, cannot create dummy image for test.")
    except Exception as e_img:
        print(f"Error creating dummy image: {e_img}")


    sample_html_content_for_test = """
    <html>
        <head><title>Test Preview</title></head>
        <body>
            <h1>Aperçu du Document</h1>
            <p>Ceci est un test de l'aperçu HTML.</p>
            <p><img src="logo.png" alt="Test Logo" /></p>
            <p>Si vous voyez le logo rouge ci-dessus, le base_url fonctionne.</p>
            <p><a href="https://www.google.com">Lien vers Google</a></p>
        </body>
    </html>
    """

    # Écrire le HTML dans le fichier dummy pour simuler un template
    with open(dummy_template_file, "w", encoding="utf-8") as f_tpl:
        f_tpl.write(sample_html_content_for_test) # Écrire le contenu avec l'image relative

    app = QApplication(sys.argv)

    # Lire le contenu HTML à partir du fichier pour le test, car c'est ce que generate_html_document ferait
    # (bien que generate_html_document retourne une chaîne déjà rendue)
    # Pour ce test, nous utilisons le contenu brut pour vérifier le chargement des ressources relatives.
    # En utilisation réelle, html_content sera déjà le HTML final.

    # Pour le test du dialogue, on a besoin du *contenu* HTML et du *chemin vers le template* original
    # pour que le dialogue puisse établir son base_url pour les ressources.

    dialog = ProformaPreviewDialog(html_content=sample_html_content_for_test,
                                   base_template_path=dummy_template_file) # Passer le chemin du template

    if dialog.exec_() == QDialog.Accepted:
        print("Action 'Générer PDF' choisie.")
    else:
        print("Dialogue d'aperçu annulé.")

    # Nettoyage
    if os.path.exists(os.path.join(test_template_dir, "logo.png")):
        os.remove(os.path.join(test_template_dir, "logo.png"))
    if os.path.exists(dummy_template_file):
        os.remove(dummy_template_file)
    if os.path.exists(test_template_dir):
        os.rmdir(test_template_dir)

    sys.exit(app.exec_())
