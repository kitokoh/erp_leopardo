# This file will contain unit tests for the conference_manager.services module.
import unittest
from datetime import datetime, timedelta

# Ajustement de l'import pour correspondre à la structure du projet et aux bonnes pratiques
# Si tests/ est au même niveau que conference_manager/ et que le point d'entrée des tests est la racine du projet:
# from conference_manager import services, models
# Cependant, pour exécution directe de ce fichier ou via `python -m unittest discover`,
# il est souvent plus simple d'ajouter le répertoire parent au PYTHONPATH ou de faire des imports relatifs.
# Pour cet environnement, je vais supposer que le PYTHONPATH est configuré ou que l'on navigue.
# Si ce n'est pas le cas, un import relatif comme suit pourrait être utilisé si la structure le permet :
# from ..conference_manager import services, models

# Solution la plus robuste pour les environnements de test typiques :
import sys
import os
# Ajoute le répertoire parent (racine du projet) au sys.path pour permettre les imports absolus des modules du projet
# Cela suppose que ce fichier de test est dans un sous-répertoire comme `tests/conference_manager/`
# et que `conference_manager` est un package au niveau de la racine du projet.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) # Remonte de deux niveaux
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from conference_manager import services
from conference_manager.models import Client, Conference


class TestConferenceServices(unittest.TestCase):

    def setUp(self):
        """Appelé avant chaque méthode de test."""
        services.reinitialiser_donnees()
        # Créer quelques données initiales si nécessaire pour de nombreux tests
        self.client1 = services.creer_client(nom="Client Test 1", coordonnees={"email": "client1@test.com"})
        self.client2 = services.creer_client(nom="Client Test 2", coordonnees={"tel": "0123456789"})

    def tearDown(self):
        """Appelé après chaque méthode de test."""
        services.reinitialiser_donnees()

    # --- Tests pour la gestion des Clients ---
    def test_creer_client(self):
        nom_client = "Nouveau Client SA"
        coordonnees_client = {"adresse": "1 rue Test"}
        client = services.creer_client(nom=nom_client, coordonnees=coordonnees_client)
        self.assertIsNotNone(client.id)
        self.assertEqual(client.nom, nom_client)
        self.assertEqual(client.coordonnees, coordonnees_client)

        retrieved_client = services.obtenir_client(client.id)
        self.assertEqual(retrieved_client, client)

    def test_creer_client_nom_vide(self):
        with self.assertRaisesRegex(ValueError, "Le nom du client ne peut pas être vide."):
            services.creer_client(nom="")

    def test_creer_client_duplique(self):
        services.creer_client(nom="Client Unique")
        with self.assertRaisesRegex(ValueError, "Un client avec le nom 'Client Unique' existe déjà."):
            services.creer_client(nom="Client Unique")

    def test_obtenir_client_inexistant(self):
        self.assertIsNone(services.obtenir_client("id_bidon"))

    def test_lister_clients(self):
        clients = services.lister_clients()
        self.assertEqual(len(clients), 2) # client1 et client2 du setUp
        services.creer_client(nom="Client Test 3")
        clients = services.lister_clients()
        self.assertEqual(len(clients), 3)


    # --- Tests pour la gestion des Conférences ---
    def test_creer_conference(self):
        titre_conf = "Réunion de Projet Alpha"
        date_prog = datetime.now() + timedelta(days=5)
        conf = services.creer_conference(
            titre=titre_conf,
            date_heure_programmation=date_prog,
            client_id=self.client1.id,
            notes="Préparer la démo.",
            participants_externes="Partenaire X"
        )
        self.assertIsNotNone(conf.id)
        self.assertEqual(conf.titre, titre_conf)
        self.assertEqual(conf.date_heure_programmation, date_prog)
        self.assertEqual(conf.client_id, self.client1.id)
        self.assertEqual(conf.notes_rapport, "Préparer la démo.")
        self.assertEqual(conf.participants_externes, "Partenaire X")
        self.assertEqual(conf.statut, Conference.CONFERENCE_STATUT_PLANNED)

        retrieved_conf = services.obtenir_details_conference(conf.id)
        self.assertEqual(retrieved_conf, conf)

    def test_creer_conference_titre_vide(self):
        with self.assertRaisesRegex(ValueError, "Le titre de la conférence ne peut pas être vide."):
            services.creer_conference(titre="")

    def test_creer_conference_client_id_inexistant(self):
        with self.assertRaisesRegex(ValueError, "Client avec ID 'id_client_bidon' non trouvé."):
            services.creer_conference(titre="Test Conf", client_id="id_client_bidon")

    def test_obtenir_conference_inexistante(self):
        self.assertIsNone(services.obtenir_details_conference("id_conf_bidon"))

    def test_ajouter_ou_maj_notes(self):
        conf = services.creer_conference(titre="Conf pour Notes", client_id=self.client1.id)
        nouvelles_notes = "Ceci sont les notes mises à jour."
        updated_conf = services.ajouter_ou_maj_notes(conf.id, nouvelles_notes)
        self.assertEqual(updated_conf.notes_rapport, nouvelles_notes)
        self.assertEqual(services.obtenir_details_conference(conf.id).notes_rapport, nouvelles_notes)

    def test_ajouter_ou_maj_notes_conf_inexistante(self):
        with self.assertRaisesRegex(ValueError, "Conférence avec ID 'id_conf_bidon' non trouvée."):
            services.ajouter_ou_maj_notes("id_conf_bidon", "notes test")

    def test_affecter_client_a_conference(self):
        conf = services.creer_conference(titre="Conf sans client initial")
        self.assertIsNone(conf.client_id)
        updated_conf = services.affecter_client_a_conference(conf.id, self.client2.id)
        self.assertEqual(updated_conf.client_id, self.client2.id)
        self.assertEqual(services.obtenir_details_conference(conf.id).client_id, self.client2.id)

    def test_affecter_client_a_conference_conf_inexistante(self):
        with self.assertRaisesRegex(ValueError, "Conférence avec ID 'id_conf_bidon' non trouvée."):
            services.affecter_client_a_conference("id_conf_bidon", self.client1.id)

    def test_affecter_client_a_conference_client_inexistant(self):
        conf = services.creer_conference(titre="Conf Test")
        with self.assertRaisesRegex(ValueError, "Client avec ID 'id_client_bidon' non trouvé."):
            services.affecter_client_a_conference(conf.id, "id_client_bidon")

    def test_changer_statut_conference(self):
        conf = services.creer_conference(titre="Conf pour Statut")
        self.assertEqual(conf.statut, Conference.CONFERENCE_STATUT_PLANNED)

        updated_conf = services.changer_statut_conference(conf.id, Conference.CONFERENCE_STATUT_COMPLETED)
        self.assertEqual(updated_conf.statut, Conference.CONFERENCE_STATUT_COMPLETED)
        self.assertEqual(services.obtenir_details_conference(conf.id).statut, Conference.CONFERENCE_STATUT_COMPLETED)

    def test_changer_statut_conference_statut_invalide(self):
        conf = services.creer_conference(titre="Conf Test Statut")
        with self.assertRaisesRegex(ValueError, "Statut invalide: STATUT_BIDON. Doit être un de"):
            services.changer_statut_conference(conf.id, "STATUT_BIDON")

    def test_changer_statut_conference_conf_inexistante(self):
        with self.assertRaisesRegex(ValueError, "Conférence avec ID 'id_conf_bidon' non trouvée."):
            services.changer_statut_conference("id_conf_bidon", Conference.CONFERENCE_STATUT_CANCELLED)

    def test_lister_conferences(self):
        conf1 = services.creer_conference(titre="Conf A", client_id=self.client1.id) # Statut par défaut: PLANNED
        conf2 = services.creer_conference(titre="Conf B", client_id=self.client2.id)
        services.changer_statut_conference(conf2.id, Conference.CONFERENCE_STATUT_COMPLETED) # Changer le statut pour le test
        conf3 = services.creer_conference(titre="Conf C", client_id=self.client1.id) # Statut par défaut: PLANNED

        all_confs = services.lister_conferences()
        self.assertEqual(len(all_confs), 3)

        client1_confs = services.lister_conferences(client_id=self.client1.id)
        self.assertEqual(len(client1_confs), 2)
        self.assertIn(conf1, client1_confs)
        self.assertIn(conf3, client1_confs)

        planned_confs = services.lister_conferences(statut=Conference.CONFERENCE_STATUT_PLANNED)
        self.assertEqual(len(planned_confs), 2)
        self.assertIn(conf1, planned_confs)
        self.assertIn(conf3, planned_confs)

        client1_planned_confs = services.lister_conferences(client_id=self.client1.id, statut=Conference.CONFERENCE_STATUT_PLANNED)
        self.assertEqual(len(client1_planned_confs), 2)

        client2_completed_confs = services.lister_conferences(client_id=self.client2.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)
        self.assertEqual(len(client2_completed_confs), 1)
        self.assertIn(conf2, client2_completed_confs)

        # Test avec client_id invalide (devrait retourner une liste vide pour ce filtre)
        confs_client_invalide = services.lister_conferences(client_id="id_client_bidon")
        self.assertEqual(len(confs_client_invalide), 0)

        # Test avec statut invalide
        with self.assertRaisesRegex(ValueError, "Statut de filtre invalide: STATUT_FILTRE_BIDON"):
            services.lister_conferences(statut="STATUT_FILTRE_BIDON")


    # --- Tests pour la Logique de Planification ---
    def test_obtenir_conferences_a_venir(self):
        maintenant = datetime.now()
        conf_passee = services.creer_conference(titre="Conf Passée", date_heure_programmation=maintenant - timedelta(days=1))
        conf_future1 = services.creer_conference(titre="Conf Future 1 (demain)", date_heure_programmation=maintenant + timedelta(days=1))
        conf_future2 = services.creer_conference(titre="Conf Future 2 (dans 5 jours)", date_heure_programmation=maintenant + timedelta(days=5))
        conf_future_terminee = services.creer_conference(titre="Conf Future Terminée", date_heure_programmation=maintenant + timedelta(days=2))
        services.changer_statut_conference(conf_future_terminee.id, Conference.CONFERENCE_STATUT_COMPLETED)
        conf_future_annulee = services.creer_conference(titre="Conf Future Annulée", date_heure_programmation=maintenant + timedelta(days=3))
        services.changer_statut_conference(conf_future_annulee.id, Conference.CONFERENCE_STATUT_CANCELLED)
        conf_sans_date = services.creer_conference(titre="Conf Sans Date")

        conferences_a_venir = services.obtenir_conferences_a_venir()

        self.assertEqual(len(conferences_a_venir), 2)
        self.assertIn(conf_future1, conferences_a_venir)
        self.assertIn(conf_future2, conferences_a_venir)
        self.assertNotIn(conf_passee, conferences_a_venir)
        self.assertNotIn(conf_future_terminee, conferences_a_venir)
        self.assertNotIn(conf_future_annulee, conferences_a_venir)
        self.assertNotIn(conf_sans_date, conferences_a_venir)

        # Vérifier l'ordre (la plus proche en premier)
        if len(conferences_a_venir) == 2: # s'assurer qu'on a bien les deux attendues
            self.assertEqual(conferences_a_venir[0], conf_future1)
            self.assertEqual(conferences_a_venir[1], conf_future2)


    # --- Tests pour la Gestion des Rapports ---
    def test_generer_texte_rapport_conference(self):
        date_prog = datetime(2025, 1, 15, 14, 30, 0)
        notes = "Points clés:\n- Item 1\n- Item 2"
        conf = services.creer_conference(
            titre="Rapport Conf Test",
            client_id=self.client1.id,
            date_heure_programmation=date_prog,
            notes=notes,
            participants_externes="M. Untel",
            # statut=Conference.CONFERENCE_STATUT_COMPLETED # Le statut par défaut est PLANNED
        )
        services.changer_statut_conference(conf.id, Conference.CONFERENCE_STATUT_COMPLETED)


        rapport = services.generer_texte_rapport_conference(conf.id)

        self.assertIn(conf.id, rapport)
        self.assertIn("Rapport Conf Test", rapport)
        self.assertIn(self.client1.nom, rapport) # Nom du client
        self.assertIn(date_prog.strftime('%Y-%m-%d %H:%M:%S'), rapport)
        self.assertIn(Conference.CONFERENCE_STATUT_COMPLETED, rapport)
        self.assertIn("M. Untel", rapport)
        self.assertIn(notes, rapport)

    def test_generer_texte_rapport_conference_minimale(self):
        conf = services.creer_conference(titre="Conf Minimale")
        # Pas de client, pas de date prog, pas de notes, pas de participants externes
        services.changer_statut_conference(conf.id, Conference.CONFERENCE_STATUT_IN_PROGRESS)

        rapport = services.generer_texte_rapport_conference(conf.id)

        self.assertIn(conf.id, rapport)
        self.assertIn("Conf Minimale", rapport)
        self.assertIn("Client Associé: Aucun", rapport)
        self.assertIn("Date Programmée: Non spécifiée", rapport)
        self.assertIn("Participants Externes: Aucun", rapport)
        self.assertIn("Aucune note enregistrée.", rapport)
        self.assertIn(Conference.CONFERENCE_STATUT_IN_PROGRESS, rapport)

    def test_generer_texte_rapport_conference_inexistante(self):
        with self.assertRaisesRegex(ValueError, "Conférence avec ID 'id_conf_bidon' non trouvée."):
            services.generer_texte_rapport_conference("id_conf_bidon")


if __name__ == '__main__':
    # Configuration pour exécuter les tests directement depuis ce fichier
    # Cela permet de lancer `python tests/conference_manager/test_conference_services.py`
    # et que les imports relatifs au projet fonctionnent.
    unittest.main()
