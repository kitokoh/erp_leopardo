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
    created_by_user_id = Column(String, ForeignKey('Users.user_id', name='fk_products_created_by_user_id', ondelete='SET NULL'), nullable=True)

    __table_args__ = (
        UniqueConstraint('product_name', 'language_code', name='uq_products_product_name_language_code'),
        # Index('idx_products_category', 'category'), # Using index=True on column def is preferred for single columns
        # Index('idx_products_is_active', 'is_active'), # Using index=True on column def is preferred for single columns
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

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Text, primary_key=True) # TEXT in SQLite often implies string UUIDs
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    role_id = Column(Integer, ForeignKey('Roles.role_id'), nullable=False) # Assumes Roles table is created by raw SQL or another model
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False) # Matching raw SQL which used INTEGER
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Biometric fields
    is_fingerprint_auth_enabled = Column(Boolean, default=False, nullable=True)
    fingerprint_template_id = Column(Text, nullable=True)
    is_face_auth_enabled = Column(Boolean, default=False, nullable=True)
    face_template_id = Column(Text, nullable=True)
    is_voice_auth_enabled = Column(Boolean, default=False, nullable=True)
    voice_profile_id = Column(Text, nullable=True)

    # __table_args__ can include UniqueConstraint if needed for other combinations, or Indexes.
    # e.g., Index('idx_users_email', 'email', unique=True) is handled by unique=True on column.
    # Index('idx_users_username', 'username', unique=True) is handled by unique=True on column.

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"
