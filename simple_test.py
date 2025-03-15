import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

def test_spotify_connection():
    """Test direct Spotify API connection first"""
    try:
        # Initialize Spotify client
        client_credentials_manager = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIPY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test track (Bohemian Rhapsody)
        track_id = '3z8h0TU7ReDPLIbEnYhWZb'
        
        # Get track info
        track = sp.track(track_id)
        logging.info(f"Successfully retrieved track: {track['name']} by {track['artists'][0]['name']}")
        
        # Get audio features
        features = sp.audio_features([track_id])[0]
        logging.info("\nAudio features:")
        for key, value in features.items():
            logging.info(f"{key}: {value}")
            
        return True
        
    except Exception as e:
        logging.error(f"Error testing Spotify connection: {str(e)}")
        return False

if __name__ == "__main__":
    if test_spotify_connection():
        logging.info("Spotify API connection test successful!")
    else:
        logging.error("Spotify API connection test failed!")