# -*- coding: utf-8 -*-
import subprocess
import logging
import atexit

class APIServerManager:
    """
    Manages the lifecycle of the background FastAPI server process.
    """
    def __init__(self):
        self.api_server_process = None
        # Register the stop method to be called on application exit
        atexit.register(self.stop_server)
        logging.info("APIServerManager initialized and stop_server registered with atexit.")

    def start_server(self):
        """Starts the FastAPI server as a subprocess."""
        if self.api_server_process and self.api_server_process.poll() is None:
            logging.warning("API server process is already running.")
            return

        try:
            command = ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

            self.api_server_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            try:
                # Check for quick failure
                self.api_server_process.wait(timeout=2)
                # If wait() returns, the process has terminated
                stdout, stderr = self.api_server_process.communicate()
                logging.error(f"FastAPI server process terminated unexpectedly. Exit code: {self.api_server_process.returncode}")
                if stdout:
                    logging.error(f"FastAPI Server Stdout:\n{stdout.decode(errors='replace').strip()}")
                if stderr:
                    logging.error(f"FastAPI Server Stderr:\n{stderr.decode(errors='replace').strip()}")
                self.api_server_process = None
            except subprocess.TimeoutExpired:
                # This is the expected outcome for a successful start
                logging.info(f"FastAPI server process started successfully with PID: {self.api_server_process.pid}.")

        except FileNotFoundError:
            logging.error("Error starting FastAPI server: 'uvicorn' command not found. Ensure uvicorn is installed and in PATH.")
            self.api_server_process = None
        except Exception as e:
            logging.error(f"An unexpected error occurred while starting the FastAPI server process: {e}", exc_info=True)
            self.api_server_process = None

    def stop_server(self):
        """Stops the FastAPI server process if it is running."""
        if not self.api_server_process or self.api_server_process.poll() is not None:
            logging.info("No running API server process to stop.")
            return

        logging.info(f"Attempting to terminate API server process with PID: {self.api_server_process.pid}")
        try:
            self.api_server_process.terminate()  # SIGTERM
            try:
                self.api_server_process.wait(timeout=5)
                logging.info(f"API server process with PID: {self.api_server_process.pid} terminated gracefully.")
            except subprocess.TimeoutExpired:
                logging.warning(f"API server process PID {self.api_server_process.pid} did not terminate in time. Killing it.")
                self.api_server_process.kill()  # SIGKILL
                self.api_server_process.wait()
                logging.info(f"API server process with PID: {self.api_server_process.pid} killed.")
        except ProcessLookupError:
            logging.info(f"API server process with PID: {self.api_server_process.pid} not found. Likely already stopped.")
        except Exception as e:
            logging.error(f"Error stopping API server process PID {self.api_server_process.pid}: {e}", exc_info=True)
        finally:
            self.api_server_process = None
