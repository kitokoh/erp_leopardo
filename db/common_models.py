from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship # Not strictly needed for this specific model to solve the FK issue

from db.connection import Base # Shared Base

class Products(Base):
    __tablename__ = "Products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    product_code = Column(String, unique=True, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True) # Simple index via index=True
    language_code = Column(String, default='fr', nullable=True)
    base_unit_price = Column(Numeric(precision=18, scale=2), nullable=False)
    unit_of_measure = Column(String, nullable=True)
    weight = Column(Numeric(precision=10, scale=2), nullable=True)
    dimensions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True) # Simple index via index=True
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(String, ForeignKey('users.user_id', name='fk_products_created_by_user_id', ondelete='SET NULL'), nullable=True) # Changed Users.user_id to users.user_id

    __table_args__ = (
        UniqueConstraint('product_name', 'language_code', name='uq_products_product_name_language_code'),
    )

    def __repr__(self):
        return f"<Products(product_id={self.product_id}, product_name='{self.product_name}')>"


class Role(Base):
    __tablename__ = "Roles" # Matches the table name from init_schema.py

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # If you need to access users associated with a role from the Role object:
    # users = relationship("User", back_populates="role") # Assumes "User" model is defined and has a "role" backref

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"

# Ensure that alembic/env.py imports db.common_models to pick up this Role model.
# The raw SQL creation of 'Roles' table in db/init_schema.py should be removed.
# The Alembic migration 26cc1deb3763_create_initial_tables.py should be updated to create 'Roles' table.

