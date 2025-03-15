import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spotify_api.log'),
        logging.StreamHandler()
    ]
)

class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors"""
    pass

class MusicAPIClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: str):
        """
        Initialize the Music API Client with Spotify authentication and enhanced error handling.

        Parameters:
            client_id (str): Spotify Application client ID
            client_secret (str): Spotify Application client secret
            redirect_uri (str): Redirect URI set in the Spotify Developer Dashboard
            scopes (str): Scopes for the Spotify API access
        """
        self.retry_delay = 2
        self.max_retries = 3
        
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scopes,
                cache_path=".spotify_token_cache",
                show_dialog=True
            ))
            # Verify connection
            self.sp.current_user()
        except Exception as e:
            logging.error(f"Failed to initialize Spotify client: {str(e)}")
            raise SpotifyAPIError("Failed to initialize Spotify client") from e

    def _retry_on_failure(self, operation: callable, *args, **kwargs) -> Any:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
            
        Raises:
            SpotifyAPIError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except spotipy.SpotifyException as e:
                last_error = e
                if e.http_status == 429:  # Rate limit
                    wait_time = int(e.headers.get('Retry-After', self.retry_delay))
                    logging.warning(f"Rate limit exceeded. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Spotify API error on attempt {attempt + 1}: {str(e)}")
                    if attempt == self.max_retries - 1:
                        break
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    
        raise SpotifyAPIError(f"Operation failed after {self.max_retries} attempts: {str(last_error)}")

    def get_top_tracks(self, time_range: str = 'short_term', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch top tracks for the current user with error handling.
        
        Args:
            time_range: Time range for top tracks ('short_term', 'medium_term', 'long_term')
            limit: Number of tracks to return (max 50)
            
        Returns:
            List of track objects
        """
        if limit > 50:
            logging.warning("Limit exceeds maximum of 50. Setting to 50.")
            limit = 50
            
        results = self._retry_on_failure(
            self.sp.current_user_top_tracks,
            time_range=time_range,
            limit=limit
        )
        return results['items']

    def create_playlist(self, user_id: str, name: str, description: str = '', public: bool = False) -> str:
        """
        Create a new playlist for a user with error handling.
        
        Args:
            user_id: The Spotify user ID
            name: The name of the playlist
            description: The description of the playlist
            public: Whether the playlist should be public
            
        Returns:
            The ID of the created playlist
        """
        playlist = self._retry_on_failure(
            self.sp.user_playlist_create,
            user=user_id,
            name=name,
            public=public,
            description=description
        )
        return playlist['id']

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        """
        Add tracks to a playlist with error handling.
        
        Args:
            playlist_id: The ID of the playlist
            track_ids: List of Spotify track IDs to add
        """
        # Split into chunks of 100 (Spotify API limit)
        chunk_size = 100
        for i in range(0, len(track_ids), chunk_size):
            chunk = track_ids[i:i + chunk_size]
            self._retry_on_failure(
                self.sp.playlist_add_items,
                playlist_id=playlist_id,
                items=chunk
            )

    def get_saved_tracks(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Fetch tracks saved in the user's library with pagination.
        
        Args:
            limit: Number of tracks per request (max 50)
            offset: The index of the first track to return
            
        Returns:
            Dict containing track information and pagination details
        """
        return self._retry_on_failure(
            self.sp.current_user_saved_tracks,
            limit=min(limit, 50),
            offset=offset
        )

    def get_recently_played(self, limit: int = 20, after: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch user's recently played tracks.
        
        Args:
            limit: Number of tracks to return (max 50)
            after: Unix timestamp in milliseconds to get tracks after
            
        Returns:
            Dict containing recently played tracks
        """
        return self._retry_on_failure(
            self.sp.current_user_recently_played,
            limit=min(limit, 50),
            after=after
        )

    def get_top_artists(self, time_range: str = 'medium_term', limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch top artists for the user.
        
        Args:
            time_range: Time range for top artists ('short_term', 'medium_term', 'long_term')
            limit: Number of artists to return (max 50)
            
        Returns:
            List of artist objects
        """
        results = self._retry_on_failure(
            self.sp.current_user_top_artists,
            time_range=time_range,
            limit=min(limit, 50)
        )
        return results['items']

    def get_track_features(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get audio features for a specific track.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            Dict containing audio features or None if not found
        """
        try:
            return self._retry_on_failure(
                self.sp.audio_features,
                tracks=[track_id]
            )[0]
        except IndexError:
            logging.warning(f"No audio features found for track {track_id}")
            return None

if __name__ == "__main__":
    try:
        # Example usage
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8080")
        
        if not all([client_id, client_secret]):
            raise ValueError(
                "Missing required environment variables. Please set "
                "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET"
            )
        
        scopes = (
            "user-read-private "
            "user-read-email "
            "playlist-read-private "
            "playlist-modify-public "
            "user-top-read"
        )
        
        # Initialize client
        music_client = MusicAPIClient(client_id, client_secret, redirect_uri, scopes)
        
        # Test connection
        top_tracks = music_client.get_top_tracks(limit=5)
        print("\nYour top 5 tracks:")
        for i, track in enumerate(top_tracks, 1):
            print(f"{i}. {track['name']} by {track['artists'][0]['name']}")
            
    except SpotifyAPIError as e:
        logging.error(f"Spotify API Error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
