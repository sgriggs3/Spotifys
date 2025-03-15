import os
import json
from flask import Flask, request, render_template_string
import pyngrok.ngrok as ngrok
import webbrowser
import logging
from urllib.parse import urlencode

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = 9090
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

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
            <button onclick="window.location.href='{{ auth_url }}'">
                Connect with Spotify
            </button>
        {% else %}
            <div class="token-display">
                <div class="success-icon">✓</div>
                <h3>Authentication Successful!</h3>
                <p>Token has been saved to .env file</p>
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
    auth_params = {
        'client_id': CLIENT_ID,
        'response_type': 'token',
        'redirect_uri': f"{ngrok.connect(PORT).public_url}/callback",
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
    
    # Check if token is in fragment (it will be handled by JavaScript)
    if '#' in request.url:
        return render_template_string(
            """
            <script>
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const token = params.get('access_token');
                if (token) {
                    fetch('/save-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({token: token})
                    }).then(() => {
                        window.location.href = '/success?token=' + token;
                    });
                }
            </script>
            """
        )
    
    return render_template_string(
        HTML_TEMPLATE,
        auth_url='/',
        token=None,
        error="No token received"
    )

@app.route('/save-token', methods=['POST'])
def save_token_endpoint():
    data = request.json
    token = data.get('token')
    if token and save_token(token):
        return {'status': 'success'}
    return {'status': 'error'}, 400

@app.route('/success')
def success():
    token = request.args.get('token')
    return render_template_string(
        HTML_TEMPLATE,
        auth_url='/',
        token=token,
        error=None
    )

def main():
    try:
        # Kill any existing ngrok tunnels
        os.system("pkill ngrok")
        
        # Start ngrok tunnel
        public_url = ngrok.connect(PORT).public_url
        logger.info("\nSpotify Authentication Server")
        logger.info("===========================")
        logger.info(f"Local URL: http://localhost:{PORT}")
        logger.info(f"Public URL: {public_url}")
        logger.info("\nAdd this URL to your Spotify App Settings:")
        logger.info(f"{public_url}/callback")
        
        # Open browser after a short delay
        webbrowser.open(public_url)
        
        # Start Flask server
        app.run(host='0.0.0.0', port=PORT)
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        ngrok.kill()

if __name__ == '__main__':
    main()