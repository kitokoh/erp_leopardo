# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

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

        # Header layout for title and refresh button
        header_layout = QHBoxLayout()

        self.title_label = QLabel(self.tr("Aperçu Rapide"))
        self.title_label.setObjectName("quickStatsTitleLabel")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.title_label, 1) # Title takes most space

        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("quickStatsRefreshButton")
        # Attempt to load a refresh icon, fallback to text "R"
        refresh_icon = QIcon.fromTheme("view-refresh", QIcon(":/icons/refresh-cw.svg")) # Common theme icon name
        if not refresh_icon.isNull():
            self.refresh_button.setIcon(refresh_icon)
        else:
            self.refresh_button.setText("R") # Fallback text
        self.refresh_button.setToolTip(self.tr("Rafraîchir les statistiques"))
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.refresh_button.setFixedSize(24, 24) # Small square button
        self.refresh_button.setIconSize(QSize(16,16))
        header_layout.addWidget(self.refresh_button)

        self.main_layout.addLayout(header_layout)

        # Container for stat items, so we can clear this part specifically
        self.stats_items_layout = QVBoxLayout()
        self.stats_items_layout.setSpacing(5) # Spacing between stat items
        self.main_layout.addLayout(self.stats_items_layout)

        self.main_layout.addStretch(1) # Push content to the top
        self.setLayout(self.main_layout)

        # Initial placeholder message if no stats loaded yet
        self.update_stats([])


    def update_stats(self, new_stats_data):
        """
        Updates the displayed statistics.
        new_stats_data should be a list of dicts, e.g.,
        [{"label": "Nouveaux Clients:", "value": "5"}]
        """
        # Clear old stat items from stats_items_layout
        while self.stats_items_layout.count() > 0:
            item = self.stats_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not new_stats_data:
            placeholder_label = QLabel(self.tr("Aucune statistique à afficher."))
            placeholder_label.setObjectName("quickStatItemPlaceholderLabel")
            placeholder_label.setAlignment(Qt.AlignCenter)
            self.stats_items_layout.addWidget(placeholder_label)
            return

        for stat in new_stats_data:
            stat_label = QLabel(f"{stat['label']} {stat['value']}")
            stat_label.setObjectName("quickStatItemLabel")
            stat_label.setWordWrap(True)
            self.stats_items_layout.addWidget(stat_label)

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
