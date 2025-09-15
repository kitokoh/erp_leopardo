from pyvirtualdisplay import Display
import subprocess
import os

# No need for pyvirtualdisplay if we use the offscreen plugin.
# The offscreen plugin should work without an X server.

# Set the QT_QPA_PLATFORM environment variable
env = os.environ.copy()
env["QT_QPA_PLATFORM"] = "offscreen"

# Now, run the main application.
# Using poetry run to ensure all dependencies are available.
process = subprocess.Popen(["poetry", "run", "python", "main.py"], env=env)

# Wait for the process to complete.
# In a real testing scenario, you might want to add a timeout
# and check the return code.
try:
    process.wait(timeout=60) # Wait for 60 seconds
except subprocess.TimeoutExpired:
    print("Application timed out. Killing process.")
    process.kill()
    process.wait()

if process.returncode == 0:
    print("Application ran successfully.")
else:
    print(f"Application exited with error code: {process.returncode}")
