import json
import os
import logging
from db.cruds.products_crud import products_crud_instance

# Chemin vers le fichier JSON des produits
# __file__ est le chemin de ce script (hidroguc_product_seeder.py)
# os.path.dirname(__file__) est le dossier 'db'
# os.path.join(...) construit le chemin correct vers 'db/seed_data/hidroguc_products.json'
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), 'seed_data', 'hidroguc_products.json')

def _add_product_if_not_exists(product_data, conn, logger):
    """Ajoute un produit s'il n'existe pas déjà basé sur product_code."""
    existing_product = products_crud_instance.get_product_by_code(product_data['product_code'], conn=conn)
    if existing_product:
        logger.info(f"Le produit avec le code '{product_data['product_code']}' existe déjà (ID: {existing_product['product_id']}). Utilisation de l'existant.")
        return existing_product['product_id']
    else:
        # S'assurer que base_unit_price est un float
        if 'base_unit_price' in product_data and isinstance(product_data['base_unit_price'], str):
            try:
                product_data['base_unit_price'] = float(product_data['base_unit_price'])
            except ValueError:
                logger.error(f"Impossible de convertir base_unit_price '{product_data['base_unit_price']}' en float pour le produit {product_data['product_code']}.")
                return None

        result = products_crud_instance.add_product(product_data, conn=conn)
        if result.get('success'):
            logger.info(f"Produit '{product_data['product_name']}' (Code: {product_data['product_code']}) ajouté avec ID: {result['id']}.")
            return result['id']
        else:
            logger.error(f"Échec de l'ajout du produit '{product_data['product_name']}' (Code: {product_data['product_code']}). Erreur: {result.get('error')}")
            return None

def _add_equivalence_if_not_exists(product_id_a, product_id_b, conn, logger):
    """Ajoute une équivalence si elle n'existe pas déjà."""
    # Vérifier si une équivalence existe déjà dans un sens ou dans l'autre
    # get_equivalent_products retourne une liste de produits, pas directement les IDs d'équivalence.
    # Il faut vérifier si product_id_b est dans les équivalents de product_id_a
    equivalents_of_a = products_crud_instance.get_equivalent_products(product_id_a, conn=conn, include_deleted=True) # include_deleted=True car on veut lier même si un est temporairement inactif
    is_already_equivalent = any(eq_prod['product_id'] == product_id_b for eq_prod in equivalents_of_a)

    if is_already_equivalent:
        logger.info(f"L'équivalence entre le produit ID {product_id_a} et ID {product_id_b} existe déjà.")
        return True

    result = products_crud_instance.add_product_equivalence(product_id_a, product_id_b, conn=conn)
    if result.get('success'):
        equivalence_id = result.get('id')
        message = result.get('message', '')
        if message == "Equivalence already exists.":
             logger.info(f"L'équivalence entre produit ID {product_id_a} et ID {product_id_b} (ID équivalence: {equivalence_id}) existe déjà (détecté par CRUD).")
        else:
            logger.info(f"Équivalence ajoutée entre produit ID {product_id_a} et ID {product_id_b} (ID équivalence: {equivalence_id}).")
        return True
    else:
        logger.error(f"Échec de l'ajout de l'équivalence entre produit ID {product_id_a} et ID {product_id_b}. Erreur: {result.get('error')}")
        return False

def _process_product_entry(entry, conn, logger):
    """Traite une entrée de produit (base, traductions, variantes) du fichier JSON."""
    base_product_data = entry.get("base_product")
    if not base_product_data:
        logger.warning("Entrée de produit sans 'base_product'. Passage au suivant.")
        return

    base_product_id = _add_product_if_not_exists(base_product_data, conn, logger)
    if not base_product_id:
        logger.error(f"Impossible de traiter les traductions/variantes pour '{base_product_data.get('product_name')}' car le produit de base n'a pas pu être ajouté/trouvé.")
        return

    # Traiter les traductions directes du produit de base
    for translation_data in entry.get("translations", []):
        translated_product_id = _add_product_if_not_exists(translation_data, conn, logger)
        if translated_product_id and base_product_id != translated_product_id: # Ne pas lier un produit à lui-même
            _add_equivalence_if_not_exists(base_product_id, translated_product_id, conn, logger)

    # Traiter les variantes (chaque variante est comme un nouveau produit de base)
    for variant_entry in entry.get("variants", []):
        # Une variante est aussi un "base_product" à part entière qui peut avoir ses propres traductions
        variant_base_product_data = variant_entry.get("base_product")
        if not variant_base_product_data:
            logger.warning("Entrée de variante sans 'base_product'. Passage au suivant.")
            continue

        variant_base_product_id = _add_product_if_not_exists(variant_base_product_data, conn, logger)
        if not variant_base_product_id:
            logger.error(f"Impossible de traiter les traductions pour la variante '{variant_base_product_data.get('product_name')}' car la variante de base n'a pas pu être ajoutée/trouvée.")
            continue

        # Lier la variante à son produit "parent" (le base_product de l'entrée principale)
        # Uniquement si la variante est distincte du produit de base principal.
        if base_product_id != variant_base_product_id:
             _add_equivalence_if_not_exists(base_product_id, variant_base_product_id, conn, logger)

        for translation_data in variant_entry.get("translations", []):
            translated_variant_id = _add_product_if_not_exists(translation_data, conn, logger)
            if translated_variant_id and variant_base_product_id != translated_variant_id:
                _add_equivalence_if_not_exists(variant_base_product_id, translated_variant_id, conn, logger)


def seed_hidroguc_products(conn, cursor, logger_passed: logging.Logger):
    """
    Remplit la base de données avec les produits HİDROGÜÇ PRES à partir d'un fichier JSON.
    Assure l'unicité des produits par product_code et gère les équivalences pour les traductions.
    """
    logger = logger_passed or logging.getLogger(__name__)
    logger.info("Début du seeding des produits HİDROGÜÇ PRES.")

    if not os.path.exists(JSON_FILE_PATH):
        logger.error(f"Le fichier JSON des produits HİDROGÜÇ est introuvable à : {JSON_FILE_PATH}")
        return

    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de décodage JSON dans {JSON_FILE_PATH}: {e}")
        return
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier {JSON_FILE_PATH}: {e}")
        return

    if not isinstance(products_data, list):
        logger.error("Le fichier JSON ne contient pas une liste de produits à la racine.")
        return

    for entry in products_data:
        _process_product_entry(entry, conn, logger)

    logger.info("Seeding des produits HİDROGÜÇ PRES terminé.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    test_logger = logging.getLogger("HidrogucProductSeederTest")

    test_logger.warning("Ce script de test direct nécessite une base de données configurée.")
    test_logger.warning("Assurez-vous que DATABASE_PATH est correct et que le schéma existe.")

    # Cette section de test direct est simplifiée et suppose que l'environnement est déjà configuré
    # pour que db.connection.get_db_connection() fonctionne (par ex. DB_CONFIG est déjà setté)
    # et que db.init_schema.initialize_database() a été appelé.
    # Dans le flux normal, db_seed.py s'en charge.

    # Pour un test isolé plus robuste, il faudrait initialiser explicitement DB_CONFIG ici.
    # from config import CONFIG # ou une config de test
    # from db.connection import set_db_config
    # set_db_config(CONFIG)

    from db.connection import get_db_connection #, DATABASE_PATH # DATABASE_PATH n'est pas défini ici
    # Pour obtenir DATABASE_PATH, il faudrait importer config ou le définir ici
    # Pour l'instant, on suppose que get_db_connection() fonctionnera grâce à un DB_CONFIG déjà setté
    # par un appel précédent si on est dans un flux d'intégration.

    test_conn = None
    try:
        test_conn = get_db_connection()
        test_cursor = test_conn.cursor()
        test_logger.info(f"Début du test de seed_hidroguc_products...")
        seed_hidroguc_products(test_conn, test_cursor, test_logger)
        test_conn.commit()
        test_logger.info("Test de seed_hidroguc_products terminé et commit effectué.")
    except Exception as e:
        test_logger.error(f"Erreur lors du test de seed_hidroguc_products: {e}", exc_info=True)
        if test_conn:
            test_conn.rollback()
    finally:
        if test_conn:
            test_conn.close()
