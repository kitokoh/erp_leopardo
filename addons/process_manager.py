# -*- coding: utf-8 -*-
import subprocess

class ProcessManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance.processes = {}
        return cls._instance

    def start(self, app_id, command):
        if self.is_running(app_id):
            print(f"{app_id} is already running.")
            return

        process = subprocess.Popen(command)
        self.processes[app_id] = process
        print(f"Started {app_id} with PID {process.pid}")

    def stop(self, app_id):
        if not self.is_running(app_id):
            print(f"{app_id} is not running.")
            return

        process = self.processes[app_id]
        process.terminate()
        process.wait()
        del self.processes[app_id]
        print(f"Stopped {app_id}")

    def is_running(self, app_id):
        return app_id in self.processes and self.processes[app_id].poll() is None

    def stop_all(self):
        for app_id in list(self.processes.keys()):
            self.stop(app_id)

process_manager = ProcessManager()
