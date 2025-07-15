from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.connection import Base

class ClientDocuments(Base):
    __tablename__ = 'ClientDocuments'

    document_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    project_id = Column(String)
    order_identifier = Column(String)
    document_name = Column(String)
    file_name_on_disk = Column(String)
    file_path_relative = Column(String)
    document_type_generated = Column(String)
    source_template_id = Column(Integer)
    version_tag = Column(String)
    notes = Column(Text)
    footer_notes = Column(Text)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    parent_document_id = Column(String)
    is_latest_version = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
