
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.recommendation_engine import RecommendationEngine
from utils.feedback_processor import FeedbackProcessor
from models.user_preference_model import UserPreferenceModel

# Load environment variables from .env file
load_dotenv()

def initialize_spotify_client():
    # Use SpotifyOAuth for user authentication and authorization
    spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        scope="user-library-read user-top-read playlist-modify-public playlist-modify-private"
    ))
    return spotify_client

if __name__ == "__main__":
    spotify_client = initialize_spotify_client()
    # Example usage of the client, more logic to be implemented as needed
