import os
import json
from flask import Flask, request, render_template_string
import webbrowser
from urllib.parse import urlencode
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = 9090
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Get the public URL using port forwarding info
def get_public_url():
    try:
        # Get hostname from environment
        hostname = os.getenv('CODESPACE_NAME')
        if hostname:
            return f"https://{hostname}-{PORT}.preview.app.github.dev"
        return f"http://localhost:{PORT}"
    except Exception as e:
        logger.error(f"Error getting public URL: {e}")
        return f"http://localhost:{PORT}"

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Spotify Authentication</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            text-align: center;
            background-color: #282828;
            color: white;
        }
        .container {
            background-color: #181818;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        button {
            background-color: #1DB954;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin: 20px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #1ed760;
        }
        .token-display {
            word-break: break-all;
            background-color: #282828;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: left;
        }
        .success-icon {
            color: #1DB954;
            font-size: 48px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Spotify Authentication</h1>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        {% if not token %}
            <button onclick="startAuth()">Connect with Spotify</button>
            <script>
                function startAuth() {
                    const clientId = '{{ client_id }}';
                    const redirectUri = '{{ redirect_uri }}';
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
                    
                    const authUrl = 'https://accounts.spotify.com/authorize?' +
                        new URLSearchParams({
                            response_type: 'token',
                            client_id: clientId,
                            scope: scopes.join(' '),
                            redirect_uri: redirectUri,
                            show_dialog: true
                        });
                    
                    window.location.href = authUrl;
                }
            </script>
        {% else %}
            <div class="token-display">
                <div class="success-icon">✓</div>
                <h3>Authentication Successful!</h3>
                <p>Token has been saved.</p>
                <p>You can close this window and return to the application.</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

def save_token(token):
    """Save token to .env file"""
    try:
        env_content = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_content = f.readlines()
        
        # Remove existing token lines
        env_content = [line for line in env_content 
                      if not line.startswith('SPOTIFY_ACCESS_TOKEN=')]
        
        # Add new token
        env_content.append(f"SPOTIFY_ACCESS_TOKEN={token}\n")
        
        with open('.env', 'w') as f:
            f.writelines(env_content)
            
        logger.info("Token saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving token: {str(e)}")
        return False

@app.route('/')
def home():
    public_url = get_public_url()
    redirect_uri = f"{public_url}/callback"
    
    return render_template_string(
        HTML_TEMPLATE,
        client_id=CLIENT_ID,
        redirect_uri=redirect_uri,
        token=None,
        error=None
    )

@app.route('/callback')
def callback():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                // Extract token from URL fragment
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const token = params.get('access_token');
                
                if (token) {
                    // Send token to server
                    fetch('/save-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({token: token})
                    }).then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            window.location.href = '/success?token=' + token;
                        } else {
                            window.location.href = '/error';
                        }
                    });
                } else {
                    window.location.href = '/error';
                }
            </script>
        </body>
        </html>
    """)

@app.route('/save-token', methods=['POST'])
def save_token_endpoint():
    data = request.json
    token = data.get('token')
    if token and save_token(token):
        return {'status': 'success'}
    return {'status': 'error'}, 400

@app.route('/success')
def success():
    return render_template_string(
        HTML_TEMPLATE,
        client_id=CLIENT_ID,
        redirect_uri='',
        token='saved',
        error=None
    )

@app.route('/error')
def error():
    return render_template_string(
        HTML_TEMPLATE,
        client_id=CLIENT_ID,
        redirect_uri='',
        token=None,
        error="Authentication failed"
    )

def main():
    try:
        public_url = get_public_url()
        
        logger.info("\nSpotify Authentication")
        logger.info("=====================")
        logger.info(f"Server URL: {public_url}")
        logger.info("\nMake sure this callback URL is added to your Spotify App Settings:")
        logger.info(f"{public_url}/callback")
        
        input("\nPress Enter to start the authentication server...")
        
        # Make port public
        os.system(f"gh codespace ports visibility {PORT}:public")
        
        # Open browser
        webbrowser.open(public_url)
        
        # Start server
        app.run(host='0.0.0.0', port=PORT)
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

if __name__ == '__main__':
    main()