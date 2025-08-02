from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Clientprojectproducts(Base):
    __tablename__ = 'client_project_products'
    client_project_product_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Text, nullable=False, ForeignKey('clients.client_id'))

    project_id = Column(Text, ForeignKey('projects.project_id'))

    product_id = Column(Integer, nullable=False, ForeignKey('products.product_id'))

    quantity = Column(Integer, nullable=False)
    unit_price_override = Column(REAL)
    total_price_calculated = Column(REAL)
    serial_number = Column(Text)
    purchase_confirmed_at = Column(DateTime)
    added_at = Column(DateTime)
    added_by_user_id = Column(Text, ForeignKey('users.user_id'))

    client_specific_product_name = Column(Text)
    line_description = Column(Text)
    line_weight = Column(REAL)
    line_dimensions_notes = Column(Text)


    def __repr__(self):
        return f'<Clientprojectproducts client_project_product_id={self.client_project_product_id}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    product_rel = relationship('Products')
    user_rel = relationship('Users')
