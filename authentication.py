# authentication.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth

def authenticate_spotify(client_id, client_secret, redirect_uri, scopes):
    """
    Authenticate with the Spotify API using OAuth.

    Parameters:
        client_id (str): Spotify Application client ID
        client_secret (str): Spotify Application client secret
        redirect_uri (str): Redirect URI set in the Spotify Developer Dashboard
        scopes (str): A string of scopes separated by commas

    Returns:
        Spotify client object for accessing the Spotify API
    """
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scopes,
        show_dialog=True,
        cache_path="token_cache"
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

if __name__ == "__main__":
    # Using the credentials from environment variables
    import os
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", 'http://localhost:8080')
    scopes = os.getenv("SPOTIPY_SCOPES", "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-read-private,playlist-read-collaborative,playlist-modify-private,playlist-modify-public,user-read-recently-played,user-library-read,streaming,user-top-read,user-read-recently-played,user-library-modify,user-read-email")
    # Authenticate and get the Spotify client
    spotify_client = authenticate_spotify(client_id, client_secret, redirect_uri, scopes)
    print("Successfully authenticated with Spotify")
