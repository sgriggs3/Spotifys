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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global variables
received_auth_code = None
server_instance = None

class SpotifyAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_auth_code
        try:
            if '/callback' in self.path:
                query_components = parse_qs(urlparse(self.path).query)
                
                if 'error' in query_components:
                    self.send_error_response(f"Authorization failed: {query_components['error'][0]}")
                    return
                    
                if 'code' not in query_components:
                    self.send_error_response("No authorization code received")
                    return
                
                received_auth_code = query_components['code'][0]
                self.send_success_response()
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            logging.error(f"Error handling callback: {str(e)}")
            self.send_error_response(str(e))

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def send_success_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        success_html = """
        <html>
        <body>
            <h1>Authorization Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
            <script>window.close()</script>
        </body>
        </html>
        """
        self.wfile.write(success_html.encode())
    
    def send_error_response(self, error_message):
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        error_html = f"""
        <html>
        <body>
            <h1>Authorization Failed</h1>
            <p>Error: {error_message}</p>
            <script>window.close();</script>
        </body>
        </html>
        """
        self.wfile.write(error_html.encode())

def get_spotify_auth(port=8080):
    """Get Spotify authorization code using localhost"""
    global received_auth_code, server_instance
    
    # Load environment variables
    load_dotenv()
    
    # Set up redirect URI using localhost
    redirect_uri = f"http://localhost:{port}/callback"
    
    # Check Spotify credentials
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("Missing Spotify credentials. Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
    
    try:
        # Start local server
        server_instance = HTTPServer(('127.0.0.1', port), SpotifyAuthHandler)
        
        # Generate authorization URL
        auth_params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': 'user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-recently-played user-library-read streaming user-top-read user-library-modify user-read-email',
            'show_dialog': 'true'
        }
        
        auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
        
        # Print instructions
        logging.info("\nSpotify Authentication")
        logging.info("=====================")
        logging.info("Opening browser for authorization...")
        logging.info("If the browser doesn't open automatically, use this URL:")
        logging.info(auth_url)
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for the authorization code
        server_instance.handle_request()
        
        return received_auth_code, redirect_uri
        
    except Exception as e:
        logging.error(f"Error during authorization: {str(e)}")
        raise
    finally:
        if server_instance:
            server_instance.server_close()

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
        auth_code, redirect_uri = get_spotify_auth()
        
        if not auth_code:
            logging.error("No authorization code received")
            return
        
        # Exchange code for tokens
        logging.info("Getting access tokens...")
        tokens = get_tokens(auth_code, redirect_uri)
        
        # Save tokens
        logging.info("Saving tokens...")
        save_tokens(tokens)
        
        logging.info("\nAuthentication completed successfully!")
        logging.info("You can now use the Spotify API.")
        
    except Exception as e:
        logging.error(f"\nAuthentication failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()