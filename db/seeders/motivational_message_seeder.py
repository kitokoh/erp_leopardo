import json
import os
import logging
import sqlite3

from db.cruds.generic_crud import GenericCRUD

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_motivational_messages(conn: sqlite3.Connection, logger: logging.Logger):
    """
    Seeds motivational messages from the motivational_messages.json file.
    """
    logger.info("Seeding motivational messages from motivational_messages.json...")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "motivational_messages.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found at: {json_path}. Skipping motivational message seeding.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Seed Default Messages
    _seed_default_messages(conn, logger, data.get("default_messages", []))

    # Seed User-defined Messages
    _seed_user_messages(conn, logger, data.get("user_messages", []))

    logger.info("Finished seeding motivational messages.")


def _seed_default_messages(conn: sqlite3.Connection, logger: logging.Logger, messages_data: list):
    logger.info("Seeding default motivational messages...")
    messages_crud = GenericCRUD(table_name='motivational_messages', primary_key='id')
    cursor = conn.cursor()
    added_count = 0
    skipped_count = 0

    for msg_data in messages_data:
        try:
            # Check for existing message based on UNIQUE constraints
            existing = None
            if msg_data["day_of_year"] is None:
                query = "SELECT id FROM motivational_messages WHERE language_code = ? AND message = ? AND day_of_year IS NULL"
                cursor.execute(query, (msg_data["language_code"], msg_data["message"]))
                existing = cursor.fetchone()
            else:
                query = "SELECT id FROM motivational_messages WHERE language_code = ? AND day_of_year = ?"
                cursor.execute(query, (msg_data["language_code"], msg_data["day_of_year"]))
                existing = cursor.fetchone()

            if existing:
                skipped_count += 1
                continue

            data_to_insert = { "language_code": msg_data["language_code"], "message": msg_data["message"], "day_of_year": msg_data["day_of_year"], "is_active": True }
            messages_crud.create(data_to_insert, conn=conn)
            added_count += 1
        except sqlite3.IntegrityError:
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error adding motivational message '{msg_data['message'][:30]}...': {e}")
            skipped_count += 1

    logger.info(f"Default motivational messages seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")


def _seed_user_messages(conn: sqlite3.Connection, logger: logging.Logger, messages_data: list):
    logger.info("Seeding user motivational messages...")
    user_messages_crud = GenericCRUD(table_name='user_motivational_messages', primary_key='id')
    cursor = conn.cursor()
    added_count = 0
    skipped_count = 0

    for msg_data in messages_data:
        try:
            query = "SELECT id FROM user_motivational_messages WHERE message = ?"
            cursor.execute(query, (msg_data["message"],))
            if cursor.fetchone():
                skipped_count += 1
                continue

            data_to_insert = { "message": msg_data["message"], "language_code": msg_data.get("language_code"), "is_active": True }
            user_messages_crud.create(data_to_insert, conn=conn)
            added_count += 1
        except sqlite3.IntegrityError:
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error adding user motivational message '{msg_data['message'][:30]}...': {e}")
            skipped_count += 1

    logger.info(f"User motivational messages seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")
