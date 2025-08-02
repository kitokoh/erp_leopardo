from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.connection import Base

class Country(Base):
    __tablename__ = 'countries'

    country_id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Country(country_id={self.country_id}, country_name='{self.country_name}')>"
