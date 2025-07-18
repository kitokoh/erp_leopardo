from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.connection import Base

class Country(Base):
    __tablename__ = 'Countries'

    country_id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class City(Base):
    __tablename__ = 'Cities'

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, ForeignKey('Countries.country_id'), nullable=False)
    city_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
