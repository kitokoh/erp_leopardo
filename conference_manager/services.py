# This file will contain the business logic for managing conferences.

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid # Bien que les modèles utilisent uuid, le service pourrait en avoir besoin pour la validation

from .models import Client, Conference # Utilisation d'un import relatif

# Structures de données en mémoire pour simuler une base de données
_clients: Dict[str, Client] = {}
_conferences: Dict[str, Conference] = {}


# --- Gestion des Clients ---

def creer_client(nom: str, coordonnees: Optional[Dict[str, str]] = None) -> Client:
    """Crée un nouveau client et le stocke en mémoire."""
    if not nom:
        raise ValueError("Le nom du client ne peut pas être vide.")

    # Vérifier si un client avec le même nom existe déjà pour éviter les doublons simples
    # Dans une vraie application, on pourrait avoir des critères plus complexes
    for client in _clients.values():
        if client.nom == nom:
            raise ValueError(f"Un client avec le nom '{nom}' existe déjà.")

    nouveau_client = Client(nom=nom, coordonnees=coordonnees if coordonnees else {})
    _clients[nouveau_client.id] = nouveau_client
    return nouveau_client

def obtenir_client(client_id: str) -> Optional[Client]:
    """Récupère un client par son ID."""
    return _clients.get(client_id)

def lister_clients() -> List[Client]:
    """Retourne la liste de tous les clients."""
    return list(_clients.values())


# --- Gestion des Conférences ---

def creer_conference(titre: str,
                     date_heure_programmation: Optional[datetime] = None,
                     notes: str = "",
                     client_id: Optional[str] = None,
                     participants_externes: str = "") -> Conference:
    """Crée une nouvelle conférence et la stocke en mémoire."""
    if not titre:
        raise ValueError("Le titre de la conférence ne peut pas être vide.")

    if client_id and client_id not in _clients:
        raise ValueError(f"Client avec ID '{client_id}' non trouvé.")

    nouvelle_conference = Conference(
        titre=titre,
        date_heure_programmation=date_heure_programmation,
        notes_rapport=notes,
        client_id=client_id,
        participants_externes=participants_externes,
        statut=Conference.CONFERENCE_STATUT_PLANNED # Statut initial
    )
    _conferences[nouvelle_conference.id] = nouvelle_conference
    return nouvelle_conference

def obtenir_details_conference(conference_id: str) -> Optional[Conference]:
    """Récupère une conférence par son ID."""
    return _conferences.get(conference_id)

def ajouter_ou_maj_notes(conference_id: str, nouvelles_notes: str) -> Conference:
    """Ajoute ou met à jour les notes d'une conférence."""
    conference = obtenir_details_conference(conference_id)
    if not conference:
        raise ValueError(f"Conférence avec ID '{conference_id}' non trouvée.")

    conference.notes_rapport = nouvelles_notes
    return conference

def affecter_client_a_conference(conference_id: str, client_id: str) -> Conference:
    """Affecte un client existant à une conférence."""
    conference = obtenir_details_conference(conference_id)
    if not conference:
        raise ValueError(f"Conférence avec ID '{conference_id}' non trouvée.")

    client = obtenir_client(client_id)
    if not client:
        raise ValueError(f"Client avec ID '{client_id}' non trouvé.")

    conference.client_id = client_id
    return conference

def changer_statut_conference(conference_id: str, nouveau_statut: str) -> Conference:
    """Change le statut d'une conférence."""
    conference = obtenir_details_conference(conference_id)
    if not conference:
        raise ValueError(f"Conférence avec ID '{conference_id}' non trouvée.")

    if nouveau_statut not in Conference.VALID_STATUSES:
        raise ValueError(f"Statut invalide: {nouveau_statut}. Doit être un de {Conference.VALID_STATUSES}")

    conference.statut = nouveau_statut
    return conference

def lister_conferences(client_id: Optional[str] = None, statut: Optional[str] = None) -> List[Conference]:
    """Retourne une liste de conférences, potentiellement filtrée par client et/ou statut."""
    resultats = list(_conferences.values())

    if client_id:
        if client_id not in _clients:
            # On pourrait aussi choisir de lever une erreur ou retourner une liste vide.
            # Pour l'instant, si le client_id est fourni mais invalide, on retourne les conférences sans client_id correspondant (liste vide pour ce filtre)
             return [conf for conf in resultats if conf.client_id == client_id]
        resultats = [conf for conf in resultats if conf.client_id == client_id]

    if statut:
        if statut not in Conference.VALID_STATUSES:
            raise ValueError(f"Statut de filtre invalide: {statut}. Doit être un de {Conference.VALID_STATUSES}")
        resultats = [conf for conf in resultats if conf.statut == statut]

    return resultats

# Fonctions utilitaires pour la gestion des données en mémoire (pour les tests ou le débogage)
def reinitialiser_donnees():
    """Réinitialise les données en mémoire. Utile pour les tests."""
    global _clients, _conferences
    _clients = {}
    _conferences = {}

# Exemple d'utilisation (peut être commenté ou retiré plus tard)
if __name__ == '__main__':
    reinitialiser_donnees()

    # Création de clients
    try:
        client1 = creer_client(nom="Alpha Inc.", coordonnees={"email": "contact@alpha.com"})
        client2 = creer_client(nom="Beta Corp.", coordonnees={"tel": "1234567890"})
        print(f"Clients créés: {lister_clients()}")
    except ValueError as e:
        print(f"Erreur création client: {e}")

    # Création de conférences
    try:
        conf1_date = datetime(2024, 9, 1, 10, 0, 0)
        conf1 = creer_conference(titre="Présentation Produit X", date_heure_programmation=conf1_date, client_id=client1.id)
        print(f"Conférence 1 créée: {conf1}")

        conf2 = creer_conference(titre="Suivi Prospect Y", participants_externes="M. Yves Martin")
        print(f"Conférence 2 créée: {conf2}")
    except ValueError as e:
        print(f"Erreur création conférence: {e}")

    # Modification de conférence
    if 'conf1' in locals():
        try:
            ajouter_ou_maj_notes(conf1.id, "Notes initiales: Discussion sur les fonctionnalités clés.")
            changer_statut_conference(conf1.id, Conference.CONFERENCE_STATUT_COMPLETED)
            print(f"Conférence 1 mise à jour: {obtenir_details_conference(conf1.id)}")
        except ValueError as e:
            print(f"Erreur MàJ Conférence 1: {e}")

    if 'conf2' in locals() and 'client2' in locals():
        try:
            affecter_client_a_conference(conf2.id, client2.id)
            print(f"Conférence 2 affectée au client 2: {obtenir_details_conference(conf2.id)}")
        except ValueError as e:
            print(f"Erreur affectation client Conférence 2: {e}")

    # Listage
    print(f"Toutes les conférences: {lister_conferences()}")
    if 'client1' in locals():
        print(f"Conférences pour Alpha Inc.: {lister_conferences(client_id=client1.id)}")
    print(f"Conférences planifiées: {lister_conferences(statut=Conference.CONFERENCE_STATUT_PLANNED)}")
    print(f"Conférences terminées: {lister_conferences(statut=Conference.CONFERENCE_STATUT_COMPLETED)}")

    # Test d'erreur: client inexistant pour une conférence
    try:
        creer_conference(titre="Test Erreur Client", client_id="id_inexistant")
    except ValueError as e:
        print(f"Erreur attendue (client inexistant): {e}")

    # Test d'erreur: statut invalide
    if 'conf1' in locals():
        try:
            changer_statut_conference(conf1.id, "STATUT_ERRONE")
        except ValueError as e:
            print(f"Erreur attendue (statut invalide): {e}")

# --- Logique de Planification ---

def obtenir_conferences_a_venir() -> List[Conference]:
    """
    Retourne une liste des conférences planifiées (date de programmation dans le futur)
    et non terminées ou annulées, triées par date de programmation.
    """
    maintenant = datetime.now()
    conferences_futures = []
    for conf in _conferences.values():
        if conf.date_heure_programmation and conf.date_heure_programmation > maintenant:
            if conf.statut not in [Conference.CONFERENCE_STATUT_COMPLETED, Conference.CONFERENCE_STATUT_CANCELLED]:
                conferences_futures.append(conf)

    # Tri par date de programmation croissante
    conferences_futures.sort(key=lambda c: c.date_heure_programmation)
    return conferences_futures


if __name__ == '__main__':
    reinitialiser_donnees()

    # Création de clients
    try:
        client1 = creer_client(nom="Alpha Inc.", coordonnees={"email": "contact@alpha.com"})
        client2 = creer_client(nom="Beta Corp.", coordonnees={"tel": "1234567890"})
        print(f"Clients créés: {lister_clients()}")
    except ValueError as e:
        print(f"Erreur création client: {e}")

    # Création de conférences
    try:
        conf1_date = datetime(2024, 9, 1, 10, 0, 0) # Passé (si on est après cette date lors de l'exécution) ou futur
        conf_passe_date = datetime(2023, 1, 1, 10, 0, 0)
        conf_futur1_date = datetime.now().replace(year=datetime.now().year + 1, month=1, day=10, hour=14)
        conf_futur2_date = datetime.now().replace(year=datetime.now().year + 1, month=1, day=5, hour=10)


        conf1 = creer_conference(titre="Présentation Produit X", date_heure_programmation=conf1_date, client_id=client1.id)
        print(f"Conférence 1 créée: {conf1}")

        conf2 = creer_conference(titre="Suivi Prospect Y", participants_externes="M. Yves Martin") # Pas de date de programmation
        print(f"Conférence 2 créée: {conf2}")

        conf_passe = creer_conference(titre="Ancienne réunion", date_heure_programmation=conf_passe_date, client_id=client1.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)
        conf_futur1 = creer_conference(titre="Réunion Future 1 (plus tard)", date_heure_programmation=conf_futur1_date, client_id=client2.id)
        conf_futur2 = creer_conference(titre="Réunion Future 2 (plus tôt)", date_heure_programmation=conf_futur2_date, client_id=client1.id)
        conf_futur_annulee = creer_conference(titre="Réunion Future Annulée", date_heure_programmation=conf_futur1_date, client_id=client2.id, statut=Conference.CONFERENCE_STATUT_CANCELLED)

    except ValueError as e:
        print(f"Erreur création conférence: {e}")

    # Modification de conférence
    if 'conf1' in locals():
        try:
            ajouter_ou_maj_notes(conf1.id, "Notes initiales: Discussion sur les fonctionnalités clés.")
            # On ne la met pas terminée pour la tester dans les conférences à venir si sa date est future
            # changer_statut_conference(conf1.id, Conference.CONFERENCE_STATUT_COMPLETED)
            print(f"Conférence 1 mise à jour: {obtenir_details_conference(conf1.id)}")
        except ValueError as e:
            print(f"Erreur MàJ Conférence 1: {e}")

    if 'conf2' in locals() and 'client2' in locals():
        try:
            affecter_client_a_conference(conf2.id, client2.id)
            print(f"Conférence 2 affectée au client 2: {obtenir_details_conference(conf2.id)}")
        except ValueError as e:
            print(f"Erreur affectation client Conférence 2: {e}")

    # Listage
    print(f"Toutes les conférences: {lister_conferences()}")
    if 'client1' in locals():
        print(f"Conférences pour Alpha Inc.: {lister_conferences(client_id=client1.id)}")
    print(f"Conférences planifiées (statut): {lister_conferences(statut=Conference.CONFERENCE_STATUT_PLANNED)}")
    print(f"Conférences terminées: {lister_conferences(statut=Conference.CONFERENCE_STATUT_COMPLETED)}")

    # Test d'erreur: client inexistant pour une conférence
    try:
        creer_conference(titre="Test Erreur Client", client_id="id_inexistant")
    except ValueError as e:
        print(f"Erreur attendue (client inexistant): {e}")

    # Test d'erreur: statut invalide
    if 'conf1' in locals(): # s'assure que conf1 a été créée
        try:
            changer_statut_conference(conf1.id, "STATUT_ERRONE")
        except ValueError as e:
            print(f"Erreur attendue (statut invalide): {e}")

    # Test de la planification
    print("\n--- Test Planification ---")
    conferences_a_venir = obtenir_conferences_a_venir()
    print(f"Conférences à venir ({len(conferences_a_venir)}):")
    for conf in conferences_a_venir:
        print(f"  - {conf.titre} le {conf.date_heure_programmation} (Statut: {conf.statut})")

# --- Gestion des Rapports ---

def generer_texte_rapport_conference(conference_id: str) -> str:
    """
    Génère un rapport textuel simple pour une conférence donnée.
    """
    conference = obtenir_details_conference(conference_id)
    if not conference:
        raise ValueError(f"Conférence avec ID '{conference_id}' non trouvée.")

    rapport_lignes = [
        f"Rapport de Conférence",
        f"-------------------------",
        f"ID Conférence: {conference.id}",
        f"Titre: {conference.titre}",
        f"Date de Création: {conference.date_heure_creation.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if conference.date_heure_programmation:
        rapport_lignes.append(f"Date Programmée: {conference.date_heure_programmation.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        rapport_lignes.append("Date Programmée: Non spécifiée")

    rapport_lignes.append(f"Statut: {conference.statut}")

    if conference.client_id:
        client = obtenir_client(conference.client_id)
        client_nom = client.nom if client else "Client inconnu (ID non trouvé)"
        rapport_lignes.append(f"Client Associé: {client_nom} (ID: {conference.client_id})")
    else:
        rapport_lignes.append("Client Associé: Aucun")

    if conference.participants_externes:
        rapport_lignes.append(f"Participants Externes: {conference.participants_externes}")
    else:
        rapport_lignes.append("Participants Externes: Aucun")

    rapport_lignes.append(f"-------------------------")
    rapport_lignes.append(f"Notes / Rapport:")
    rapport_lignes.append(conference.notes_rapport if conference.notes_rapport else "Aucune note enregistrée.")
    rapport_lignes.append(f"-------------------------")

    return "\n".join(rapport_lignes)


if __name__ == '__main__':
    reinitialiser_donnees()

    # Création de clients
    try:
        client1 = creer_client(nom="Alpha Inc.", coordonnees={"email": "contact@alpha.com"})
        client2 = creer_client(nom="Beta Corp.", coordonnees={"tel": "1234567890"})
        # print(f"Clients créés: {lister_clients()}")
    except ValueError as e:
        print(f"Erreur création client: {e}")

    # Création de conférences
    conf_id_rapport = None
    try:
        conf1_date = datetime(2024, 9, 1, 10, 0, 0)
        conf_futur1_date = datetime.now().replace(year=datetime.now().year + 1, month=1, day=10, hour=14)
        conf_futur2_date = datetime.now().replace(year=datetime.now().year + 1, month=1, day=5, hour=10)


        conf1 = creer_conference(titre="Présentation Produit X", date_heure_programmation=conf1_date, client_id=client1.id, notes="Discussion sur A, B, C.")
        conf_id_rapport = conf1.id # Sauvegarder pour le rapport
        changer_statut_conference(conf1.id, Conference.CONFERENCE_STATUT_COMPLETED)


        creer_conference(titre="Suivi Prospect Y", participants_externes="M. Yves Martin", notes="Prospect intéressé, rappel à faire.")

        creer_conference(titre="Ancienne réunion", date_heure_programmation=datetime(2023,1,1), client_id=client1.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)
        creer_conference(titre="Réunion Future 1 (plus tard)", date_heure_programmation=conf_futur1_date, client_id=client2.id)
        creer_conference(titre="Réunion Future 2 (plus tôt)", date_heure_programmation=conf_futur2_date, client_id=client1.id)
        creer_conference(titre="Réunion Future Annulée", date_heure_programmation=conf_futur1_date, client_id=client2.id, statut=Conference.CONFERENCE_STATUT_CANCELLED)

    except ValueError as e:
        print(f"Erreur création conférence: {e}")

    # ... (autres tests du main) ...

    # Test de la planification
    print("\n--- Test Planification ---")
    conferences_a_venir = obtenir_conferences_a_venir()
    print(f"Conférences à venir ({len(conferences_a_venir)}):")
    for conf in conferences_a_venir:
        print(f"  - {conf.titre} le {conf.date_heure_programmation} (Statut: {conf.statut})")

    # Test de génération de rapport
    if conf_id_rapport:
        print("\n--- Test Génération de Rapport ---")
        try:
            rapport_texte = generer_texte_rapport_conference(conf_id_rapport)
            print(rapport_texte)
        except ValueError as e:
            print(f"Erreur génération rapport: {e}")

    # Test rapport pour conférence sans notes et sans client
    conf_sans_details_id = None
    try:
        conf_sans_details = creer_conference(titre="Conférence minimale")
        conf_sans_details_id = conf_sans_details.id
        changer_statut_conference(conf_sans_details_id, Conference.CONFERENCE_STATUT_IN_PROGRESS)
    except ValueError as e:
        print(f"Erreur création conf simple: {e}")

    if conf_sans_details_id:
        print("\n--- Test Rapport Conférence Minimale ---")
        try:
            rapport_minimal = generer_texte_rapport_conference(conf_sans_details_id)
            print(rapport_minimal)
        except ValueError as e:
            print(f"Erreur rapport minimal: {e}")
