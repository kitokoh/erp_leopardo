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

import sqlite3 # Pour attraper les erreurs spécifiques si nécessaire, bien que les services devraient les encapsuler.
from app.conference_manager import services
from app.conference_manager.models import Client, Conference
from app.conference_manager.database import DATABASE_NAME # Pourrait être utile si on veut tester avec un fichier spécifique


class TestConferenceServicesWithDB(unittest.TestCase): # Renommer pour indiquer l'utilisation de la BD

    @classmethod
    def setUpClass(cls):
        """Appelé une fois avant tous les tests de la classe."""
        services.TEST_DB_NAME = ":memory:"
        # services.reinitialiser_donnees() # Appelée dans setUp pour chaque test maintenant
        # Il est important que la connexion en mémoire soit établie avant tout,
        # et que les tables soient créées une fois sur cette connexion.
        # reinitialiser_donnees() dans setUp s'en chargera.

    @classmethod
    def tearDownClass(cls):
        """Appelé une fois après tous les tests de la classe."""
        from conference_manager.database import close_all_connections
        close_all_connections() # Ferme la connexion en mémoire partagée

    def setUp(self):
        """Appelé avant chaque méthode de test."""
        # Nettoyer les tables avant chaque test pour assurer l'isolation
        # reinitialiser_donnees() s'occupe de cela en recréant les tables
        services.reinitialiser_donnees()

        # Créer des données initiales communes si nécessaire
        try:
            self.client1 = services.creer_client(nom="Client Test Alpha", coordonnees={"email": "alpha@test.com"})
            self.client2 = services.creer_client(nom="Client Test Beta", coordonnees={"tel": "0123456789"})
        except Exception as e:
            # Si la création échoue ici, les tests suivants pourraient avoir des problèmes.
            # Il est crucial que creer_client fonctionne correctement.
            print(f"Erreur critique dans setUp initialisant les clients: {e}")
            raise

    # def tearDown(self):
        # Pas nécessaire de faire services.reinitialiser_donnees() ici si on le fait dans setUp
        # et que la base est en mémoire (elle est jetée après la dernière connexion fermée)
        # Si on utilisait un fichier, on pourrait le supprimer ici ou dans tearDownClass.
        # Pour :memory:, la base est fraîche à chaque nouvelle connexion après la fermeture de la précédente.
        # Cependant, nos services ferment la connexion après chaque opération.
        # reinitialiser_donnees() dans setUp garantit que les tables sont vides et recréées.
        # pass


    # --- Tests pour la gestion des Clients ---
    def test_creer_client(self):
        nom_client = "Nouveau Client Gamma"
        coordonnees_client = {"adresse": "3 rue Gamma"}

        client = services.creer_client(nom=nom_client, coordonnees=coordonnees_client)
        self.assertIsNotNone(client.id)
        self.assertEqual(client.nom, nom_client)
        self.assertEqual(client.coordonnees, coordonnees_client)

        retrieved_client = services.obtenir_client(client.id)
        self.assertIsNotNone(retrieved_client)
        self.assertEqual(retrieved_client.id, client.id)
        self.assertEqual(retrieved_client.nom, client.nom)
        self.assertEqual(retrieved_client.coordonnees, client.coordonnees)

    def test_creer_client_nom_vide(self):
        with self.assertRaisesRegex(ValueError, "Le nom du client ne peut pas être vide."):
            services.creer_client(nom="  ") # Test avec espaces aussi

    # La vérification de duplicata de nom n'est plus dans creer_client service,
    # elle dépendrait d'une contrainte UNIQUE en BD ou d'une logique addtionnelle.
    # Pour l'instant, on ne peut pas tester cela de la même manière.
    # On pourrait tester une contrainte UNIQUE si on l'ajoute à la table.
    # def test_creer_client_nom_duplique_via_contrainte_bd(self):
    #     services.creer_client(nom="Client Unique DB")
    #     with self.assertRaises(sqlite3.IntegrityError): # Ou une exception personnalisée si le service la gère
    #         services.creer_client(nom="Client Unique DB") # Si la table avait UNIQUE(nom)

    def test_obtenir_client_inexistant(self):
        self.assertIsNone(services.obtenir_client("id-totalement-bidon"))

    def test_lister_clients(self):
        # self.client1 et self.client2 sont créés dans setUp
        clients_initial = services.lister_clients()
        self.assertEqual(len(clients_initial), 2)

        services.creer_client(nom="Client Test Gamma")
        clients_apres_ajout = services.lister_clients()
        self.assertEqual(len(clients_apres_ajout), 3)

        # Vérifier que les clients du setUp sont bien dans la liste
        noms_clients = [c.nom for c in clients_apres_ajout]
        self.assertIn(self.client1.nom, noms_clients)
        self.assertIn(self.client2.nom, noms_clients)
        self.assertIn("Client Test Gamma", noms_clients)

    def test_mettre_a_jour_client(self):
        client_original = services.creer_client(nom="Client À Mettre À Jour", coordonnees={"ville": "Origiville"})
        self.assertIsNotNone(client_original)

        # Mettre à jour le nom
        client_maj_nom = services.mettre_a_jour_client(client_original.id, nom="Client Nom MàJ")
        self.assertIsNotNone(client_maj_nom)
        self.assertEqual(client_maj_nom.nom, "Client Nom MàJ")
        self.assertEqual(client_maj_nom.coordonnees, {"ville": "Origiville"}) # Coordonnées inchangées

        # Mettre à jour les coordonnées
        nouvelles_coords = {"ville": "Neoville", "cp": "12345"}
        client_maj_coords = services.mettre_a_jour_client(client_original.id, coordonnees=nouvelles_coords)
        self.assertIsNotNone(client_maj_coords)
        self.assertEqual(client_maj_coords.nom, "Client Nom MàJ") # Nom précédent conservé
        self.assertEqual(client_maj_coords.coordonnees, nouvelles_coords)

        # Mettre à jour les deux
        client_maj_deux = services.mettre_a_jour_client(client_original.id, nom="Client MàJ Totale", coordonnees={"tel": "111222333"})
        self.assertIsNotNone(client_maj_deux)
        self.assertEqual(client_maj_deux.nom, "Client MàJ Totale")
        self.assertEqual(client_maj_deux.coordonnees, {"tel": "111222333"})

        # Vérifier en relisant depuis la BD
        client_relu = services.obtenir_client(client_original.id)
        self.assertEqual(client_relu.nom, "Client MàJ Totale")
        self.assertEqual(client_relu.coordonnees, {"tel": "111222333"})

    def test_mettre_a_jour_client_nom_vide(self):
        with self.assertRaisesRegex(ValueError, "Le nom du client ne peut pas être vide."):
            services.mettre_a_jour_client(self.client1.id, nom=" ")

    def test_mettre_a_jour_client_inexistant(self):
        client_maj = services.mettre_a_jour_client("id-inexistant-encore", nom="Test")
        self.assertIsNone(client_maj)

    def test_mettre_a_jour_client_sans_champs(self):
        with self.assertRaisesRegex(ValueError, "Au moins un champ .* doit être fourni pour la mise à jour."):
            services.mettre_a_jour_client(self.client1.id)

    def test_supprimer_client(self):
        client_a_supprimer = services.creer_client(nom="Client À Supprimer")
        self.assertIsNotNone(services.obtenir_client(client_a_supprimer.id)) # Vérifier qu'il existe

        resultat_suppression = services.supprimer_client(client_a_supprimer.id)
        self.assertTrue(resultat_suppression)
        self.assertIsNone(services.obtenir_client(client_a_supprimer.id)) # Vérifier qu'il n'existe plus

    def test_supprimer_client_inexistant(self):
        resultat_suppression = services.supprimer_client("id-vraiment-bidon")
        self.assertFalse(resultat_suppression)

    # --- Tests pour la gestion des Conférences ---
    def test_creer_conference(self):
        titre_conf = "Réunion de Projet Delta"
        date_prog = datetime.now() + timedelta(days=10)
        conf_obj = services.creer_conference(
            titre=titre_conf,
            date_heure_programmation=date_prog,
            client_id=self.client1.id,
            notes="Préparer la présentation.",
            participants_externes="Consultant Y",
            lieu="Salle B01",
            description_calendrier="Présentation Alpha pour Calendrier",
            rappel_active=True,
            minutes_rappel_avant=15

        )
        self.assertIsNotNone(conf_obj.id)
        self.assertEqual(conf_obj.titre, titre_conf)
        # SQLite peut stocker les datetime avec une précision différente, donc comparer les attributs pertinents
        if conf_obj.date_heure_programmation and date_prog:
            self.assertEqual(conf_obj.date_heure_programmation.date(), date_prog.date())
            self.assertEqual(conf_obj.date_heure_programmation.hour, date_prog.hour)
            self.assertEqual(conf_obj.date_heure_programmation.minute, date_prog.minute)
        self.assertEqual(conf_obj.client_id, self.client1.id)
        self.assertEqual(conf_obj.notes_rapport, "Préparer la présentation.")
        self.assertEqual(conf_obj.participants_externes, "Consultant Y")
        self.assertEqual(conf_obj.statut, Conference.CONFERENCE_STATUT_PLANNED)
        self.assertEqual(conf_obj.lieu, "Salle B01")
        self.assertEqual(conf_obj.description_calendrier, "Présentation Alpha pour Calendrier")
        self.assertTrue(conf_obj.rappel_active)
        self.assertEqual(conf_obj.minutes_rappel_avant, 15)



        retrieved_conf = services.obtenir_details_conference(conf_obj.id)
        self.assertIsNotNone(retrieved_conf)
        self.assertEqual(retrieved_conf.id, conf_obj.id)
        self.assertEqual(retrieved_conf.titre, conf_obj.titre)
        self.assertEqual(retrieved_conf.lieu, "Salle B01")
        self.assertTrue(retrieved_conf.rappel_active)
        self.assertEqual(retrieved_conf.minutes_rappel_avant, 15)


    def test_creer_conference_rappel_inactif_pas_de_minutes(self):
        conf = services.creer_conference(
            titre="Conf sans rappel actif",
            rappel_active=False,
            minutes_rappel_avant=60 # Devrait être ignoré et mis à None
        )
        self.assertFalse(conf.rappel_active)
        self.assertIsNone(conf.minutes_rappel_avant)
        retrieved_conf = services.obtenir_details_conference(conf.id)
        self.assertFalse(retrieved_conf.rappel_active)
        self.assertIsNone(retrieved_conf.minutes_rappel_avant)



    def test_creer_conference_titre_vide(self):
        with self.assertRaisesRegex(ValueError, "Le titre de la conférence ne peut pas être vide."):
            services.creer_conference(titre="  ")

    def test_creer_conference_client_id_inexistant(self):
        with self.assertRaisesRegex(ValueError, "Client avec ID 'id_client_totalement_bidon' non trouvé."):
            services.creer_conference(titre="Test Conf Client Inexistant", client_id="id_client_totalement_bidon")

    def test_obtenir_conference_inexistante(self):
        self.assertIsNone(services.obtenir_details_conference("id_conf_super_bidon"))

    def test_mettre_a_jour_conference_notes(self):
        conf = services.creer_conference(titre="Conf pour MàJ Notes", client_id=self.client1.id)
        nouvelles_notes = "Notes importantes après mise à jour."
        updated_conf = services.mettre_a_jour_conference(conf.id, notes_rapport=nouvelles_notes)
        self.assertIsNotNone(updated_conf)
        self.assertEqual(updated_conf.notes_rapport, nouvelles_notes)
        # Vérifier en relisant
        relu_conf = services.obtenir_details_conference(conf.id)
        self.assertEqual(relu_conf.notes_rapport, nouvelles_notes)

    def test_mettre_a_jour_conference_affecter_client(self):
        conf = services.creer_conference(titre="Conf pour Affectation Client")
        self.assertIsNone(conf.client_id)
        updated_conf = services.mettre_a_jour_conference(conf.id, client_id=self.client2.id)
        self.assertIsNotNone(updated_conf)
        self.assertEqual(updated_conf.client_id, self.client2.id)
         # Vérifier en relisant
        relu_conf = services.obtenir_details_conference(conf.id)
        self.assertEqual(relu_conf.client_id, self.client2.id)

    def test_mettre_a_jour_conference_desaffecter_client(self):
        conf = services.creer_conference(titre="Conf avec Client à Désaffecter", client_id=self.client1.id)
        self.assertEqual(conf.client_id, self.client1.id)
        updated_conf = services.mettre_a_jour_conference(conf.id, client_id="") # "" pour désaffecter
        self.assertIsNotNone(updated_conf)
        self.assertIsNone(updated_conf.client_id)
        relu_conf = services.obtenir_details_conference(conf.id)
        self.assertIsNone(relu_conf.client_id)


    def test_mettre_a_jour_conference_statut(self):
        conf = services.creer_conference(titre="Conf pour MàJ Statut")
        self.assertEqual(conf.statut, Conference.CONFERENCE_STATUT_PLANNED)

        updated_conf = services.mettre_a_jour_conference(conf.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)
        self.assertIsNotNone(updated_conf)
        self.assertEqual(updated_conf.statut, Conference.CONFERENCE_STATUT_COMPLETED)
        relu_conf = services.obtenir_details_conference(conf.id)
        self.assertEqual(relu_conf.statut, Conference.CONFERENCE_STATUT_COMPLETED)

    def test_mettre_a_jour_conference_statut_invalide(self):
        conf = services.creer_conference(titre="Conf Test Statut Invalide")
        with self.assertRaisesRegex(ValueError, "Statut invalide: STATUT_NON_VALIDE. Doit être un de"):
            services.mettre_a_jour_conference(conf.id, statut="STATUT_NON_VALIDE")

    def test_mettre_a_jour_conference_inexistante(self):
        # Tenter de mettre à jour une conférence qui n'existe pas devrait lever une erreur ou retourner None/False
        # La logique actuelle de mettre_a_jour_conference relit la conf, donc si elle n'est pas trouvée après la tentative de MàJ, elle lèvera une ValueError.
         with self.assertRaisesRegex(ValueError, "Conférence avec ID 'id_conf_bidon_maj' non trouvée pour la mise à jour."):
            services.mettre_a_jour_conference("id_conf_bidon_maj", titre="Nouveau Titre")


    def test_mettre_a_jour_conference_plusieurs_champs(self):
        conf = services.creer_conference(titre="Conf Initiale", client_id=self.client1.id)
        nouveau_titre = "Conf Super MàJ"
        nouvelles_notes = "Tout a été revu."
        nouveau_statut = Conference.CONFERENCE_STATUT_IN_PROGRESS
        nouvelle_date_prog = datetime.now() + timedelta(days=30)

        updated_conf = services.mettre_a_jour_conference(
            conf.id,
            titre=nouveau_titre,
            notes_rapport=nouvelles_notes,
            statut=nouveau_statut,
            date_heure_programmation=nouvelle_date_prog,
            client_id=self.client2.id # Changer de client
        )
        self.assertIsNotNone(updated_conf)
        self.assertEqual(updated_conf.titre, nouveau_titre)
        self.assertEqual(updated_conf.notes_rapport, nouvelles_notes)
        self.assertEqual(updated_conf.statut, nouveau_statut)
        self.assertEqual(updated_conf.client_id, self.client2.id)
        if updated_conf.date_heure_programmation and nouvelle_date_prog:
             self.assertEqual(updated_conf.date_heure_programmation.date(), nouvelle_date_prog.date())
        # Vérifier aussi les nouveaux champs si on les ajoute ici
        # Pour l'instant, ce test reste focalisé sur les champs existants plus client_id et date_prog

    def test_mettre_a_jour_conference_champs_calendrier_rappel(self):
        conf = services.creer_conference(titre="Conf pour MàJ Calendrier")

        # Mise à jour initiale des champs
        updated_conf = services.mettre_a_jour_conference(
            conf.id,
            lieu="Nouveau Lieu",
            description_calendrier="Description pour le calendrier",
            rappel_active=True,
            minutes_rappel_avant=45
        )
        self.assertIsNotNone(updated_conf)
        self.assertEqual(updated_conf.lieu, "Nouveau Lieu")
        self.assertEqual(updated_conf.description_calendrier, "Description pour le calendrier")
        self.assertTrue(updated_conf.rappel_active)
        self.assertEqual(updated_conf.minutes_rappel_avant, 45)

        # Désactiver le rappel
        updated_conf_rappel_off = services.mettre_a_jour_conference(conf.id, rappel_active=False)
        self.assertIsNotNone(updated_conf_rappel_off)
        self.assertFalse(updated_conf_rappel_off.rappel_active)
        self.assertIsNone(updated_conf_rappel_off.minutes_rappel_avant, "minutes_rappel_avant devrait être None si rappel_active est False")

        # Réactiver le rappel avec une nouvelle durée
        updated_conf_rappel_on_again = services.mettre_a_jour_conference(conf.id, rappel_active=True, minutes_rappel_avant=10)
        self.assertIsNotNone(updated_conf_rappel_on_again)
        self.assertTrue(updated_conf_rappel_on_again.rappel_active)
        self.assertEqual(updated_conf_rappel_on_again.minutes_rappel_avant, 10)

        # Mettre à jour seulement les minutes (rappel doit rester actif)
        updated_conf_minutes_only = services.mettre_a_jour_conference(conf.id, minutes_rappel_avant=5)
        self.assertIsNotNone(updated_conf_minutes_only)
        self.assertTrue(updated_conf_minutes_only.rappel_active) # Doit rester True
        self.assertEqual(updated_conf_minutes_only.minutes_rappel_avant, 5)

        # Mettre minutes_rappel_avant à None explicitement (via -1 ou autre convention si nécessaire)
        # La logique actuelle dans services.py pour minutes_rappel_avant met à None si < 0
        updated_conf_no_minutes = services.mettre_a_jour_conference(conf.id, minutes_rappel_avant=-1)
        self.assertIsNotNone(updated_conf_no_minutes)
        self.assertTrue(updated_conf_no_minutes.rappel_active) # Rappel reste actif
        self.assertIsNone(updated_conf_no_minutes.minutes_rappel_avant) # Mais sans durée spécifique



    def test_lister_conferences(self):
        conf1 = services.creer_conference(titre="Conf Alpha", client_id=self.client1.id)
        conf2_obj = services.creer_conference(titre="Conf Beta", client_id=self.client2.id)
        services.mettre_a_jour_conference(conf2_obj.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)
        conf3 = services.creer_conference(titre="Conf Gamma", client_id=self.client1.id)

        # Relire conf2 pour avoir l'objet à jour avec le statut
        conf2 = services.obtenir_details_conference(conf2_obj.id)

        all_confs = services.lister_conferences()
        # Le nombre de conférences peut varier si des tests précédents en ont laissé
        # setUpClass et setUp devraient gérer cela en nettoyant.
        # On s'attend à 3 conférences créées spécifiquement pour ce test + celles de setUp si elles ne sont pas nettoyées
        # Avec reinitialiser_donnees() dans setUp, on devrait avoir exactement 3.
        self.assertEqual(len(all_confs), 3, "Devrait y avoir 3 conférences listées après création pour ce test.")


        client1_confs = services.lister_conferences(client_id=self.client1.id)
        self.assertEqual(len(client1_confs), 2)
        # Les comparaisons d'objets directement peuvent échouer si les instances ne sont pas les mêmes
        # Il vaut mieux comparer les IDs ou les attributs pertinents.
        self.assertIn(conf1.id, [c.id for c in client1_confs])
        self.assertIn(conf3.id, [c.id for c in client1_confs])


        planned_confs = services.lister_conferences(statut=Conference.CONFERENCE_STATUT_PLANNED)
        # conf1 et conf3 sont PLANNED par défaut
        self.assertEqual(len(planned_confs), 2)
        self.assertIn(conf1.id, [c.id for c in planned_confs])
        self.assertIn(conf3.id, [c.id for c in planned_confs])



        client1_planned_confs = services.lister_conferences(client_id=self.client1.id, statut=Conference.CONFERENCE_STATUT_PLANNED)
        self.assertEqual(len(client1_planned_confs), 2)

        client2_completed_confs = services.lister_conferences(client_id=self.client2.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)
        self.assertEqual(len(client2_completed_confs), 1)
        self.assertIn(conf2.id, [c.id for c in client2_completed_confs])

        confs_client_invalide = services.lister_conferences(client_id="id_client_bidon_liste")
        self.assertEqual(len(confs_client_invalide), 0)

        with self.assertRaisesRegex(ValueError, "Statut de filtre invalide: STATUT_FILTRE_BIDON_LISTE."):
            services.lister_conferences(statut="STATUT_FILTRE_BIDON_LISTE")

    def test_supprimer_conference(self):
        conf_a_suppr = services.creer_conference(titre="Conf à Supprimer")
        self.assertIsNotNone(services.obtenir_details_conference(conf_a_suppr.id))

        resultat = services.supprimer_conference(conf_a_suppr.id)
        self.assertTrue(resultat)
        self.assertIsNone(services.obtenir_details_conference(conf_a_suppr.id))

    def test_supprimer_conference_inexistante(self):
        resultat = services.supprimer_conference("id_conf_vraiment_bidon_suppr")
        self.assertFalse(resultat)


    # --- Tests pour la Logique de Planification ---
    def test_obtenir_conferences_a_venir(self):
        maintenant = datetime.now()

        # Conférences de test
        conf_passee_obj = services.creer_conference(titre="Conf Passée", date_heure_programmation=maintenant - timedelta(days=1))

        conf_future1_obj = services.creer_conference(titre="Conf Future 1 (demain)", date_heure_programmation=maintenant + timedelta(days=1))

        conf_future2_obj = services.creer_conference(titre="Conf Future 2 (dans 5 jours)", date_heure_programmation=maintenant + timedelta(days=5))

        conf_future_terminee_obj = services.creer_conference(titre="Conf Future Terminée", date_heure_programmation=maintenant + timedelta(days=2))
        if conf_future_terminee_obj:
            services.mettre_a_jour_conference(conf_future_terminee_obj.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)

        conf_future_annulee_obj = services.creer_conference(titre="Conf Future Annulée", date_heure_programmation=maintenant + timedelta(days=3))
        if conf_future_annulee_obj:
            services.mettre_a_jour_conference(conf_future_annulee_obj.id, statut=Conference.CONFERENCE_STATUT_CANCELLED)

        conf_sans_date_obj = services.creer_conference(titre="Conf Sans Date de Programmation")

        conferences_a_venir = services.obtenir_conferences_a_venir() # Devrait lire depuis SQLite

        self.assertEqual(len(conferences_a_venir), 2, "Devrait y avoir 2 conférences à venir non terminées/annulées.")

        ids_conferences_a_venir = [c.id for c in conferences_a_venir]
        self.assertIn(conf_future1_obj.id, ids_conferences_a_venir)
        self.assertIn(conf_future2_obj.id, ids_conferences_a_venir)

        if conf_passee_obj: self.assertNotIn(conf_passee_obj.id, ids_conferences_a_venir)
        if conf_future_terminee_obj: self.assertNotIn(conf_future_terminee_obj.id, ids_conferences_a_venir)
        if conf_future_annulee_obj: self.assertNotIn(conf_future_annulee_obj.id, ids_conferences_a_venir)
        if conf_sans_date_obj: self.assertNotIn(conf_sans_date_obj.id, ids_conferences_a_venir)


        # Vérifier l'ordre (la plus proche en premier)
        if len(conferences_a_venir) == 2:
            self.assertEqual(conferences_a_venir[0].id, conf_future1_obj.id)
            self.assertEqual(conferences_a_venir[1].id, conf_future2_obj.id)


    # --- Tests pour la Gestion des Rapports ---
    def test_generer_texte_rapport_conference(self):
        date_creation_originale = datetime(2024, 1, 1, 10, 0, 0) # Pour contrôler la date de création
        date_prog = datetime(2025, 1, 15, 14, 30, 0)
        notes = "Points clés:\n- Item 1\n- Item 2"
        lieu_test = "Salle de Conférence Principale"
        desc_cal_test = "Session de test pour le rapport iCal."
        minutes_rappel = 15

        conf_obj = services.creer_conference(
            titre="Rapport Conf Test",
            client_id=self.client1.id,
            date_heure_programmation=date_prog,
            notes=notes,
            participants_externes="M. Untel",
            lieu=lieu_test,
            description_calendrier=desc_cal_test,
            rappel_active=True,
            minutes_rappel_avant=minutes_rappel
        )
        services.mettre_a_jour_conference(conf_obj.id, statut=Conference.CONFERENCE_STATUT_COMPLETED)

        conf = services.obtenir_details_conference(conf_obj.id)
        self.assertIsNotNone(conf)


        rapport = services.generer_texte_rapport_conference(conf.id)

        self.assertIn(conf.id, rapport)
        self.assertIn("Rapport Conf Test", rapport)
        self.assertIn(self.client1.nom, rapport)
        if conf.date_heure_creation: # Doit exister
             self.assertIn(conf.date_heure_creation.strftime('%Y-%m-%d %H:%M:%S'), rapport)
        if date_prog: # Doit exister
            self.assertIn(date_prog.strftime('%Y-%m-%d %H:%M:%S'), rapport)
        self.assertIn(Conference.CONFERENCE_STATUT_COMPLETED, rapport)
        self.assertIn("M. Untel", rapport)
        self.assertIn(notes, rapport)
        self.assertIn(f"Lieu: {lieu_test}", rapport)
        self.assertIn(f"Description Calendrier:\n{desc_cal_test}", rapport)
        self.assertIn("Rappel Actif: Oui", rapport)
        self.assertIn(f"Rappel Avant (minutes): {minutes_rappel}", rapport)


    def test_generer_texte_rapport_conference_minimale(self):
        conf_obj = services.creer_conference(
            titre="Conf Rapport Minimal",
            rappel_active=False # Tester avec rappel inactif
        )

        services.mettre_a_jour_conference(conf_obj.id, statut=Conference.CONFERENCE_STATUT_IN_PROGRESS)

        conf = services.obtenir_details_conference(conf_obj.id)
        self.assertIsNotNone(conf)
        rapport = services.generer_texte_rapport_conference(conf.id)

        self.assertIn(conf.id, rapport)
        self.assertIn("Conf Rapport Minimal", rapport)
        self.assertIn("Client Associé: Aucun", rapport)
        self.assertIn("Lieu: Non spécifié", rapport)
        self.assertIn("Date Programmée: Non spécifiée", rapport)
        self.assertIn("Participants Externes: Aucun", rapport)
        self.assertIn("Description Calendrier:\nAucune description pour calendrier.", rapport)
        self.assertIn("Notes / Rapport Détaillé:\nAucune note enregistrée.", rapport)
        self.assertIn(Conference.CONFERENCE_STATUT_IN_PROGRESS, rapport)
        self.assertIn("Rappel Actif: Non", rapport)
        self.assertNotIn("Rappel Avant (minutes):", rapport) # Ne doit pas apparaître si rappel inactif

        if conf.date_heure_creation:
            self.assertIn(conf.date_heure_creation.strftime('%Y-%m-%d %H:%M:%S'), rapport)


    def test_generer_texte_rapport_conference_inexistante(self):
        with self.assertRaisesRegex(ValueError, "Conférence avec ID 'id_conf_rapport_bidon' non trouvée."):
            services.generer_texte_rapport_conference("id_conf_rapport_bidon")

    # --- Tests pour la Logique de Rappel ---
    def test_obtenir_conferences_necessitant_rappel(self):
        maintenant = datetime.now()

        # Conférence dont le rappel est imminent (dans la fenêtre)
        conf_rappel_imminent = services.creer_conference(
            titre="Conf Rappel Imminent",
            date_heure_programmation=maintenant + timedelta(minutes=10), # Dans 10 mins
            rappel_active=True, minutes_rappel_avant=8 # Rappel dans 2 mins
        )
        # Conférence dont le rappel est déjà passé mais conf pas encore commencée
        conf_rappel_passe = services.creer_conference(
            titre="Conf Rappel Passé",
            date_heure_programmation=maintenant + timedelta(hours=1), # Dans 1 heure
            rappel_active=True, minutes_rappel_avant=90 # Rappel était il y a 30 mins
        )
        # Conférence dont le rappel est trop loin dans le futur
        conf_rappel_futur_lointain = services.creer_conference(
            titre="Conf Rappel Futur Lointain",
            date_heure_programmation=maintenant + timedelta(hours=2), # Dans 2 heures
            rappel_active=True, minutes_rappel_avant=30 # Rappel dans 1h30
        )
        # Conférence avec rappel inactif
        conf_rappel_inactif = services.creer_conference(
            titre="Conf Rappel Inactif",
            date_heure_programmation=maintenant + timedelta(minutes=5),
            rappel_active=False, minutes_rappel_avant=5
        )
        # Conférence passée
        conf_passee_avec_rappel = services.creer_conference(
            titre="Conf Passée avec Rappel",
            date_heure_programmation=maintenant - timedelta(hours=1),
            rappel_active=True, minutes_rappel_avant=30
        )
        # Conférence avec rappel mais sans minutes_rappel_avant
        conf_rappel_sans_minutes = services.creer_conference(
            titre="Conf Rappel Sans Minutes",
            date_heure_programmation=maintenant + timedelta(minutes=20),
            rappel_active=True, minutes_rappel_avant=None
        )
        # Conférence avec rappel et minutes_rappel_avant = 0 (rappel à l'heure de la conf)
        conf_rappel_zero_minute = services.creer_conference(
            titre="Conf Rappel Zéro Minute",
            date_heure_programmation=maintenant + timedelta(minutes=3), # Dans 3 mins
            rappel_active=True, minutes_rappel_avant=0 # Rappel maintenant/dans 3 mins
        )


        # Utiliser une fenêtre de 5 minutes pour le test
        conferences_pour_rappel = services.obtenir_conferences_necessitant_rappel(fenetre_proche_futur_minutes=5)

        ids_pour_rappel = [c.id for c in conferences_pour_rappel]

        self.assertIn(conf_rappel_imminent.id, ids_pour_rappel, "Rappel imminent devrait être inclus")
        self.assertIn(conf_rappel_passe.id, ids_pour_rappel, "Rappel passé (conf future) devrait être inclus")
        self.assertIn(conf_rappel_zero_minute.id, ids_pour_rappel, "Rappel zéro minute (conf future proche) devrait être inclus")

        self.assertNotIn(conf_rappel_futur_lointain.id, ids_pour_rappel, "Rappel futur lointain ne devrait pas être inclus")
        self.assertNotIn(conf_rappel_inactif.id, ids_pour_rappel, "Rappel inactif ne devrait pas être inclus")
        if conf_passee_avec_rappel : self.assertNotIn(conf_passee_avec_rappel.id, ids_pour_rappel, "Conférence passée ne devrait pas être incluse")
        if conf_rappel_sans_minutes: self.assertNotIn(conf_rappel_sans_minutes.id, ids_pour_rappel, "Conférence avec rappel mais sans minutes ne devrait pas être incluse")

        # Vérifier l'ordre: conf_rappel_passe (son heure de rappel est la plus ancienne),
        # puis conf_rappel_zero_minute, puis conf_rappel_imminent
        # Les heures de rappel sont :
        # Passe: maintenant - 30m
        # ZeroMinute: maintenant + 3m
        # Imminent: maintenant + 2m
        # L'ordre devrait être Passé, Imminent, ZeroMinute
        expected_order_ids = [
            conf_rappel_passe.id, # Heure rappel = maintenant - 30m
            conf_rappel_imminent.id, # Heure rappel = maintenant + 2m
            conf_rappel_zero_minute.id, # Heure rappel = maintenant + 3m
        ]

        # Filtrer les expected_order_ids pour ne garder que ceux présents dans ids_pour_rappel, dans le bon ordre
        actual_ordered_ids_in_expected_subset = [id_val for id_val in expected_order_ids if id_val in ids_pour_rappel]

        self.assertEqual(len(ids_pour_rappel), len(actual_ordered_ids_in_expected_subset), "Nombre d'éléments pour rappel ne correspond pas")
        if len(ids_pour_rappel) == len(actual_ordered_ids_in_expected_subset): # Pour éviter erreur si tailles differentes
            self.assertEqual(ids_pour_rappel, actual_ordered_ids_in_expected_subset, "L'ordre des rappels n'est pas correct.")

    # --- Tests pour l'Export iCalendar ---
    def test_generer_contenu_ics_pour_conference(self):
        maintenant = datetime.now()
        date_prog = maintenant + timedelta(days=1, hours=2) # Demain dans 2 heures
        conf = services.creer_conference(
            titre="Conférence pour ICS",
            date_heure_programmation=date_prog,
            notes="Notes de la conf ICS.",
            description_calendrier="Description spéciale pour iCal.",
            lieu="Bureau 101",
            client_id=self.client1.id,
            rappel_active=True,
            minutes_rappel_avant=30
        )
        self.assertIsNotNone(conf)

        ics_content = services.generer_contenu_ics_pour_conference(conf.id)
        self.assertIsNotNone(ics_content)

        # Vérifications basiques du contenu ICS
        self.assertIn("BEGIN:VCALENDAR", ics_content)
        self.assertIn("END:VCALENDAR", ics_content)
        self.assertIn("BEGIN:VEVENT", ics_content)
        self.assertIn("END:VEVENT", ics_content)
        self.assertIn(f"UID:{conf.id}@votredomaine.com", ics_content)
        self.assertIn(f"SUMMARY:Conférence pour ICS", ics_content)
        # Les dates/heures dans ICS sont au format YYYYMMDDTHHMMSSZ (pour UTC) ou YYYYMMDDTHHMMSS
        # Notre objet datetime est "naive", donc la librairie icalendar pourrait le formater sans 'Z'.
        # On va vérifier la présence de la date et de l'heure au moins.
        self.assertIn(f"DTSTART:{date_prog.strftime('%Y%m%dT%H%M%S')}", ics_content.replace("Z",""))

        # Vérifier la durée par défaut de 60 minutes
        date_fin_attendue = date_prog + timedelta(minutes=60)
        self.assertIn(f"DTEND:{date_fin_attendue.strftime('%Y%m%dT%H%M%S')}", ics_content.replace("Z",""))

        self.assertIn(f"LOCATION:Bureau 101", ics_content)
        self.assertIn(f"DESCRIPTION:Description spéciale pour iCal.", ics_content)

        # Vérifier l'alarme
        self.assertIn("BEGIN:VALARM", ics_content)
        self.assertIn("ACTION:DISPLAY", ics_content)
        self.assertIn("TRIGGER:-PT30M", ics_content) # -PT30M signifie 30 minutes avant
        self.assertIn("DESCRIPTION:Rappel: Conférence pour ICS", ics_content)
        self.assertIn("END:VALARM", ics_content)

    def test_generer_contenu_ics_conference_sans_date_programmation(self):
        conf = services.creer_conference(titre="Conf sans date prog pour ICS")
        ics_content = services.generer_contenu_ics_pour_conference(conf.id)
        self.assertIsNone(ics_content, "Devrait retourner None si pas de date de programmation")

    def test_generer_contenu_ics_conference_inexistante(self):
        ics_content = services.generer_contenu_ics_pour_conference("id-conf-bidon-ics")
        self.assertIsNone(ics_content, "Devrait retourner None si la conférence n'existe pas")

    def test_generer_contenu_ics_rappel_inactif(self):
        date_prog = datetime.now() + timedelta(days=1)
        conf = services.creer_conference(
            titre="Conf ICS Rappel Inactif",
            date_heure_programmation=date_prog,
            rappel_active=False,
            minutes_rappel_avant=30 # Devrait être ignoré
        )
        ics_content = services.generer_contenu_ics_pour_conference(conf.id)
        self.assertIsNotNone(ics_content)
        self.assertNotIn("BEGIN:VALARM", ics_content, "Ne devrait pas y avoir d'alarme si rappel_active est False")



if __name__ == '__main__':
    # Configuration pour exécuter les tests directement depuis ce fichier
    # Cela permet de lancer `python tests/conference_manager/test_conference_services.py`
    # et que les imports relatifs au projet fonctionnent.
    unittest.main()
