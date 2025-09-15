from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class UserSessionTokens(Base):
    __tablename__ = 'user_session_tokens'
    token_id = Column(Text, primary_key=True)
    user_id = Column(Text, ForeignKey('users.user_id'), nullable=False)
    token_hash = Column(Text, nullable=False, unique=True)
    device_identifier = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime)
    last_used_at = Column(DateTime)

    user_rel = relationship('User')

    def __repr__(self):
        return f'<Usersessiontokens token_id={self.token_id}>'
