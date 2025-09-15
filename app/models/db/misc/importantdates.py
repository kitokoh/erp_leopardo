from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ImportantDate(Base):
    __tablename__ = 'important_dates'

    important_date_id = Column(Integer, primary_key=True, autoincrement=True)
    date_name = Column(String)
    date_value = Column(Date)
    is_recurring_annually = Column(Boolean)
    language_code = Column(String)
    email_template_id = Column(Integer, ForeignKey('templates.template_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<ImportantDate(important_date_id='{self.important_date_id}')>"
