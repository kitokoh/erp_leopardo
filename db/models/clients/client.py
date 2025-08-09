from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, false
from db.connection import Base

class Client(Base):
    __tablename__ = 'clients'

    client_id = Column(String, primary_key=True)
    client_name = Column(String, nullable=False)
    company_name = Column(String)
    primary_need_description = Column(Text)
    project_identifier = Column(String)
    country_id = Column(Integer, ForeignKey('countries.country_id'))
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    default_base_folder_path = Column(String, unique=True)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    selected_languages = Column(String)
    price = Column(Float, server_default='0')
    notes = Column(Text)
    category = Column(String)
    distributor_specific_info = Column(Text)
    default_template_id = Column(Integer, ForeignKey('templates.template_id'))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    is_deleted = Column(Boolean, server_default=false(), nullable=False)
    deleted_at = Column(DateTime)
    lead_source = Column(String)

    creator = relationship("User")
    country = relationship("Country")
    city = relationship("City")
    status = relationship("StatusSetting")
    # default_template = relationship("Template")
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<Client(client_id='{self.client_id}', client_name='{self.client_name}')>"
