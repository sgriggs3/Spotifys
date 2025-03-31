import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

class MusicAPIClient:
    def __init__(self, client_id, client_secret, redirect_uri, scopes):
        """
        Initializes the Music API Client with Spotify authentication.

        Parameters:
            client_id (str): Spotify Application client ID
            client_secret (str): Spotify Application client secret
            redirect_uri (str): Redirect URI set in the Spotify Developer Dashboard
            scopes (str): Scopes for the Spotify API access
        """
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                                            client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                                            redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
                                                            scope="user-read-recently-played user-library-read user-top-read playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-playback-state user-modify-playback-state user-read-currently-playing streaming user-library-modify user-read-email user-read-private",
                                                            cache_path="spotify_token_cache",
                                                            show_dialog=True))

    def get_top_tracks(self, time_range='short_term', limit=10):
        """
        Fetches the top tracks for the current user.

        Parameters:
            time_range (str): Time range for the top tracks ('short_term', 'medium_term', 'long_term')
            limit (int): Number of tracks to return

        Returns:
            list: A list of top tracks for the current user
        """
        results = self.sp.current_user_top_tracks(time_range=time_range, limit=limit)
        top_tracks = results['items']
        return top_tracks

    def create_playlist(self, user_id, name, description='', public=False):
        """
        Creates a new playlist for a user.

        Parameters:
            user_id (str): The Spotify user ID
            name (str): The name of the playlist
            description (str): The description of the playlist
            public (bool): Whether the playlist should be public

        Returns:
            str: The ID of the created playlist
        """
        playlist = self.sp.user_playlist_create(user=user_id, name=name, public=public, description=description)
        return playlist['id']

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """
        Adds tracks to a specific playlist.

        Parameters:
            playlist_id (str): The ID of the playlist
            track_ids (list): A list of Spotify track IDs to add to the playlist
        """
        self.sp.playlist_add_items(playlist_id=playlist_id, items=track_ids)

    # New methods added for enhanced data fetching:
    def get_saved_tracks(self, limit=20):
        """Fetches tracks saved in the user's 'Your Music' library."""
        return self.sp.current_user_saved_tracks(limit=limit)

    def get_recently_played(self, limit=20):
        """Fetches the user's recent listen history."""
        return self.sp.current_user_recently_played(limit=limit)

    def get_top_artists(self, time_range='medium_term', limit=20):
        """Fetches the top artists for the user over a specified time range."""
        return self.sp.current_user_top_artists(time_range=time_range, limit=limit)

if __name__ == "__main__":
    # Example usage
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
    scopes = "user-read-recently-played user-library-read user-top-read playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-playback-state user-modify-playback-state user-read-currently-playing streaming user-library-modify user-read-email user-read-private"

    music_client = MusicAPIClient(client_id, client_secret, redirect_uri, scopes)
    print("Spotify client initialized. Ready to fetch top tracks and manage playlists.")
