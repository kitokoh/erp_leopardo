from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Activitylog(Base):
    __tablename__ = 'activity_log'
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey('users.user_id'))

    action_type = Column(Text, nullable=False)
    details = Column(Text)
    related_entity_type = Column(Text)
    related_entity_id = Column(Text)
    related_client_id = Column(Text, ForeignKey('clients.client_id'))

    ip_address = Column(Text)
    user_agent = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Activitylog log_id={self.log_id}>'
    user_rel = relationship('Users')
    client_rel = relationship('Clients')
