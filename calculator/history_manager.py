# Manages the history of calculations, with database persistence.

import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc # For ordering results

# Attempt to import the CalculationHistory model
try:
    from .models import CalculationHistory
except ImportError:
    # This might happen if running standalone or if models.py has issues
    # For robust error handling, you might log this or raise a specific error.
    print("WARNING (calculator.history_manager): Could not import CalculationHistory model. DB features will fail.")
    CalculationHistory = None

class HistoryManager:
    def __init__(self, db_session_factory, max_display_items=100):
        """
        Initializes the HistoryManager.
        :param db_session_factory: A factory function that provides a SQLAlchemy session (e.g., SessionLocal).
        :param max_display_items: Max items to retrieve from DB for display by default.
        """
        self.db_session_factory = db_session_factory
        self.max_display_items = max_display_items
        # In-memory list is now primarily a cache or not used if always fetching from DB.
        # For simplicity in this phase, we'll fetch from DB each time get_history is called.

    def _get_db(self) -> Session | None:
        """
        Provides a database session using the configured session factory.
        Returns:
            sqlalchemy.orm.Session | None: A SQLAlchemy session, or None if factory is not set.
        """
        if not self.db_session_factory:
            # print("ERROR (HistoryManager): Database session factory not configured.") # Or log this
            return None
        return self.db_session_factory()

    def add_entry(self, calculator_type: str, expression: str, result: str, user_id: str):
        """
        Adds a new calculation entry to the history in the database.
        Args:
            calculator_type (str): The type of calculator used (e.g., "Commercial", "Scientific").
            expression (str): The mathematical expression or input summary.
            result (str): The result of the calculation or output summary.
            user_id (str): The ID of the user who performed the calculation.
        """
        if CalculationHistory is None:
            print("ERROR (HistoryManager): CalculationHistory model not available. Cannot add entry to DB.")
            return

        db: Session = self._get_db()
        if not db:
            return

        try:
            db_entry = CalculationHistory(
                user_id=str(user_id), # Ensure string
                calculator_type=str(calculator_type),
                expression=str(expression),
                result=str(result),
                timestamp=datetime.datetime.utcnow()
            )
            db.add(db_entry)
            db.commit()
            # db.refresh(db_entry) # Optional: if you need the ID of the new entry immediately
            # print(f"History added to DB: {db_entry}") # For debugging
        except Exception as e:
            print(f"ERROR (HistoryManager): Failed to add history entry to DB: {e}")
            db.rollback()
        finally:
            db.close()

    def get_history(self, user_id: str, limit: int = None) -> list:
        """
        Returns the calculation history for a given user_id from the database.
        :param user_id: The ID of the user whose history is to be fetched.
        :param limit: Max number of items to return. Defaults to self.max_display_items.
        :return: A list of history entry dictionaries.
        """
        if CalculationHistory is None:
            print("ERROR (HistoryManager): CalculationHistory model not available. Cannot get history from DB.")
            return []

        db: Session = self._get_db()
        if not db:
            return []

        if limit is None:
            limit = self.max_display_items

        history_data = []
        try:
            entries = db.query(CalculationHistory)\
                        .filter(CalculationHistory.user_id == str(user_id))\
                        .order_by(desc(CalculationHistory.timestamp))\
                        .limit(limit)\
                        .all()

            for entry in entries:
                history_data.append({
                    "user_id": entry.user_id,
                    "calculator_type": entry.calculator_type,
                    "expression": entry.expression,
                    "result": entry.result,
                    "timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") # Format for display
                })
        except Exception as e:
            print(f"ERROR (HistoryManager): Failed to get history from DB for user {user_id}: {e}")
        finally:
            db.close()
        return history_data # Returns newest first due to order_by desc

    def clear_history(self, user_id: str) -> bool:
        """
        Clears all history entries for a given user_id from the database.
        Args:
            user_id (str): The ID of the user whose history is to be cleared.
        Returns:
            bool: True if successful or no user-specific entries to delete, False on error.
        """
        if CalculationHistory is None:
            print("ERROR (HistoryManager): CalculationHistory model not available. Cannot clear history in DB.")
            return False

        db: Session = self._get_db()
        if not db:
            return False

        try:
            num_deleted = db.query(CalculationHistory)\
                            .filter(CalculationHistory.user_id == str(user_id))\
                            .delete(synchronize_session=False)
            db.commit()
            print(f"INFO (HistoryManager): Cleared {num_deleted} history entries for user {user_id} from DB.")
            return True
        except Exception as e:
            print(f"ERROR (HistoryManager): Failed to clear history from DB for user {user_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

if __name__ == '__main__':
    # --- Example Usage with a mock SQLAlchemy session ---
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base as CalculatorBase # Use the Base from calculator.models

    print("Testing HistoryManager with in-memory SQLite DB...")

    # Setup in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    CalculatorBase.metadata.create_all(engine) # Create the calculation_history table

    # Create a session factory (like SessionLocal in a FastAPI app)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Instantiate HistoryManager with the session factory
    history_mgr = HistoryManager(db_session_factory=TestSessionLocal)

    # Test data
    user1 = "user_alpha"
    user2 = "user_beta"

    # Add entries
    print(f"\nAdding entries for {user1}...")
    history_mgr.add_entry("Commercial", "10+5", "15", user_id=user1)
    history_mgr.add_entry("Scientific", "math.sqrt(16)", "4.0", user_id=user1)

    print(f"\nAdding entries for {user2}...")
    history_mgr.add_entry("Cylindre Performances", "D:50,S:100,P:100", "Fp:19634N", user_id=user2)

    # Get history for user1
    print(f"\nHistory for {user1}:")
    user1_history = history_mgr.get_history(user_id=user1)
    if user1_history:
        for item in user1_history:
            print(item)
    else:
        print("No history found for user1.")

    # Get history for user2
    print(f"\nHistory for {user2}:")
    user2_history = history_mgr.get_history(user_id=user2)
    if user2_history:
        for item in user2_history:
            print(item)
    else:
        print("No history found for user2.")

    # Clear history for user1
    print(f"\nClearing history for {user1}...")
    if history_mgr.clear_history(user_id=user1):
        print(f"History for {user1} cleared.")
        user1_history_after_clear = history_mgr.get_history(user_id=user1)
        if not user1_history_after_clear:
            print("Verified: No history for user1 after clearing.")
        else:
            print("Error: History for user1 still present after clearing.")
            for item in user1_history_after_clear: print(item)

    # Check history for user2 again (should be unaffected)
    print(f"\nHistory for {user2} (should be unaffected):")
    user2_history_final = history_mgr.get_history(user_id=user2)
    if user2_history_final:
        for item in user2_history_final:
            print(item)
    else:
        print(f"Error: History for {user2} was affected by clearing {user1}'s history.")

    print("\nTest complete.")
