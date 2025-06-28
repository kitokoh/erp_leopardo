from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class CompanyCalendarSettings(BaseModel):
    id: Optional[int] = None
    user_id: str # or company_id, to link to a user or company
    business_type: str # B2B, B2C, Both
    activity_category: str
    country_iso: str = Field(..., description="ISO 3166-1 alpha-2 country code, e.g., 'US', 'FR'")
    region: Optional[str] = Field(None, description="Subdivision of the country, e.g., state, province. Varies by country.")

    class Config:
        from_attributes = True

class UserCalendarEvent(BaseModel):
    id: Optional[int] = None
    user_id: str
    event_date: date
    event_type: str # Holiday, RemoteWork, WorkDay, OtherPersonal
    description: Optional[str] = None

    class Config:
        from_attributes = True

# Example for SQLAlchemy models (to be defined in db/models.py or similar if following project structure)
# from sqlalchemy import Column, Integer, String, Date, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship

# Base = declarative_base()

# class DBCompanyCalendarSettings(Base):
#     __tablename__ = "company_calendar_settings"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(String, index=True, nullable=False) # Assuming user_id is a string UUID
#     business_type = Column(String)
#     activity_category = Column(String)
#     country_iso = Column(String, nullable=False)
#     region = Column(String, nullable=True)

# class DBUserCalendarEvent(Base):
#     __tablename__ = "user_calendar_events"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(String, index=True, nullable=False) # Assuming user_id is a string UUID
#     event_date = Column(Date, nullable=False)
#     event_type = Column(String, nullable=False)
#     description = Column(String, nullable=True)

# Note: Actual SQLAlchemy model definitions should go into the central db/models.py
# or a new db/calendar_models.py and be imported by db/init_schema.py
# For now, these Pydantic models are for API request/response validation and internal logic.
