import json
import os
import logging
from db.cruds.products.products_crud import products_crud_instance
from sqlalchemy.orm import Session

# Chemin vers le fichier JSON des produits
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), 'seed_data', 'hidroguc_products.json')

def _add_product_if_not_exists(product_data, db: Session, logger):
    """Ajoute un produit s'il n'existe pas déjà basé sur product_name."""
    existing_product = products_crud_instance.get_product_by_name(product_data['product_name'], db=db)
    if existing_product:
        logger.info(f"Le produit avec le nom '{product_data['product_name']}' existe déjà (ID: {existing_product.product_id}). Utilisation de l'existant.")
        return existing_product.product_id
    else:
        if 'base_unit_price' in product_data and isinstance(product_data['base_unit_price'], str):
            try:
                product_data['base_unit_price'] = float(product_data['base_unit_price'])
            except ValueError:
                logger.error(f"Impossible de convertir base_unit_price '{product_data['base_unit_price']}' en float pour le produit {product_data.get('product_name')}.")
                return None

        new_product = products_crud_instance.add_product(product_data, db=db)
        if new_product and new_product.product_id:
            logger.info(f"Produit '{new_product.product_name}' ajouté avec ID: {new_product.product_id}.")
            return new_product.product_id
        else:
            logger.error(f"Échec de l'ajout du produit '{product_data.get('product_name')}'.")
            return None

def _add_equivalence_if_not_exists(product_id_a, product_id_b, db: Session, logger):
    """Ajoute une équivalence si elle n'existe pas déjà."""
    equivalents_of_a = products_crud_instance.get_equivalent_products(product_id_a, db=db, include_deleted=True)
    is_already_equivalent = any(eq_prod.product_id == product_id_b for eq_prod in equivalents_of_a)

    if is_already_equivalent:
        logger.info(f"L'équivalence entre le produit ID {product_id_a} et ID {product_id_b} existe déjà.")
        return True

    new_equivalence = products_crud_instance.add_product_equivalence(product_id_a, product_id_b, db=db)
    if new_equivalence:
        logger.info(f"Équivalence ajoutée entre produit ID {product_id_a} et ID {product_id_b}.")
        return True
    else:
        logger.error(f"Échec de l'ajout de l'équivalence entre produit ID {product_id_a} et ID {product_id_b}.")
        return False

def _process_product_entry(entry, db: Session, logger):
    """Traite une entrée de produit (base, traductions, variantes) du fichier JSON."""
    base_product_data = entry.get("base_product")
    if not base_product_data:
        logger.warning("Entrée de produit sans 'base_product'. Passage au suivant.")
        return

    base_product_id = _add_product_if_not_exists(base_product_data, db, logger)
    if not base_product_id:
        logger.error(f"Impossible de traiter les traductions/variantes pour '{base_product_data.get('product_name')}' car le produit de base n'a pas pu être ajouté/trouvé.")
        return

    for translation_data in entry.get("translations", []):
        translated_product_id = _add_product_if_not_exists(translation_data, db, logger)
        if translated_product_id and base_product_id != translated_product_id:
            _add_equivalence_if_not_exists(base_product_id, translated_product_id, db, logger)

    for variant_entry in entry.get("variants", []):
        variant_base_product_data = variant_entry.get("base_product")
        if not variant_base_product_data:
            logger.warning("Entrée de variante sans 'base_product'. Passage au suivant.")
            continue

        variant_base_product_id = _add_product_if_not_exists(variant_base_product_data, db, logger)
        if not variant_base_product_id:
            logger.error(f"Impossible de traiter les traductions pour la variante '{variant_base_product_data.get('product_name')}' car la variante de base n'a pas pu être ajoutée/trouvée.")
            continue

        if base_product_id != variant_base_product_id:
             _add_equivalence_if_not_exists(base_product_id, variant_base_product_id, db, logger)

        for translation_data in variant_entry.get("translations", []):
            translated_variant_id = _add_product_if_not_exists(translation_data, db, logger)
            if translated_variant_id and variant_base_product_id != translated_variant_id:
                _add_equivalence_if_not_exists(variant_base_product_id, translated_variant_id, db, logger)

def seed_hidroguc_products(db: Session, logger_passed: logging.Logger):
    """
    Remplit la base de données avec les produits HİDROGÜÇ PRES à partir d'un fichier JSON.
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
        _process_product_entry(entry, db, logger)

    logger.info("Seeding des produits HİDROGÜÇ PRES terminé.")
