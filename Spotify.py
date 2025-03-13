import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FILE PATH ---
file_paths = ['spotify_history_part_1.csv', 'spotify_history_part_2.csv', 'spotify_history_part_3.csv', 'spotify_history_part_4.csv', 'spotify_history_part_5.csv']

# --- Authorization ---
def authenticate_spotify():
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played user-top-read user-library-read user-library-modify playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"

    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope, cache_path='.cache')
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

# --- Load CSV files ---
def load_csv_files(file_paths):
    dataframes = []
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            dataframes.append(df)
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
    return dataframes

# --- Extract track IDs ---
def get_track_ids_from_uris(track_uris):
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

# --- Fetch Audio Features ---
def fetch_audio_features(sp, track_ids, batch_size=50, retries=3, retry_delay=5):
    audio_features_list = []
    for i in range(0, len(track_ids), batch_size):
        batch_ids = [id for id in track_ids[i:i + batch_size] if id]
        if not batch_ids:
            audio_features_list.extend([None] * (min(batch_size, len(track_ids) - i)))
            continue

        for attempt in range(retries):
            try:
                features_batch = sp.audio_features(tracks=batch_ids)
                if features_batch:
                    for features in features_batch:
                        if features is not None:
                            audio_features_list.append(features)
                        else:
                            audio_features_list.append(None)
                else:
                    audio_features_list.extend([None] * len(batch_ids))
                break
            except spotipy.SpotifyException as e:
                if e.http_status == 429:
                    wait_time = int(e.headers.get('Retry-After', retry_delay))
                    logging.warning(f"Rate limit exceeded. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif e.http_status == 403:
                    logging.error("Forbidden (403). Check credentials/permissions.")
                    audio_features_list.extend([None] * len(batch_ids))
                    break
                else:
                    logging.error(f"Error (batch {i}, attempt {attempt+1}): {e}")
                    time.sleep(retry_delay)
                    if attempt == retries - 1:
                        audio_features_list.extend([None] * len(batch_ids))
            except Exception as e:
                logging.error(f"Unexpected error (batch {i}, attempt {attempt+1}): {e}")
                time.sleep(retry_delay)
                if attempt == retries - 1:
                    audio_features_list.extend([None] * len(batch_ids))
        else:
            if features_batch is not None and len(batch_ids) > 0:
                if all(item is None for item in features_batch):
                    audio_features_list.extend([None] * len(batch_ids))

    return audio_features_list

# --- Process CSV files ---
def process_csv_files(sp, dataframes):
    for i, df in enumerate(dataframes):
        if 'spotify_track_uri' not in df.columns:
            logging.error(f"'spotify_track_uri' column is missing in file {file_paths[i]}. Cannot add audio features.")
            continue

        df['track_id'] = get_track_ids_from_uris(df['spotify_track_uri'])
        audio_features = fetch_audio_features(sp, df['track_id'].tolist())
        audio_features_df = pd.DataFrame(audio_features)
        df_with_audio_features = pd.concat([df, audio_features_df], axis=1)

        output_file_path = f'processed_data/spotify_history_part_{i+1}_processed.csv'
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        df_with_audio_features.to_csv(output_file_path, index=False)
        logging.info(f"Data saved to {output_file_path}")

# --- Main Execution ---
if __name__ == "__main__":
    sp = authenticate_spotify()
    dataframes = load_csv_files(file_paths)
    process_csv_files(sp, dataframes)
