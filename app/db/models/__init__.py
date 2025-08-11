# This file is intentionally left mostly blank to prevent circular dependencies
# caused by importing all models into a single namespace.
# Other modules should import directly from the specific model file they need,
# e.g., 'from app.db.models.users.user import User'
import logging
logging.warning("The app.db.models package is being imported, but its __init__.py is mostly empty to prevent circular imports. Ensure all imports are directed to submodules.")
