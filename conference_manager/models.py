# This file will contain the data models for the conference manager.

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

class Client:
    """Represents a client."""
    def __init__(self, nom: str, coordonnees: Optional[Dict[str, str]] = None, client_id: Optional[str] = None):
        self.id: str = client_id if client_id else str(uuid.uuid4())
        self.nom: str = nom
        self.coordonnees: Dict[str, str] = coordonnees if coordonnees else {}

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, nom='{self.nom}')>"

class Conference:
    """Represents a conference or meeting."""
    CONFERENCE_STATUT_PLANNED = "Planifiée"
    CONFERENCE_STATUT_IN_PROGRESS = "En cours"
    CONFERENCE_STATUT_COMPLETED = "Terminée"
    CONFERENCE_STATUT_CANCELLED = "Annulée"

    VALID_STATUSES = [
        CONFERENCE_STATUT_PLANNED,
        CONFERENCE_STATUT_IN_PROGRESS,
        CONFERENCE_STATUT_COMPLETED,
        CONFERENCE_STATUT_CANCELLED,
    ]

    def __init__(self,
                 titre: str,
                 conference_id: Optional[str] = None,
                 date_heure_creation: Optional[datetime] = None,
                 date_heure_programmation: Optional[datetime] = None,
                 notes_rapport: str = "",
                 client_id: Optional[str] = None,
                 participants_externes: str = "",
                 statut: str = CONFERENCE_STATUT_PLANNED,
                 lieu: Optional[str] = None,
                 description_calendrier: Optional[str] = None,
                 rappel_active: bool = True,
                 minutes_rappel_avant: Optional[int] = 30,
                 utilisateur_id: Optional[str] = None,
                 duree_minutes: Optional[int] = 60, # Valeur par défaut de 60 minutes
                 rappel_envoye: bool = False):

        self.id: str = conference_id if conference_id else str(uuid.uuid4())
        self.titre: str = titre
        self.date_heure_creation: datetime = date_heure_creation if date_heure_creation else datetime.now()
        self.date_heure_programmation: Optional[datetime] = date_heure_programmation
        self.notes_rapport: str = notes_rapport
        self.client_id: Optional[str] = client_id
        self.participants_externes: str = participants_externes

        if statut not in self.VALID_STATUSES:
            raise ValueError(f"Statut invalide: {statut}. Doit être un de {self.VALID_STATUSES}")
        self.statut: str = statut

        self.lieu: Optional[str] = lieu
        self.description_calendrier: Optional[str] = description_calendrier
        self.rappel_active: bool = rappel_active
        self.minutes_rappel_avant: Optional[int] = minutes_rappel_avant if rappel_active else None # Pas de minutes si rappel inactif
        self.utilisateur_id: Optional[str] = utilisateur_id
        self.duree_minutes: Optional[int] = duree_minutes
        self.rappel_envoye: bool = rappel_envoye

    def __repr__(self) -> str:
        return f"<Conference(id={self.id}, titre='{self.titre}', statut='{self.statut}', utilisateur_id='{self.utilisateur_id}', rappel_envoye={self.rappel_envoye})>"

# Example usage (optional, for testing or demonstration)
if __name__ == '__main__':
    client1 = Client(nom="Entreprise Test", coordonnees={"email": "contact@entreprise.com"})
    print(client1)

    conference1 = Conference(titre="Réunion de lancement",
                             date_heure_programmation=datetime(2024, 8, 15, 14, 0, 0),
                             client_id=client1.id,
                             statut=Conference.CONFERENCE_STATUT_PLANNED)
    print(conference1)

    conference2 = Conference(titre="Point de suivi",
                             notes_rapport="Discussion sur les avancées du projet X.",
                             participants_externes="M. Dupont (Prospect)",
                             statut=Conference.CONFERENCE_STATUT_COMPLETED)
    print(conference2)

    try:
        conference_invalid_status = Conference(titre="Test Statut", statut="Invalide")
    except ValueError as e:
        print(f"Error: {e}")
