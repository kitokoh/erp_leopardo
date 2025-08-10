# license_request_server.py
from flask import Flask, request, jsonify
import logging
from datetime import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

@app.route('/api/license/request', methods=['POST'])
def handle_license_request():
    try:
        data = request.get_json()
        if not data:
            logging.error("Aucune donnée JSON reçue dans la requête.")
            return jsonify({"status": "error", "message": "Aucune donnée JSON reçue."}), 400

        logging.info(f"Demande de licence reçue : {data}")

        # Champs attendus (liste non exhaustive, pour validation basique)
        required_fields = ['user_id', 'username', 'email', 'requested_license_type', 'machine_info', 'request_timestamp']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            logging.warning(f"Champs manquants dans la demande : {', '.join(missing_fields)}")
            return jsonify({"status": "error", "message": f"Champs manquants : {', '.join(missing_fields)}"}), 400

        # Validation simple du type de licence demandé
        if data.get('requested_license_type') not in ['limite', 'complet']:
            logging.warning(f"Type de licence demandé invalide : {data.get('requested_license_type')}")
            return jsonify({"status": "error", "message": "Type de licence demandé invalide."}), 400

        # Ici, dans une vraie application, vous traiteriez la demande :
        # - Enregistrer la demande dans une base de données
        # - Envoyer une notification à un administrateur
        # - Potentiellement, interagir avec un système de paiement ou de gestion de clés
        # - Etc.

        # Pour cette simulation, nous renvoyons simplement un succès.
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')}" # Générer un ID de demande simple
        logging.info(f"Demande traitée avec succès. ID de demande simulé: {request_id}")

        return jsonify({
            "status": "success",
            "message": "Votre demande de licence a été reçue et est en cours de traitement. Vous serez contacté prochainement.",
            "request_id": request_id
        }), 200

    except Exception as e:
        logging.error(f"Erreur lors du traitement de la demande de licence : {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Une erreur interne est survenue sur le serveur."}), 500

if __name__ == '__main__':
    # Note : Utiliser `debug=True` uniquement pour le développement.
    # Pour un déploiement, utiliser un serveur WSGI comme Gunicorn ou Waitress.
    # Le port 5678 est arbitraire, assurez-vous qu'il est libre.
    logging.info("Démarrage du serveur de demande de licence Flask sur http://127.0.0.1:5678")
    app.run(host='0.0.0.0', port=5678, debug=True)
