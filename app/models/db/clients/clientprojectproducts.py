from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ClientProjectProduct(Base):
    __tablename__ = 'client_project_products'

    client_project_product_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Text, ForeignKey('clients.client_id'), nullable=False)
    project_id = Column(Text, ForeignKey('projects.project_id'))
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    added_by_user_id = Column(Text, ForeignKey('users.user_id'))

    quantity = Column(Integer, nullable=False)
    unit_price_override = Column(REAL)
    total_price_calculated = Column(REAL)
    serial_number = Column(Text)
    purchase_confirmed_at = Column(DateTime(timezone=True))
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    client_specific_product_name = Column(Text)
    line_description = Column(Text)
    line_weight = Column(REAL)
    line_dimensions_notes = Column(Text)

    # Relationships
    client = relationship('Client') # Needs back_populates in Client
    project = relationship('Project') # Needs back_populates in Project
    product = relationship('Product') # Needs back_populates in Product
    added_by = relationship('User') # Needs back_populates in User

    def __repr__(self):
        return f'<ClientProjectProduct id={self.client_project_product_id}>'
