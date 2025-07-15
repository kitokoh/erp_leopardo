# -*- coding: utf-8 -*-

class AppContext:
    def __init__(self, main_window):
        self._main_window = main_window

    def notify(self, title, message, type='INFO', duration=5000):
        self._main_window.notify(title, message, type, duration)

    def get_current_user(self):
        return self._main_window.current_user_info
