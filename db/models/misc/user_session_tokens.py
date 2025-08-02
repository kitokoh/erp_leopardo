from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class UserSessionToken(Base):
    __tablename__ = 'user_session_tokens'

    token_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    token_hash = Column(String)
    device_identifier = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime)
    last_used_at = Column(DateTime)

    def __repr__(self):
        return f"<UserSessionToken(token_id='{self.token_id}')>"
