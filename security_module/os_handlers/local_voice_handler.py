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
import time
from sklearn.mixture import GaussianMixture
import joblib # For saving/loading scikit-learn models

logger = logging.getLogger(__name__)

# Configuration
SAMPLE_RATE = 16000
DURATION_PER_SAMPLE = 2 # Réduire un peu pour des phrases plus courtes, ou rendre dynamique
N_MFCC = 13
N_COMPONENTS_GMM = 16 # Nombre de composantes pour le GMM, à ajuster
COVARIANCE_TYPE_GMM = 'diag' # Type de covariance pour GMM ('full', 'tied', 'diag', 'spherical')
                            # 'diag' est souvent un bon compromis.
N_SAMPLES_ENROLL = 5 # Augmenter pour un meilleur modèle GMM
VOICE_PROFILES_DIR = "voice_profiles_gmm"
MODEL_FILE_EXTENSION = ".joblib"

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
        return os.path.join(VOICE_PROFILES_DIR, f"user_{user_app_id}_gmm_profile{MODEL_FILE_EXTENSION}")

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
            A NumPy array representing the MFCCs (frames x n_mfcc), or None on error.
        """
        try:
            if audio_data is None or audio_data.size == 0:
                logger.warning("Attempting to extract MFCCs from empty audio data.")
                return None
            audio_data_float = audio_data.astype(np.float32)
            # hop_length can be adjusted; typically sr/100 for 10ms frames, sr/40 for 25ms frames
            # n_fft usually power of 2, e.g. 2048 for 16kHz sr
            mfccs = librosa.feature.mfcc(y=audio_data_float, sr=sample_rate, n_mfcc=n_mfcc,
                                         n_fft=int(sample_rate*0.025), hop_length=int(sample_rate*0.010))
            return mfccs.T # Transpose to have (frames, n_mfcc)
        except Exception as e:
            logger.error(f"Error during MFCC extraction: {e}", exc_info=True)
            return None

    def is_available(self, method: str = "voice") -> bool:
        """Checks if the local voice method is 'available' (i.e., dependencies are present)."""
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

        all_mfcc_frames = [] # Collect all MFCC frames from all samples
        for i in range(N_SAMPLES_ENROLL):
            # The UI calling this should provide prompts like these.
            # For handler's direct test, these prints are placeholders.
            print(f"ENROLL_SIM_UI: Préparez-vous pour l'enregistrement {i+1}/{N_SAMPLES_ENROLL}. Parlez après le bip (simulé).") # Placeholder UI
            time.sleep(0.5)

            audio_sample = self._record_audio(DURATION_PER_SAMPLE, SAMPLE_RATE)
            if audio_sample is None or audio_sample.size == 0:
                logger.warning(f"Échantillon vocal {i+1} pour {user_app_id} vide ou échec enregistrement.")
                # QMessageBox.warning(None, "Enregistrement Échoué", f"L'enregistrement de l'échantillon {i+1} a échoué. Veuillez réessayer l'enrôlement.")
                return False

            mfcc_frames = self._extract_mfccs(audio_sample, SAMPLE_RATE, N_MFCC)
            if mfcc_frames is None or mfcc_frames.shape[0] == 0:
                logger.warning(f"Extraction MFCC pour l'échantillon {i+1} de {user_app_id} a échoué ou n'a produit aucune trame.")
                # QMessageBox.warning(None, "Erreur MFCC", f"L'analyse de l'échantillon {i+1} a échoué. Veuillez réessayer l'enrôlement.")
                return False
            all_mfcc_frames.append(mfcc_frames)

            if i < N_SAMPLES_ENROLL - 1:
                print(f"ENROLL_SIM_UI: Échantillon {i+1} enregistré. Préparez-vous pour le suivant...")
                time.sleep(0.2)

        if not all_mfcc_frames:
            logger.error(f"Aucune trame MFCC n'a pu être extraite pour l'enrôlement de {user_app_id}.")
            return False

        # Concaténer toutes les trames MFCC pour entraîner le GMM
        training_data = np.vstack(all_mfcc_frames)
        if training_data.shape[0] < N_COMPONENTS_GMM : # Basic check: need at least as many frames as components
            logger.error(f"Pas assez de trames MFCC ({training_data.shape[0]}) pour entraîner le GMM avec {N_COMPONENTS_GMM} composantes pour {user_app_id}.")
            # QMessageBox.critical(None, "Erreur d'enrôlement", "Pas assez de données vocales pour créer un profil fiable. Essayez de parler plus clairement et plus longtemps.")
            return False

        logger.info(f"Entraînement du GMM pour {user_app_id} avec {training_data.shape[0]} trames MFCC et {N_COMPONENTS_GMM} composantes.")
        gmm = GaussianMixture(n_components=N_COMPONENTS_GMM, covariance_type=COVARIANCE_TYPE_GMM, random_state=0, warm_start=False, reg_covar=1e-6)
        try:
            gmm.fit(training_data)
            if not gmm.converged_:
                 logger.warning(f"Entraînement GMM pour {user_app_id} n'a pas convergé.")
                 # Peut retourner False ici ou continuer avec le modèle non convergé.
                 # Pour l'instant, on continue.
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du GMM pour {user_app_id}: {e}", exc_info=True)
            # QMessageBox.critical(None, "Erreur d'entraînement", "Une erreur est survenue lors de la création de votre profil vocal.")
            return False

        profile_path = self._get_profile_path(user_app_id)
        try:
            joblib.dump(gmm, profile_path)
            logger.info(f"Modèle GMM pour {user_app_id} sauvegardé dans {profile_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle GMM pour {user_app_id}: {e}", exc_info=True)
            return False

    def verify(self, user_app_id: str, username_hint: str = "", window_handle=None) -> bool:
        """Vérifie la voix de l'utilisateur contre un modèle GMM enregistré."""
        if not self.is_available():
            logger.error(f"Impossible de vérifier la voix pour {user_app_id}: service non disponible.")
            return False

        profile_path = self._get_profile_path(user_app_id)
        if not os.path.exists(profile_path):
            logger.warning(f"Aucun profil vocal (modèle GMM) trouvé pour {user_app_id} à {profile_path}. Enrôlement nécessaire.")
            return False

        try:
            gmm = joblib.load(profile_path)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle GMM pour {user_app_id}: {e}", exc_info=True)
            return False

        logger.info(f"Tentative de vérification vocale pour {user_app_id} (Hint: {username_hint}) avec modèle GMM.")
        print(f"VERIFY_SIM_UI: Veuillez prononcer votre phrase de passe maintenant (pour vérification GMM).")

        audio_sample = self._record_audio(DURATION_PER_SAMPLE, SAMPLE_RATE)
        if audio_sample is None or audio_sample.size == 0:
            logger.warning(f"Échantillon vocal pour vérification GMM de {user_app_id} vide ou échec.")
            return False

        mfcc_frames = self._extract_mfccs(audio_sample, SAMPLE_RATE, N_MFCC)
        if mfcc_frames is None or mfcc_frames.shape[0] == 0:
            logger.warning(f"Extraction MFCC pour vérification GMM de {user_app_id} a échoué.")
            return False

        try:
            # Calculer le score de log-vraisemblance moyenne
            log_likelihood = gmm.score(mfcc_frames) # score() returns per-sample (frame) log-likelihood.
                                                    # For GMM, it's often the sum or mean of these.
                                                    # sklearn's gmm.score() directly gives average log-likelihood.
            logger.info(f"Score de log-vraisemblance GMM pour {user_app_id}: {log_likelihood}")
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score GMM pour {user_app_id}: {e}", exc_info=True)
            return False

        # TODO: Définir un seuil approprié pour la log-vraisemblance.
        # Un score plus élevé (moins négatif) est meilleur. Ce seuil est très empirique.
        # Il dépendra de N_COMPONENTS_GMM, des données, etc.
        # Il faudra l'ajuster après des tests.
        # Par exemple, pour des MFCC normalisés, des scores peuvent être entre -5 et -20.
        threshold = -15.0  # EXEMPLE DE SEUIL - À AJUSTER EMPIRIQUEMENT

        if log_likelihood > threshold:
            logger.info(f"Vérification vocale GMM pour {user_app_id} RÉUSSIE (score {log_likelihood:.2f} > seuil {threshold:.2f}).")
            return True
        else:
            logger.warning(f"Vérification vocale GMM pour {user_app_id} ÉCHOUÉE (score {log_likelihood:.2f} <= seuil {threshold:.2f}).")
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
