# api_server_manager.py
# This file will contain the logic for starting and stopping the FastAPI server.

import subprocess
import logging
import os # os might be needed by how uvicorn resolves paths or for environment variables

# Global variable for the API server process, specific to this manager
api_server_process = None

# Functions start_api_server and stop_api_server will be moved here.

def start_api_server():
    """Starts the FastAPI server as a subprocess."""
    global api_server_process
    try:
        # Ensure the command is correctly formatted.
        # If 'api.main' is a module, uvicorn needs to be able to find it.
        # This might require adjusting PYTHONPATH or running from a specific directory.
        # For now, assume 'api.main:app' is discoverable by uvicorn in the current environment.
        command = ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

        # Using Popen for non-blocking execution.
        # Ensure that the subprocess's stdout/stderr are handled appropriately
        # to prevent blocking or deadlocks if they fill up.
        # For basic logging, we can capture them or redirect to DEVNULL if not needed.
        api_server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Try to communicate with the process to get output.
        # This will wait for the process to terminate if it does so quickly.
        # If it's a long-running server, communicate() won't return until it's done,
        # so we need a timeout for the initial check.
        try:
            stdout, stderr = api_server_process.communicate(timeout=2) # Wait 2 seconds for initial output / quick failure
            # If communicate() returns, the process has terminated.
            logging.error(f"FastAPI server process terminated unexpectedly. Exit code: {api_server_process.returncode}")
            stdout_str = stdout.decode(errors='replace').strip()
            stderr_str = stderr.decode(errors='replace').strip()
            if stdout_str:
                logging.error(f"FastAPI Server Stdout:\n{stdout_str}")
            if stderr_str:
                logging.error(f"FastAPI Server Stderr:\n{stderr_str}")
            api_server_process = None # Reset as it failed
        except subprocess.TimeoutExpired:
            # This is the expected path for a successfully started server.
            # The process is still running after the timeout.
            if api_server_process.poll() is None:
                logging.info(f"FastAPI server process started successfully with PID: {api_server_process.pid}. Command: {' '.join(command)}")
                # Optionally, you could start threads here to monitor api_server_process.stdout and api_server_process.stderr
                # and log their output in real-time if continuous logging is needed.
            else:
                # Process terminated after TimeoutExpired was raised but before poll() - less likely but possible
                stdout, stderr = api_server_process.communicate() # get any final output
                logging.error(f"FastAPI server process failed to start or terminated shortly after. Exit code: {api_server_process.returncode}")
                stdout_str = stdout.decode(errors='replace').strip()
                stderr_str = stderr.decode(errors='replace').strip()
                if stdout_str:
                    logging.error(f"FastAPI Server Stdout (after timeout check):\n{stdout_str}")
                if stderr_str:
                    logging.error(f"FastAPI Server Stderr (after timeout check):\n{stderr_str}")
                api_server_process = None
        except Exception as e_comm:
            # Other errors during communicate
            logging.error(f"Error communicating with FastAPI server process: {e_comm}", exc_info=True)
            if api_server_process.poll() is not None:
                logging.error(f"FastAPI server process also terminated with exit code: {api_server_process.returncode}")
            api_server_process = None


    except FileNotFoundError:
        logging.error("Error starting FastAPI server: 'uvicorn' command not found. Ensure uvicorn is installed and in PATH.")
        api_server_process = None
    except Exception as e:
        logging.error(f"An unexpected error occurred while starting the FastAPI server process: {e}", exc_info=True)
        api_server_process = None

def stop_api_server():
    """Stops the FastAPI server process if it is running."""
    global api_server_process
    if api_server_process and api_server_process.poll() is None: # Check if process exists and is running
        logging.info(f"Attempting to terminate API server process with PID: {api_server_process.pid}")
        try:
            api_server_process.terminate() # Send SIGTERM
            try:
                # Wait for a few seconds for graceful shutdown
                api_server_process.wait(timeout=5)
                logging.info(f"API server process with PID: {api_server_process.pid} terminated.")
            except subprocess.TimeoutExpired:
                logging.warning(f"API server process with PID: {api_server_process.pid} did not terminate in time. Sending SIGKILL.")
                api_server_process.kill() # Send SIGKILL
                api_server_process.wait() # Wait for kill to complete
                logging.info(f"API server process with PID: {api_server_process.pid} killed.")
            except Exception as e_wait: # Catch other errors during wait (e.g. process already died)
                logging.info(f"Error waiting for API server process {api_server_process.pid} to terminate: {e_wait}. It might have already exited.")
        except ProcessLookupError: # Raised if process does not exist (e.g. already terminated)
            logging.info(f"API server process with PID: {api_server_process.pid} not found. Likely already stopped.")
        except Exception as e:
            logging.error(f"Error terminating/killing API server process with PID: {api_server_process.pid}: {e}", exc_info=True)
    elif api_server_process: # Process exists but poll() is not None, meaning it already terminated
        logging.info(f"API server process with PID: {api_server_process.pid} was already stopped (return code: {api_server_process.returncode}).")
    else: # api_server_process is None
        logging.info("No API server process to stop (api_server_process is None).")

if __name__ == '__main__':
    # This section could be used to allow starting the server independently,
    # for example, by running: python api_server_manager.py start
    # For now, it will be empty or have basic test logic.
    logging.basicConfig(level=logging.INFO)
    logging.info("API Server Manager - This script is intended to be imported or called with arguments.")
    # Example:
    # import sys
    # if len(sys.argv) > 1 and sys.argv[1] == 'start':
    #     start_api_server()
    #     # Keep alive or manage process
    # elif len(sys.argv) > 1 and sys.argv[1] == 'stop':
    #     # This would require knowing the PID or having a mechanism to signal a running server
    #     # stop_api_server() # stop_api_server as defined expects global api_server_process
    #     pass
