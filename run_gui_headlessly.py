from pyvirtualdisplay import Display
import subprocess
import sys
import os
import time

print("--- Starting GUI Test with Virtual Display ---")

# Start virtual display
try:
    display = Display(visible=0, size=(1280, 1024))
    display.start()
    print("Virtual display started successfully.")
except Exception as e:
    print(f"Failed to start virtual display: {e}")
    sys.exit(1)

# Path to the main application script
main_script_path = os.path.join(os.path.dirname(__file__), 'main.py')
print(f"Attempting to run: {main_script_path}")

process = None
try:
    # Run the main application as a subprocess
    # It will inherit the DISPLAY environment variable from this script
    print("Launching main.py as a subprocess...")
    process = subprocess.Popen(
        [sys.executable, main_script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # The GUI will launch and the login window should appear.
    # Since this is a headless test, I can't interact with it,
    # but I can check if it runs without crashing for a few seconds.
    print("Waiting for 15 seconds to see if the application runs without crashing...")
    time.sleep(15)

    # Check if the process is still running
    if process.poll() is None:
        print(">>> GUI Verification PASSED: Application launched and remained running. <<<")
        # The process is still running, which is a good sign.
        # We can now terminate it.
        process.terminate()
        try:
            # Wait for a moment for the process to terminate
            outs, errs = process.communicate(timeout=5)
            print("--- Application stdout ---")
            print(outs)
            print("--- Application stderr ---")
            print(errs)
        except subprocess.TimeoutExpired:
            print("Process did not terminate gracefully, killing.")
            process.kill()

    else:
        # The process terminated early, indicating a crash.
        print(f">>> GUI Verification FAILED: Application crashed. Exit code: {process.poll()} <<<")
        outs, errs = process.communicate()
        print("--- Application stdout ---")
        print(outs)
        print("--- Application stderr ---")
        print(errs)

except Exception as e:
    print(f"An error occurred while running the subprocess: {e}")

finally:
    if process and process.poll() is None:
        process.kill()
    print("Stopping virtual display.")
    display.stop()
    print("--- GUI Test Finished ---")
