from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from db.connection import Base

class Client(Base):
    __tablename__ = 'Clients'

    client_id = Column(String, primary_key=True)
    client_name = Column(String, nullable=False)
    company_name = Column(String)
    primary_need_description = Column(Text)
    project_identifier = Column(String)
    country_id = Column(Integer, ForeignKey('Countries.country_id'))
    city_id = Column(Integer, ForeignKey('Cities.city_id'))
    default_base_folder_path = Column(String)
    status_id = Column(Integer, ForeignKey('StatusSettings.status_id'))
    selected_languages = Column(String)
    price = Column(Float, default=0)
    notes = Column(Text)
    category = Column(String)
    lead_source = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    default_template_id = Column(Integer, ForeignKey('Templates.template_id'))
    distributor_specific_info = Column(Text)
