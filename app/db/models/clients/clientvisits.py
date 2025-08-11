from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Clientvisits(Base):
    __tablename__ = 'client_visits'
    visit_id = Column(Text, primary_key=True)
    client_id = Column(Text, ForeignKey('clients.client_id'), nullable=False)
    visit_date = Column(Text, nullable=False)
    visit_type = Column(Text)
    visit_purpose = Column(Text)
    notes_impressions = Column(Text)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Clientvisits visit_id={self.visit_id}>'
    client_rel = relationship('Client')
    user_rel = relationship('User')
