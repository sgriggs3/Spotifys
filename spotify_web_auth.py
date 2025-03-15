import os
import json
import http.server
import socketserver
import webbrowser
from urllib.parse import urlencode
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
PORT = 8080
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Get Codespace URL or use localhost
CODESPACE_NAME = os.getenv('CODESPACE_NAME')
if CODESPACE_NAME:
    REDIRECT_URI = f"https://{CODESPACE_NAME}-{PORT}.preview.app.github.dev"
else:
    REDIRECT_URI = f"http://localhost:{PORT}"

# HTML template for the authentication page
AUTH_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Spotify Authentication</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            text-align: center;
        }}
        button {{
            background-color: #1DB954;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin: 20px;
        }}
        button:hover {{
            background-color: #1ed760;
        }}
        #token-display {{
            word-break: break-all;
            background-color: #f8f8f8;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
            display: none;
        }}
    </style>
</head>
<body>
    <h1>Spotify Authentication</h1>
    <button onclick="startAuth()">Authenticate with Spotify</button>
    <div id="token-display"></div>

    <script>
        function startAuth() {{
            const authEndpoint = 'https://accounts.spotify.com/authorize';
            const clientId = '{client_id}';
            const redirectUri = '{redirect_uri}';
            const scopes = [
                'user-read-playback-state',
                'user-modify-playback-state',
                'user-read-currently-playing',
                'playlist-read-private',
                'playlist-read-collaborative',
                'playlist-modify-private',
                'playlist-modify-public',
                'user-read-recently-played',
                'user-library-read',
                'streaming',
                'user-top-read',
                'user-library-modify',
                'user-read-email'
            ];

            const authUrl = `${{authEndpoint}}?` + new URLSearchParams({{
                response_type: 'token',
                client_id: clientId,
                scope: scopes.join(' '),
                redirect_uri: redirectUri,
                show_dialog: true
            }});

            window.location.href = authUrl;
        }}

        // Handle the redirect with hash fragment
        if (window.location.hash) {{
            const params = new URLSearchParams(window.location.hash.substring(1));
            const accessToken = params.get('access_token');
            const refreshToken = params.get('refresh_token');
            
            if (accessToken) {{
                const tokenDisplay = document.getElementById('token-display');
                tokenDisplay.style.display = 'block';
                tokenDisplay.innerHTML = `
                    <h3>Authentication Successful!</h3>
                    <p>Access Token: ${{accessToken}}</p>
                    <p>Please save this token and use it in your application.</p>
                `;

                // Send token to server
                fetch('/save_token', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ access_token: accessToken }})
                }});
            }}
        }}
    </script>
</body>
</html>
"""

class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Render the HTML template with client ID and redirect URI
            html_content = AUTH_PAGE.format(
                client_id=CLIENT_ID,
                redirect_uri=REDIRECT_URI
            )
            self.wfile.write(html_content.encode())
            return

    def do_POST(self):
        if self.path == '/save_token':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            token_data = json.loads(post_data.decode('utf-8'))
            
            # Save the token
            self.save_token(token_data.get('access_token'))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            return

    def save_token(self, access_token):
        """Save the access token to .env file"""
        try:
            env_content = []
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.readlines()
            
            # Remove existing token lines
            env_content = [line for line in env_content 
                          if not line.startswith('SPOTIFY_ACCESS_TOKEN=')]
            
            # Add new token
            env_content.append(f"SPOTIFY_ACCESS_TOKEN={access_token}\n")
            
            with open('.env', 'w') as f:
                f.writelines(env_content)
                
            logging.info("Token saved successfully")
        except Exception as e:
            logging.error(f"Error saving token: {str(e)}")

def main():
    try:
        if not CLIENT_ID:
            raise ValueError("SPOTIPY_CLIENT_ID environment variable not set")

        logging.info("\nStarting Spotify Web Authentication")
        logging.info("================================")
        logging.info(f"Server URL: {REDIRECT_URI}")
        
        # Create and start the server
        with socketserver.TCPServer(("", PORT), AuthHandler) as httpd:
            logging.info(f"Server started at port {PORT}")
            logging.info("Opening browser for authentication...")
            
            # Open the browser
            webbrowser.open(f"{REDIRECT_URI}")
            
            # Serve until interrupted
            httpd.serve_forever()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()