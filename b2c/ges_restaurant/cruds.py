import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime

# Assuming models are in the same directory
from .models import RestaurantTable, RestaurantCommande, RestaurantLigneCommande, RestaurantPaiement

# Attempt to import _manage_conn from generic_crud or db.connection
# This requires PROJECT_ROOT to be in sys.path for db.cruds.generic_crud to be found
try:
    from db.cruds.generic_crud import _manage_conn, GenericCRUD
    from db.connection import get_db_connection # For direct session management if needed
    print("Successfully imported _manage_conn and GenericCRUD from db.cruds.generic_crud")
except ImportError as e:
    print(f"Failed to import from db.cruds.generic_crud: {e}. CRUD operations will need manual session management or a fallback.")
    # Fallback: Define a dummy _manage_conn if import fails, actual session handling will need to be addressed.
    def _manage_conn(func):
        def wrapper(*args, **kwargs):
            # This is a placeholder. In a real scenario, you'd obtain a session here.
            # For example, if a global session factory is available:
            # session = SessionLocal()
            # kwargs['conn'] = session # Assuming 'conn' is used for session/connection
            # result = func(*args, **kwargs)
            # session.close()
            # return result
            logging.error("CRITICAL: _manage_conn decorator is not available. Database operations will likely fail.")
            # Attempt to get a connection if the function expects one.
            # This is a very basic fallback.
            db_conn_internal = kwargs.get('conn')
            if not db_conn_internal:
                # Try to get a new connection/session if not provided
                try:
                    db_conn_internal = get_db_connection() # Assumes get_db_connection gives a SQLAlchemy Session or Connection
                    kwargs['conn'] = db_conn_internal
                    # This session needs to be managed (committed, rollbacked, closed) by the caller or a context manager
                    # if _manage_conn is just a passthrough.
                    # The original _manage_conn likely handles this.
                    return func(*args, **kwargs)
                except Exception as e_conn:
                    logging.error(f"Fallback _manage_conn: Failed to get DB connection: {e_conn}")
                    raise
                finally:
                    if db_conn_internal and not kwargs.get('conn'): # If we opened it, we might try to close it
                        # This is risky without knowing if it's a session or connection, or if it should be closed here.
                        # db_conn_internal.close() # Best to let the caller handle it if _manage_conn is a dummy
                        pass


            return func(*args, **kwargs) # Call the original function
        return wrapper

    class GenericCRUD: # Dummy GenericCRUD if import fails
        def __init__(self, model_class):
            self.model_class = model_class
            self.table_name = model_class.__tablename__
            self.id_column = model_class.__mapper__.primary_key[0].name


# --- RestaurantTable CRUD ---

class RestaurantTableCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(RestaurantTable)

    @_manage_conn
    def create_table(self, table_data: Dict[str, Any], conn: Session = None) -> Optional[RestaurantTable]:
        try:
            db_table = RestaurantTable(**table_data)
            conn.add(db_table)
            conn.commit()
            conn.refresh(db_table)
            return db_table
        except IntegrityError as e:
            conn.rollback()
            logging.error(f"Error creating restaurant table (IntegrityError): {e}", exc_info=True)
            # Check if it's a unique constraint violation for numero_table
            if "UNIQUE constraint failed: restaurant_tables.numero_table" in str(e.orig):
                 raise ValueError(f"Table number '{table_data.get('numero_table')}' already exists.")
            raise
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error creating restaurant table: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_table_by_id(self, table_id: int, conn: Session = None) -> Optional[RestaurantTable]:
        try:
            return conn.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
        except SQLAlchemyError as e:
            logging.error(f"Error getting restaurant table by id {table_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_table_by_numero(self, numero_table: str, conn: Session = None) -> Optional[RestaurantTable]:
        try:
            return conn.query(RestaurantTable).filter(RestaurantTable.numero_table == numero_table).first()
        except SQLAlchemyError as e:
            logging.error(f"Error getting restaurant table by numero {numero_table}: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_all_tables(self, skip: int = 0, limit: int = 100, conn: Session = None) -> List[RestaurantTable]:
        try:
            return conn.query(RestaurantTable).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting all restaurant tables: {e}", exc_info=True)
            return []

    @_manage_conn
    def update_table(self, table_id: int, update_data: Dict[str, Any], conn: Session = None) -> Optional[RestaurantTable]:
        try:
            db_table = conn.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
            if db_table:
                for key, value in update_data.items():
                    if hasattr(db_table, key):
                        setattr(db_table, key, value)
                db_table.updated_at = func.now() # Manually update if not auto-set by DB trigger on all updates
                conn.commit()
                conn.refresh(db_table)
            return db_table
        except IntegrityError as e:
            conn.rollback()
            logging.error(f"Error updating restaurant table {table_id} (IntegrityError): {e}", exc_info=True)
            if "UNIQUE constraint failed: restaurant_tables.numero_table" in str(e.orig):
                 raise ValueError(f"Table number '{update_data.get('numero_table')}' already exists for another table.")
            raise
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error updating restaurant table {table_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def delete_table(self, table_id: int, conn: Session = None) -> bool:
        # Note: Consider implications if table has active commandes.
        # This is a hard delete. Soft delete might be preferable.
        try:
            db_table = conn.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
            if db_table:
                # Check for active commandes before deleting
                active_commandes_count = conn.query(RestaurantCommande)\
                    .filter(RestaurantCommande.table_id == table_id)\
                    .filter(RestaurantCommande.statut.notin_(['payee', 'annulee']))\
                    .count()
                if active_commandes_count > 0:
                    logging.warning(f"Attempt to delete table {table_id} which has {active_commandes_count} active commandes.")
                    raise ValueError(f"Cannot delete table '{db_table.numero_table}'. It has active commandes.")

                conn.delete(db_table)
                conn.commit()
                return True
            return False
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error deleting restaurant table {table_id}: {e}", exc_info=True)
            if isinstance(e, IntegrityError): # Foreign key constraint
                raise ValueError(f"Cannot delete table '{db_table.numero_table if 'db_table' in locals() else table_id}'. It is referenced by existing commandes or other records.")
            return False

# --- RestaurantCommande CRUD ---
class RestaurantCommandeCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(RestaurantCommande)

    @_manage_conn
    def create_commande(self, commande_data: Dict[str, Any], lignes_commande_data: List[Dict[str, Any]] = None, conn: Session = None) -> Optional[RestaurantCommande]:
        try:
            # Separate lignes_commande if present
            db_commande = RestaurantCommande(**{k:v for k,v in commande_data.items() if k != 'lignes_commande'})
            conn.add(db_commande)
            # Must flush to get db_commande.id if lines are added immediately
            conn.flush()

            if lignes_commande_data:
                for ligne_data in lignes_commande_data:
                    # Calculate prix_total_ht_ligne
                    prix_unitaire = ligne_data.get('prix_unitaire_ht_commande', 0)
                    quantite = ligne_data.get('quantite', 0)
                    ligne_data['prix_total_ht_ligne'] = prix_unitaire * quantite

                    db_ligne = RestaurantLigneCommande(commande_id=db_commande.id, **ligne_data)
                    conn.add(db_ligne)

            # Recalculate total_commande_ht and total_commande_ttc for the commande
            # This should ideally be a method on the Commande model or a service function
            # For now, let's do a simple sum here if lines were added.
            # This requires another flush if lines were just added to query them.
            conn.flush() # Ensure lines are in session to be queried by db_commande.lignes_commande relationship

            current_total_ht = sum(ligne.prix_total_ht_ligne for ligne in db_commande.lignes_commande)
            db_commande.total_commande_ht = current_total_ht
            # Assuming a simple VAT calculation for TTC for now. This needs proper tax logic.
            vat_rate = 0.20 # Example VAT rate (20%)
            db_commande.total_commande_ttc = current_total_ht * (1 + vat_rate)

            conn.commit()
            conn.refresh(db_commande)
            return db_commande
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error creating restaurant commande: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_commande_by_id(self, commande_id: int, conn: Session = None) -> Optional[RestaurantCommande]:
        try:
            return conn.query(RestaurantCommande)\
                       .options(joinedload(RestaurantCommande.lignes_commande),
                                joinedload(RestaurantCommande.paiements),
                                joinedload(RestaurantCommande.table))\
                       .filter(RestaurantCommande.id == commande_id).first()
        except SQLAlchemyError as e:
            logging.error(f"Error getting restaurant commande by id {commande_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_commandes_for_table(self, table_id: int, statut: Optional[str] = None, conn: Session = None) -> List[RestaurantCommande]:
        try:
            query = conn.query(RestaurantCommande).filter(RestaurantCommande.table_id == table_id)
            if statut:
                query = query.filter(RestaurantCommande.statut == statut)
            return query.order_by(RestaurantCommande.date_heure_creation.desc()).all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting commandes for table {table_id}: {e}", exc_info=True)
            return []

    @_manage_conn
    def get_open_commandes(self, conn: Session = None) -> List[RestaurantCommande]:
        """ Fetches all commandes that are not 'payee' or 'annulee'. """
        try:
            return conn.query(RestaurantCommande)\
                       .options(joinedload(RestaurantCommande.table), # Load table info for display
                                joinedload(RestaurantCommande.lignes_commande))\
                       .filter(RestaurantCommande.statut.notin_(['payee', 'annulee']))\
                       .order_by(RestaurantCommande.date_heure_creation.desc())\
                       .all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting open restaurant commandes: {e}", exc_info=True)
            return []


    @_manage_conn
    def update_commande_statut(self, commande_id: int, new_statut: str, conn: Session = None) -> Optional[RestaurantCommande]:
        try:
            db_commande = conn.query(RestaurantCommande).filter(RestaurantCommande.id == commande_id).first()
            if db_commande:
                db_commande.statut = new_statut
                if new_statut in ['payee', 'annulee'] and not db_commande.date_heure_cloture:
                    db_commande.date_heure_cloture = datetime.utcnow() # Or func.now() if timezone handled by DB

                # Potentially recalculate totals if status change implies it (e.g. adding items)
                # For now, just status update.
                conn.commit()
                conn.refresh(db_commande)
            return db_commande
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error updating statut for commande {commande_id}: {e}", exc_info=True)
            return None

    # More commande updates (add/remove line, update client notes etc.) would go here

# --- RestaurantLigneCommande CRUD ---
class RestaurantLigneCommandeCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(RestaurantLigneCommande)

    @_manage_conn
    def add_ligne_to_commande(self, commande_id: int, ligne_data: Dict[str, Any], conn: Session = None) -> Optional[RestaurantLigneCommande]:
        # First, check if commande exists and is in a state that allows adding lines
        commande = conn.query(RestaurantCommande).filter(RestaurantCommande.id == commande_id).first()
        if not commande:
            logging.error(f"Commande {commande_id} not found. Cannot add line.")
            return None
        if commande.statut in ['payee', 'annulee']:
            logging.warning(f"Attempt to add line to commande {commande_id} with status {commande.statut}.")
            # Depending on business rules, this might be an error or allowed with status change.
            # For now, let's prevent adding to closed/cancelled orders.
            raise ValueError(f"Cannot add items to a commande that is already '{commande.statut}'.")

        try:
            # Calculate prix_total_ht_ligne
            prix_unitaire = ligne_data.get('prix_unitaire_ht_commande', 0)
            quantite = ligne_data.get('quantite', 0)
            ligne_data['prix_total_ht_ligne'] = prix_unitaire * quantite

            db_ligne = RestaurantLigneCommande(commande_id=commande_id, **ligne_data)
            conn.add(db_ligne)

            # After adding the line, recalculate and update commande totals
            conn.flush() # Ensure the new line is associated for calculation

            current_total_ht = sum(ligne.prix_total_ht_ligne for ligne in commande.lignes_commande)
            commande.total_commande_ht = current_total_ht
            # Assuming a simple VAT calculation for TTC for now. This needs proper tax logic.
            vat_rate = 0.20 # Example VAT rate (20%)
            commande.total_commande_ttc = current_total_ht * (1 + vat_rate)

            conn.commit()
            conn.refresh(db_ligne)
            conn.refresh(commande) # Refresh commande to get updated totals
            return db_ligne
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error adding ligne to commande {commande_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def update_ligne_commande(self, ligne_id: int, update_data: Dict[str, Any], conn: Session = None) -> Optional[RestaurantLigneCommande]:
        try:
            db_ligne = conn.query(RestaurantLigneCommande).filter(RestaurantLigneCommande.id == ligne_id).first()
            if db_ligne:
                commande = db_ligne.commande # Get the parent commande
                if commande.statut in ['payee', 'annulee']:
                     raise ValueError(f"Cannot modify items in a commande that is already '{commande.statut}'.")

                original_quantite = db_ligne.quantite
                original_prix_unitaire = db_ligne.prix_unitaire_ht_commande

                for key, value in update_data.items():
                    if hasattr(db_ligne, key):
                        setattr(db_ligne, key, value)

                # Recalculate prix_total_ht_ligne if quantite or prix_unitaire changed
                new_quantite = update_data.get('quantite', original_quantite)
                new_prix_unitaire = update_data.get('prix_unitaire_ht_commande', original_prix_unitaire)
                db_ligne.prix_total_ht_ligne = new_quantite * new_prix_unitaire

                # After updating the line, recalculate and update commande totals
                conn.flush() # Ensure line changes are in session for calculation

                current_total_ht = sum(l.prix_total_ht_ligne for l in commande.lignes_commande)
                commande.total_commande_ht = current_total_ht
                vat_rate = 0.20 # Example VAT rate
                commande.total_commande_ttc = current_total_ht * (1 + vat_rate)

                conn.commit()
                conn.refresh(db_ligne)
                conn.refresh(commande)
            return db_ligne
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error updating ligne commande {ligne_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def remove_ligne_from_commande(self, ligne_id: int, conn: Session = None) -> bool:
        try:
            db_ligne = conn.query(RestaurantLigneCommande).filter(RestaurantLigneCommande.id == ligne_id).first()
            if db_ligne:
                commande = db_ligne.commande
                if commande.statut in ['payee', 'annulee']:
                     raise ValueError(f"Cannot remove items from a commande that is already '{commande.statut}'.")

                conn.delete(db_ligne)

                # After deleting the line, recalculate and update commande totals
                conn.flush() # Ensure delete is processed for calculation

                current_total_ht = sum(l.prix_total_ht_ligne for l in commande.lignes_commande)
                commande.total_commande_ht = current_total_ht
                vat_rate = 0.20 # Example VAT rate
                commande.total_commande_ttc = current_total_ht * (1 + vat_rate)

                conn.commit()
                conn.refresh(commande)
                return True
            return False
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error removing ligne {ligne_id} from commande: {e}", exc_info=True)
            return False

# --- RestaurantPaiement CRUD ---
class RestaurantPaiementCRUD(GenericCRUD):
    def __init__(self):
        super().__init__(RestaurantPaiement)

    @_manage_conn
    def add_paiement_to_commande(self, commande_id: int, paiement_data: Dict[str, Any], conn: Session = None) -> Optional[RestaurantPaiement]:
        # Check if commande exists
        commande = conn.query(RestaurantCommande).filter(RestaurantCommande.id == commande_id).first()
        if not commande:
            logging.error(f"Commande {commande_id} not found. Cannot add paiement.")
            return None
        if commande.statut == 'annulee':
            raise ValueError("Cannot add payment to a cancelled commande.")
        # Business rule: Can we add payment to an already 'payee' order? Usually no, unless it's for adjustments.
        # For now, let's allow, but this might need refinement.

        try:
            db_paiement = RestaurantPaiement(commande_id=commande_id, **paiement_data)
            conn.add(db_paiement)

            # After adding payment, check if commande is fully paid and update its status
            conn.flush() # Ensure payment is associated for calculation

            total_paye = sum(p.montant_paye for p in commande.paiements)
            if commande.total_commande_ttc is not None and total_paye >= commande.total_commande_ttc:
                commande.statut = 'payee'
                if not commande.date_heure_cloture:
                    commande.date_heure_cloture = datetime.utcnow()

            conn.commit()
            conn.refresh(db_paiement)
            if commande.statut == 'payee': # If status changed, refresh commande too
                 conn.refresh(commande)
            return db_paiement
        except SQLAlchemyError as e:
            conn.rollback()
            logging.error(f"Error adding paiement to commande {commande_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_paiements_for_commande(self, commande_id: int, conn: Session = None) -> List[RestaurantPaiement]:
        try:
            return conn.query(RestaurantPaiement)\
                       .filter(RestaurantPaiement.commande_id == commande_id)\
                       .order_by(RestaurantPaiement.date_heure_paiement.asc())\
                       .all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting paiements for commande {commande_id}: {e}", exc_info=True)
            return []


# Instantiate CRUD handlers
restaurant_table_crud = RestaurantTableCRUD()
restaurant_commande_crud = RestaurantCommandeCRUD()
restaurant_ligne_commande_crud = RestaurantLigneCommandeCRUD()
restaurant_paiement_crud = RestaurantPaiementCRUD()

# __all__ for explicit export if needed by other modules via "from .cruds import *"
__all__ = [
    "restaurant_table_crud",
    "restaurant_commande_crud",
    "restaurant_ligne_commande_crud",
    "restaurant_paiement_crud",
    # Individual functions if you expose them directly, e.g.:
    # "create_table", "get_table_by_id", ...
]
