# gui/widgets/notification_panel.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QIcon

class NotificationPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("notificationPanel")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("notificationScrollArea")

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("notificationScrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(5)

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setDuration(300)

        self.hide()

    def add_notification(self, title, message, icon_path=None):
        notification_widget = QFrame()
        notification_widget.setObjectName("notificationItem")
        layout = QVBoxLayout(notification_widget)

        title_label = QLabel(title)
        title_label.setObjectName("notificationTitle")
        layout.addWidget(title_label)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setObjectName("notificationMessage")
        layout.addWidget(message_label)

        self.scroll_layout.insertWidget(0, notification_widget)

    def toggle_panel(self):
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel()

    def show_panel(self):
        if not self.parent():
            return

        parent_pos = self.parent().mapToGlobal(self.parent().rect().bottomRight())
        self.setGeometry(parent_pos.x() - 300, parent_pos.y(), 300, 400)

        start_rect = QRect(self.x(), self.y(), self.width(), 0)
        end_rect = self.geometry()

        self.setGeometry(start_rect)
        self.show()

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def hide_panel(self):
        start_rect = self.geometry()
        end_rect = QRect(self.x(), self.y(), self.width(), 0)

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.finished.connect(self.hide)
        self.animation.start()
