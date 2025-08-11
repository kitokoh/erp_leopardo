# db/cruds/__init__.py
# This file is intentionally left blank for now to break circular dependencies.
# The original content imported from all submodules, which created cycles.
# The correct approach is to have other modules import directly from the
# specific submodule they need, e.g., 'from app.db.cruds.users.users_crud import ...'
import logging
logging.warning("The app.db.cruds package is being imported, but its __init__.py is mostly empty to prevent circular imports. Ensure all imports are directed to submodules.")
