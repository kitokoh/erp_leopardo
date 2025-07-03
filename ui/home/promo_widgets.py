# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal

class PromoSectionWidget(QFrame):
    """
    A widget to display a promotional message with a title and body.
    It inherits from QFrame to allow styling via QSS (e.g., border, background).
    """
    # Signal to indicate the widget was clicked, could be used to cycle content or open a link
    clicked = pyqtSignal()

    def __init__(self, title="", body="", parent=None):
        super().__init__(parent)
        self.setObjectName("PromoSectionWidget") # For QSS styling
        self._init_ui(title, body)

    def _init_ui(self, title, body):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the frame
        self.main_layout.setSpacing(5)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("promoTitleLabel") # For QSS styling
        self.title_label.setAlignment(Qt.AlignCenter | Qt.AlignTop) # Align title to top
        self.title_label.setWordWrap(True)

        self.body_label = QLabel(body)
        self.body_label.setObjectName("promoBodyLabel") # For QSS styling
        self.body_label.setAlignment(Qt.AlignJustify | Qt.AlignTop) # Align body to top, justify text
        self.body_label.setWordWrap(True)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.body_label)
        self.main_layout.addStretch(1) # Pushes content to the top if space is available

        self.setLayout(self.main_layout)

        # Set a minimum height or size policy as needed, or let the content define it.
        # self.setMinimumHeight(100)
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)


    def set_content(self, title, body):
        """Updates the title and body of the promotional message."""
        self.title_label.setText(title)
        self.body_label.setText(body)

    def mousePressEvent(self, event):
        """Emits the clicked signal when the widget is pressed."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Example Usage
    main_window = QWidget()
    main_window.setWindowTitle("PromoSectionWidget Test")
    layout = QVBoxLayout(main_window)

    promo1 = PromoSectionWidget("Test Title 1", "This is the body text for the first promotional item. It might be a bit longer to test word wrapping.")
    promo1.setStyleSheet("""
        QFrame#PromoSectionWidget {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 5px;
        }
        QLabel#promoTitleLabel {
            font-weight: bold;
            font-size: 16px;
            color: #333;
            margin-bottom: 5px;
        }
        QLabel#promoBodyLabel {
            font-size: 12px;
            color: #555;
        }
    """)

    promo2 = PromoSectionWidget("Another Tip", "Short and sweet tip here.")
    # promo2 can use the same stylesheet if applied globally or inherit from parent

    layout.addWidget(promo1)
    layout.addWidget(promo2)

    def on_promo1_clicked():
        print("Promo 1 clicked! Updating content.")
        promo1.set_content("Updated Title!", "The content has been changed dynamically.")

    promo1.clicked.connect(on_promo1_clicked)
    promo2.clicked.connect(lambda: print("Promo 2 clicked!"))


    main_window.resize(300, 400)
    main_window.show()
    sys.exit(app.exec_())
