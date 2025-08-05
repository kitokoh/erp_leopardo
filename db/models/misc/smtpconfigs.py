from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class SmtpConfig(Base):
    __tablename__ = 'smtp_configs'

    smtp_config_id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String)
    smtp_server = Column(String)
    smtp_port = Column(Integer)
    username = Column(String)
    password_encrypted = Column(String)
    use_tls = Column(Boolean)
    is_default = Column(Boolean)
    sender_email_address = Column(String)
    sender_display_name = Column(String)

    def __repr__(self):
        return f"<SmtpConfig(smtp_config_id='{self.smtp_config_id}')>"
