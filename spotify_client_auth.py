import os
import base64
import json
import requests
import logging
from flask import Flask, request, render_template_string
import webbrowser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = 9090
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Simple HTML page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Spotify Token</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            text-align: center;
        }
        .success {
            color: #1DB954;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .error {
            color: #e74c3c;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>Spotify Authentication</h1>
    {% if success %}
        <div class="success">
            <h2>✓ Authentication Successful!</h2>
            <p>The access token has been saved.</p>
            <p>You can close this window and return to the terminal.</p>
        </div>
    {% else %}
        <div class="error">
            <h2>× Authentication Failed</h2>
            <p>{{ error }}</p>
        </div>
    {% endif %}
</body>
</html>
"""

def get_client_credentials_token():
    """Get access token using client credentials flow"""
    try:
        # Create Basic Auth header
        auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        
        # Request token
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers={
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                'grant_type': 'client_credentials'
            }
        )
        
        response.raise_for_status()
        return response.json()['access_token']
        
    except Exception as e:
        logger.error(f"Error getting token: {str(e)}")
        return None

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
    # Get token using client credentials
    token = get_client_credentials_token()
    
    if token:
        # Save token
        if save_token(token):
            return render_template_string(HTML, success=True)
        else:
            return render_template_string(HTML, success=False, error="Failed to save token")
    else:
        return render_template_string(HTML, success=False, error="Failed to get token")

def main():
    try:
        if not all([CLIENT_ID, CLIENT_SECRET]):
            raise ValueError("Missing Spotify credentials. Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
        
        # Get hostname
        hostname = os.getenv('CODESPACE_NAME')
        if hostname:
            base_url = f"https://{hostname}-{PORT}.preview.app.github.dev"
        else:
            base_url = f"http://localhost:{PORT}"
        
        logger.info("\nSpotify Authentication")
        logger.info("=====================")
        logger.info(f"Opening {base_url} in your browser...")
        
        # Make port public
        os.system(f"gh codespace ports visibility {PORT}:public")
        
        # Open browser
        webbrowser.open(base_url)
        
        # Start server
        app.run(host='0.0.0.0', port=PORT)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    main()