import sys
import os

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(f"conftest.py: Injected project root '{project_root}' into sys.path.")
print(f"conftest.py: Current sys.path: {sys.path}")
