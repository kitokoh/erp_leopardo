from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class UserGoogleAccounts(Base):
    __tablename__ = 'user_google_accounts'
    user_google_account_id = Column(Text, primary_key=True, nullable=False)
    user_id = Column(Text, ForeignKey('users.user_id'), nullable=False, index=True)
    google_account_id = Column(Text, nullable=False, unique=True)
    access_token = Column(Text)
    last_sync_initiated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship('User', back_populates='google_accounts')

    def __repr__(self):
        return f'<UserGoogleAccounts user_id={self.user_id}>'
