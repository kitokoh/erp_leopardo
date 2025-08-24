import os
import subprocess
from pathlib import Path

def run(cmd):
    print(f"\n>>> {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def delete_file(path):
    p = Path(path)
    if p.exists():
        print(f"Deleting {path}")
        p.unlink()

if __name__ == "__main__":
    print("--- Deleting old database file for a clean start ---")
    delete_file("app/core/app_data.db")
    delete_file("app/app_data.db")

    print("--- Running Database Migrations ---")
    run("poetry run alembic upgrade head")

    print("--- Running Data Seeding ---")
    run("poetry run python -m app.db.db_seed")

    print("--- Setup Complete ---")

    # --- CHOOSE YOUR LAUNCH OPTION ---

    # Option 1: Main GUI app
    print("--- Starting Application ---")
    run("poetry run python main.py")

    # Option 2: Headless login test
    # Comment above and uncomment below if needed
    # print("--- Running Headless Login Test ---")
    # run("poetry run python login_test.py")
