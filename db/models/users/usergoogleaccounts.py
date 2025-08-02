from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Usergoogleaccounts(Base):
    __tablename__ = 'user_google_accounts'
    user_google_account_id = Column(Text, primary_key=True, nullable=False)
    google_account_id = Column(Text, nullable=False, unique=True)
    access_token = Column(Text)
    last_sync_initiated_at = Column(DateTime)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Usergoogleaccounts user_google_account_id={self.user_google_account_id}>'
