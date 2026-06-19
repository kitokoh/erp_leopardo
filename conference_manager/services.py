# This file will contain the business logic for managing conferences.

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid # Bien que les modèles utilisent uuid, le service pourrait en avoir besoin pour la validation

from .models import Client, Conference # Utilisation d'un import relatif

# _clients: Dict[str, Client] = {} # Géré par SQLite
# _conferences: Dict[str, Conference] = {} # Sera géré par SQLite

# Imports pour SQLite
import json
import sqlite3 # Ajout de l'import manquant
from . import database # Pour accéder à database._memory_conn
# from .database import get_db_connection, DATABASE_NAME, init_db # DATABASE_NAME n'est plus utilisé directement ici
from .database import get_db_connection as db_get_db_connection # Renommer pour éviter confusion
from .database import init_db
from .models import Client, Conference # Assurez-vous que l'import des modèles est correct

# Variable pour surcharger le nom de la base de données pour les tests
# Par défaut, utilise le nom défini dans database.py (qui est "conference_manager.db")
# Les tests peuvent la modifier pour utiliser ":memory:"
TEST_DB_NAME = database.DATABASE_NAME

def _get_service_db_connection():
    """Fonction interne pour obtenir la connexion DB correcte pour les services."""
    conn = db_get_db_connection(TEST_DB_NAME)
    # print(f"DEBUG SVC _get_service_db_connection: TEST_DB_NAME is '{TEST_DB_NAME}', conn id: {id(conn) if conn else 'None'}")
    return conn


# --- Gestion des Clients (avec SQLite) ---

def creer_client(nom: str, coordonnees: Optional[Dict[str, str]] = None) -> Client:
    """Crée un nouveau client et le stocke en base de données SQLite."""
    if not nom or not nom.strip():
        raise ValueError("Le nom du client ne peut pas être vide.")

    nouveau_client = Client(nom=nom.strip(), coordonnees=coordonnees if coordonnees else {})
    coordonnees_json = json.dumps(nouveau_client.coordonnees)

    conn = _get_service_db_connection()
    if not conn:
        raise ConnectionError("Impossible d'établir une connexion à la base de données.")

    sql = """INSERT INTO clients (id, nom, coordonnees)
             VALUES (?, ?, ?)"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (nouveau_client.id, nouveau_client.nom, coordonnees_json))
        conn.commit()
    except sqlite3.IntegrityError as e: # Par exemple, si l'ID existait déjà (peu probable avec UUID)
        conn.rollback()
        raise ValueError(f"Erreur d'intégrité lors de la création du client: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Erreur SQLite lors de la création du client: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()

    return nouveau_client

def obtenir_client(client_id: str) -> Optional[Client]:
    """Récupère un client par son ID depuis la base de données."""
    conn = _get_service_db_connection()
    if not conn:
        # Idéalement, logger cette erreur ou la gérer plus globalement
        print("Avertissement: Impossible d'établir une connexion à la base de données pour obtenir_client.")
        return None

    sql = "SELECT id, nom, coordonnees FROM clients WHERE id = ?"
    client_obj = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (client_id,))
        row = cursor.fetchone()
        if row:
            coordonnees_dict = json.loads(row["coordonnees"]) if row["coordonnees"] else {}
            client_obj = Client(client_id=row["id"], nom=row["nom"], coordonnees=coordonnees_dict)
    except sqlite3.Error as e:
        print(f"Erreur SQLite lors de la récupération du client {client_id}: {e}")
        # Gérer l'erreur, peut-être logger et retourner None
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()
    return client_obj

def lister_clients() -> List[Client]:
    """Retourne la liste de tous les clients depuis la base de données."""
    conn = _get_service_db_connection()
    if not conn:
        print("Avertissement: Impossible d'établir une connexion à la base de données pour lister_clients.")
        return []

    clients_list = []
    sql = "SELECT id, nom, coordonnees FROM clients ORDER BY nom"
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            coordonnees_dict = json.loads(row["coordonnees"]) if row["coordonnees"] else {}
            clients_list.append(Client(client_id=row["id"], nom=row["nom"], coordonnees=coordonnees_dict))
    except sqlite3.Error as e:
        print(f"Erreur SQLite lors du listage des clients: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()
    return clients_list

def mettre_a_jour_client(client_id: str, nom: Optional[str] = None, coordonnees: Optional[Dict[str, str]] = None) -> Optional[Client]:
    """Met à jour le nom et/ou les coordonnées d'un client existant."""
    if not nom and coordonnees is None:
        raise ValueError("Au moins un champ (nom ou coordonnees) doit être fourni pour la mise à jour.")

    client_existant = obtenir_client(client_id)
    if not client_existant:
        return None # Le client n'existe pas

    fields_to_update = []
    params = []

    if nom is not None:
        if not nom.strip(): # S'assurer que le nom n'est pas vide s'il est fourni
            raise ValueError("Le nom du client ne peut pas être vide.")
        fields_to_update.append("nom = ?")
        params.append(nom)
        client_existant.nom = nom # Mettre à jour l'objet en mémoire aussi pour le retour

    if coordonnees is not None:
        fields_to_update.append("coordonnees = ?")
        params.append(json.dumps(coordonnees))
        client_existant.coordonnees = coordonnees # Mettre à jour l'objet en mémoire

    if not fields_to_update: # Aucun champ n'a été réellement modifié (ne devrait pas arriver avec la vérification initiale)
        return client_existant

    params.append(client_id) # Pour la clause WHERE

    conn = _get_service_db_connection()
    if not conn:
        raise ConnectionError("Impossible d'établir une connexion à la base de données.")

    sql = f"UPDATE clients SET {', '.join(fields_to_update)} WHERE id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount == 0: # Aucun enregistrement mis à jour (par exemple, ID non trouvé)
            return None # Ou lever une exception spécifique
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Erreur SQLite lors de la mise à jour du client {client_id}: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()

    return client_existant # Retourne l'objet Client mis à jour

def supprimer_client(client_id: str) -> bool:
    """Supprime un client de la base de données.
    Retourne True si la suppression a réussi, False sinon.
    Note: La clé étrangère dans `conferences` est ON DELETE SET NULL,
    donc les `client_id` des conférences associées seront mis à NULL.
    """
    conn = _get_service_db_connection()
    if not conn:
        raise ConnectionError("Impossible d'établir une connexion à la base de données.")

    sql = "DELETE FROM clients WHERE id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (client_id,))
        conn.commit()
        return cursor.rowcount > 0 # True si au moins une ligne a été affectée
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Erreur SQLite lors de la suppression du client {client_id}: {e}")
        return False # Ou lever une exception plus spécifique
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()


# --- Gestion des Conférences (sera adapté ensuite) ---

def creer_conference(titre: str,
                     date_heure_programmation: Optional[datetime] = None,
                     notes: str = "",
                     client_id: Optional[str] = None,
                     participants_externes: str = "",
                     lieu: Optional[str] = None,
                     description_calendrier: Optional[str] = None,
                     rappel_active: bool = True,
                     minutes_rappel_avant: Optional[int] = 30,
                     utilisateur_id: Optional[str] = None,
                     duree_minutes: Optional[int] = 60,
                     # rappel_envoye n'est pas un paramètre de création, il est initialisé à False par défaut
                     ) -> Conference:
    """Crée une nouvelle conférence et la stocke en base de données SQLite."""
    if not titre or not titre.strip():
        raise ValueError("Le titre de la conférence ne peut pas être vide.")

    if client_id and not obtenir_client(client_id): # Vérifie si le client existe en BD
        raise ValueError(f"Client avec ID '{client_id}' non trouvé.")

    # Crée une instance de Conference pour générer l'ID, la date de création et gérer la logique des rappels
    nouvelle_conference_obj = Conference(
        titre=titre.strip(), # Assurer que le titre est nettoyé aussi
        date_heure_programmation=date_heure_programmation,
        notes_rapport=notes,
        client_id=client_id,
        participants_externes=participants_externes,
        statut=Conference.CONFERENCE_STATUT_PLANNED, # Statut initial par défaut
        lieu=lieu,
        description_calendrier=description_calendrier,
        rappel_active=rappel_active,
        minutes_rappel_avant=minutes_rappel_avant,
        utilisateur_id=utilisateur_id,
        duree_minutes=duree_minutes,
        rappel_envoye=False # Initialisation explicite dans l'objet modèle
    )

    # La vérification obtenir_client utilise déjà _get_service_db_connection
    # Donc la connexion principale pour cette fonction :
    conn = _get_service_db_connection()
    if not conn:
        raise ConnectionError("Impossible d'établir une connexion à la base de données.")

    sql = """INSERT INTO conferences (id, titre, date_heure_creation, date_heure_programmation,
                                    notes_rapport, client_id, participants_externes, statut,
                                    lieu, description_calendrier, rappel_active, minutes_rappel_avant,
                                    utilisateur_id, duree_minutes, rappel_envoye)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""" # Ajout de rappel_envoye
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            nouvelle_conference_obj.id,
            nouvelle_conference_obj.titre,
            nouvelle_conference_obj.date_heure_creation,
            nouvelle_conference_obj.date_heure_programmation,
            nouvelle_conference_obj.notes_rapport,
            nouvelle_conference_obj.client_id,
            nouvelle_conference_obj.participants_externes,
            nouvelle_conference_obj.statut,
            nouvelle_conference_obj.lieu,
            nouvelle_conference_obj.description_calendrier,
            1 if nouvelle_conference_obj.rappel_active else 0,
            nouvelle_conference_obj.minutes_rappel_avant,
            nouvelle_conference_obj.utilisateur_id,
            nouvelle_conference_obj.duree_minutes,
            1 if nouvelle_conference_obj.rappel_envoye else 0 # Devrait être 0 ici
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        # Si c'est une violation de clé étrangère pour client_id
        if "FOREIGN KEY constraint failed" in str(e) and client_id:
             raise ValueError(f"Client avec ID '{client_id}' non trouvé ou contrainte de clé étrangère violée.")
        raise ValueError(f"Erreur d'intégrité lors de la création de la conférence: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Erreur SQLite lors de la création de la conférence: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()

    return nouvelle_conference_obj


def _row_to_conference_obj(row: sqlite3.Row) -> Optional[Conference]:
    """Convertit un sqlite3.Row en objet Conference."""
    if not row:
        return None
    return Conference(
        conference_id=row["id"],
        titre=row["titre"],
        date_heure_creation=datetime.fromisoformat(row["date_heure_creation"]) if row["date_heure_creation"] else None,
        date_heure_programmation=datetime.fromisoformat(row["date_heure_programmation"]) if row["date_heure_programmation"] else None,
        notes_rapport=row["notes_rapport"],
        client_id=row["client_id"],
        participants_externes=row["participants_externes"],
        statut=row["statut"],
        lieu=row["lieu"],
        description_calendrier=row["description_calendrier"],
        rappel_active=bool(row["rappel_active"]),
        minutes_rappel_avant=row["minutes_rappel_avant"],
        utilisateur_id=row["utilisateur_id"],
        duree_minutes=row["duree_minutes"],
        rappel_envoye=bool(row["rappel_envoye"]) # Convertir int (0/1) de SQLite en bool
    )

def obtenir_details_conference(conference_id: str) -> Optional[Conference]:
    """Récupère une conférence par son ID depuis la base de données."""
    conn = _get_service_db_connection() # Déjà correct
    if not conn:
        print(f"Avertissement: Impossible d'établir une connexion BD pour obtenir_details_conference({conference_id}).")
        return None

    sql = "SELECT * FROM conferences WHERE id = ?"
    conference_obj = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (conference_id,))
        row = cursor.fetchone()
        conference_obj = _row_to_conference_obj(row)
    except sqlite3.Error as e:
        print(f"Erreur SQLite lors de la récupération de la conférence {conference_id}: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()
    return conference_obj


def mettre_a_jour_conference(conference_id: str,
                             titre: Optional[str] = None,
                             date_heure_programmation: Optional[datetime] = None,
                             notes_rapport: Optional[str] = None,
                             client_id: Optional[str] = None,
                             participants_externes: Optional[str] = None,
                             statut: Optional[str] = None,
                             lieu: Optional[str] = None,
                             description_calendrier: Optional[str] = None,
                             rappel_active: Optional[bool] = None,
                             minutes_rappel_avant: Optional[int] = None,
                             utilisateur_id: Optional[str] = None,
                             duree_minutes: Optional[int] = None,
                             rappel_envoye: Optional[bool] = None
                            ) -> Optional[Conference]:
    """Met à jour les champs spécifiés d'une conférence existante."""

    # Vérifier d'abord si la conférence existe
    # Si le contrat est de lever une erreur si la conférence n'existe pas, on peut le faire ici.
    # Si le contrat est de retourner None, alors obtenir_details_conference est la première étape.
    # Pour l'instant, la logique existante tente la MàJ puis relit.
    # Modifions pour vérifier l'existence au début si c'est plus propre pour le contrat.

    # Toutefois, pour minimiser les changements, gardons la logique actuelle et ajustons l'erreur.
    # La ValueError est levée si rowcount est 0 ET que la conférence n'est pas trouvée après.
    # Si marquer_rappel_envoye doit retourner None, elle doit gérer cette ValueError.

    _sentinel = object()
    provided_args = {
        'titre': titre, 'date_heure_programmation': date_heure_programmation,
        'notes_rapport': notes_rapport, 'client_id': client_id,
        'participants_externes': participants_externes, 'statut': statut,
        'lieu': lieu, 'description_calendrier': description_calendrier,
        'rappel_active': rappel_active, 'minutes_rappel_avant': minutes_rappel_avant,
        'utilisateur_id': utilisateur_id, 'duree_minutes': duree_minutes,
        'rappel_envoye': rappel_envoye
    }
    if all(value is None for value in provided_args.values()): # type: ignore
         raise ValueError("Aucun champ fourni pour la mise à jour de la conférence.")

    # Récupérer la conférence existante pour vérifier son existence
    # Cependant, il est plus sûr de relire après la MàJ ou de construire l'objet avec les nouvelles valeurs.

    fields_to_update = []
    params = []

    if titre is not None:
        if not titre.strip(): raise ValueError("Le titre ne peut pas être vide.")
        fields_to_update.append("titre = ?")
        params.append(titre)

    # Pour date_heure_programmation, on peut vouloir permettre de la mettre à NULL
    if date_heure_programmation is not None: # On pourrait avoir un marqueur spécial pour la passer à NULL
        fields_to_update.append("date_heure_programmation = ?")
        params.append(date_heure_programmation) # SQLite gère la conversion en timestamp

    if notes_rapport is not None:
        fields_to_update.append("notes_rapport = ?")
        params.append(notes_rapport)

    # Gestion spéciale pour client_id: si on passe "", on le met à NULL.
    # Si on passe un ID valide, on vérifie qu'il existe.
    if client_id is not None:
        if client_id == "": # Convention pour désaffecter
            fields_to_update.append("client_id = ?")
            params.append(None)
        else:
            if not obtenir_client(client_id):
                raise ValueError(f"Client avec ID '{client_id}' non trouvé pour l'affectation.")
            fields_to_update.append("client_id = ?")
            params.append(client_id)

    if participants_externes is not None:
        fields_to_update.append("participants_externes = ?")
        params.append(participants_externes)

    if statut is not None:
        if statut not in Conference.VALID_STATUSES:
            raise ValueError(f"Statut invalide: {statut}. Doit être un de {Conference.VALID_STATUSES}")
        fields_to_update.append("statut = ?")
        params.append(statut)

    if lieu is not None:
        fields_to_update.append("lieu = ?")
        params.append(lieu if lieu.strip() else None) # Stocker NULL si vide après strip

    if description_calendrier is not None:
        fields_to_update.append("description_calendrier = ?")
        params.append(description_calendrier) # Peut être une chaîne vide

    if rappel_active is not None:
        fields_to_update.append("rappel_active = ?")
        params.append(1 if rappel_active else 0)
        # Si rappel_active devient False, s'assurer que minutes_rappel_avant est NULL
        if not rappel_active and "minutes_rappel_avant = ?" not in [f.split(" = ")[0] for f in fields_to_update]:
             # Si minutes_rappel_avant n'est pas déjà en train d'être mis à jour, le mettre à NULL
            fields_to_update.append("minutes_rappel_avant = ?")
            params.append(None)


    if minutes_rappel_avant is not None:
        # Si rappel_active est explicitement mis à False dans le même appel, minutes_rappel_avant sera ignoré ou mis à NULL
        # La logique ci-dessus pour rappel_active=False gère la mise à NULL de minutes_rappel_avant.
        # Si rappel_active n'est pas fourni ou est True, on met à jour minutes_rappel_avant.
        if rappel_active is None or rappel_active is True:
            if "minutes_rappel_avant = ?" not in [f.split(" = ")[0] for f in fields_to_update]: # Eviter double ajout
                 fields_to_update.append("minutes_rappel_avant = ?")
                 params.append(minutes_rappel_avant if minutes_rappel_avant >=0 else None) # Permettre de le mettre à NULL avec -1
            else: # Si déjà dans la liste (par le bloc rappel_active=False), modifier la valeur
                try:
                    idx = [f.split(" = ")[0] for f in fields_to_update].index("minutes_rappel_avant")
                    if params[idx] is None : # Si rappel_active=False l'a mis à None, on respecte cela, sauf si minutes_rappel_avant est explicitement fourni et >=0
                         if minutes_rappel_avant >=0 : params[idx] = minutes_rappel_avant
                    # Sinon, la valeur de minutes_rappel_avant est déjà celle désirée
                except ValueError: # Ne devrait pas arriver
                    pass

    if utilisateur_id is not None:
        fields_to_update.append("utilisateur_id = ?")
        params.append(utilisateur_id if utilisateur_id.strip() else None) # Stocker NULL si vide

    if duree_minutes is not None:
        if duree_minutes < 0: # On peut choisir de mettre à NULL si durée négative
            fields_to_update.append("duree_minutes = ?")
            params.append(None)
        else:
            fields_to_update.append("duree_minutes = ?")
            params.append(duree_minutes)

    if rappel_envoye is not None:
        fields_to_update.append("rappel_envoye = ?")
        params.append(1 if rappel_envoye else 0)


    if not fields_to_update:
        return obtenir_details_conference(conference_id)

    params.append(conference_id) # Pour la clause WHERE

    conn = _get_service_db_connection() # Déjà correct
    if not conn:
        raise ConnectionError("Impossible d'établir une connexion à la base de données.")

    sql = f"UPDATE conferences SET {', '.join(fields_to_update)} WHERE id = ?"

    updated_conference = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            updated_conference = obtenir_details_conference(conference_id) # Relire pour avoir l'état à jour
        else:
            # Soit l'ID n'existe pas, soit aucune valeur n'a réellement changé (peu probable ici)
            # On vérifie si la conférence existe toujours
            if not obtenir_details_conference(conference_id):
                 raise ValueError(f"Conférence avec ID '{conference_id}' non trouvée pour la mise à jour.")
            # Si elle existe mais rowcount est 0, c'est étrange, mais on peut retourner l'état actuel.
            updated_conference = obtenir_details_conference(conference_id)

    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "FOREIGN KEY constraint failed" in str(e) and client_id and client_id != "":
             raise ValueError(f"Client avec ID '{client_id}' non trouvé ou contrainte de clé étrangère violée lors de la MàJ.")
        raise ValueError(f"Erreur d'intégrité lors de la mise à jour de la conférence: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Erreur SQLite lors de la mise à jour de la conférence {conference_id}: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()

    return updated_conference


# Les fonctions spécifiques comme ajouter_ou_maj_notes, affecter_client_a_conference, changer_statut_conference
# peuvent maintenant être des alias ou des wrappers de mettre_a_jour_conference.

def ajouter_ou_maj_notes(conference_id: str, nouvelles_notes: str) -> Optional[Conference]:
    """Met à jour les notes d'une conférence."""
    return mettre_a_jour_conference(conference_id, notes_rapport=nouvelles_notes)

def affecter_client_a_conference(conference_id: str, client_id: str) -> Optional[Conference]:
    """Affecte un client existant à une conférence. Si client_id est vide, désaffecte."""
    if not client_id: # Permettre de désaffecter en passant un client_id vide
        return mettre_a_jour_conference(conference_id, client_id="")
    return mettre_a_jour_conference(conference_id, client_id=client_id)

def changer_statut_conference(conference_id: str, nouveau_statut: str) -> Optional[Conference]:
    """Change le statut d'une conférence."""
    return mettre_a_jour_conference(conference_id, statut=nouveau_statut)


def lister_conferences(client_id: Optional[str] = None,
                       statut: Optional[str] = None,
                       par_utilisateur_id: Optional[str] = None) -> List[Conference]:
    """Retourne une liste de conférences depuis la BD, potentiellement filtrée."""
    conn = _get_service_db_connection() # Déjà correct
    if not conn:
        print("Avertissement: Impossible d'établir une connexion BD pour lister_conferences.")
        return []

    conferences_list = []
    params = []
    sql_conditions = []

    if client_id:
        sql_conditions.append("client_id = ?")
        params.append(client_id)

    if statut:
        if statut not in Conference.VALID_STATUSES:
            raise ValueError(f"Statut de filtre invalide: {statut}.")
        sql_conditions.append("statut = ?")
        params.append(statut)

    if par_utilisateur_id:
        sql_conditions.append("utilisateur_id = ?")
        params.append(par_utilisateur_id)

    sql = "SELECT * FROM conferences"
    if sql_conditions:
        sql += " WHERE " + " AND ".join(sql_conditions)
    sql += " ORDER BY date_heure_creation DESC" # Ou date_heure_programmation

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        for row in rows:
            conferences_list.append(_row_to_conference_obj(row))
    except sqlite3.Error as e:
        print(f"Erreur SQLite lors du listage des conférences: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()
    return conferences_list

def supprimer_conference(conference_id: str) -> bool:
    """Supprime une conférence de la base de données.
    Retourne True si la suppression a réussi, False sinon.
    """
    conn = _get_service_db_connection() # Déjà correct
    if not conn:
        raise ConnectionError("Impossible d'établir une connexion à la base de données.")

    sql = "DELETE FROM conferences WHERE id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (conference_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Erreur SQLite lors de la suppression de la conférence {conference_id}: {e}")
        return False
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()


# Fonctions utilitaires pour la gestion des données (pour les tests ou le débogage)
# Variable globale pour le nom de la base de données de test, peut être configurée
TEST_DB_NAME = ":memory:"
# TEST_DB_NAME = "test_conference_manager_services.db" # Alternative pour inspecter le fichier après les tests

def reinitialiser_donnees(db_name: str = TEST_DB_NAME):
    """
    Réinitialise la base de données (la recrée à partir de zéro si c'est un fichier)
    et les structures en mémoire. Utile pour les tests.
    """
    # global _conferences # _clients n'est plus géré en mémoire ici

    # S'assurer que os et sqlite3 sont importés si ce n'est pas déjà le cas globalement
    import os
    import sqlite3 # Nécessaire pour les erreurs sqlite3.Error dans les services
    # print(f"DEBUG SVC reinitialiser_donnees: db_name is '{db_name}', TEST_DB_NAME is '{TEST_DB_NAME}'")


    if db_name != ":memory:" and os.path.exists(db_name):
        try:
            # Il faut s'assurer qu'aucune connexion n'est active sur le fichier avant de le supprimer
            # C'est généralement géré par les tests eux-mêmes (fermeture des connexions)
            os.remove(db_name)
        except OSError as e:
            print(f"Avertissement: Impossible de supprimer l'ancienne base de données de test '{db_name}': {e}")
            print("Cela peut se produire si une connexion est toujours active.")

    # Pour les tests, s'assurer de toujours supprimer les tables existantes pour un état propre
    is_test_context = (db_name == TEST_DB_NAME and TEST_DB_NAME == ":memory:") or \
                      (db_name == TEST_DB_NAME and "test" in db_name.lower()) # Heuristique pour les fichiers de test

    init_db(db_name, drop_tables_for_test=is_test_context)

    # Réinitialiser les données en mémoire pour les entités non encore migrées (Conférences)
    # _conferences = {} # Les conférences sont maintenant dans SQLite
    # print(f"Données réinitialisées. Base de données utilisée: '{db_name}'")


# Exemple d'utilisation (pour la démonstration et le test manuel du module)
if __name__ == '__main__':
    # Utiliser un fichier de test spécifique pour la démo __main__ pour éviter les conflits
    main_demo_db_file = "conference_manager_demo.db"
    reinitialiser_donnees(db_name=main_demo_db_file)

    print("\n--- Démo Gestion Clients (SQLite) ---")
    client1_id, client2_id = None, None
    try:
        client1 = creer_client(nom="Alpha Inc. (Démo SQLite)", coordonnees={"email": "contact@alpha-demo.com"})
        client1_id = client1.id
        client2 = creer_client(nom="Beta Corp. (Démo SQLite)", coordonnees={"tel": "1234567890"})
        client2_id = client2.id
        print(f"Client 1 créé: ID {client1.id}, Nom: {client1.nom}")
        print(f"Client 2 créé: ID {client2.id}, Nom: {client2.nom}")

        print("\nListe des clients après création:")
        for c_idx, c in enumerate(lister_clients()):
            print(f" {c_idx + 1}. ID: {c.id}, Nom: {c.nom}, Coordonnées: {c.coordonnees}")

        if client1_id:
            retrieved_c1 = obtenir_client(client1_id)
            print(f"\nDétails Client 1 (obtenu par ID): {retrieved_c1.nom if retrieved_c1 else 'Non trouvé'}")

            print("\nMise à jour Client 1...")
            client1_maj = mettre_a_jour_client(client1_id, nom="Alpha Inc. Modifié (Démo)", coordonnees={"email": "new@alpha-demo.com", "tel": "987654321"})
            print(f"Client 1 après MàJ: Nom: {client1_maj.nom if client1_maj else 'Non trouvé'}, Coordonnées: {client1_maj.coordonnees if client1_maj else ''}")

        print(f"\nObtenir un client inexistant: {obtenir_client('id-bidon-123')}")

        if client2_id:
            print(f"\nSuppression Client 2 (ID: {client2_id})...")
            supprime_ok = supprimer_client(client2_id)
            print(f"Client 2 supprimé avec succès: {supprime_ok}")
            print(f"Tentative d'obtenir Client 2 après suppression: {obtenir_client(client2_id)}")

        print("\nListe des clients après suppression:")
        for c_idx, c in enumerate(lister_clients()):
            print(f" {c_idx + 1}. ID: {c.id}, Nom: {c.nom}")

        # Test de suppression d'un client déjà supprimé ou inexistant
        print("\nTentative de suppression d'un client inexistant (id-bidon-456)...")
        supprime_ko = supprimer_client("id-bidon-456")
        print(f"Suppression client inexistant réussie (attendu False): {supprime_ko}")


    except ValueError as e:
        print(f"Erreur de valeur: {e}")
    except ConnectionError as e:
        print(f"Erreur de connexion BD: {e}")
    except RuntimeError as e:
        print(f"Erreur runtime BD: {e}")
    except Exception as e: # Attraper d'autres exceptions potentielles
        import traceback
        print(f"Erreur inattendue lors de la démo client: {e}")
        traceback.print_exc()


    # --- Démo Gestion Conférences (maintenant avec SQLite) ---
    print("\n\n--- Démo Gestion Conférences (SQLite) ---")

    demo_client_for_conf = None
    if client1_id:
         demo_client_for_conf = obtenir_client(client1_id)

    conf1_demo_id, conf2_demo_id = None, None
    try:
        print("\nCréation de conférences...")
        conf1_date_prog = datetime.now() + timedelta(days=5)
        conf1_demo = creer_conference(
            titre="Conférence Démo 1 (SQLite)",
            date_heure_programmation=conf1_date_prog,
            client_id=demo_client_for_conf.id if demo_client_for_conf else None,
            notes="Notes pour la démo 1."
        )
        conf1_demo_id = conf1_demo.id
        print(f"Conférence 1 créée: {conf1_demo.titre} (ID: {conf1_demo.id})")

        conf2_demo = creer_conference(
            titre="Conférence Démo 2 (SQLite)",
            participants_externes="Participant Externe Démo",
            notes="Notes pour la démo 2."
        )
        conf2_demo_id = conf2_demo.id
        print(f"Conférence 2 créée: {conf2_demo.titre} (ID: {conf2_demo.id})")

        print("\nListe de toutes les conférences (SQLite):")
        all_confs_sqlite = lister_conferences()
        for conf_idx, conf_item in enumerate(all_confs_sqlite):
            print(f" {conf_idx+1}. {conf_item.titre} (ID: {conf_item.id}), Statut: {conf_item.statut}, Client: {conf_item.client_id or 'Aucun'}")

        if conf1_demo_id:
            print(f"\nDétails Conférence 1: {obtenir_details_conference(conf1_demo_id).titre}")
            print("Mise à jour Conférence 1 (notes et statut)...")
            conf1_updated = ajouter_ou_maj_notes(conf1_demo_id, "Notes mises à jour pour la démo 1.")
            conf1_updated = changer_statut_conference(conf1_demo_id, Conference.CONFERENCE_STATUT_COMPLETED)
            print(f"Conférence 1 MàJ: Titre: {conf1_updated.titre}, Notes: '{conf1_updated.notes_rapport}', Statut: {conf1_updated.statut}")

        if conf2_demo_id and demo_client_for_conf:
            print(f"\nAffectation du client '{demo_client_for_conf.nom}' à la Conférence 2...")
            conf2_updated = affecter_client_a_conference(conf2_demo_id, demo_client_for_conf.id)
            print(f"Conférence 2 MàJ: Titre: {conf2_updated.titre}, Client ID: {conf2_updated.client_id}")

        print("\nListe des conférences COMPLETED:")
        completed_confs = lister_conferences(statut=Conference.CONFERENCE_STATUT_COMPLETED)
        for conf_item in completed_confs:
            print(f" - {conf_item.titre}")

        if demo_client_for_conf:
            print(f"\nListe des conférences pour client '{demo_client_for_conf.nom}':")
            client_confs = lister_conferences(client_id=demo_client_for_conf.id)
            for conf_item in client_confs:
                print(f" - {conf_item.titre}")

        if conf2_demo_id:
            print(f"\nSuppression Conférence 2 (ID: {conf2_demo_id})...")
            deleted_conf2 = supprimer_conference(conf2_demo_id)
            print(f"Conférence 2 supprimée: {deleted_conf2}")
            print(f"Vérification Conférence 2: {obtenir_details_conference(conf2_demo_id)}")

        print("\nListe finale des conférences (SQLite):")
        for conf_item in lister_conferences():
            print(f" - {conf_item.titre}, Statut: {conf_item.statut}")

    except ValueError as e:
        print(f"Erreur de valeur (conférences SQLite): {e}")
    except ConnectionError as e:
        print(f"Erreur de connexion BD (conférences SQLite): {e}")
    except RuntimeError as e:
        print(f"Erreur runtime BD (conférences SQLite): {e}")
    except Exception as e:
        import traceback
        print(f"Erreur inattendue lors de la démo conférences (SQLite): {e}")
        traceback.print_exc()


# --- Logique de Planification ---

def obtenir_conferences_a_venir() -> List[Conference]:
    """
    Retourne une liste des conférences planifiées (date de programmation dans le futur)
    et non terminées ou annulées, triées par date de programmation, depuis la base de données.
    """
    maintenant = datetime.now()
    conferences_futures_list = []

    conn = _get_service_db_connection() # Déjà correct
    if not conn:
        print("Avertissement: Impossible d'établir une connexion BD pour obtenir_conferences_a_venir.")
        return []

    sql = """
        SELECT * FROM conferences
        WHERE date_heure_programmation IS NOT NULL
          AND date_heure_programmation > ?
          AND statut NOT IN (?, ?)
        ORDER BY date_heure_programmation ASC
    """

    params = (
        maintenant,
        Conference.CONFERENCE_STATUT_COMPLETED,
        Conference.CONFERENCE_STATUT_CANCELLED
    )

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        for row in rows:
            conferences_futures_list.append(_row_to_conference_obj(row))
    except sqlite3.Error as e:
        print(f"Erreur SQLite lors de la récupération des conférences à venir: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()

    return conferences_futures_list


# --- Logique de Rappel ---

def obtenir_conferences_necessitant_rappel(fenetre_proche_futur_minutes: int = 5) -> List[Conference]:
    """
    Identifie les conférences futures pour lesquelles un rappel devrait être envoyé.

    Un rappel est nécessaire si :
    - Le rappel est actif pour la conférence.
    - L'heure de la conférence n'est pas encore passée.
    - Le statut de la conférence n'est ni "Terminée" ni "Annulée".
    - L'heure de rappel calculée (heure_conf - minutes_rappel_avant) est :
        - Soit déjà passée.
        - Soit dans les `fenetre_proche_futur_minutes` prochaines minutes.

    Retourne une liste de conférences triées par heure de rappel (la plus proche en premier).
    """
    maintenant = datetime.now()
    limite_futur_proche = maintenant + timedelta(minutes=fenetre_proche_futur_minutes)

    conferences_pour_rappel = []
    conn = _get_service_db_connection()
    if not conn:
        print("Avertissement: Impossible d'établir une connexion BD pour obtenir_conferences_necessitant_rappel.")
        return []

    # Sélectionner les conférences candidates
    sql = """
        SELECT * FROM conferences
        WHERE rappel_active = 1
          AND date_heure_programmation IS NOT NULL
          AND date_heure_programmation > ?       -- La conférence elle-même doit être dans le futur
          AND statut NOT IN (?, ?)
          AND minutes_rappel_avant IS NOT NULL AND minutes_rappel_avant >= 0
          AND rappel_envoye = 0                  -- Ne prendre que celles dont le rappel n'a pas été envoyé
    """
    # Le filtrage fin sur l'heure de rappel se fera en Python après récupération.

    params = (
        maintenant,
        Conference.CONFERENCE_STATUT_COMPLETED,
        Conference.CONFERENCE_STATUT_CANCELLED
    )

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        for row in rows:
            conf = _row_to_conference_obj(row)
            if not conf or not conf.date_heure_programmation or conf.minutes_rappel_avant is None:
                continue

            heure_rappel = conf.date_heure_programmation - timedelta(minutes=conf.minutes_rappel_avant)

            # Condition pour le rappel:
            # 1. L'heure de rappel est passée ou dans la fenêtre future proche.
            # 2. Mais la conférence elle-même n'a pas encore commencé (ceci est déjà en partie géré par la requête SQL
            #    `date_heure_programmation > ?` (maintenant), mais on peut le re-vérifier pour être sûr).
            if heure_rappel <= limite_futur_proche and conf.date_heure_programmation > maintenant :
                # Ajouter l'heure de rappel calculée à l'objet pour le tri, si nécessaire, ou trier sur l'objet
                # Pour l'instant, on ajoute juste la conférence.
                conferences_pour_rappel.append(conf)

    except sqlite3.Error as e:
        print(f"Erreur SQLite lors de la récupération des conférences pour rappel: {e}")
    finally:
        if conn and conn is not database._memory_conn:
            conn.close()

    # Trier les conférences par leur heure de rappel effective (la plus ancienne/proche en premier)
    conferences_pour_rappel.sort(key=lambda c: (c.date_heure_programmation - timedelta(minutes=c.minutes_rappel_avant if c.minutes_rappel_avant is not None else 0)))

    return conferences_pour_rappel

def marquer_rappel_envoye(conference_id: str) -> Optional[Conference]:
    """
    Marque le champ `rappel_envoye` d'une conférence comme True.
    Retourne la conférence mise à jour ou None si la conférence n'est pas trouvée.
    """
    try:
        return mettre_a_jour_conference(conference_id, rappel_envoye=True)
    except ValueError as e:
        # Si mettre_a_jour_conference lève ValueError car la conf n'est pas trouvée
        if "non trouvée pour la mise à jour" in str(e): # Heuristique fragile
            return None
        raise # Renvoyer d'autres ValueErrors (ex: statut invalide)


# --- Export iCalendar ---
from icalendar import Calendar, Event as IcsEvent, Alarm # Importer Alarm
from datetime import timedelta # Déjà importé globalement, mais bon à noter ici

def generer_contenu_ics_pour_conference(conference_id: str, default_duration_minutes: int = 60) -> Optional[str]:
    """
    Génère une chaîne de caractères au format iCalendar (.ics) pour une conférence donnée.
    Retourne None si la conférence n'est pas trouvée ou n'a pas de date de programmation.
    """
    conference = obtenir_details_conference(conference_id)

    if not conference or not conference.date_heure_programmation:
        return None

    cal = Calendar()
    # Propriétés standard du calendrier
    cal.add('prodid', '-//MonLogicielDeConference//votredomaine.com//')
    cal.add('version', '2.0')

    event = IcsEvent()
    event.add('uid', f"{conference.id}@votredomaine.com") # Assurer un UID unique
    event.add('summary', conference.titre)
    event.add('dtstart', conference.date_heure_programmation)

    # Calculer dtend basé sur conference.duree_minutes si disponible et positive, sinon durée par défaut
    duration_to_use = default_duration_minutes
    if conference.duree_minutes is not None and conference.duree_minutes > 0:
        duration_to_use = conference.duree_minutes

    dt_end = conference.date_heure_programmation + timedelta(minutes=duration_to_use)
    event.add('dtend', dt_end)

    # dtstamp est généralement l'heure de création/modification de l'événement .ics lui-même
    event.add('dtstamp', conference.date_heure_creation if conference.date_heure_creation else datetime.now())

    if conference.lieu:
        event.add('location', conference.lieu)

    description_ics = conference.description_calendrier if conference.description_calendrier else conference.notes_rapport
    if description_ics: # S'assurer qu'il y a une description à ajouter
        event.add('description', description_ics)

    # Ajouter un rappel si configuré dans la conférence
    if conference.rappel_active and conference.minutes_rappel_avant is not None and conference.minutes_rappel_avant >= 0:
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        # Le trigger doit être une propriété de type DURATION, négative pour "avant"
        alarm.add('trigger', timedelta(minutes=-conference.minutes_rappel_avant))
        alarm.add('description', f"Rappel: {conference.titre}")
        event.add_component(alarm)

    cal.add_component(event)

    try:
        return cal.to_ical().decode('utf-8').replace('\r\n', '\n') # Normaliser les fins de ligne pour tests/comparaisons
    except Exception as e:
        print(f"Erreur lors de la génération du contenu iCalendar pour la conférence {conference.id}: {e}")
        return None


# --- Gestion des Rapports ---

def generer_texte_rapport_conference(conference_id: str) -> str:
    """
    Génère un rapport textuel simple pour une conférence donnée.
    """
    conference = obtenir_details_conference(conference_id) # Utilise déjà SQLite
    if not conference:
        raise ValueError(f"Conférence avec ID '{conference_id}' non trouvée.")

    rapport_lignes = [
        f"Rapport de Conférence",
        f"-------------------------",
        f"ID Conférence: {conference.id}",
        f"Titre: {conference.titre}",
    ]
    if conference.date_heure_creation:
        # Vérification ajoutée car date_heure_creation peut être None si _row_to_conference_obj
        # reçoit une date mal formatée ou NULL de la BD, bien que la colonne soit NOT NULL.
        # C'est une double sécurité.
        rapport_lignes.append(f"Date de Création: {conference.date_heure_creation.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        rapport_lignes.append("Date de Création: Non disponible")


    if conference.date_heure_programmation:
        rapport_lignes.append(f"Date Programmée: {conference.date_heure_programmation.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        rapport_lignes.append("Date Programmée: Non spécifiée")

    rapport_lignes.append(f"Statut: {conference.statut}")

    if conference.client_id:
        client = obtenir_client(conference.client_id) # Utilise déjà SQLite
        client_nom = client.nom if client else "Client inconnu (ID non trouvé)"
        rapport_lignes.append(f"Client Associé: {client_nom} (ID: {conference.client_id})")
    else:
        rapport_lignes.append("Client Associé: Aucun")

    if conference.lieu:
        rapport_lignes.append(f"Lieu: {conference.lieu}")
    else:
        rapport_lignes.append("Lieu: Non spécifié")

    if conference.duree_minutes is not None and conference.duree_minutes > 0:
        rapport_lignes.append(f"Durée Prévue: {conference.duree_minutes} minutes")
    else:
        rapport_lignes.append("Durée Prévue: Non spécifiée")

    if conference.participants_externes:
        rapport_lignes.append(f"Participants Externes: {conference.participants_externes}")
    else:
        rapport_lignes.append("Participants Externes: Aucun")

    rapport_lignes.append(f"Rappel Actif: {'Oui' if conference.rappel_active else 'Non'}")
    if conference.rappel_active and conference.minutes_rappel_avant is not None:
        rapport_lignes.append(f"Rappel Avant (minutes): {conference.minutes_rappel_avant}")

    rapport_lignes.append(f"-------------------------")
    rapport_lignes.append(f"Description Calendrier:")
    rapport_lignes.append(conference.description_calendrier if conference.description_calendrier else "Aucune description pour calendrier.")
    rapport_lignes.append(f"-------------------------")
    rapport_lignes.append(f"Notes / Rapport Détaillé:")
    rapport_lignes.append(conference.notes_rapport if conference.notes_rapport else "Aucune note enregistrée.")
    rapport_lignes.append(f"-------------------------")

    return "\n".join(rapport_lignes)


if __name__ == '__main__':
    # Utiliser un fichier de test spécifique pour la démo __main__ pour éviter les conflits
    main_demo_db_file = "conference_manager_demo.db"
    reinitialiser_donnees(db_name=main_demo_db_file)

    print("\n--- Démo Gestion Clients (SQLite) ---")
    client1_id, client2_id = None, None
    try:
        client1 = creer_client(nom="Alpha Inc. (Démo SQLite)", coordonnees={"email": "contact@alpha-demo.com"})
        client1_id = client1.id
        client2 = creer_client(nom="Beta Corp. (Démo SQLite)", coordonnees={"tel": "1234567890"})
        client2_id = client2.id
        print(f"Client 1 créé: ID {client1.id}, Nom: {client1.nom}")
        print(f"Client 2 créé: ID {client2.id}, Nom: {client2.nom}")

        print("\nListe des clients après création:")
        for c_idx, c in enumerate(lister_clients()):
            print(f" {c_idx + 1}. ID: {c.id}, Nom: {c.nom}, Coordonnées: {c.coordonnees}")

        if client1_id:
            retrieved_c1 = obtenir_client(client1_id)
            print(f"\nDétails Client 1 (obtenu par ID): {retrieved_c1.nom if retrieved_c1 else 'Non trouvé'}")

            print("\nMise à jour Client 1...")
            client1_maj = mettre_a_jour_client(client1_id, nom="Alpha Inc. Modifié (Démo)", coordonnees={"email": "new@alpha-demo.com", "tel": "987654321"})
            print(f"Client 1 après MàJ: Nom: {client1_maj.nom if client1_maj else 'Non trouvé'}, Coordonnées: {client1_maj.coordonnees if client1_maj else ''}")

        print(f"\nObtenir un client inexistant: {obtenir_client('id-bidon-123')}")

        if client2_id:
            print(f"\nSuppression Client 2 (ID: {client2_id})...")
            supprime_ok = supprimer_client(client2_id)
            print(f"Client 2 supprimé avec succès: {supprime_ok}")
            print(f"Tentative d'obtenir Client 2 après suppression: {obtenir_client(client2_id)}")

        print("\nListe des clients après suppression:")
        for c_idx, c in enumerate(lister_clients()):
            print(f" {c_idx + 1}. ID: {c.id}, Nom: {c.nom}")

        # Test de suppression d'un client déjà supprimé ou inexistant
        print("\nTentative de suppression d'un client inexistant (id-bidon-456)...")
        supprime_ko = supprimer_client("id-bidon-456")
        print(f"Suppression client inexistant réussie (attendu False): {supprime_ko}")


    except ValueError as e:
        print(f"Erreur de valeur: {e}")
    except ConnectionError as e:
        print(f"Erreur de connexion BD: {e}")
    except RuntimeError as e:
        print(f"Erreur runtime BD: {e}")
    except Exception as e: # Attraper d'autres exceptions potentielles
        import traceback
        print(f"Erreur inattendue lors de la démo client: {e}")
        traceback.print_exc()


    # --- Démo Gestion Conférences (maintenant avec SQLite) ---
    print("\n\n--- Démo Gestion Conférences (SQLite) ---")

    demo_client_for_conf = None
    if client1_id:
         demo_client_for_conf = obtenir_client(client1_id)

    conf1_demo_id, conf2_demo_id = None, None
    try:
        print("\nCréation de conférences...")
        conf1_date_prog = datetime.now() + timedelta(days=5)
        conf1_demo = creer_conference(
            titre="Conférence Démo 1 (SQLite)",
            date_heure_programmation=conf1_date_prog,
            client_id=demo_client_for_conf.id if demo_client_for_conf else None,
            notes="Notes pour la démo 1."
        )
        conf1_demo_id = conf1_demo.id
        print(f"Conférence 1 créée: {conf1_demo.titre} (ID: {conf1_demo.id})")

        conf2_demo = creer_conference(
            titre="Conférence Démo 2 (SQLite)",
            participants_externes="Participant Externe Démo",
            notes="Notes pour la démo 2."
        )
        conf2_demo_id = conf2_demo.id
        print(f"Conférence 2 créée: {conf2_demo.titre} (ID: {conf2_demo.id})")

        print("\nListe de toutes les conférences (SQLite):")
        all_confs_sqlite = lister_conferences()
        for conf_idx, conf_item in enumerate(all_confs_sqlite):
            print(f" {conf_idx+1}. {conf_item.titre} (ID: {conf_item.id}), Statut: {conf_item.statut}, Client: {conf_item.client_id or 'Aucun'}")

        if conf1_demo_id:
            print(f"\nDétails Conférence 1: {obtenir_details_conference(conf1_demo_id).titre}")
            print("Mise à jour Conférence 1 (notes et statut)...")
            conf1_updated = ajouter_ou_maj_notes(conf1_demo_id, "Notes mises à jour pour la démo 1.")
            conf1_updated = changer_statut_conference(conf1_demo_id, Conference.CONFERENCE_STATUT_COMPLETED)
            print(f"Conférence 1 MàJ: Titre: {conf1_updated.titre}, Notes: '{conf1_updated.notes_rapport}', Statut: {conf1_updated.statut}")

        if conf2_demo_id and demo_client_for_conf:
            print(f"\nAffectation du client '{demo_client_for_conf.nom}' à la Conférence 2...")
            conf2_updated = affecter_client_a_conference(conf2_demo_id, demo_client_for_conf.id)
            print(f"Conférence 2 MàJ: Titre: {conf2_updated.titre}, Client ID: {conf2_updated.client_id}")

        print("\nListe des conférences COMPLETED:")
        completed_confs = lister_conferences(statut=Conference.CONFERENCE_STATUT_COMPLETED)
        for conf_item in completed_confs:
            print(f" - {conf_item.titre}")

        if demo_client_for_conf:
            print(f"\nListe des conférences pour client '{demo_client_for_conf.nom}':")
            client_confs = lister_conferences(client_id=demo_client_for_conf.id)
            for conf_item in client_confs:
                print(f" - {conf_item.titre}")

        if conf2_demo_id:
            print(f"\nSuppression Conférence 2 (ID: {conf2_demo_id})...")
            deleted_conf2 = supprimer_conference(conf2_demo_id)
            print(f"Conférence 2 supprimée: {deleted_conf2}")
            print(f"Vérification Conférence 2: {obtenir_details_conference(conf2_demo_id)}")

        print("\nListe finale des conférences (SQLite):")
        for conf_item in lister_conferences():
            print(f" - {conf_item.titre}, Statut: {conf_item.statut}")

    except ValueError as e:
        print(f"Erreur de valeur (conférences SQLite): {e}")
    except ConnectionError as e:
        print(f"Erreur de connexion BD (conférences SQLite): {e}")
    except RuntimeError as e:
        print(f"Erreur runtime BD (conférences SQLite): {e}")
    except Exception as e:
        import traceback
        print(f"Erreur inattendue lors de la démo conférences (SQLite): {e}")
        traceback.print_exc()


    # --- Logique de Planification (maintenant avec SQLite) ---
    print("\n\n--- Démo Planification (SQLite) ---")

    # Créer quelques conférences futures pour tester la planification en BD
    if demo_client_for_conf:
        try:
            # S'assurer que ces conférences aient des statuts initiaux corrects pour être récupérées
            conf_plan_A = creer_conference(titre="Conf Future A (Planif Démo)", date_heure_programmation=datetime.now() + timedelta(days=2), client_id=demo_client_for_conf.id)
            conf_plan_B = creer_conference(titre="Conf Future B (Planif Démo)", date_heure_programmation=datetime.now() + timedelta(days=1))
            conf_plan_C_annulee = creer_conference(titre="Conf Future C (Planif Démo, Sera Annulée)", date_heure_programmation=datetime.now() + timedelta(days=3), client_id=demo_client_for_conf.id)
            if conf_plan_C_annulee: # Vérifier si la création a réussi
                mettre_a_jour_conference(conf_plan_C_annulee.id, statut=Conference.CONFERENCE_STATUT_CANCELLED) # Utiliser la fonction SQLite

            # Conférence passée pour s'assurer qu'elle n'est pas listée
            creer_conference(titre="Conf Passée (Planif Démo)", date_heure_programmation=datetime.now() - timedelta(days=1), client_id=demo_client_for_conf.id)

        except Exception as e:
            print(f"Erreur création conf pour planification: {e}")

    conferences_a_venir_sqlite = obtenir_conferences_a_venir()
    print(f"Conférences à venir (depuis SQLite: {len(conferences_a_venir_sqlite)}):")
    for conf_idx, conf_item in enumerate(conferences_a_venir_sqlite):
        prog_date_str = conf_item.date_heure_programmation.strftime('%Y-%m-%d %H:%M') if conf_item.date_heure_programmation else "N/A"
        print(f" {conf_idx+1}. {conf_item.titre} le {prog_date_str} (Statut: {conf_item.statut})")


    # --- Génération de Rapport (devrait fonctionner si obtenir_details_conference est OK) ---
    print("\n\n--- Démo Génération de Rapport (SQLite) ---")
    if conf1_demo_id: # S'assurer que conf1_demo_id a été défini
        conf_pour_rapport = obtenir_details_conference(conf1_demo_id) # Obtenir l'objet conférence
        if conf_pour_rapport:
            print(f"Génération du rapport pour la conférence: {conf_pour_rapport.titre} (ID: {conf_pour_rapport.id})")
            try:
                rapport_texte_sqlite = generer_texte_rapport_conference(conf_pour_rapport.id)
                print(rapport_texte_sqlite)
            except ValueError as e:
                print(f"Erreur génération rapport: {e}")
        else:
            print(f"Conférence avec ID {conf1_demo_id} non trouvée pour le rapport.")
    else:
        print("Aucune conférence de démo (conf1_demo_id) disponible pour générer un rapport.")


    # Nettoyage du fichier de base de données de démo
    if main_demo_db_file != ":memory:" and os.path.exists(main_demo_db_file):
        try:
            # Petite pause pour s'assurer que les connexions sont bien fermées avant de supprimer
            # import time
            # time.sleep(0.1)
            os.remove(main_demo_db_file)
            print(f"\nFichier de base de données de démo '{main_demo_db_file}' supprimé.")
        except OSError as e:
            print(f"\nImpossible de supprimer le fichier de base de données de démo '{main_demo_db_file}': {e}")
            print("Cela peut arriver si une connexion est toujours active (par ex. un explorateur de BD SQLite).")
