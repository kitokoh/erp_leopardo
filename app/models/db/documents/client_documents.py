from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ClientDocument(Base):
    __tablename__ = 'client_documents'

    document_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    project_id = Column(String, ForeignKey('projects.project_id'))
    order_identifier = Column(String)
    document_name = Column(String)
    file_name_on_disk = Column(String)
    file_path_relative = Column(String)
    document_type_generated = Column(String)
    source_template_id = Column(Integer, ForeignKey('templates.template_id'))
    version_tag = Column(String)
    notes = Column(Text)
    footer_notes = Column(Text)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    parent_document_id = Column(String, ForeignKey('client_documents.document_id'))
    is_latest_version = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    client = relationship("Client")
    project = relationship("Project")
    source_template = relationship("Template")
    creator = relationship("User")
    parent_document = relationship("ClientDocument", remote_side=[document_id])

    def __repr__(self):
        return f"<ClientDocument(document_id='{self.document_id}', document_name='{self.document_name}')>"
