from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class MoneyTransferAgent(Base):
    __tablename__ = 'money_transfer_agents'

    agent_id = Column(String, primary_key=True)
    name = Column(String)
    agent_type = Column(String)
    phone_number = Column(String)
    email = Column(String)
    country_id = Column(String, ForeignKey('countries.country_id'))
    city_id = Column(String, ForeignKey('cities.city_id'))
    created_at = Column(String)
    updated_at = Column(String)
    is_deleted = Column(Integer)
    deleted_at = Column(String)

    def __repr__(self):
        return f"<MoneyTransferAgent(agent_id='{self.agent_id}')>"
