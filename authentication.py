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
    # Using the credentials from the 'env.txt' file
    client_id = "6a8af75e08324ff3a05dc2194eec8657"
    client_secret = "f6c805ec2970419cbe3fcb79d733dc71"
    redirect_uri = 'http://localhost:8080'
    scopes = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-read-private,playlist-read-collaborative,playlist-modify-private,playlist-modify-public,user-read-recently-played,user-library-read,streaming,user-top-read,user-read-recently-played,user-library-modify,user-read-email"

    # Authenticate and get the Spotify client
    spotify_client = authenticate_spotify(client_id, client_secret, redirect_uri, scopes)
    print("Successfully authenticated with Spotify")
