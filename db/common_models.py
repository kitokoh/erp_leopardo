from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship # Not strictly needed for this specific model to solve the FK issue

from db.connection import Base # Shared Base

class Products(Base):
    __tablename__ = "Products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    product_code = Column(String, unique=True, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    language_code = Column(String, default='fr', nullable=True)
    base_unit_price = Column(Numeric(precision=18, scale=2), nullable=False)
    unit_of_measure = Column(String, nullable=True)
    weight = Column(Numeric(precision=10, scale=2), nullable=True)
    dimensions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(String, ForeignKey('Users.user_id', name='fk_products_created_by_user_id', ondelete='SET NULL'), nullable=True)

    __table_args__ = (
        UniqueConstraint('product_name', 'language_code', name='uq_products_product_name_language_code'),
    )

    def __repr__(self):
        return f"<Products(product_id={self.product_id}, product_name='{self.product_name}')>"

# Note on ForeignKey to Users.user_id:
# The 'Users' table is created via raw SQL in `db/init_schema.py`.
# For SQLAlchemy to fully manage and validate this relationship during `metadata.create_all()`,
# the 'Users' table would ideally also be defined as an SQLAlchemy model using the same `Base`.
# However, the immediate error is about `Products` table not being found for the FK from `restaurant_lignes_commande`.
# Defining this `Products` model should resolve that specific error.
# The `ondelete='SET NULL'` matches the raw SQL definition.
# Naming conventions for constraints (fk_products_created_by_user_id, uq_products_product_name_language_code)
# are made slightly more explicit.
