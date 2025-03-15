from flask import Flask, request, render_template_string
import os
import webbrowser
from urllib.parse import urlencode
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = 9090
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Get Codespace URL or use localhost
CODESPACE_NAME = os.getenv('CODESPACE_NAME')
if CODESPACE_NAME:
    REDIRECT_URI = f"https://{CODESPACE_NAME}-{PORT}.preview.app.github.dev/callback"
    BASE_URL = f"https://{CODESPACE_NAME}-{PORT}.preview.app.github.dev"
else:
    REDIRECT_URI = f"http://localhost:{PORT}/callback"
    BASE_URL = f"http://localhost:{PORT}"

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
        }
        button:hover {
            background-color: #1ed760;
        }
        .token-display {
            word-break: break-all;
            background-color: #f8f8f8;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Spotify Authentication</h1>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    {% if not token %}
        <button onclick="window.location.href='{{ auth_url }}'">
            Connect with Spotify
        </button>
    {% else %}
        <div class="token-display">
            <h3>Authentication Successful!</h3>
            <p>Token has been saved to .env file</p>
        </div>
    {% endif %}
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
    auth_params = {
        'client_id': CLIENT_ID,
        'response_type': 'token',
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join([
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
        ]),
        'show_dialog': 'true'
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    
    return render_template_string(
        HTML_TEMPLATE,
        auth_url=auth_url,
        token=None,
        error=None
    )

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return render_template_string(
            HTML_TEMPLATE,
            auth_url='/',
            token=None,
            error=request.args.get('error')
        )
    
    token = request.args.get('access_token')
    if token:
        if save_token(token):
            return render_template_string(
                HTML_TEMPLATE,
                auth_url='/',
                token=token,
                error=None
            )
        else:
            return render_template_string(
                HTML_TEMPLATE,
                auth_url='/',
                token=None,
                error="Failed to save token"
            )
    
    return render_template_string(
        HTML_TEMPLATE,
        auth_url='/',
        token=None,
        error="No token received"
    )

def main():
    try:
        logger.info("\nSpotify Authentication Server")
        logger.info("===========================")
        logger.info(f"Server URL: {BASE_URL}")
        logger.info(f"Callback URL: {REDIRECT_URI}")
        logger.info("\nMake sure this callback URL is added to your Spotify App settings!")
        
        # Open browser
        webbrowser.open(BASE_URL)
        
        # Start server
        app.run(host='0.0.0.0', port=PORT)
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

if __name__ == '__main__':
    main()