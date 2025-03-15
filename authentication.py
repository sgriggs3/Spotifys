import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import logging
import os
from typing import Optional, Dict, Any, cast
import time
import socket
import webbrowser
import base64
import hashlib
import secrets
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spotify_auth.log'),
        logging.StreamHandler()
    ]
)

class SpotifyAuthError(Exception):
    """Custom exception for Spotify authentication errors"""
    pass

class PKCEUtil:
    """Handles PKCE (Proof Key for Code Exchange) flow"""
    
    @staticmethod
    def generate_code_verifier(length: int = 64) -> str:
        """Generate a code verifier for PKCE"""
        code_verifier = secrets.token_urlsafe(length)
        return code_verifier[:length]
    
    @staticmethod
    def generate_code_challenge(code_verifier: str) -> str:
        """Generate a code challenge from the code verifier"""
        if not code_verifier:
            raise ValueError("Code verifier cannot be empty")
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').replace('=', '')
        return code_challenge

class TokenManager:
    """Manages Spotify authentication tokens with enhanced security"""
    
    def __init__(self, auth_manager: SpotifyOAuth):
        self.auth_manager = auth_manager
        self.last_refresh = 0
        self.min_token_lifetime = 300  # 5 minutes
        
    def get_token(self) -> Dict[str, Any]:
        """Get a valid token, refreshing if necessary with exponential backoff"""
        token = self.auth_manager.get_cached_token()
        
        if not token:
            logging.info("No cached token found. Starting new authentication flow.")
            return cast(Dict[str, Any], self.auth_manager.get_access_token(check_cache=False))
        
        # Check if token will expire soon
        if self.auth_manager.is_token_expired(token) or \
           (token.get('expires_at', 0) - time.time()) < self.min_token_lifetime:
            logging.info("Token expired or expiring soon. Refreshing...")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    refresh_token = token.get('refresh_token')
                    if not refresh_token:
                        raise SpotifyAuthError("No refresh token available")
                        
                    token = self.auth_manager.refresh_access_token(refresh_token)
                    self.last_refresh = time.time()
                    return token
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise SpotifyAuthError(f"Failed to refresh token after {max_retries} attempts") from e
                    
                    wait_time = 2 ** attempt
                    logging.warning(f"Token refresh failed (attempt {attempt + 1}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    
        return token

def find_free_port() -> int:
    """Find an available port for the redirect URI"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def validate_redirect_uri(redirect_uri: str) -> str:
    """Validate and normalize redirect URI"""
    try:
        parsed = urlparse(redirect_uri)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid redirect URI format")
            
        # Ensure localhost for development
        if parsed.hostname not in ('localhost', '127.0.0.1'):
            logging.warning("Using non-localhost redirect URI in development environment")
            
        return redirect_uri
        
    except Exception as e:
        raise SpotifyAuthError(f"Invalid redirect URI: {str(e)}")

def authenticate_spotify(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scopes: str,
    use_pkce: bool = True
) -> Optional[spotipy.Spotify]:
    """
    Authenticate with the Spotify API using OAuth with enhanced security.

    Parameters:
        client_id (str): Spotify Application client ID
        client_secret (str): Spotify Application client secret
        redirect_uri (str): Redirect URI set in the Spotify Developer Dashboard
        scopes (str): A string of scopes separated by spaces
        use_pkce (bool): Whether to use PKCE flow (recommended for public clients)

    Returns:
        Optional[spotipy.Spotify]: Authenticated Spotify client object
        
    Raises:
        SpotifyAuthError: If authentication fails
    """
    try:
        # Validate inputs
        if not all([client_id, client_secret, redirect_uri, scopes]):
            raise SpotifyAuthError("Missing required authentication parameters")
            
        # Validate and normalize redirect URI
        redirect_uri = validate_redirect_uri(redirect_uri)
        
        # Generate PKCE verifier and challenge if needed
        code_verifier = PKCEUtil.generate_code_verifier() if use_pkce else None
        code_challenge = PKCEUtil.generate_code_challenge(code_verifier) if code_verifier else None
        
        # Initialize auth manager with retry mechanism
        retries = 3
        for attempt in range(retries):
            try:
                auth_kwargs: Dict[str, Any] = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'scope': scopes,
                    'show_dialog': True,
                    'cache_path': ".spotify_token_cache",
                    'open_browser': False
                }
                
                if use_pkce and code_verifier and code_challenge:
                    auth_kwargs.update({
                        'code_verifier': code_verifier,
                        'code_challenge': code_challenge,
                        'code_challenge_method': 'S256'
                    })
                
                auth_manager = SpotifyOAuth(**auth_kwargs)
                
                # Create token manager
                token_manager = TokenManager(auth_manager)
                
                # Get initial token
                token = token_manager.get_token()
                
                if not token:
                    raise SpotifyAuthError("Failed to obtain access token")
                
                # Create Spotify client with custom retry handling
                sp = spotipy.Spotify(
                    auth_manager=auth_manager,
                    requests_timeout=10,
                    retries=3,
                    status_forcelist=(429, 500, 502, 503, 504)
                )
                
                # Verify authentication
                sp.current_user()
                
                logging.info("Successfully authenticated with Spotify")
                return sp
                
            except SpotifyException as e:
                logging.error(f"Spotify API error on attempt {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    raise SpotifyAuthError("Failed to verify authentication with Spotify API") from e
                time.sleep(2 ** attempt)
                
    except Exception as e:
        logging.error(f"Unexpected error during authentication: {str(e)}")
        raise SpotifyAuthError("Authentication failed due to unexpected error") from e

def get_authorization_url(client_id: str, redirect_uri: str, scopes: str) -> str:
    """
    Get the Spotify authorization URL for manual browser authentication.
    
    Parameters:
        client_id (str): Spotify Application client ID
        redirect_uri (str): Redirect URI set in the Spotify Developer Dashboard
        scopes (str): A string of scopes separated by spaces
        
    Returns:
        str: Authorization URL
    """
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scopes,
        show_dialog=True
    )
    return auth_manager.get_authorize_url()

if __name__ == "__main__":
    try:
        # Load credentials from environment variables
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8080")
        
        # Verify required environment variables
        if not client_id or not client_secret:
            raise SpotifyAuthError(
                "Missing required environment variables. Please set "
                "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET"
            )
        
        # Required scopes for the application
        scopes = (
            "user-read-playback-state "
            "user-modify-playback-state "
            "user-read-currently-playing "
            "playlist-read-private "
            "playlist-read-collaborative "
            "playlist-modify-private "
            "playlist-modify-public "
            "user-read-recently-played "
            "user-library-read "
            "streaming "
            "user-top-read "
            "user-library-modify "
            "user-read-email"
        )
        
        # Authenticate and get the Spotify client
        spotify_client = authenticate_spotify(
            client_id,
            client_secret,
            redirect_uri,
            scopes,
            use_pkce=True  # Enable PKCE flow
        )
        
        if spotify_client:
            print("Successfully authenticated with Spotify")
            # Get user info as a test
            user_info = spotify_client.current_user()
            if user_info:
                display_name = user_info.get('display_name', 'Unknown')
                user_id = user_info.get('id', 'Unknown')
                print(f"Authenticated as: {display_name} ({user_id})")
            else:
                print("Authenticated successfully but could not fetch user info")
            
    except SpotifyAuthError as e:
        print(f"Authentication Error: {str(e)}")
        if client_id:
            # Get manual authorization URL
            auth_url = get_authorization_url(client_id, redirect_uri, scopes)
            print("\nPlease visit the following URL to authorize the application:")
            print(auth_url)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
