from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Country(Base):
    __tablename__ = 'countries'

    country_id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String, nullable=False, unique=True)
    iso_a2_code = Column(String(2), nullable=True)  # Add the new column
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<Country(country_id={self.country_id}, country_name='{self.country_name}', iso_a2_code='{self.iso_a2_code}')>"
