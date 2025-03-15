import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
import requests
import signal
import sys
from dotenv import load_dotenv
import logging
import socket

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_codespace_url(port):
    """Get the Codespace public URL"""
    codespace_name = os.getenv('CODESPACE_NAME')
    if codespace_name:
        return f"https://{codespace_name}-{port}.preview.app.github.dev"
    return None

def verify_spotify_app_settings(redirect_uri):
    """Verify Spotify app settings before starting the server"""
    logging.info("\nSpotify Application Configuration Check")
    logging.info("===================================")
    logging.info("Before proceeding, please verify these settings in your Spotify Application:")
    logging.info("\n1. Redirect URI Configuration")
    logging.info("   Make sure this exact URI is added to your Spotify App's redirect URIs:")
    logging.info(f"   {redirect_uri}")
    
    response = input("\nHave you added this redirect URI to your Spotify App settings? (yes/no): ")
    if response.lower() != 'yes':
        logging.info("\nPlease follow these steps:")
        logging.info("1. Go to https://developer.spotify.com/dashboard")
        logging.info("2. Select your application")
        logging.info("3. Click 'Edit Settings'")
        logging.info("4. Add the redirect URI shown above")
        logging.info("5. Click 'Save'")
        logging.info("\nThen run this script again.")
        sys.exit(1)

def handle_auth(port=8080):
    """Handle the Spotify OAuth flow"""
    # Load environment variables
    load_dotenv()
    
    # Check credentials
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("Missing Spotify credentials. Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")

    # Set up the redirect URI
    base_url = get_codespace_url(port) or f"http://localhost:{port}"
    redirect_uri = f"{base_url}/callback"
    
    # Verify app settings
    verify_spotify_app_settings(redirect_uri)
    
    # Generate authorization URL
    auth_params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-recently-played user-library-read streaming user-top-read user-library-modify user-read-email',
        'show_dialog': 'true'
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    
    # Create server
    class AuthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                if '/callback' in self.path:
                    query = urlparse(self.path).query
                    params = parse_qs(query)
                    
                    if 'error' in params:
                        self.send_error_response(params['error'][0])
                        self.server.auth_code = None
                        return
                        
                    if 'code' not in params:
                        self.send_error_response("No code parameter received")
                        self.server.auth_code = None
                        return
                        
                    self.server.auth_code = params['code'][0]
                    self.send_success_response()
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            except Exception as e:
                logging.error(f"Callback error: {str(e)}")
                self.send_error_response(str(e))
                self.server.auth_code = None
        
        def log_message(self, format, *args):
            """Suppress default logging"""
            pass
            
        def send_success_response(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>window.close()</script>
                </body></html>
            """)
            
        def send_error_response(self, error):
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html><body>
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                </body></html>
            """.encode('utf-8'))
    
    # Start server
    server = HTTPServer(('0.0.0.0', port), AuthHandler)
    server.auth_code = None
    
    logging.info("\nStarting authentication process...")
    logging.info(f"Listening on {base_url}")
    
    # Open browser
    logging.info("\nOpening browser for authorization...")
    webbrowser.open(auth_url)
    
    # Handle one request
    server.handle_request()
    
    # Get the authorization code
    auth_code = server.auth_code
    server.server_close()
    
    if not auth_code:
        raise ValueError("Failed to get authorization code")
        
    return auth_code, redirect_uri

def get_tokens(auth_code, redirect_uri):
    """Exchange authorization code for tokens"""
    try:
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'client_id': os.getenv('SPOTIPY_CLIENT_ID'),
                'client_secret': os.getenv('SPOTIPY_CLIENT_SECRET'),
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error getting tokens: {str(e)}")
        raise

def save_tokens(tokens):
    """Save tokens to .env file"""
    try:
        env_content = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_content = f.readlines()
        
        # Remove existing token lines
        env_content = [line for line in env_content 
                      if not line.startswith('SPOTIFY_REFRESH_TOKEN=')]
        
        # Add new token
        env_content.append(f"SPOTIFY_REFRESH_TOKEN={tokens['refresh_token']}\n")
        
        with open('.env', 'w') as f:
            f.writelines(env_content)
            
        logging.info("Tokens saved to .env file")
    except Exception as e:
        logging.error(f"Error saving tokens: {str(e)}")
        raise

def main():
    try:
        # Get authorization code
        auth_code, redirect_uri = handle_auth()
        
        # Exchange authorization code for tokens
        logging.info("Getting access tokens...")
        tokens = get_tokens(auth_code, redirect_uri)
        
        # Save tokens
        save_tokens(tokens)
        
        logging.info("\nAuthentication completed successfully!")
        logging.info("You can now use the Spotify API.")
        
    except Exception as e:
        logging.error(f"\nAuthentication failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()