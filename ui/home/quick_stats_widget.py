# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSizePolicy, QProgressBar
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

class QuickStatsWidget(QFrame):
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("QuickStatsWidget")
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        self.title_label = QLabel(self.tr("Aperçu Rapide"))
        self.title_label.setObjectName("quickStatsTitleLabel")
        header_layout.addWidget(self.title_label, 1)

        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("quickStatsRefreshButton")
        refresh_icon = QIcon.fromTheme("view-refresh", QIcon(":/icons/refresh-cw.svg"))
        self.refresh_button.setIcon(refresh_icon)
        self.refresh_button.setToolTip(self.tr("Rafraîchir les statistiques"))
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.refresh_button.setFixedSize(24, 24)
        self.refresh_button.setIconSize(QSize(16, 16))
        header_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(header_layout)

        self.stats_items_layout = QVBoxLayout()
        self.stats_items_layout.setSpacing(10) # Augmentation de l'espacement
        self.main_layout.addLayout(self.stats_items_layout)

        self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)
        self.update_stats([])

    def update_stats(self, new_stats_data):
        while self.stats_items_layout.count() > 0:
            item = self.stats_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not new_stats_data:
            placeholder_label = QLabel(self.tr("Aucune statistique à afficher."))
            placeholder_label.setObjectName("quickStatItemPlaceholderLabel")
            self.stats_items_layout.addWidget(placeholder_label)
            return

        # Définir une valeur maximale pour la normalisation des barres
        max_value = 0
        for stat in new_stats_data:
            try:
                # La valeur peut être un string, il faut la convertir
                value = int(stat['value'])
                if value > max_value:
                    max_value = value
            except (ValueError, TypeError):
                continue

        # Pour éviter une division par zéro et avoir une barre vide pour une valeur de 0
        if max_value == 0:
            max_value = 100

        for stat in new_stats_data:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0,0,0,0)
            stat_layout.setSpacing(2)

            label_layout = QHBoxLayout()
            label = QLabel(stat['label'])
            label.setObjectName("quickStatItemLabel")
            value_label = QLabel(stat['value'])
            value_label.setObjectName("quickStatValueLabel")
            label_layout.addWidget(label)
            label_layout.addStretch()
            label_layout.addWidget(value_label)

            progress_bar = QProgressBar()
            progress_bar.setObjectName("quickStatProgressBar")
            progress_bar.setTextVisible(False)
            try:
                value = int(stat['value'])
                progress_bar.setValue(int((value / max_value) * 100))
            except (ValueError, TypeError):
                progress_bar.setValue(0)

            stat_layout.addLayout(label_layout)
            stat_layout.addWidget(progress_bar)
            self.stats_items_layout.addWidget(stat_widget)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    stats_widget = QuickStatsWidget()
    stats_widget.setStyleSheet("""
        QFrame#QuickStatsWidget { background-color: #F8F9FA; border: 1px solid #DEE2E6; border-radius: 6px; }
        QLabel#quickStatsTitleLabel { font-size: 16px; font-weight: bold; color: #0056B3; padding-bottom: 5px; border-bottom: 1px solid #E9ECEF; }
        QLabel#quickStatItemLabel { font-size: 13px; color: #495057; }
        QLabel#quickStatValueLabel { font-size: 13px; font-weight: bold; color: #333; }
        QProgressBar#quickStatProgressBar { height: 8px; border: 1px solid #ccc; border-radius: 4px; background-color: #e9ecef; }
        QProgressBar#quickStatProgressBar::chunk { background-color: #007BFF; border-radius: 3px; }
    """)
    layout.addWidget(stats_widget)

    # Données d'exemple pour le test
    example_data = [
        {"label": "Clients Actifs:", "value": "150"},
        {"label": "Projets en Cours:", "value": "20"},
        {"label": "Tâches Ouvertes:", "value": "12"},
    ]
    stats_widget.update_stats(example_data)

    main_window.setWindowTitle("QuickStatsWidget Test")
    main_window.resize(250, 300)
    main_window.show()
    sys.exit(app.exec_())
