from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Smtpconfigs(Base):
    __tablename__ = 'smtp_configs'
    smtp_config_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    smtp_server = Column(Text, nullable=False)
    password_encrypted = Column(Text)
    sender_email_address = Column(Text, nullable=False)


    def __repr__(self):
        return f'<Smtpconfigs smtp_config_id={self.smtp_config_id}>'
