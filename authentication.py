# authentication.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def authenticate_spotify():
    """
    Authenticate with the Spotify API using OAuth.

    Returns:
        Spotify client object for accessing the Spotify API
    """
    auth_manager = SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
        scope="user-read-recently-played user-library-read user-top-read playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-playback-state user-modify-playback-state user-read-currently-playing streaming user-library-modify user-read-email user-read-private",
        show_dialog=True,
        cache_path="token_cache"
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

if __name__ == "__main__":
    # Authenticate and get the Spotify client
    spotify_client = authenticate_spotify()
    print("Successfully authenticated with Spotify")
