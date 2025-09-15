from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base
from .country import Country

class City(Base):
    __tablename__ = 'cities'

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, ForeignKey('countries.country_id'), nullable=False)
    city_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    country = relationship("Country")
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<City(city_id={self.city_id}, city_name='{self.city_name}')>"
