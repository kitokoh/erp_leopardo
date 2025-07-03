# security_module/os_handlers/local_voice_handler.py
"""
Handles local voice biometric authentication using basic MFCC and distance comparison.

WARNING: This is a basic implementation for demonstration and is NOT suitable for
production environments due to:
- Low robustness against voice variations, noise, different microphones.
- High vulnerability to replay attacks (playing a recording of the user's voice).
- Fixed threshold that may not work well for all users or environments.
- Simple feature averaging for enrollment, which is not very discriminative.

For a production system, more advanced techniques such as GMM-UBM, i-vectors,
x-vectors (deep learning embeddings), and liveness detection would be necessary.
"""
import logging
import os
import numpy as np
import sounddevice as sd
import librosa
import time # For unique filenames or waiting

logger = logging.getLogger(__name__)

# Configuration (pourrait être dans un fichier de config global)
SAMPLE_RATE = 16000  # Hz (taux d'échantillonnage)
DURATION_PER_SAMPLE = 3  # secondes par échantillon d'enregistrement
N_MFCC = 13  # Nombre de coefficients MFCC à extraire
N_SAMPLES_ENROLL = 3 # Nombre d'échantillons à prendre pour l'enrôlement
VOICE_PROFILES_DIR = "voice_profiles" # Répertoire pour stocker les modèles vocaux

# Créer le répertoire des profils vocaux s'il n'existe pas
if not os.path.exists(VOICE_PROFILES_DIR):
    try:
        os.makedirs(VOICE_PROFILES_DIR)
    except OSError as e:
        logger.error(f"Failed to create voice profiles directory '{VOICE_PROFILES_DIR}': {e}")


class LocalVoiceHandler:
    """
    Handles local voice enrollment, verification, and profile management.
    Uses MFCCs as features and a simple averaging for enrollment,
    and Euclidean distance for verification against a fixed threshold.
    """
    def __init__(self):
        logger.info("LocalVoiceHandler initialized.")
        # Dependency check is implicitly done in is_available or upon first use.

    def _get_profile_path(self, user_app_id: str) -> str:
        """
        Constructs the file path for a user's voice profile.
        Args:
            user_app_id: The application-specific ID of the user.
        Returns:
            The full path to where the voice profile should be stored.
        """
        return os.path.join(VOICE_PROFILES_DIR, f"user_{user_app_id}_voice_profile.npy")

    def _record_audio(self, duration_seconds: int, sample_rate: int) -> np.ndarray | None:
        """
        Records audio from the default microphone.
        Args:
            duration_seconds: Duration of the recording in seconds.
            sample_rate: The sample rate for the recording.
        Returns:
            A NumPy array containing the audio data, or None on error.
        """
        try:
            logger.info(f"Début de l'enregistrement audio pour {duration_seconds} secondes...")
            # UI calling this should prompt the user to speak.
            recording = sd.rec(int(duration_seconds * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()  # Wait for the recording to complete.
            logger.info("Enregistrement terminé.")
            return recording.flatten()
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement audio: {e}", exc_info=True)
            return None

    def _extract_mfccs(self, audio_data: np.ndarray, sample_rate: int, n_mfcc: int) -> np.ndarray | None:
        """
        Extracts MFCCs from an audio signal.
        Args:
            audio_data: NumPy array of the audio signal.
            sample_rate: Sample rate of the audio signal.
            n_mfcc: Number of MFCC coefficients to extract.
        Returns:
            A NumPy array representing the mean of MFCCs, or None on error.
        """
        try:
            if audio_data is None or audio_data.size == 0:
                logger.warning("Tentative d'extraction de MFCCs sur des données audio vides.")
                return None
            # Assurer que les données sont de type float pour librosa
            audio_data_float = audio_data.astype(np.float32)
            mfccs = librosa.feature.mfcc(y=audio_data_float, sr=sample_rate, n_mfcc=n_mfcc)
            # Prendre la moyenne des MFCCs sur les trames temporelles pour obtenir un vecteur de caractéristiques fixe
            return np.mean(mfccs.T, axis=0)
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des MFCCs: {e}", exc_info=True)
            return None

    def is_available(self, method: str = "voice") -> bool:
        """Vérifie si la méthode vocale locale est 'disponible' (càd si les dépendances sont là)."""
        if method != "voice":
            return False
        try:
            # Tenter d'importer et d'utiliser une fonction basique de sounddevice
            sd.query_devices()
            logger.info("LocalVoiceHandler: Sounddevice semble disponible.")
            return True
        except Exception as e:
            logger.error(f"LocalVoiceHandler: Sounddevice non disponible ou erreur: {e}. L'authentification vocale ne sera pas possible.")
            return False

    def enroll(self, user_app_id: str, window_handle=None) -> bool:
        """Enregistre un profil vocal pour l'utilisateur."""
        if not self.is_available():
            logger.error(f"Impossible d'enrôler la voix pour {user_app_id}: service non disponible.")
            return False

        logger.info(f"Début de l'enrôlement vocal pour l'utilisateur {user_app_id}.")
        # L'UI devrait guider l'utilisateur ici (ex: "Veuillez prononcer la phrase X trois fois")

        all_mfccs = []
        for i in range(N_SAMPLES_ENROLL):
            # L'UI devrait indiquer à l'utilisateur de parler pour l'échantillon i+1
            print(f"ENROLL_SIM_UI: Préparez-vous pour l'échantillon {i+1}/{N_SAMPLES_ENROLL}. Parlez après le bip (simulé).") # Placeholder UI
            time.sleep(1) # Pause pour que l'utilisateur se prépare

            audio_sample = self._record_audio(DURATION_PER_SAMPLE, SAMPLE_RATE)
            if audio_sample is None:
                logger.warning(f"Échantillon vocal {i+1} pour {user_app_id} a échoué ou était vide.")
                # TODO: L'UI devrait informer l'utilisateur et peut-être permettre de réessayer l'échantillon
                return False # Échec de l'enrôlement si un échantillon manque

            mfccs = self._extract_mfccs(audio_sample, SAMPLE_RATE, N_MFCC)
            if mfccs is None:
                logger.warning(f"Extraction MFCC pour l'échantillon {i+1} de {user_app_id} a échoué.")
                return False
            all_mfccs.append(mfccs)

            if i < N_SAMPLES_ENROLL - 1:
                print(f"ENROLL_SIM_UI: Échantillon {i+1} enregistré. Préparez-vous pour le suivant...") # Placeholder UI
                time.sleep(0.5)


        if not all_mfccs:
            logger.error(f"Aucun MFCC n'a pu être extrait pour l'enrôlement de {user_app_id}.")
            return False

        # Créer le profil vocal en moyennant les MFCCs (approche simple)
        voice_profile = np.mean(all_mfccs, axis=0)
        profile_path = self._get_profile_path(user_app_id)

        try:
            np.save(profile_path, voice_profile)
            logger.info(f"Profil vocal pour {user_app_id} sauvegardé dans {profile_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du profil vocal pour {user_app_id}: {e}", exc_info=True)
            return False

    def verify(self, user_app_id: str, username_hint: str = "", window_handle=None) -> bool:
        """Vérifie la voix de l'utilisateur contre un profil enregistré."""
        if not self.is_available():
            logger.error(f"Impossible de vérifier la voix pour {user_app_id}: service non disponible.")
            return False

        profile_path = self._get_profile_path(user_app_id)
        if not os.path.exists(profile_path):
            logger.warning(f"Aucun profil vocal trouvé pour {user_app_id} à {profile_path}. Enrôlement nécessaire.")
            return False

        try:
            enrolled_profile_mfccs = np.load(profile_path)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du profil vocal pour {user_app_id}: {e}", exc_info=True)
            return False

        logger.info(f"Tentative de vérification vocale pour {user_app_id}. (Hint: {username_hint})")
        # L'UI devrait indiquer à l'utilisateur de parler
        print(f"VERIFY_SIM_UI: Veuillez prononcer votre phrase de passe maintenant.") # Placeholder UI

        audio_sample = self._record_audio(DURATION_PER_SAMPLE, SAMPLE_RATE)
        if audio_sample is None:
            logger.warning(f"Échantillon vocal pour vérification de {user_app_id} a échoué ou était vide.")
            return False

        current_mfccs = self._extract_mfccs(audio_sample, SAMPLE_RATE, N_MFCC)
        if current_mfccs is None:
            logger.warning(f"Extraction MFCC pour vérification de {user_app_id} a échoué.")
            return False

        # Comparaison simple : distance euclidienne (plus petit = plus similaire)
        distance = np.linalg.norm(enrolled_profile_mfccs - current_mfccs)
        logger.info(f"Distance vocale pour {user_app_id}: {distance}")

        # TODO: Définir un seuil approprié. Cela nécessite des tests et un ajustement.
        # Ce seuil est très arbitraire et dépendra fortement des caractéristiques et de la méthode.
        threshold = 15.0 # EXEMPLE DE SEUIL - À AJUSTER EMPIRIQUEMENT

        if distance < threshold:
            logger.info(f"Vérification vocale pour {user_app_id} RÉUSSIE (distance {distance} < seuil {threshold}).")
            return True
        else:
            logger.warning(f"Vérification vocale pour {user_app_id} ÉCHOUÉE (distance {distance} >= seuil {threshold}).")
            return False

    def delete_enrollment(self, user_app_id: str, method: str = "voice") -> bool:
        """Supprime le profil vocal enregistré pour l'utilisateur."""
        if method != "voice": return False # Ce handler ne gère que la voix

        profile_path = self._get_profile_path(user_app_id)
        if os.path.exists(profile_path):
            try:
                os.remove(profile_path)
                logger.info(f"Profil vocal pour {user_app_id} supprimé de {profile_path}.")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du profil vocal pour {user_app_id}: {e}", exc_info=True)
                return False
        else:
            logger.info(f"Aucun profil vocal à supprimer pour {user_app_id} (fichier non trouvé).")
            return True # Considéré comme un succès car l'état désiré (pas de profil) est atteint

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    handler = LocalVoiceHandler()
    test_user = "test_voice_user_123"

    if handler.is_available():
        print(f"\n--- Test d'enrôlement vocal pour {test_user} ---")
        # Supprimer un profil existant pour le test
        handler.delete_enrollment(test_user)

        # Simuler l'interaction UI pour l'enrôlement
        print(f"Demande d'enrôlement pour {test_user}. Vous devrez parler {N_SAMPLES_ENROLL} fois.")
        if handler.enroll(test_user):
            print(f"Enrôlement pour {test_user} réussi.")

            print(f"\n--- Test de vérification vocale pour {test_user} (devrait réussir) ---")
            # Simuler l'interaction UI pour la vérification
            print(f"Demande de vérification pour {test_user}. Parlez maintenant.")
            if handler.verify(test_user):
                print(f"Vérification pour {test_user} réussie.")
            else:
                print(f"Vérification pour {test_user} échouée.")

            print(f"\n--- Test de vérification vocale pour un autre utilisateur (devrait échouer si profil différent) ---")
            # Cela testerait mieux si on avait un profil pour "other_user" ou si on parlait différemment.
            # Pour l'instant, ça va probablement réussir si vous parlez de la même façon.
            print(f"Demande de vérification pour 'other_user' (en utilisant le profil de {test_user}). Parlez maintenant.")
            if handler.verify(test_user): # On vérifie toujours contre le profil de test_user
                 print(f"Vérification (avec la voix de test_user) a réussi - ce qui est attendu.")
            else:
                 print(f"Vérification (avec la voix de test_user) a échoué - inattendu si vous avez parlé comme avant.")

        else:
            print(f"Enrôlement pour {test_user} échoué.")

        # Nettoyage
        # handler.delete_enrollment(test_user)
    else:
        print("Authentification vocale locale non disponible (vérifiez les dépendances et le microphone).")

    print("\nLocalVoiceHandler test complete.")

# Dépendances à installer:
# pip install sounddevice librosa numpy
# Pour sounddevice, vous pourriez avoir besoin de dépendances système (ex: portaudio sur Linux/macOS)
# sudo apt-get install libportaudio2 (Linux Debian/Ubuntu)
# brew install portaudio (macOS)
