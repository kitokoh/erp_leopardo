from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey('users.user_id'), nullable=False)
    token_hash = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime)
    used_at = Column(DateTime)

    def __repr__(self):
        return f"<PasswordResetToken(id='{self.id}')>"
