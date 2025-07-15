# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread, pyqtSignal

class Thread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.function(*self.args, **self.kwargs)
        self.finished.emit(result)
