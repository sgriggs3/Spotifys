!pip install spotipy --upgrade

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyPKCE
import pandas as pd
import time
import secrets
import requests


# --- FILE PATH ---
file_path = '/content/your_extended_history_file.csv'

# Load the dataframe
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: File not found at '{file_path}'.  Make sure the file is uploaded and the name is correct.")
    raise

# Check if `spotify_track_uri` column exists
if 'spotify_track_uri' not in df.columns:
    print("Error: 'spotify_track_uri' column is missing. Cannot add audio features.")
else:
    # --- Authorization (PKCE) ---
    cid = 'dcc2df507bde447c93a0199358ca219d'  # Your Client ID
    secret = '128089720b414d1e8233290d94fb38a0'  # Your Client Secret - Not needed for pure PKCE, but good practice with Spotipy
    redirect_uri = 'http://localhost:8888/callback'  # Set in your Spotify app's settings
    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played user-top-read user-library-read user-library-modify playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"


    # PKCE: Use SpotifyPKCE directly.  No manual challenge generation needed.
    auth_manager = SpotifyPKCE(client_id=cid,
                                 redirect_uri=redirect_uri,
                                 scope=scope,
                                open_browser=False)  # For Colab

    # Manual URL handling for Colab (as before)
    auth_url = auth_manager.get_authorize_url()
    print("Copy and paste this URL into your browser:")
    print(auth_url)
    print()
    redirected_url = input("Paste the URL you were redirected to here:")

    # Get the token.  Remove as_dict
    token_info = auth_manager.get_access_token(code=auth_manager.parse_response_code(redirected_url))

    # Use the access token directly.
    sp = spotipy.Spotify(auth=token_info['access_token'])



    def get_track_ids_from_uris(track_uris):
        """Extracts track IDs, handling NaNs and errors."""
        track_ids = []
        for uri in track_uris:
            if pd.isna(uri):
                track_ids.append(None)
            else:
                try:
                    track_ids.append(uri.split(':')[-1])
                except (AttributeError, IndexError):
                    track_ids.append(None)
        return track_ids

    # Get track IDs
    df['track_id'] = get_track_ids_from_uris(df['spotify_track_uri'])

    # --- Fetch Audio Features (with error handling and retries) ---
    def fetch_audio_features(track_ids, batch_size=50, retries=3, retry_delay=5):
        """Fetches audio features in batches, with retries/error handling."""
        audio_features_list = []
        for i in range(0, len(track_ids), batch_size):
            batch_ids = [id for id in track_ids[i:i + batch_size] if id]  # Filter None
            if not batch_ids:
                audio_features_list.extend([None] * (min(batch_size, len(track_ids) - i)))
                continue

            for attempt in range(retries):
                try:
                    features_batch = sp.audio_features(tracks=batch_ids)
                    # Check for None within the batch results
                    if features_batch:
                         for features in features_batch:
                             if features is not None: # Check if features is not None
                                audio_features_list.append(features)
                             else:
                                audio_features_list.append(None)  # Append None if features is None
                    else:
                        audio_features_list.extend([None] * len(batch_ids))
                    break  # Success
                except spotipy.SpotifyException as e:
                    if e.http_status == 429:
                        wait_time = int(e.headers.get('Retry-After', retry_delay))
                        print(f"Rate limit exceeded. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    elif e.http_status == 403:
                        print(f"Forbidden (403). Check credentials/permissions.")
                        audio_features_list.extend([None] * len(batch_ids))
                        break
                    else:
                        print(f"Error (batch {i}, attempt {attempt+1}): {e}")
                        time.sleep(retry_delay)
                        if attempt == retries - 1:
                            audio_features_list.extend([None] * len(batch_ids))

                except Exception as e:
                    print(f"Unexpected error (batch {i}, attempt {attempt+1}): {e}")
                    time.sleep(retry_delay)
                    if attempt == retries-1:
                            audio_features_list.extend([None] * len(batch_ids))
            else:
                if features_batch is not None and len(batch_ids) > 0 :
                  if all(item is None for item in features_batch):
                    audio_features_list.extend([None] * len(batch_ids))

        return audio_features_list

    audio_features = fetch_audio_features(df['track_id'].tolist())

    # Create DataFrame and merge
    audio_features_df = pd.DataFrame(audio_features)
    df_with_audio_features = pd.concat([df, audio_features_df], axis=1)

    # --- SAVE OUTPUT ---
    output_file_path = '/content/spotify_merged_with_audio_features.csv'  # Output path
    df_with_audio_features.to_csv(output_file_path, index=False)
    print(f"Data saved to {output_file_path}")
