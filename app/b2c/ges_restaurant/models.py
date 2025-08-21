from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import sys
import os

# Adjust path to import from the root 'db' module for Base and engine configuration
# This assumes 'b2c' is at the same level as 'db', 'gui', etc.
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# if PROJECT_ROOT not in sys.path:
#    sys.path.insert(0, PROJECT_ROOT)

# Instead of trying to re-import Base from db.connection,
# we should use the application's existing Base.
# For now, let's define a new Base for this module if it's meant to be semi-independent
# or potentially part of a different DB.
# However, the request implies integration, so ideally we would use the existing Base.
# This will require careful handling of imports when integrating with the main app's DB setup.

# For now, to make this file self-contained for definition:
# from db.connection import Base # This would be the ideal if paths are set up correctly for modules
# If that fails, we define a local Base and figure out integration later.
try:
    # Attempt to import the existing Base from the application's db.connection
    # This requires that the Python path is correctly configured when this module is loaded.
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..')) # Add project root
    from app.db.connection import Base
    from app.models.db.products.product import Product as Products
    print("Successfully imported Base from db.connection in b2c.ges_restaurant.models")
except ImportError:
    print("Failed to import Base from db.connection in b2c.ges_restaurant.models. Using a local Base.")
    Base = declarative_base()


class RestaurantTable(Base):
    __tablename__ = 'restaurant_tables'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero_table = Column(String(50), unique=True, nullable=False, index=True)
    capacite = Column(Integer, default=4, nullable=False)
    statut = Column(String(20), nullable=False, default='libre', index=True) # libre, occupee, reservee, a_nettoyer
    emplacement = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    commandes = relationship("RestaurantCommande", back_populates="table")

    def __repr__(self):
        return f"<RestaurantTable(id={self.id}, numero='{self.numero_table}', statut='{self.statut}')>"

class RestaurantCommande(Base):
    __tablename__ = 'restaurant_commandes'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey('restaurant_tables.id'), nullable=False)

    date_heure_creation = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_heure_cloture = Column(DateTime(timezone=True), nullable=True)

    statut = Column(String(20), nullable=False, default='en_cours', index=True) # en_cours, servie, payee, annulee

    total_commande_ht = Column(Float, nullable=True, default=0.0)
    total_commande_ttc = Column(Float, nullable=True, default=0.0) # Assuming TTC might be stored, or calculated on the fly
    # If you have VAT rates, you might store vat_rate_percentage and vat_amount

    notes_client = Column(Text, nullable=True)
    nom_client_facultatif = Column(String(100), nullable=True) # As requested, optional client name

    # Assuming user_id of the staff who created/managed the order might be useful
    # created_by_user_id = Column(Integer, ForeignKey('Users.user_id'), nullable=True) # Link to existing Users table

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    table = relationship("RestaurantTable", back_populates="commandes")
    lignes_commande = relationship("RestaurantLigneCommande", back_populates="commande", cascade="all, delete-orphan")
    paiements = relationship("RestaurantPaiement", back_populates="commande", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RestaurantCommande(id={self.id}, table_id={self.table_id}, statut='{self.statut}', total_ttc='{self.total_commande_ttc}')>"

class RestaurantLigneCommande(Base):
    __tablename__ = 'restaurant_lignes_commande'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    commande_id = Column(Integer, ForeignKey('restaurant_commandes.id'), nullable=False)
    # Assuming your existing product table is named 'Products' and has 'product_id'
    # If the table name or pk is different, adjust ForeignKey('your_product_table_name.your_product_pk_column')
    produit_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)

    quantite = Column(Integer, nullable=False, default=1)
    __table_args__ = {'extend_existing': True}
    prix_unitaire_ht_commande = Column(Float, nullable=False) # Price at the time of order
    prix_total_ht_ligne = Column(Float, nullable=False) # Should be calculated: quantite * prix_unitaire_ht_commande

    notes = Column(Text, nullable=True) # e.g., "extra cheese", "no onions"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    commande = relationship("RestaurantCommande", back_populates="lignes_commande")
    # produit = relationship("Product", back_populates="lignes_commande_restaurant") # If Product model has this relationship

    def __repr__(self):
        return f"<RestaurantLigneCommande(id={self.id}, commande_id={self.commande_id}, produit_id={self.produit_id}, qte={self.quantite})>"

class RestaurantPaiement(Base):
    __tablename__ = 'restaurant_paiements'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    commande_id = Column(Integer, ForeignKey('restaurant_commandes.id'), nullable=False)

    date_heure_paiement = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    montant_paye = Column(Float, nullable=False)
    methode_paiement = Column(String(50), nullable=False) # e.g., 'especes', 'carte_bancaire', 'cheque_restaurant', 'en_compte'
    reference_transaction = Column(String(100), nullable=True) # For card transaction IDs, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    commande = relationship("RestaurantCommande", back_populates="paiements")

    def __repr__(self):
        return f"<RestaurantPaiement(id={self.id}, commande_id={self.commande_id}, montant='{self.montant_paye}', methode='{self.methode_paiement}')>"

# To integrate these models with the main application's database,
# ensure that the Base used here is the same Base instance used by the rest of the application.
# The main application should then include these models when creating the database schema,
# typically by calling Base.metadata.create_all(engine) where `engine` is the SQLAlchemy engine.

# Example of how to get engine and create tables (this part would typically be in main app setup)
# from db.connection import get_engine
#
# def create_restaurant_tables():
#     engine = get_engine() # Get the app's main engine
#     Base.metadata.create_all(bind=engine)
#
# if __name__ == '__main__':
#     # This is for standalone testing/creation if needed
#     # In production, the main app's db setup (e.g., in db.init_schema or app_setup)
#     # should discover and create these tables.
#     test_engine = create_engine('sqlite:///./test_restaurant.db')
#     Base.metadata.create_all(bind=test_engine)
#     print("Restaurant tables created in test_restaurant.db")

    # Note: The ForeignKey to 'Products.product_id' assumes that your existing
    # products table is named 'Products' and its primary key is 'product_id'.
    # Adjust this if your existing schema is different.
    # For example, if it's 'products.id', change to ForeignKey('products.id').
    # This also means that the 'Product' class (SQLAlchemy model for products)
    # must be defined and known to the Base metadata when tables are created.
    # If 'Products' table is managed by a different Base or in a different way,
    # this direct ForeignKey might need to be handled differently (e.g. no ORM relationship, just store ID).
    # For tight integration, it's best if all models share the same Base.
    # The `from db.connection import Base` tries to achieve this.
    # If it fails, the local Base will mean these tables are isolated unless explicitly merged.
    # The print statements for Base import success/failure will indicate current state.
    # The print statement `Successfully imported Base from db.connection in b2c.ges_restaurant.models`
    # or `Failed to import Base from db.connection...` will show up in console during execution.
    # For this task, I'm assuming the import will succeed if the overall project structure allows it.
    # If `db.connection.Base` is not found, the `except ImportError` block will execute,
    # defining a new `Base`. This would require `create_restaurant_tables()` to be called with
    # an engine that knows about this specific `Base`.
    # The ideal scenario is that `main.py` or `app_setup.py` ensures that `db.connection.Base`
    # is the single source of truth for all declarative models in the application.
    # This usually involves importing all model modules (like this one) before `Base.metadata.create_all(engine)` is called.
    #
    # The `created_by_user_id` in `RestaurantCommande` is commented out as it requires
    # the `Users` table to be known to this `Base`. If `Users` table is part of the same `Base`,
    # this ForeignKey can be uncommented.
    # Example:
    # from ..auth.models import User # If User model is in auth/models.py
    # created_by_user_id = Column(Integer, ForeignKey(User.id), nullable=True)

    # The `Products.product_id` ForeignKey needs to be confirmed against the actual schema.
    # I am proceeding with the assumption that a table named `Products` with a primary key `product_id` exists
    # and is declared using the same `Base` as this module will eventually use.
    # If this is not the case, adjustments will be needed during the integration phase.
    # For instance, if the product table is `products` (lowercase) and key is `id`, it would be:
    # produit_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    # The current schema has `db/cruds/products_crud.py` referring to `self.table_name = "Products"`
    # and `self.id_column = "product_id"`, so `Products.product_id` should be correct.
    #
    # Final check on table names from `db/init_schema.py` would confirm this.
    # Looking at `db/init_schema.py`:
    # It defines `Products` table with `product_id INTEGER PRIMARY KEY AUTOINCREMENT`.
    # So, `ForeignKey('Products.product_id')` is correct.
    # It also defines `Users` table with `user_id INTEGER PRIMARY KEY AUTOINCREMENT`.
    # So, `ForeignKey('Users.user_id')` would be correct if `Users` model is also part of the same Base.
    # I will assume for now that `Users` table integration will be handled later if needed.
    # The critical part is that `Products` table is correctly referenced.
    # The `from db.connection import Base` should ensure all models are registered with the same metadata.
    # If the application's `db.initialize_database()` calls `Base.metadata.create_all(engine)`,
    # and this `models.py` file is imported *before* that call, these tables will be created.
    # This is a common pattern for SQLAlchemy applications.
# ```

# J'ai ajouté des commentaires dans le code pour souligner les points d'intégration importants, notamment l'utilisation de `Base` de `db.connection` et la référence à la table `Products` existante.

# **2. `b2c/ges_restaurant/schemas.py` (Pydantic - Optionnel mais recommandé)**

# Pour la validation des données, surtout si on envisage une API plus tard, ou pour structurer les données passées entre les fonctions :

# ```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Schemas for RestaurantTable
class RestaurantTableBase(BaseModel):
    numero_table: str = Field(..., max_length=50)
    capacite: int = Field(4, gt=0)
    statut: str = Field('libre', max_length=20) # libre, occupee, reservee, a_nettoyer
    emplacement: Optional[str] = Field(None, max_length=100)

class RestaurantTableCreate(RestaurantTableBase):
    pass

class RestaurantTableUpdate(BaseModel):
    numero_table: Optional[str] = Field(None, max_length=50)
    capacite: Optional[int] = Field(None, gt=0)
    statut: Optional[str] = Field(None, max_length=20)
    emplacement: Optional[str] = Field(None, max_length=100)

class RestaurantTableInDB(RestaurantTableBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas for RestaurantLigneCommande
class RestaurantLigneCommandeBase(BaseModel):
    produit_id: int
    quantite: int = Field(1, gt=0)
    prix_unitaire_ht_commande: float = Field(..., ge=0)
    # prix_total_ht_ligne is calculated, so not usually in create/update base
    notes: Optional[str] = None

class RestaurantLigneCommandeCreate(RestaurantLigneCommandeBase):
    pass

class RestaurantLigneCommandeUpdate(BaseModel):
    quantite: Optional[int] = Field(None, gt=0)
    prix_unitaire_ht_commande: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class RestaurantLigneCommandeInDB(RestaurantLigneCommandeBase):
    id: int
    commande_id: int
    prix_total_ht_ligne: float # Calculated and stored
    created_at: datetime
    updated_at: Optional[datetime] = None
    # We might want to include product details here for responses
    # produit_nom: Optional[str] = None # Example if joining

    class Config:
        from_attributes = True

# Schemas for RestaurantPaiement
class RestaurantPaiementBase(BaseModel):
    montant_paye: float = Field(..., gt=0)
    methode_paiement: str = Field(..., max_length=50)
    reference_transaction: Optional[str] = Field(None, max_length=100)

class RestaurantPaiementCreate(RestaurantPaiementBase):
    commande_id: int # Required on creation through specific endpoint or nested

class RestaurantPaiementInDB(RestaurantPaiementBase):
    id: int
    commande_id: int
    date_heure_paiement: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas for RestaurantCommande
class RestaurantCommandeBase(BaseModel):
    table_id: int
    statut: str = Field('en_cours', max_length=20) # en_cours, servie, payee, annulee
    notes_client: Optional[str] = None
    nom_client_facultatif: Optional[str] = Field(None, max_length=100)

class RestaurantCommandeCreate(RestaurantCommandeBase):
    lignes_commande: List[RestaurantLigneCommandeCreate] = [] # Allow creating lines with command

class RestaurantCommandeUpdate(BaseModel):
    table_id: Optional[int] = None
    statut: Optional[str] = Field(None, max_length=20)
    notes_client: Optional[str] = None
    nom_client_facultatif: Optional[str] = Field(None, max_length=100)
    # Closing a command would likely set total_commande_ht/ttc and date_heure_cloture

class RestaurantCommandeInDB(RestaurantCommandeBase):
    id: int
    date_heure_creation: datetime
    date_heure_cloture: Optional[datetime] = None
    total_commande_ht: Optional[float] = None
    total_commande_ttc: Optional[float] = None
    # created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    lignes_commande: List[RestaurantLigneCommandeInDB] = []
    paiements: List[RestaurantPaiementInDB] = []
    table: Optional[RestaurantTableInDB] = None # For richer responses

    class Config:
        from_attributes = True

# ```
# Je vais créer ce fichier également.
