# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, pyqtSignal, QProcess

class ProcessManager(QObject):
    _instance = None
    process_finished = pyqtSignal(str)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            # QObject.__init__(cls._instance) # This is not correct
            cls._instance.processes = {}
        return cls._instance

    def __init__(self):
        # This will be called every time ProcessManager() is invoked
        # but the actual object is the same. We need to ensure QObject init is called only once.
        if not hasattr(self, '_initialized'):
            super().__init__()
            self.processes = {}
            self._initialized = True

    def start(self, app_id, command):
        if self.is_running(app_id):
            print(f"{app_id} is already running.")
            return

        process = QProcess()
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.finished.connect(lambda: self.on_process_finished(app_id))

        # Correctly unpack command for start
        program = command[0]
        arguments = command[1:]
        process.start(program, arguments)

        self.processes[app_id] = process
        print(f"Started {app_id}")

    def on_process_finished(self, app_id):
        if app_id in self.processes:
            print(f"Process for {app_id} finished.")
            del self.processes[app_id]
            self.process_finished.emit(app_id)

    def stop(self, app_id):
        if not self.is_running(app_id):
            print(f"{app_id} is not running.")
            return

        process = self.processes[app_id]
        process.terminate()
        # No need to wait, the finished signal will handle the cleanup

    def is_running(self, app_id):
        return app_id in self.processes and self.processes[app_id].state() != QProcess.NotRunning

    def stop_all(self):
        for app_id in list(self.processes.keys()):
            self.stop(app_id)

process_manager = ProcessManager()
