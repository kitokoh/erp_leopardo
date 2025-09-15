import sqlite3
from typing import List, Optional, Dict, Any
from .models import CompanyCalendarSettings, UserCalendarEvent # Pydantic models
from app.db.connection import get_db_connection # Assuming similar connection management
from app.db.cruds.generic_crud import GenericCRUD, _manage_conn # For consistency
import logging
from datetime import date

# Placeholder for the actual database table names
COMPANY_SETTINGS_TABLE = "CompanyCalendarSettings"
USER_EVENTS_TABLE = "UserCalendarEvents"

class CompanyCalendarSettingsCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(COMPANY_SETTINGS_TABLE, "id") # Assuming 'id' is the primary key

    @_manage_conn
    def get_settings_by_user_id(self, user_id: str, conn: sqlite3.Connection = None) -> Optional[CompanyCalendarSettings]:
        """Fetches calendar settings for a given user_id."""
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return CompanyCalendarSettings(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Error fetching company calendar settings for user {user_id}: {e}")
            return None

    @_manage_conn
    def save_settings(self, settings: CompanyCalendarSettings, conn: sqlite3.Connection = None) -> Optional[CompanyCalendarSettings]:
        """Saves or updates calendar settings for a user. Assumes user_id is unique for settings."""
        cursor = conn.cursor()
        # Check if settings for this user_id already exist
        existing_settings = self.get_settings_by_user_id(settings.user_id, conn=conn) # Pass connection

        try:
            if existing_settings and existing_settings.id is not None:
                # Update existing settings
                sql = f"""UPDATE {self.table_name} SET
                            business_type = ?, activity_category = ?, country_iso = ?, region = ?
                          WHERE user_id = ?"""
                params = (settings.business_type, settings.activity_category,
                          settings.country_iso, settings.region, settings.user_id)
                cursor.execute(sql, params)
                # conn.commit() # Managed by decorator
                return self.get_settings_by_user_id(settings.user_id, conn=conn) # Return updated settings
            else:
                # Insert new settings
                sql = f"""INSERT INTO {self.table_name}
                            (user_id, business_type, activity_category, country_iso, region)
                          VALUES (?, ?, ?, ?, ?)"""
                params = (settings.user_id, settings.business_type, settings.activity_category,
                          settings.country_iso, settings.region)
                cursor.execute(sql, params)
                # conn.commit() # Managed by decorator
                # Get the last inserted ID if your DB supports it and model needs it, or re-fetch
                # For SQLite, lastrowid would give the rowid, not necessarily a specific 'id' column if it's not INTEGER PRIMARY KEY
                # It's often better to re-fetch by a unique key like user_id here.
                return self.get_settings_by_user_id(settings.user_id, conn=conn)
        except sqlite3.Error as e:
            logging.error(f"Error saving company calendar settings for user {settings.user_id}: {e}")
            # conn.rollback() # Managed by decorator
            return None

class UserCalendarEventsCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(USER_EVENTS_TABLE, "id") # Assuming 'id' is the primary key

    @_manage_conn
    def add_event(self, event: UserCalendarEvent, conn: sqlite3.Connection = None) -> Optional[UserCalendarEvent]:
        """Adds a new calendar event for a user."""
        cursor = conn.cursor()
        sql = f"""INSERT INTO {self.table_name}
                    (user_id, event_date, event_type, description)
                  VALUES (?, ?, ?, ?)"""
        # Convert date to ISO format string for SQLite
        event_date_str = event.event_date.isoformat()
        params = (event.user_id, event_date_str, event.event_type, event.description)
        try:
            cursor.execute(sql, params)
            event_id = cursor.lastrowid
            # conn.commit() # Managed by decorator
            if event_id:
                return self.get_by_id(event_id, conn=conn) # Use GenericCRUD's get_by_id
            return None
        except sqlite3.Error as e:
            logging.error(f"Error adding calendar event for user {event.user_id}: {e}")
            # conn.rollback() # Managed by decorator
            return None

    @_manage_conn
    def get_events_by_user_id(self, user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, conn: sqlite3.Connection = None) -> List[UserCalendarEvent]:
        """Fetches calendar events for a given user_id, optionally filtered by date range."""
        cursor = conn.cursor()
        sql = f"SELECT * FROM {self.table_name} WHERE user_id = ?"
        params: List[Any] = [user_id]

        if start_date:
            sql += " AND event_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            sql += " AND event_date <= ?"
            params.append(end_date.isoformat())

        sql += " ORDER BY event_date"

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [UserCalendarEvent(**dict(row)) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error fetching calendar events for user {user_id}: {e}")
            return []

    @_manage_conn
    def update_event(self, event_id: int, event_update_data: Dict[str, Any], conn: sqlite3.Connection = None) -> Optional[UserCalendarEvent]:
        """Updates an existing calendar event."""
        # Use GenericCRUD's update method if suitable, or implement custom logic
        # For this example, assume GenericCRUD.update handles dicts of fields to update.
        # Need to convert date object to string if 'event_date' is in update_data
        if 'event_date' in event_update_data and isinstance(event_update_data['event_date'], date):
            event_update_data['event_date'] = event_update_data['event_date'].isoformat()

        update_result = super().update(event_id, event_update_data, conn=conn)
        if update_result.get('success'):
            return self.get_by_id(event_id, conn=conn) # Re-fetch the updated event
        return None

    @_manage_conn
    def delete_event(self, event_id: int, conn: sqlite3.Connection = None) -> bool:
        """Deletes a calendar event by its ID."""
        # Use GenericCRUD's delete method
        delete_result = super().delete(event_id, conn=conn)
        return delete_result.get('success', False)

# Instantiate CRUD classes for easy import
company_calendar_settings_crud = CompanyCalendarSettingsCRUD()
user_calendar_events_crud = UserCalendarEventsCRUD()

__all__ = [
    "company_calendar_settings_crud",
    "user_calendar_events_crud",
    "CompanyCalendarSettingsCRUD",
    "UserCalendarEventsCRUD"
]
