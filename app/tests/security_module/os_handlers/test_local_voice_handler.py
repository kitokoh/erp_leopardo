import unittest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import os

# Temporairement ajouter le chemin du projet pour que les imports fonctionnent
# Cela peut être nécessaire si les tests sont exécutés directement et que
# la structure du projet n'est pas automatiquement dans PYTHONPATH.
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.security_module.os_handlers.local_voice_handler import LocalVoiceHandler, \
    SAMPLE_RATE, N_MFCC, DURATION_PER_SAMPLE, N_SAMPLES_ENROLL, VOICE_PROFILES_DIR, N_COMPONENTS_GMM

# Mock joblib avant qu'il ne soit importé par le module testé si nécessaire
# ou mocker directement dans les tests.
# Pour ce test, nous allons mocker les fonctions spécifiques (dump, load) via patch.

@unittest.skip("PortAudio library not available in this environment")
class TestLocalVoiceHandler(unittest.TestCase):

    def setUp(self):
        self.test_user_id = "test_user_voice_handler"
        self.handler = LocalVoiceHandler()
        # Assurer que le répertoire des profils existe pour les tests qui pourraient l'utiliser
        if not os.path.exists(VOICE_PROFILES_DIR):
            os.makedirs(VOICE_PROFILES_DIR)

        # Chemin de profil pour ce testeur
        self.profile_path = self.handler._get_profile_path(self.test_user_id)

    def tearDown(self):
        # Nettoyer les fichiers de profil créés pendant les tests
        if os.path.exists(self.profile_path):
            try:
                os.remove(self.profile_path)
            except OSError: # Peut arriver si le test échoue avant la création du fichier
                pass
        # Optionnel: supprimer le répertoire VOICE_PROFILES_DIR s'il est vide et créé par les tests
        # Mais attention si d'autres tests ou le module lui-même le crée au chargement.
        # if os.path.exists(VOICE_PROFILES_DIR) and not os.listdir(VOICE_PROFILES_DIR):
        #     os.rmdir(VOICE_PROFILES_DIR)


    @patch('sounddevice.rec')
    @patch('sounddevice.wait')
    def test_01_record_audio_simulation(self, mock_sd_wait, mock_sd_rec):
        """Test _record_audio simulation returns an array of correct size."""
        # Simuler que sd.rec retourne un array numpy de la bonne taille
        expected_frames = int(DURATION_PER_SAMPLE * SAMPLE_RATE)
        mock_audio_data = np.random.randn(expected_frames, 1).astype(np.float32)
        mock_sd_rec.return_value = mock_audio_data

        audio_data = self.handler._record_audio(DURATION_PER_SAMPLE, SAMPLE_RATE)

        mock_sd_rec.assert_called_once_with(expected_frames, samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        mock_sd_wait.assert_called_once()
        self.assertIsNotNone(audio_data)
        self.assertEqual(audio_data.ndim, 1) # Should be flattened
        self.assertEqual(audio_data.shape[0], expected_frames)

    def test_02_extract_mfccs_basic(self):
        """Test _extract_mfccs returns an array of correct shape or None for bad input."""
        # Create a dummy audio signal (1 second of stereo, convert to mono for MFCC)
        dummy_audio_stereo = np.random.randn(SAMPLE_RATE * 1, 2).astype(np.float32)
        dummy_audio_mono = librosa.to_mono(dummy_audio_stereo.T) # librosa expects (channels, samples)

        mfccs = self.handler._extract_mfccs(dummy_audio_mono, SAMPLE_RATE, N_MFCC)
        self.assertIsNotNone(mfccs)
        self.assertEqual(mfccs.shape[1], N_MFCC) # (frames, N_MFCC)
        self.assertTrue(mfccs.shape[0] > 0) # Should have some frames

        # Test with empty data
        empty_audio = np.array([])
        mfccs_empty = self.handler._extract_mfccs(empty_audio, SAMPLE_RATE, N_MFCC)
        self.assertIsNone(mfccs_empty)

        # Test with None
        mfccs_none = self.handler._extract_mfccs(None, SAMPLE_RATE, N_MFCC)
        self.assertIsNone(mfccs_none)

    @patch.object(LocalVoiceHandler, '_record_audio')
    @patch('joblib.dump')
    def test_03_enroll_successful(self, mock_joblib_dump, mock_record_audio):
        """Test successful enrollment process."""
        # Mock _record_audio to return consistent dummy MFCCs for each sample
        # Each call to _record_audio should return a simulated audio recording
        # _extract_mfccs will then process this.
        # Let's create plausible MFCC frames (e.g., 100 frames per recording)
        mock_mfcc_frames_per_sample = np.random.randn(100, N_MFCC).astype(np.float32)

        # We need _record_audio to return audio data that _extract_mfccs can process.
        # So, mock_record_audio should return raw audio.
        # Then, we can additionally mock _extract_mfccs if we want to control its output directly,
        # or let it run with the mocked audio. For this test, let's let _extract_mfccs run.

        # Simulate DURATION_PER_SAMPLE seconds of audio
        sim_audio_sample = np.random.randn(int(DURATION_PER_SAMPLE * SAMPLE_RATE)).astype(np.float32)
        mock_record_audio.return_value = sim_audio_sample

        result = self.handler.enroll(self.test_user_id)
        self.assertTrue(result)
        self.assertEqual(mock_record_audio.call_count, N_SAMPLES_ENROLL)
        mock_joblib_dump.assert_called_once()
        # Check if the first argument to dump is a GaussianMixture model (or any, for simplicity)
        self.assertIsInstance(mock_joblib_dump.call_args[0][0], GaussianMixture)
        self.assertEqual(mock_joblib_dump.call_args[0][1], self.profile_path)


    @patch.object(LocalVoiceHandler, '_record_audio')
    def test_04_enroll_not_enough_data(self, mock_record_audio):
        """Test enrollment failure if not enough MFCC frames are collected."""
        # Simulate audio that results in very few MFCC frames
        # (e.g., by returning very short audio or mocking _extract_mfccs)

        # Simulate audio that's too short to produce enough frames for N_COMPONENTS_GMM
        # Let's say N_COMPONENTS_GMM is 16, we need at least 16 frames total.
        # If each recording gives only 1 frame, and N_SAMPLES_ENROLL is 5, we get 5 frames.
        short_audio_sample = np.random.randn(int(0.1 * SAMPLE_RATE)).astype(np.float32) # 0.1 sec audio
        mock_record_audio.return_value = short_audio_sample # This will likely produce few frames

        # Clean up any existing profile from previous tests
        if os.path.exists(self.profile_path): os.remove(self.profile_path)

        result = self.handler.enroll(self.test_user_id)
        self.assertFalse(result, "Enrollment should fail if MFCC frames < GMM components")


    @patch('os.path.exists')
    @patch('joblib.load')
    @patch.object(LocalVoiceHandler, '_record_audio')
    def test_05_verify_successful(self, mock_record_audio, mock_joblib_load, mock_os_path_exists):
        """Test successful verification."""
        mock_os_path_exists.return_value = True # Simulate profile exists

        # Create a dummy GMM model and MFCC data
        # The GMM needs to be 'trained' on something, even if simple for the mock
        dummy_training_data = np.random.randn(100, N_MFCC) # 100 frames, N_MFCC features
        mock_gmm = GaussianMixture(n_components=min(N_COMPONENTS_GMM, dummy_training_data.shape[0]), covariance_type='diag', random_state=0)
        mock_gmm.fit(dummy_training_data)
        mock_joblib_load.return_value = mock_gmm

        # Simulate recorded audio for verification that should match the GMM
        # For a good match, the score should be high (less negative).
        # We'll mock _extract_mfccs to return data similar to training data.
        # Or, let _extract_mfccs run on simulated audio.
        sim_verify_audio = np.random.randn(int(DURATION_PER_SAMPLE * SAMPLE_RATE)).astype(np.float32)
        mock_record_audio.return_value = sim_verify_audio

        # To ensure verify *can* succeed, we need gmm.score(test_data) > threshold.
        # We can patch the threshold or mock gmm.score.
        # For this test, let's assume the threshold is reasonably set and
        # that providing mfcc_frames similar to what it was trained on results in a high score.
        # A more direct way is to patch gmm.score itself.

        with patch.object(mock_gmm, 'score', return_value= -5.0): # Simulate a good score (>-15 threshold)
            result = self.handler.verify(self.test_user_id)
            self.assertTrue(result)
            mock_record_audio.assert_called_once()
            mock_joblib_load.assert_called_with(self.profile_path)


    @patch('os.path.exists')
    @patch('joblib.load')
    @patch.object(LocalVoiceHandler, '_record_audio')
    def test_06_verify_failed_bad_match(self, mock_record_audio, mock_joblib_load, mock_os_path_exists):
        """Test verification failure due to bad voice match (low GMM score)."""
        mock_os_path_exists.return_value = True

        dummy_training_data = np.random.randn(100, N_MFCC)
        mock_gmm = GaussianMixture(n_components=min(N_COMPONENTS_GMM,100), covariance_type='diag', random_state=0)
        mock_gmm.fit(dummy_training_data)
        mock_joblib_load.return_value = mock_gmm

        sim_verify_audio = np.random.randn(int(DURATION_PER_SAMPLE * SAMPLE_RATE)).astype(np.float32)
        mock_record_audio.return_value = sim_verify_audio

        # Simulate a GMM score that is below the threshold
        with patch.object(mock_gmm, 'score', return_value= -50.0): # Simulate a bad score (< -15 threshold)
            result = self.handler.verify(self.test_user_id)
            self.assertFalse(result)

    @patch('os.path.exists')
    def test_07_verify_profile_not_exists(self, mock_os_path_exists):
        """Test verification failure if voice profile does not exist."""
        mock_os_path_exists.return_value = False # Simulate profile does NOT exist
        result = self.handler.verify(self.test_user_id)
        self.assertFalse(result)

    @patch('os.path.exists')
    @patch('os.remove')
    def test_08_delete_enrollment(self, mock_os_remove, mock_os_path_exists):
        """Test deleting an enrollment."""
        # Case 1: Profile exists
        mock_os_path_exists.return_value = True
        result = self.handler.delete_enrollment(self.test_user_id)
        self.assertTrue(result)
        mock_os_remove.assert_called_with(self.profile_path)

        # Case 2: Profile does not exist
        mock_os_path_exists.return_value = False
        mock_os_remove.reset_mock() # Reset mock for the next call
        result_not_exist = self.handler.delete_enrollment(self.test_user_id)
        self.assertTrue(result_not_exist) # Should still be true as desired state is achieved
        mock_os_remove.assert_not_called() # os.remove should not be called if file doesn't exist

    def test_09_is_available(self):
        """Test is_available method (basic check for sounddevice)."""
        # This test is a bit fragile as it depends on the actual environment's sounddevice.
        # A more robust test would mock sd.query_devices().
        with patch('sounddevice.query_devices', return_value=["mock_device"]) as mock_query:
            self.assertTrue(self.handler.is_available("voice"))
            mock_query.assert_called_once()

        with patch('sounddevice.query_devices', side_effect=Exception("Test SD error")) as mock_query_fail:
            self.assertFalse(self.handler.is_available("voice"))
            mock_query_fail.assert_called_once()

        self.assertFalse(self.handler.is_available("fingerprint")) # Should be false for other methods

if __name__ == '__main__':
    unittest.main()
