from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import select, update, delete, func, or_, and_
from ...models import (
    Product,
    ProductDimension,
    ProductEquivalency,
    ProductMediaLink
)
from ...connection import get_db_connection
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

class ProductsCRUD:
    """
    Manages CRUD operations for products using SQLAlchemy ORM.
    """

    def add_product(self, product_data: dict, db: Session) -> Product:
        """Adds a new product to the database."""
        new_product = Product(**product_data)
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    def get_product_by_id(self, product_id: int, db: Session, include_deleted: bool = False) -> Optional[Product]:
        """Fetches a single product by its ID."""
        query = db.query(Product).options(
            subqueryload(Product.media_links),
            subqueryload(Product.dimensions),
            subqueryload(Product.equivalencies_a),
            subqueryload(Product.equivalencies_b)
        ).filter(Product.product_id == product_id)

        if not include_deleted:
            query = query.filter(Product.is_deleted == False)

        return query.first()

    def get_all_products(self, db: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[Product]:
        """Retrieves all products with pagination."""
        query = db.query(Product)
        if not include_deleted:
            query = query.filter(Product.is_deleted == False)
        return query.offset(skip).limit(limit).all()

    def update_product(self, product_id: int, update_data: Dict[str, Any], db: Session) -> Optional[Product]:
        """Updates a product's information."""
        if not update_data:
            return self.get_product_by_id(product_id, db)

        update_data['updated_at'] = datetime.utcnow()
        db.query(Product).filter(Product.product_id == product_id).update(update_data)
        db.commit()
        return self.get_product_by_id(product_id, db)

    def delete_product(self, product_id: int, db: Session) -> bool:
        """Soft deletes a product."""
        result = db.query(Product).filter(Product.product_id == product_id).update({
            'is_deleted': True,
            'is_active': False,
            'deleted_at': datetime.utcnow()
        })
        db.commit()
        return result > 0

    def add_product_dimension(self, product_id: int, dimension_data: dict, db: Session) -> ProductDimension:
        """Adds or updates dimensions for a product."""
        dimension = db.query(ProductDimension).filter(ProductDimension.product_id == product_id).first()
        if dimension:
            for key, value in dimension_data.items():
                setattr(dimension, key, value)
            dimension.updated_at = datetime.utcnow()
        else:
            dimension_data['product_id'] = product_id
            dimension = ProductDimension(**dimension_data)
            db.add(dimension)

        db.commit()
        db.refresh(dimension)
        return dimension

    def get_product_dimension(self, product_id: int, db: Session) -> Optional[ProductDimension]:
        """Retrieves dimensions for a product."""
        return db.query(ProductDimension).filter(ProductDimension.product_id == product_id).first()

    def add_product_equivalence(self, product_id_a: int, product_id_b: int, db: Session) -> ProductEquivalency:
        """Adds an equivalence link between two products."""
        # Normalize order to prevent duplicates
        id_a, id_b = min(product_id_a, product_id_b), max(product_id_a, product_id_b)

        existing_equivalence = db.query(ProductEquivalence).filter_by(product_id_a=id_a, product_id_b=id_b).first()
        if existing_equivalence:
            return existing_equivalence

        new_equivalence = ProductEquivalence(product_id_a=id_a, product_id_b=id_b)
        db.add(new_equivalence)
        db.commit()
        db.refresh(new_equivalence)
        return new_equivalence

    def get_equivalent_products(self, product_id: int, db: Session) -> List[Product]:
        """Retrieves all products equivalent to a given product."""
        equivalences = db.query(ProductEquivalence).filter(
            (ProductEquivalence.product_id_a == product_id) | (ProductEquivalence.product_id_b == product_id)
        ).all()

        equivalent_ids = set()
        for eq in equivalences:
            if eq.product_id_a != product_id:
                equivalent_ids.add(eq.product_id_a)
            if eq.product_id_b != product_id:
                equivalent_ids.add(eq.product_id_b)

        if not equivalent_ids:
            return []

        return db.query(Product).filter(Product.product_id.in_(equivalent_ids), Product.is_deleted == False).all()


products_crud = ProductsCRUD()
