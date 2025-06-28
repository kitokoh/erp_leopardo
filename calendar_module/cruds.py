import sqlite3
from typing import List, Optional, Dict, Any
from .models import CompanyCalendarSettings, UserCalendarEvent # Pydantic models
from db.connection import get_db_connection # Assuming similar connection management
from db.cruds.generic_crud import GenericCRUD, _manage_conn # For consistency
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
from datetime import date, datetime # Ensure datetime is imported
from dateutil import rrule
# from dateutil.parser import isoparse # Not strictly needed if dates are handled as date objects

# ... (other imports remain the same)

class UserCalendarEventsCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(USER_EVENTS_TABLE, "id") # Assuming 'id' is the primary key

    @_manage_conn
    def add_event(self, event: UserCalendarEvent, conn: sqlite3.Connection = None) -> Optional[UserCalendarEvent]:
        """Adds a new calendar event for a user, including recurrence fields."""
        cursor = conn.cursor()
        sql = f"""INSERT INTO {self.table_name}
                    (user_id, event_date, event_type, description, recurrence_rule, recurrence_end_date)
                  VALUES (?, ?, ?, ?, ?, ?)"""

        event_date_str = event.event_date.isoformat()
        recurrence_end_date_str = event.recurrence_end_date.isoformat() if event.recurrence_end_date else None

        params = (event.user_id, event_date_str, event.event_type, event.description,
                  event.recurrence_rule, recurrence_end_date_str)
        try:
            cursor.execute(sql, params)
            event_id = cursor.lastrowid
            if event_id:
                raw_event = super().get_by_id(event_id, conn=conn) # GenericCRUD.get_by_id returns a dict
                return UserCalendarEvent(**raw_event) if raw_event else None
            return None
        except sqlite3.Error as e:
            logging.error(f"Error adding calendar event for user {event.user_id}: {e}")
            return None

    @_manage_conn
    def get_events_by_user_id(self, user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, conn: sqlite3.Connection = None) -> List[UserCalendarEvent]:
        """
        Fetches calendar events for a given user_id, optionally filtered by date range.
        Expands recurring events within the requested date range.
        """
        cursor = conn.cursor()
        # Fetch base events that could occur in the range.
        # A recurring event starting before end_date and ending after start_date (or no end) is relevant.
        # A non-recurring event must be within start_date and end_date.

        # Base query to fetch all events for the user for simplicity in this step.
        # Optimization: Filter more strictly in SQL later if performance becomes an issue.
        sql = f"SELECT * FROM {self.table_name} WHERE user_id = ?"
        params: List[Any] = [user_id]

        all_user_events_raw = []
        try:
            cursor.execute(sql, params)
            all_user_events_raw = cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error fetching base calendar events for user {user_id}: {e}")
            return []

        expanded_events: List[UserCalendarEvent] = []
        for row_data in all_user_events_raw:
            base_event_dict = dict(row_data)

            # Ensure date fields are parsed correctly from DB (TEXT to date or datetime)
            # SQLite stores dates as TEXT in ISO format.
            if isinstance(base_event_dict.get('event_date'), str):
                base_event_dict['event_date'] = date.fromisoformat(base_event_dict['event_date'])
            if base_event_dict.get('recurrence_end_date') and isinstance(base_event_dict['recurrence_end_date'], str):
                base_event_dict['recurrence_end_date'] = date.fromisoformat(base_event_dict['recurrence_end_date'])
            elif base_event_dict.get('recurrence_end_date') == '': # Handle empty string from DB if not NULL
                 base_event_dict['recurrence_end_date'] = None


            base_event = UserCalendarEvent(**base_event_dict)

            if base_event.recurrence_rule and start_date and end_date:
                try:
                    dtstart = datetime.combine(base_event.event_date, datetime.min.time())

                    # Parse RRULE string.
                    # rrulestr correctly handles dtstart if it's part of the string or passed as argument.
                    # For simplicity, assume dtstart in UserCalendarEvent.event_date is the true start.
                    rule_obj = rrule.rrulestr(base_event.recurrence_rule, dtstart=dtstart)

                    # Determine the effective end for this rule's iteration for this query window
                    iteration_limit_dt = datetime.combine(end_date, datetime.max.time())
                    if base_event.recurrence_end_date:
                        rule_specific_end_dt = datetime.combine(base_event.recurrence_end_date, datetime.max.time())
                        iteration_limit_dt = min(iteration_limit_dt, rule_specific_end_dt)

                    # Iterate occurrences within the query window [start_date, end_date]
                    # but not exceeding the rule's own end date or the iteration_limit_dt.
                    occurrences_dts = rule_obj.between(
                        datetime.combine(start_date, datetime.min.time()),
                        iteration_limit_dt, # Use the calculated iteration limit
                        inc=True
                    )

                    for occ_dt in occurrences_dts:
                        # Ensure the occurrence is not before the actual start_date of the query window
                        if occ_dt.date() < start_date:
                            continue

                        expanded_events.append(UserCalendarEvent(
                            id=base_event.id,
                            user_id=base_event.user_id,
                            event_date=occ_dt.date(),
                            event_type=base_event.event_type,
                            description=base_event.description,
                            # Keep recurrence_rule and recurrence_end_date from base for context,
                            # though this expanded event is a single occurrence.
                            recurrence_rule=base_event.recurrence_rule,
                            recurrence_end_date=base_event.recurrence_end_date
                        ))
                except Exception as e_rrule:
                    logging.error(f"Error expanding rrule for event ID {base_event.id} ('{base_event.recurrence_rule}'): {e_rrule}. Adding base event only if in range.")
                    if start_date <= base_event.event_date <= end_date:
                        expanded_events.append(base_event)
            else: # Non-recurring event or no date range for expansion
                if start_date and end_date: # If range provided, check if non-recurring falls within
                    if start_date <= base_event.event_date <= end_date:
                        expanded_events.append(base_event)
                elif not start_date and not end_date: # No date range, add all non-recurring
                    expanded_events.append(base_event)
                # Add other conditions if only start_date or only end_date is provided, if necessary

        expanded_events.sort(key=lambda x: x.event_date)
        return expanded_events

    @_manage_conn
    def update_event(self, event_id: int, event_update_data: Dict[str, Any], conn: sqlite3.Connection = None) -> Optional[UserCalendarEvent]:
        """Updates an existing calendar event, including recurrence fields."""

        if 'event_date' in event_update_data and isinstance(event_update_data['event_date'], date):
            event_update_data['event_date'] = event_update_data['event_date'].isoformat()

        if 'recurrence_end_date' in event_update_data: # Check existence before isinstance
            if isinstance(event_update_data['recurrence_end_date'], date):
                event_update_data['recurrence_end_date'] = event_update_data['recurrence_end_date'].isoformat()
            # If None, it will be passed as None to SQL, which is fine.

        update_result = super().update(event_id, event_update_data, conn=conn)
        if update_result.get('success'):
            raw_event = super().get_by_id(event_id, conn=conn) # GenericCRUD.get_by_id returns a dict
            return UserCalendarEvent(**raw_event) if raw_event else None
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

# Placeholder for the actual database table name for Custom Holidays
CUSTOM_HOLIDAYS_TABLE = "CustomHolidays"

class CustomHolidaysCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(CUSTOM_HOLIDAYS_TABLE, "id")

    @_manage_conn
    def add_custom_holiday(self, holiday_data: CustomHoliday, conn: sqlite3.Connection = None) -> Optional[CustomHoliday]:
        cursor = conn.cursor()
        sql = f"""INSERT INTO {self.table_name}
                    (user_id, holiday_date, description)
                  VALUES (?, ?, ?)"""
        try:
            cursor.execute(sql, (holiday_data.user_id, holiday_data.holiday_date.isoformat(), holiday_data.description))
            holiday_id = cursor.lastrowid
            if holiday_id:
                raw_holiday = super().get_by_id(holiday_id, conn=conn)
                return CustomHoliday(**raw_holiday) if raw_holiday else None
            return None
        except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violation (user_id, holiday_date)
            logging.warning(f"Failed to add custom holiday due to integrity error (likely duplicate): {e}")
            return None
        except sqlite3.Error as e:
            logging.error(f"Error adding custom holiday for user {holiday_data.user_id}: {e}")
            return None

    @_manage_conn
    def get_custom_holidays_by_user_id(self, user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, conn: sqlite3.Connection = None) -> List[CustomHoliday]:
        cursor = conn.cursor()
        sql = f"SELECT * FROM {self.table_name} WHERE user_id = ?"
        params: List[Any] = [user_id]

        if start_date:
            sql += " AND holiday_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            sql += " AND holiday_date <= ?"
            params.append(end_date.isoformat())

        sql += " ORDER BY holiday_date"

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            holidays_list = []
            for row in rows:
                row_dict = dict(row)
                if isinstance(row_dict.get('holiday_date'), str):
                    row_dict['holiday_date'] = date.fromisoformat(row_dict['holiday_date'])
                holidays_list.append(CustomHoliday(**row_dict))
            return holidays_list
        except sqlite3.Error as e:
            logging.error(f"Error fetching custom holidays for user {user_id}: {e}")
            return []

    @_manage_conn
    def delete_custom_holiday(self, holiday_id: int, conn: sqlite3.Connection = None) -> bool:
        delete_result = super().delete(holiday_id, conn=conn)
        return delete_result.get('success', False)

custom_holidays_crud = CustomHolidaysCRUD()

__all__ = [
    "company_calendar_settings_crud",
    "user_calendar_events_crud",
    "custom_holidays_crud", # Added
    "CompanyCalendarSettingsCRUD",
    "UserCalendarEventsCRUD",
    "CustomHolidaysCRUD" # Added
]
