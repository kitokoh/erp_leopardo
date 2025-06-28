import unittest
import sqlite3
import os
from datetime import date, datetime, timedelta

# Adjust import paths if your test runner requires it or if project structure is different
# This assumes that 'calendar_module' and 'db' are discoverable Python packages.
try:
    from calendar_module.models import CompanyCalendarSettings, UserCalendarEvent
    from calendar_module.cruds import CompanyCalendarSettingsCRUD, UserCalendarEventsCRUD
    from db.init_schema import initialize_database # To set up the schema in memory
    from db.connection import get_db_connection # To get a connection for setup/teardown
except ImportError:
    # This block allows running tests directly if paths are not set up,
    # by temporarily adding the project root to sys.path.
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from calendar_module.models import CompanyCalendarSettings, UserCalendarEvent
    from calendar_module.cruds import CompanyCalendarSettingsCRUD, UserCalendarEventsCRUD
    from db.init_schema import initialize_database
    from db.connection import _get_db_connection_for_testing, _close_db_connection_for_testing


# Use a global variable for the test database path for simplicity in this example
# In a more complex setup, this might be configured via environment variables or a test config file.
TEST_DB_PATH = ":memory:" # Use in-memory SQLite database for tests

# Store the original get_db_connection and set it to a test-specific one
original_get_db_connection = None
original_db_path_config = None

def setUpModule():
    """Called once before any tests in this module."""
    global original_get_db_connection, original_db_path_config

    # 1. Override db.connection.DATABASE_PATH if possible, or the config used by get_db_connection
    # This depends on how db.connection is implemented.
    # For this example, let's assume db.connection might have a way to set its path,
    # or we directly patch where it gets the DB_PATH from.
    # A simple way for this example is to patch the config object if db.connection uses it.
    # If db.connection.DATABASE_PATH is a direct global, we might need to mock it.

    # Assuming db.connection has a setup like:
    # import config as app_config
    # DATABASE_PATH = app_config.DATABASE_PATH
    # We would need to patch app_config.DATABASE_PATH

    # For this test, we'll directly use a test-specific connection function.
    # This avoids complex patching of the global config.

    if 'db.connection' in sys.modules:
        import db.connection
        original_get_db_connection = db.connection.get_db_connection
        db.connection.get_db_connection = _get_db_connection_for_testing_with_path(TEST_DB_PATH)

        # If db.init_schema also uses a global config for DB_PATH, that needs to be handled too.
        # For initialize_database() to use the in-memory DB:
        # It uses 'import config' then 'config.DATABASE_PATH'.
        # We need to make sure 'config.DATABASE_PATH' points to TEST_DB_PATH when initialize_database() is called.
        if 'config' in sys.modules:
            import config as app_config
            original_db_path_config = app_config.DATABASE_PATH
            app_config.DATABASE_PATH = TEST_DB_PATH


    # 2. Initialize the schema on the in-memory database
    initialize_database() # This should now use TEST_DB_PATH due to the config patch

    # Seed a dummy user for FK constraints if Users table is involved and not managed by GenericCRUD
    conn = _get_db_connection_for_testing_with_path(TEST_DB_PATH)() # Get a direct connection
    cursor = conn.cursor()
    try:
        # Ensure Users table exists (it should after initialize_database)
        cursor.execute("SELECT 1 FROM Users WHERE user_id = 'test_user_for_calendar'")
        if cursor.fetchone() is None:
            # Minimal user data for FK satisfaction
            cursor.execute("""
                INSERT INTO Users (user_id, username, password_hash, salt, email, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('test_user_for_calendar', 'testcalendaruser', 'hash', 'salt', 'calendar@test.com', 'user'))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Warning: Could not seed dummy user for calendar tests: {e}")
    finally:
        if conn:
            conn.close()


def tearDownModule():
    """Called once after all tests in this module."""
    global original_get_db_connection, original_db_path_config
    if 'db.connection' in sys.modules and original_get_db_connection:
        import db.connection
        db.connection.get_db_connection = original_get_db_connection

    if 'config' in sys.modules and original_db_path_config:
        import config as app_config
        app_config.DATABASE_PATH = original_db_path_config

    # If using a file-based test DB, os.remove(TEST_DB_PATH) would go here.
    # For :memory:, it's cleared when the last connection closes.
    # Explicitly close any test-specific connections if managed globally by _get_db_connection_for_testing
    _close_db_connection_for_testing()


def _get_db_connection_for_testing_with_path(db_path):
    """Returns a function that provides a connection to the specified DB path."""
    # This is a simplified connection manager for tests.
    # A more robust solution might use a session/connection pool for tests.
    _test_conn = None
    def get_conn():
        nonlocal _test_conn
        if _test_conn is None or _is_connection_closed(_test_conn): # Ensure connection is open
            _test_conn = sqlite3.connect(db_path)
            _test_conn.row_factory = sqlite3.Row
        return _test_conn
    return get_conn

def _is_connection_closed(conn):
    try:
        # Attempt a simplepragma to check if connection is live
        conn.execute("PRAGMA user_version")
        return False
    except (sqlite3.ProgrammingError, sqlite3.OperationalError): # ProgrammingError if closed, OperationalError if already busy/closed
        return True


class TestCompanyCalendarSettingsCRUD(unittest.TestCase):
    def setUp(self):
        """Called before each test method."""
        self.crud = CompanyCalendarSettingsCRUD()
        self.user_id = "test_user_for_calendar" # Ensure this user exists or is created in setUpModule/test
        self.conn = _get_db_connection_for_testing_with_path(TEST_DB_PATH)() # Get a fresh connection for each test

        # Clean up table before each test to ensure isolation
        try:
            with self.conn: # Use 'with' for auto-commit/rollback on this cleanup
                 self.conn.execute(f"DELETE FROM {self.crud.table_name}")
        except sqlite3.Error as e:
            # Table might not exist if schema init failed for some reason, or first run
            print(f"Pre-test cleanup warning for {self.crud.table_name}: {e}")


    def tearDown(self):
        """Called after each test method."""
        # Connection is managed by _get_db_connection_for_testing_with_path,
        # and closed in tearDownModule. If each test needs its own separate :memory: DB,
        # then TEST_DB_PATH would need to be unique per test or connection handling adjusted.
        # For a shared :memory: DB for the module, cleaning tables is key.
        pass

    def test_01_save_new_settings(self):
        settings_data = CompanyCalendarSettings(
            user_id=self.user_id,
            business_type="B2B",
            activity_category="Tech",
            country_iso="FR",
            region="IDF"
        )
        saved_settings = self.crud.save_settings(settings_data, conn=self.conn)
        self.assertIsNotNone(saved_settings)
        self.assertEqual(saved_settings.user_id, self.user_id)
        self.assertEqual(saved_settings.country_iso, "FR")

    def test_02_get_settings_by_user_id(self):
        # First, save some settings
        settings_data = CompanyCalendarSettings(user_id=self.user_id, business_type="B2C", activity_category="Retail", country_iso="US", region="CA")
        self.crud.save_settings(settings_data, conn=self.conn)

        retrieved_settings = self.crud.get_settings_by_user_id(self.user_id, conn=self.conn)
        self.assertIsNotNone(retrieved_settings)
        self.assertEqual(retrieved_settings.country_iso, "US")

    def test_03_update_existing_settings(self):
        # Initial save
        initial_settings = CompanyCalendarSettings(user_id=self.user_id, business_type="B2B", activity_category="Software", country_iso="DE")
        self.crud.save_settings(initial_settings, conn=self.conn)

        # Update
        updated_data = CompanyCalendarSettings(user_id=self.user_id, business_type="Both", activity_category="Consulting", country_iso="DE", region="BY")
        updated_settings = self.crud.save_settings(updated_data, conn=self.conn)

        self.assertIsNotNone(updated_settings)
        self.assertEqual(updated_settings.business_type, "Both")
        self.assertEqual(updated_settings.region, "BY")

        # Verify by getting again
        refetched_settings = self.crud.get_settings_by_user_id(self.user_id, conn=self.conn)
        self.assertEqual(refetched_settings.business_type, "Both")


class TestUserCalendarEventsCRUD(unittest.TestCase):
    def setUp(self):
        self.crud = UserCalendarEventsCRUD()
        self.user_id = "test_user_for_calendar"
        self.conn = _get_db_connection_for_testing_with_path(TEST_DB_PATH)()
        # Clean up table
        try:
            with self.conn:
                self.conn.execute(f"DELETE FROM {self.crud.table_name}")
        except sqlite3.Error as e:
             print(f"Pre-test cleanup warning for {self.crud.table_name}: {e}")


    def test_01_add_event(self):
        event_data = UserCalendarEvent(
            user_id=self.user_id,
            event_date=date(2024, 1, 15),
            event_type="WorkDay",
            description="Team Meeting"
        )
        added_event = self.crud.add_event(event_data, conn=self.conn)
        self.assertIsNotNone(added_event)
        self.assertIsNotNone(added_event.id)
        self.assertEqual(added_event.description, "Team Meeting")

    def test_02_get_events_by_user_id(self):
        # Add a couple of events
        event1_data = UserCalendarEvent(user_id=self.user_id, event_date=date(2024, 2, 10), event_type="RemoteWork", description="Project X")
        event2_data = UserCalendarEvent(user_id=self.user_id, event_date=date(2024, 2, 12), event_type="Holiday", description="Public Holiday")
        self.crud.add_event(event1_data, conn=self.conn)
        self.crud.add_event(event2_data, conn=self.conn)

        events = self.crud.get_events_by_user_id(self.user_id, conn=self.conn)
        self.assertEqual(len(events), 2)

    def test_03_get_events_by_user_id_with_date_range(self):
        today = date.today()
        event1 = UserCalendarEvent(user_id=self.user_id, event_date=today, event_type="WorkDay", description="Event 1")
        event2 = UserCalendarEvent(user_id=self.user_id, event_date=today + timedelta(days=2), event_type="RemoteWork", description="Event 2")
        event3 = UserCalendarEvent(user_id=self.user_id, event_date=today + timedelta(days=5), event_type="OtherPersonal", description="Event 3")
        self.crud.add_event(event1, conn=self.conn)
        self.crud.add_event(event2, conn=self.conn)
        self.crud.add_event(event3, conn=self.conn)

        # Test range including first two
        events_in_range = self.crud.get_events_by_user_id(self.user_id, start_date=today, end_date=today + timedelta(days=3), conn=self.conn)
        self.assertEqual(len(events_in_range), 2)
        self.assertTrue(any(e.description == "Event 1" for e in events_in_range))
        self.assertTrue(any(e.description == "Event 2" for e in events_in_range))

        # Test range including only middle one
        events_only_middle = self.crud.get_events_by_user_id(self.user_id, start_date=today + timedelta(days=1), end_date=today + timedelta(days=3), conn=self.conn)
        self.assertEqual(len(events_only_middle), 1)
        self.assertEqual(events_only_middle[0].description, "Event 2")


    def test_04_update_event(self):
        event_data = UserCalendarEvent(user_id=self.user_id, event_date=date(2024, 3, 5), event_type="WorkDay", description="Initial Description")
        added_event = self.crud.add_event(event_data, conn=self.conn)
        self.assertIsNotNone(added_event)
        self.assertIsNotNone(added_event.id)

        update_payload = {"description": "Updated Description", "event_type": "RemoteWork"}
        updated_event = self.crud.update_event(added_event.id, update_payload, conn=self.conn)

        self.assertIsNotNone(updated_event)
        self.assertEqual(updated_event.description, "Updated Description")
        self.assertEqual(updated_event.event_type, "RemoteWork")

        # Verify by getting again
        refetched_event = self.crud.get_by_id(added_event.id, conn=self.conn) # Assuming GenericCRUD's get_by_id
        self.assertIsNotNone(refetched_event) # get_by_id returns a dict from GenericCRUD
        self.assertEqual(refetched_event['description'], "Updated Description")


    def test_05_delete_event(self):
        event_data = UserCalendarEvent(user_id=self.user_id, event_date=date(2024, 4, 1), event_type="OtherPersonal", description="To Be Deleted")
        added_event = self.crud.add_event(event_data, conn=self.conn)
        self.assertIsNotNone(added_event)
        self.assertIsNotNone(added_event.id)

        delete_success = self.crud.delete_event(added_event.id, conn=self.conn)
        self.assertTrue(delete_success)

        # Verify it's gone
        deleted_event_check = self.crud.get_by_id(added_event.id, conn=self.conn)
        self.assertIsNone(deleted_event_check)

    def test_06_add_recurring_event_daily(self):
        event_data = UserCalendarEvent(
            user_id=self.user_id,
            event_date=date(2024, 5, 1), # Start date
            event_type="Routine",
            description="Daily Standup",
            recurrence_rule="FREQ=DAILY;INTERVAL=1",
            recurrence_end_date=date(2024, 5, 5) # Recur for 5 days
        )
        added_event = self.crud.add_event(event_data, conn=self.conn)
        self.assertIsNotNone(added_event)
        self.assertEqual(added_event.recurrence_rule, "FREQ=DAILY;INTERVAL=1")

        # Fetch events for the period and check occurrences
        events_in_range = self.crud.get_events_by_user_id(
            self.user_id,
            start_date=date(2024, 5, 1),
            end_date=date(2024, 5, 7), # Query a bit beyond the recurrence end
            conn=self.conn
        )
        self.assertEqual(len(events_in_range), 5) # Should be 5 occurrences: May 1, 2, 3, 4, 5
        expected_dates = [date(2024, 5, i) for i in range(1, 6)]
        occurrence_dates = sorted([e.event_date for e in events_in_range])
        self.assertEqual(occurrence_dates, expected_dates)
        for e in events_in_range:
            self.assertEqual(e.description, "Daily Standup")
            self.assertEqual(e.id, added_event.id) # All occurrences should link to the base event ID

    def test_07_add_recurring_event_weekly(self):
        # Weekly event, every Monday, for 3 weeks
        # Let's find a Monday, e.g., 2024-05-06 is a Monday
        start_monday = date(2024, 5, 6)
        event_data = UserCalendarEvent(
            user_id=self.user_id,
            event_date=start_monday,
            event_type="Meeting",
            description="Weekly Sync",
            recurrence_rule="FREQ=WEEKLY;BYDAY=MO;INTERVAL=1",
            # 3 occurrences: May 6, May 13, May 20. End date should be on or after May 20.
            recurrence_end_date=date(2024, 5, 20)
        )
        added_event = self.crud.add_event(event_data, conn=self.conn)
        self.assertIsNotNone(added_event)

        events_in_range = self.crud.get_events_by_user_id(
            self.user_id,
            start_date=date(2024, 5, 1),
            end_date=date(2024, 5, 31),
            conn=self.conn
        )

        self.assertEqual(len(events_in_range), 3)
        expected_dates = [date(2024, 5, 6), date(2024, 5, 13), date(2024, 5, 20)]
        occurrence_dates = sorted([e.event_date for e in events_in_range])
        self.assertEqual(occurrence_dates, expected_dates)
        for e in events_in_range:
            self.assertEqual(e.description, "Weekly Sync")

    def test_08_recurring_event_no_end_date(self):
        # Daily event with no specific recurrence_end_date (should be limited by query range)
        event_data = UserCalendarEvent(
            user_id=self.user_id,
            event_date=date(2024, 6, 1),
            event_type="Reminder",
            description="Check Emails",
            recurrence_rule="FREQ=DAILY;INTERVAL=1",
            recurrence_end_date=None # No explicit end
        )
        self.crud.add_event(event_data, conn=self.conn)

        # Query for 3 days
        events_in_range = self.crud.get_events_by_user_id(
            self.user_id,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 3),
            conn=self.conn
        )
        self.assertEqual(len(events_in_range), 3) # June 1, 2, 3

    def test_09_update_recurring_event_details(self):
        event_data = UserCalendarEvent(
            user_id=self.user_id, event_date=date(2024, 7, 1), event_type="Task",
            description="Initial Task", recurrence_rule="FREQ=DAILY", recurrence_end_date=date(2024, 7, 2)
        )
        added_event = self.crud.add_event(event_data, conn=self.conn)
        self.assertIsNotNone(added_event)

        update_payload = {
            "description": "Updated Task Description",
            "event_type": "ImportantTask",
            # To change recurrence, one might change rule or end_date
            "recurrence_end_date": date(2024, 7, 3)
        }
        updated_event_base = self.crud.update_event(added_event.id, update_payload, conn=self.conn)
        self.assertIsNotNone(updated_event_base)
        self.assertEqual(updated_event_base.description, "Updated Task Description")
        self.assertEqual(updated_event_base.recurrence_end_date, date(2024, 7, 3))

        # Fetch and check occurrences
        events_in_range = self.crud.get_events_by_user_id(
            self.user_id, start_date=date(2024, 7, 1), end_date=date(2024, 7, 5), conn=self.conn
        )
        self.assertEqual(len(events_in_range), 3) # July 1, 2, 3
        for e in events_in_range:
            self.assertEqual(e.description, "Updated Task Description")
            self.assertEqual(e.event_type, "ImportantTask")


class TestCustomHolidaysCRUD(unittest.TestCase):
    def setUp(self):
        self.crud = CustomHolidaysCRUD()
        self.user_id = "test_user_for_calendar"
        self.conn = _get_db_connection_for_testing_with_path(TEST_DB_PATH)()
        try:
            with self.conn:
                self.conn.execute(f"DELETE FROM {self.crud.table_name}")
        except sqlite3.Error as e:
            print(f"Pre-test cleanup warning for {self.crud.table_name}: {e}")

    def test_01_add_custom_holiday(self):
        holiday_data = CustomHoliday(
            user_id=self.user_id,
            holiday_date=date(2024, 8, 15),
            description="Company Anniversary"
        )
        added_holiday = self.crud.add_custom_holiday(holiday_data, conn=self.conn)
        self.assertIsNotNone(added_holiday)
        self.assertIsNotNone(added_holiday.id)
        self.assertEqual(added_holiday.description, "Company Anniversary")

    def test_02_get_custom_holidays_by_user_id(self):
        h1 = CustomHoliday(user_id=self.user_id, holiday_date=date(2024, 9, 1), description="Team Outing")
        h2 = CustomHoliday(user_id=self.user_id, holiday_date=date(2024, 9, 15), description="Workshop Day")
        self.crud.add_custom_holiday(h1, conn=self.conn)
        self.crud.add_custom_holiday(h2, conn=self.conn)

        holidays_list = self.crud.get_custom_holidays_by_user_id(self.user_id, conn=self.conn)
        self.assertEqual(len(holidays_list), 2)

        # Test with date range
        holidays_in_range = self.crud.get_custom_holidays_by_user_id(
            self.user_id, start_date=date(2024, 9, 10), end_date=date(2024, 9, 20), conn=self.conn
        )
        self.assertEqual(len(holidays_in_range), 1)
        self.assertEqual(holidays_in_range[0].description, "Workshop Day")

    def test_03_delete_custom_holiday(self):
        holiday_data = CustomHoliday(user_id=self.user_id, holiday_date=date(2024, 10, 10), description="To Be Deleted Holiday")
        added_holiday = self.crud.add_custom_holiday(holiday_data, conn=self.conn)
        self.assertIsNotNone(added_holiday)
        self.assertIsNotNone(added_holiday.id)

        delete_success = self.crud.delete_custom_holiday(added_holiday.id, conn=self.conn)
        self.assertTrue(delete_success)

        # Verify it's gone
        deleted_holiday_check = self.crud.get_by_id(added_holiday.id, conn=self.conn)
        self.assertIsNone(deleted_holiday_check)

    def test_04_add_duplicate_custom_holiday(self):
        # Tests the UNIQUE constraint (user_id, holiday_date)
        holiday_data = CustomHoliday(
            user_id=self.user_id,
            holiday_date=date(2024, 11, 11),
            description="Remembrance Day Custom"
        )
        added_holiday1 = self.crud.add_custom_holiday(holiday_data, conn=self.conn)
        self.assertIsNotNone(added_holiday1)

        # Try adding the same holiday again for the same user
        added_holiday2 = self.crud.add_custom_holiday(holiday_data, conn=self.conn)
        self.assertIsNone(added_holiday2, "Adding a duplicate custom holiday should fail and return None.")

        # Ensure only one record exists
        holidays_list = self.crud.get_custom_holidays_by_user_id(self.user_id, start_date=date(2024,11,11), end_date=date(2024,11,11), conn=self.conn)
        self.assertEqual(len(holidays_list), 1)


if __name__ == '__main__':
    # This allows running the tests directly from this file
    # Ensure that setUpModule and tearDownModule are correctly managing the DB context for this.
    unittest.main()
