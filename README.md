# Spotify API Integration

This project provides a robust Python implementation for interacting with the Spotify API, featuring comprehensive error handling, retry mechanisms, and audio feature analysis.

## Setup Requirements

### 1. Spotify Developer Account
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Note down your `Client ID` and `Client Secret`
4. Add a redirect URI (e.g., `http://localhost:8080`)
5. Add it to the allowlist in your application settings

### 2. Environment Variables
Create a `.env` file in the project root with:
```env
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:8080
```

### 3. Python Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

## Core Components

### 1. Authentication (`authentication.py`)
- Implements OAuth2 authentication flow
- Handles token refresh automatically
- Includes retry mechanisms for failed authentication
- Provides manual authorization URL fallback
- Custom port management for redirect URI

### 2. Music API Client (`music_api_client.py`)
- High-level interface for Spotify API operations
- Comprehensive error handling
- Rate limiting protection
- Methods for:
  - Fetching top tracks/artists
  - Creating and managing playlists
  - Getting recently played tracks
  - Accessing user's saved tracks
  - Retrieving audio features

### 3. Audio Features Processing (`spotify_audio_features.py`)
- Batch processing of audio features
- Progress tracking
- Automatic retry on failures
- CSV file processing and merging
- Custom error handling

## Usage Examples

### Basic Authentication
```python
from authentication import authenticate_spotify

client_id = "your_client_id"
client_secret = "your_client_secret"
redirect_uri = "http://localhost:8080"
scopes = "user-read-private user-read-email playlist-read-private"

spotify_client = authenticate_spotify(client_id, client_secret, redirect_uri, scopes)
```

### Using the Music API Client
```python
from music_api_client import MusicAPIClient

client = MusicAPIClient(client_id, client_secret, redirect_uri, scopes)

# Get user's top tracks
top_tracks = client.get_top_tracks(limit=10)

# Create a playlist
playlist_id = client.create_playlist(
    user_id="your_user_id",
    name="My Playlist",
    description="Created with Spotify API"
)

# Add tracks to playlist
track_ids = ["spotify:track:id1", "spotify:track:id2"]
client.add_tracks_to_playlist(playlist_id, track_ids)
```

### Processing Audio Features
```python
from spotify_audio_features import SpotifyAudioFeatures

# Initialize processor
processor = SpotifyAudioFeatures(spotify_client)

# Process a CSV file with track URIs
processor.process_dataframe(
    df=your_dataframe,
    output_path="processed_data/output.csv"
)
```

## Error Handling

The implementation includes comprehensive error handling for:
- Authentication failures
- Rate limiting
- Network issues
- Invalid requests
- Token expiration
- Missing permissions

Each component has custom exceptions and logging for better debugging:
```python
try:
    client = MusicAPIClient(...)
except SpotifyAPIError as e:
    logging.error(f"API Error: {str(e)}")
except Exception as e:
    logging.error(f"Unexpected error: {str(e)}")
```

## Testing

Run the test suite to verify functionality:
```bash
python -m unittest spotify_test.py
```

The test suite includes:
- Authentication flow tests
- Token refresh mechanism tests
- API error handling tests
- Audio features processing tests

## Logging

All components include detailed logging:
- Authentication logs: `spotify_auth.log`
- API operation logs: `spotify_api.log`
- Audio features processing logs: `spotify_script_output.log`

## Best Practices

1. Token Management:
   - Store refresh tokens securely
   - Implement automatic token refresh
   - Handle expired tokens gracefully

2. Rate Limiting:
   - Implement exponential backoff
   - Respect Spotify's rate limits
   - Handle 429 responses appropriately

3. Error Handling:
   - Use custom exceptions for different error types
   - Implement retry mechanisms with backoff
   - Provide detailed error messages and logging

## Common Issues and Solutions

1. Authentication Failures:
   - Verify client credentials are correct
   - Ensure redirect URI matches Spotify dashboard
   - Check required scopes are properly configured

2. Rate Limiting:
   - Implement proper delays between requests
   - Use batch processing for multiple operations
   - Handle 429 responses with appropriate waiting periods

3. Permission Issues:
   - Verify all required scopes are requested
   - Check user authorization status
   - Ensure token has required permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
