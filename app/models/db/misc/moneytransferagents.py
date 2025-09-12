from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, false
from app.db.session_manager import Base

class MoneyTransferAgent(Base):
    __tablename__ = 'money_transfer_agents'

    agent_id = Column(String, primary_key=True)
    name = Column(String)
    agent_type = Column(String)
    phone_number = Column(String)
    email = Column(String)
    country_id = Column(String, ForeignKey('countries.country_id'))
    city_id = Column(String, ForeignKey('cities.city_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, server_default=false())
    deleted_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<MoneyTransferAgent(agent_id='{self.agent_id}')>"
