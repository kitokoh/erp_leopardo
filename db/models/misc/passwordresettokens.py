from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Passwordresettokens(Base):
    __tablename__ = 'password_reset_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False, ForeignKey('users.user_id'))

    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime)
    used_at = Column(DateTime)


    def __repr__(self):
        return f'<Passwordresettokens id={self.id}>'
    user_rel = relationship('Users')
