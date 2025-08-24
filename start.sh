#!/bin/bash

# This script orchestrates the setup and launch of the application.
# It ensures the database is created, migrated, and seeded before running the app.

# Exit on any error
set -e

echo "--- Deleting old database file for a clean start ---"
rm -f app/core/app_data.db
rm -f app/app_data.db

echo "--- Running Database Migrations ---"
poetry run alembic upgrade head

echo "--- Running Data Seeding ---"
poetry run python -m app.db.db_seed

echo "--- Setup Complete ---"

# --- CHOOSE YOUR LAUNCH OPTION ---

# Option 1: Run the main GUI application (default)
# This requires a graphical environment (X11 or Wayland).
echo "--- Starting Application ---"
poetry run python main.py

# Option 2: Run the headless login test
# This is useful for CI/CD or environments without a GUI to verify that
# the database and basic user authentication are working.
# To use this, comment out the main application line above and uncomment the line below.
#
# echo "--- Running Headless Login Test ---"
# poetry run python login_test.py
