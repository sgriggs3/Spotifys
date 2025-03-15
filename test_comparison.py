orrectimport logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from spotify_mcp_client import SpotifyMCPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

def get_spotify_client():
    """Initialize Spotify client with OAuth"""
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri='http://localhost:8080',
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing",
        cache_path=".cache"
    ))

def test_direct_and_mcp():
    """Test both direct Spotify API and MCP server"""
    try:
        # Initialize Spotify client
        sp = get_spotify_client()
        
        # Initialize MCP client
        mcp_client = SpotifyMCPClient()
        
        # Test tracks
        track_ids = [
            '3z8h0TU7ReDPLIbEnYhWZb',  # Bohemian Rhapsody
            '4cOdK2wGLETKBW3PvgPWqT',  # Never Gonna Give You Up
        ]
        
        # Test direct API
        logging.info("\nTesting direct Spotify API:")
        features_direct = sp.audio_features(track_ids)
        for track_id, feature in zip(track_ids, features_direct):
            if feature:
                logging.info(f"\nDirect API - Audio features for track {track_id}:")
                for key, value in feature.items():
                    logging.info(f"{key}: {value}")
        
        # Test MCP server
        logging.info("\nTesting MCP server:")
        features_mcp = mcp_client.get_audio_features(track_ids)
        for track_id, feature in zip(track_ids, features_mcp):
            if feature:
                logging.info(f"\nMCP Server - Audio features for track {track_id}:")
                for key, value in feature.items():
                    logging.info(f"{key}: {value}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        if test_direct_and_mcp():
            logging.info("Comparison test completed successfully!")
        else:
            logging.error("Comparison test failed!")
    except Exception as e:
        logging.error(f"Test failed with error: {str(e)}")
        raise