from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.db.products.product import Product
from app.services.api.models import ProductCreate


class ProductsCRUD:
    def create_product(self, db: Session, product: ProductCreate) -> Product:
        """
        Creates a new product in the database.
        """
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product

    def get_product_by_name(self, db: Session, product_name: str) -> Optional[Product]:
        """
        Fetches a single product by its name.
        """
        return db.query(Product).filter(Product.product_name == product_name, Product.is_deleted == False).first()

    def get_all_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Retrieves all products with pagination.
        """
        return db.query(Product).filter(Product.is_deleted == False).offset(skip).limit(limit).all()

    def update_product(self, db: Session, product_id: int, product_data: dict) -> Optional[Product]:
        """
        Updates a product's information.
        """
        db_product = db.query(Product).filter(Product.product_id == product_id, Product.is_deleted == False).first()
        if db_product:
            for key, value in product_data.items():
                setattr(db_product, key, value)
            db.commit()
            db.refresh(db_product)
        return db_product

    def delete_product(self, db: Session, product_id: int) -> Optional[Product]:
        """
        Soft deletes a product.
        """
        db_product = db.query(Product).filter(Product.product_id == product_id).first()
        if db_product:
            db_product.is_deleted = True
            db_product.is_active = False
            db.commit()
            db.refresh(db_product)
        return db_product


products_crud = ProductsCRUD()
