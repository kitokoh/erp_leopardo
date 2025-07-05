# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

class QuickStatsWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("QuickStatsWidget")
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        title_label = QLabel(self.tr("Aperçu Rapide"))
        title_label.setObjectName("quickStatsTitleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(title_label)

        # Placeholder stats - these would ideally come from a data source
        stats_data = [
            {"label": self.tr("Clients Actifs:"), "value": "157"},
            {"label": self.tr("Projets en Cours:"), "value": "23"},
            {"label": self.tr("Tâches Ouvertes:"), "value": "8"},
            {"label": self.tr("Nouveaux Documents (Mois):"), "value": "78"}
        ]

        for stat in stats_data:
            stat_label = QLabel(f"{stat['label']} {stat['value']}")
            stat_label.setObjectName("quickStatItemLabel")
            stat_label.setWordWrap(True)
            self.main_layout.addWidget(stat_label)

        self.main_layout.addStretch(1) # Push content to the top

        self.setLayout(self.main_layout)

    def update_stats(self, new_stats_data):
        """
        Updates the displayed statistics.
        new_stats_data should be a list of dicts, e.g.,
        [{"label": "Nouveaux Clients:", "value": "5"}]
        """
        # Clear old stats first, except title
        while self.main_layout.count() > 1: # Keep title_label
            item = self.main_layout.itemAt(1) # Get item below title
            if item.widget():
                item.widget().deleteLater()
            else:
                self.main_layout.removeItem(item) # If it's a spacer or something

        # Remove stretch if it exists
        if self.main_layout.itemAt(self.main_layout.count()-1).spacerItem():
             self.main_layout.takeAt(self.main_layout.count()-1)


        for stat in new_stats_data:
            stat_label = QLabel(f"{stat['label']} {stat['value']}")
            stat_label.setObjectName("quickStatItemLabel")
            stat_label.setWordWrap(True)
            self.main_layout.addWidget(stat_label)

        self.main_layout.addStretch(1)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Example Usage
    main_window = QWidget()
    layout = QVBoxLayout(main_window)

    stats_widget = QuickStatsWidget()
    stats_widget.setStyleSheet("""
        QFrame#QuickStatsWidget {
            background-color: #F8F9FA;
            border: 1px solid #DEE2E6;
            border-radius: 6px;
        }
        QLabel#quickStatsTitleLabel {
            font-size: 16px;
            font-weight: bold;
            color: #0056B3; /* Dark Blue */
            padding-bottom: 5px;
            border-bottom: 1px solid #E9ECEF; /* Light separator */
        }
        QLabel#quickStatItemLabel {
            font-size: 13px;
            color: #495057; /* Dark Gray */
            padding-top: 3px;
        }
    """)
    layout.addWidget(stats_widget)

    # Example of updating stats
    # def update_example():
    #     new_data = [
    #         {"label": "Projets Terminés:", "value": "120"},
    #         {"label": "Tickets Support:", "value": "3"}
    #     ]
    #     stats_widget.update_stats(new_data)
    # from PyQt5.QtCore import QTimer
    # QTimer.singleShot(3000, update_example)

    main_window.setWindowTitle("QuickStatsWidget Test")
    main_window.resize(250, 300)
    main_window.show()
    sys.exit(app.exec_())
