from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
import logging # Added for consistent logging

from datetime import datetime, timedelta

from app.db.cruds.misc.status_settings_crud import get_all_status_settings
from app.db.cruds.projects.projects_crud import get_all_projects
from app.db.cruds.projects.tasks_crud import get_tasks_by_project_id


class CustomNotificationBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("customNotificationBanner")
        self.setFixedHeight(50)
        self.setFixedWidth(350)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.icon_label = QLabel("ℹ️")
        self.icon_label.setObjectName("notificationIconLabel")
        self.icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.message_label = QLabel("Notification message will appear here.")
        self.message_label.setObjectName("notificationMessageLabel")
        self.message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.message_label.setWordWrap(True)

        self.close_button = QPushButton("X")
        self.close_button.setObjectName("notificationCloseButton")
        self.close_button.setToolTip("Close")
        self.close_button.setFixedSize(25, 25)
        self.close_button.clicked.connect(self.hide)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.message_label)
        layout.addStretch()
        layout.addWidget(self.close_button)
        self.hide()

    def set_message(self, title, message):
        full_message = f"<b>{title}</b><br>{message}"
        self.message_label.setText(full_message)
        if "error" in title.lower() or "alert" in title.lower():
            self.icon_label.setText("⚠️")
        elif "success" in title.lower():
            self.icon_label.setText("✅")
        elif "urgent" in title.lower() or "reminder" in title.lower():
            self.icon_label.setText("🔔")
        else:
            self.icon_label.setText("ℹ️")


class NotificationManager:
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.timer = QTimer(parent_window)
        self.notification_banner = None  # Initialize to None

    def _ensure_banner_exists(self):
        """Lazily creates the notification banner if it doesn't exist."""
        if self.notification_banner is None:
            app_instance = QApplication.instance()
            if not app_instance:
                logging.error("ProjectManagement NotifMgr: QApplication not available for banner creation.")
                return False
            if not self.parent_window:
                logging.error("ProjectManagement NotifMgr: Parent window not set, cannot create banner.")
                return False

            try:
                self.notification_banner = CustomNotificationBanner(self.parent_window)
                self.notification_banner.raise_()
                # Initial positioning logic (can be error prone if parent not fully sized)
                # It's safer to position when showing.
                logging.info("ProjectManagement CustomNotificationBanner created.")
            except Exception as e_create:
                logging.error(f"ProjectManagement NotifMgr: Error creating CustomNotificationBanner: {e_create}", exc_info=True)
                return False
        return True

    def setup_timer(self, interval_ms=300000):
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(interval_ms)
        logging.info(f"ProjectManagement Notification timer started with interval: {interval_ms}ms")

    def check_notifications(self):
        logging.debug(f"Checking project notifications at {datetime.now()}")
        notifications_found = []
        all_project_statuses = {s['status_id']: s for s in get_all_status_settings(type_filter='Project')}
        all_task_statuses = {s['status_id']: s for s in get_all_status_settings(type_filter='Task')}

        try:
            all_projects_list = get_all_projects()
            if all_projects_list is None: all_projects_list = []
            today_str = datetime.now().strftime('%Y-%m-%d')
            three_days_later = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')

            for p in all_projects_list:
                project_status_id = p.get('status_id')
                project_status_info = all_project_statuses.get(project_status_id, {})
                is_completed_or_archived = project_status_info.get('is_completion_status', False) or \
                                           project_status_info.get('is_archival_status', False)

                if p.get('priority') == 2 and not is_completed_or_archived:
                    notifications_found.append({"title": "Urgent Project Reminder", "message": f"Project '{p.get('project_name')}' (ID: {p.get('project_id')}) is high priority."})
                deadline_str = p.get('deadline_date')
                if deadline_str and deadline_str < today_str and not is_completed_or_archived:
                    notifications_found.append({"title": "Overdue Project Alert", "message": f"Project '{p.get('project_name')}' (ID: {p.get('project_id')}) was due on {deadline_str}."})

                tasks_for_project_list = get_tasks_by_project_id(p.get('project_id'))
                if tasks_for_project_list is None: tasks_for_project_list = []
                for t in tasks_for_project_list:
                    task_status_id = t.get('status_id')
                    task_status_info = all_task_statuses.get(task_status_id, {})
                    is_task_completed = task_status_info.get('is_completion_status', False)
                    task_deadline_str = t.get('due_date')
                    if t.get('priority') == 2 and not is_task_completed and \
                       task_deadline_str and today_str <= task_deadline_str <= three_days_later:
                        notifications_found.append({"title": "High Priority Task Nearing Deadline", "message": f"Task '{t.get('task_name')}' for project '{p.get('project_name')}' (Deadline: {task_deadline_str}) is high priority."})
                    if task_deadline_str and task_deadline_str < today_str and not is_task_completed:
                         notifications_found.append({"title": "Overdue Task Alert", "message": f"Task '{t.get('task_name')}' for project '{p.get('project_name')}' was due on {task_deadline_str}."})

        except Exception as e:
            logging.error(f"Error checking project notifications: {e}", exc_info=True)
            return

        if notifications_found:
            logging.info(f"Found {len(notifications_found)} project notifications.")
            for notification in notifications_found:
                self.show_notification(notification["title"], notification["message"])
        else:
            logging.debug("No new project notifications.")

    def show_notification(self, title, message, project_id=None, task_id=None):
        QTimer.singleShot(0, lambda t=title, m=message: self._deferred_show_notification(t, m))

    def _deferred_show_notification(self, title, message):
        if not self._ensure_banner_exists():
            logging.error("ProjectManagement NotifMgr: Banner does not exist or couldn't be created, cannot show notification.")
            return

        self.notification_banner.set_message(title, message)

        if self.parent_window and self.notification_banner:
            try:
                parent_width = self.parent_window.width()
                banner_width = self.notification_banner.width()
                if banner_width == 0:
                    banner_width = self.notification_banner.sizeHint().width()
                    if banner_width == 0:
                         banner_width = self.notification_banner.minimumWidth() if self.notification_banner.minimumWidth() > 0 else 350

                x = parent_width - banner_width - 10
                y = 10
                self.notification_banner.move(x, y)
                self.notification_banner.show()
                self.notification_banner.raise_()
                QTimer.singleShot(7000, self.notification_banner.hide)
                logging.info(f"Showing project_management custom notification (deferred): {title} - {message}")
            except Exception as e_show:
                logging.error(f"Error showing/positioning project management banner: {e_show}", exc_info=True)
        else:
            logging.warning("Cannot show project management notification, parent_window or banner is None after ensure.")

    def check_notification(self, title, message): # Unused by current logic but was in original
        if not self.notification_banner:
            return False
        return self.notification_banner.message_label.text() == f"<b>{title}</b><br>{message}"
