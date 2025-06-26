# Database models for the calculator module

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base # Using modern declarative_base
import datetime

# Attempt to import Base from the project's existing DB setup
# This path might need adjustment based on your project structure.
# If 'db.connection.Base' is standard, this should work.
# Otherwise, we might need to define a local Base or get it passed.
try:
    from db.connection import Base # Assuming your project uses a Base like this
except ImportError:
    print("WARNING (calculator.models): Could not import Base from db.connection. Falling back to local Base for calculator history.")
    Base = declarative_base()


class CalculationHistory(Base):
    __tablename__ = "calculation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    calculator_type = Column(String, index=True, nullable=False)
    expression = Column(String, nullable=True) # Expression might be long or not applicable (e.g. cylinder calc summary)
    result = Column(String, nullable=True)     # Result might also be a summary
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return (f"<CalculationHistory(id={self.id}, user_id='{self.user_id}', "
                f"type='{self.calculator_type}', timestamp='{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}')>")

# To ensure this table is created if it doesn't exist,
# this model needs to be imported somewhere before `Base.metadata.create_all(engine)` is called
# in your main database initialization script (e.g., in `db/init_schema.py` or `main.py`).
# Example in your db/init_schema.py or similar:
#
# from db.connection import engine, Base
# from calculator.models import CalculationHistory # Ensure this import
# ... other model imports
#
# def init_db():
#     Base.metadata.create_all(bind=engine)
#
# if __name__ == "__main__":
#     init_db()

# If running this file directly for testing (not typical for models):
if __name__ == '__main__':
    # This is just for a quick check if the model definition is okay.
    # It does not interact with a real database here.
    entry = CalculationHistory(
        user_id="test_user",
        calculator_type="Commercial",
        expression="10+5",
        result="15"
    )
    print(entry)
    # To test with a real in-memory DB:
    # from sqlalchemy import create_engine
    # from sqlalchemy.orm import sessionmaker
    # engine = create_engine('sqlite:///:memory:')
    # Base.metadata.create_all(engine)
    # SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # db = SessionLocalTest()
    # db.add(entry)
    # db.commit()
    # print(db.query(CalculationHistory).first())
    # db.close()
