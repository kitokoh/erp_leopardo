from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Importantdates(Base):
    __tablename__ = 'important_dates'
    important_date_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    date_value = Column(Date, nullable=False)
    language_code = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Importantdates important_date_id={self.important_date_id}>'
    template_rel = relationship('Templates')
