from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Usersessiontokens(Base):
    __tablename__ = 'user_session_tokens'
    token_id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False, ForeignKey('users.user_id'))

    token_hash = Column(Text, nullable=False, unique=True)
    device_identifier = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime)
    last_used_at = Column(DateTime)


    def __repr__(self):
        return f'<Usersessiontokens token_id={self.token_id}>'
    user_rel = relationship('Users')
