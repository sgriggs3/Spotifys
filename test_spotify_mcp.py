import os
import logging
from spotify_mcp_client import SpotifyMCPClient
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_audio_features():
    """Test fetching audio features through MCP"""
    
    # Example track IDs (Bohemian Rhapsody and a few other popular songs)
    test_tracks = [
        "3z8h0TU7ReDPLIbEnYhWZb",  # Bohemian Rhapsody
        "4cOdK2wGLETKBW3PvgPWqT",  # Never Gonna Give You Up
        "4gphxUgq0JSFv2BCLhNDiE"   # Smells Like Teen Spirit
    ]
    
    try:
        # Initialize MCP client
        client = SpotifyMCPClient()
        
        # Fetch audio features
        logging.info("Fetching audio features for test tracks...")
        features = client.get_audio_features(test_tracks)
        
        # Display results
        for track_id, feature in zip(test_tracks, features):
            if feature:
                logging.info(f"\nAudio features for track {track_id}:")
                for key, value in feature.items():
                    logging.info(f"{key}: {value}")
            else:
                logging.error(f"Failed to get audio features for track {track_id}")
                
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_audio_features()