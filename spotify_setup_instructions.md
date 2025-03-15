# Spotify Authentication Setup for Codespace

## 1. Configure Port Forwarding
1. In your Codespace, click the "Ports" tab in the lower panel
2. Click "Add Port"
3. Enter `8080`
4. Right-click the added port and select "Port Visibility" -> "Public"

## 2. Configure Spotify Application
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Select your application
3. Click "Edit Settings"
4. Add these Redirect URIs:
   - `http://localhost:8080/callback` (for local testing)
   - `https://YOUR-CODESPACE-NAME-8080.preview.app.github.dev/callback` (for Codespace)
   Note: Replace YOUR-CODESPACE-NAME with your actual Codespace name
5. Click "Save"

## 3. Run Authentication
1. Make sure you have the environment variables set:
   ```bash
   export SPOTIPY_CLIENT_ID=your_client_id
   export SPOTIPY_CLIENT_SECRET=your_client_secret
   ```
2. Run the authentication script:
   ```bash
   python spotify_auth_setup.py
   ```
3. When the browser opens, log in to Spotify and authorize the application
4. The script will save your refresh token in the .env file

## Troubleshooting
- If the callback fails, make sure port 8080 is publicly accessible
- Check that your Redirect URI exactly matches the one in your Spotify app settings
- If using Codespace, ensure the Codespace URL is added to your Spotify app's Redirect URIs