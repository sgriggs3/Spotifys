import unittest
import os
import logging
from unittest.mock import patch, MagicMock
import spotipy
from authentication import authenticate_spotify
from music_api_client import MusicAPIClient
from spotify_audio_features import fetch_audio_features

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TestSpotifyIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment variables"""
        os.environ['SPOTIPY_CLIENT_ID'] = 'test_client_id'
        os.environ['SPOTIPY_CLIENT_SECRET'] = 'test_client_secret'
        os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8080'
        
        self.scopes = "user-read-private user-read-email playlist-read-private user-top-read"
        
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_authentication(self, mock_oauth, mock_spotify):
        """Test authentication flow"""
        # Setup mock
        mock_oauth.return_value = MagicMock()
        mock_spotify.return_value = MagicMock()
        
        try:
            client = authenticate_spotify(
                os.environ['SPOTIPY_CLIENT_ID'],
                os.environ['SPOTIPY_CLIENT_SECRET'],
                os.environ['SPOTIPY_REDIRECT_URI'],
                self.scopes
            )
            self.assertIsNotNone(client)
        except Exception as e:
            self.fail(f"Authentication failed: {str(e)}")

    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_token_refresh(self, mock_oauth, mock_spotify):
        """Test token refresh mechanism"""
        # Setup mock
        mock_oauth.return_value = MagicMock()
        mock_spotify.return_value = MagicMock()
        mock_spotify.return_value.auth_manager.get_cached_token.return_value = None
        
        client = authenticate_spotify(
            os.environ['SPOTIPY_CLIENT_ID'],
            os.environ['SPOTIPY_CLIENT_SECRET'],
            os.environ['SPOTIPY_REDIRECT_URI'],
            self.scopes
        )
        
        # Verify token refresh was attempted
        mock_spotify.return_value.auth_manager.get_cached_token.assert_called_once()

    @patch('spotipy.Spotify')
    def test_audio_features(self, mock_spotify):
        """Test audio features retrieval"""
        # Setup mock
        mock_spotify.return_value = MagicMock()
        mock_spotify.return_value.audio_features.return_value = [
            {'danceability': 0.8, 'energy': 0.9},
            {'danceability': 0.7, 'energy': 0.8}
        ]
        
        track_ids = ['track1', 'track2']
        features = fetch_audio_features(mock_spotify.return_value, track_ids)
        
        self.assertEqual(len(features), 2)
        self.assertIn('danceability', features[0])
        self.assertIn('energy', features[0])

    @patch('spotipy.Spotify')
    def test_error_handling(self, mock_spotify):
        """Test API error handling"""
        # Setup mock for rate limit error
        mock_spotify.return_value = MagicMock()
        mock_spotify.return_value.audio_features.side_effect = spotipy.SpotifyException(
            429, -1, 'Rate limit exceeded'
        )
        
        track_ids = ['track1']
        features = fetch_audio_features(mock_spotify.return_value, track_ids)
        
        # Should return None for failed requests
        self.assertIsNone(features[0])

if __name__ == '__main__':
    unittest.main()