import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
import logging
import socket
import subprocess
import platform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    filename='spotify_script_output.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- FILE PATH ---
file_paths = ['cleaned_spotify_history.csv']

# --- Authentication ---

def kill_port(port):
    """Kill process using the specified port"""
    if platform.system() == "Windows":
        try:
            subprocess.run(['taskkill', '/f', '/im', 'node.exe'], check=True)
        except subprocess.CalledProcessError:
            pass
    else:
        try:
            subprocess.run(['lsof', '-ti', f':{port}', '-sTCP:LISTEN', '-t'], check=True)
            subprocess.run(['kill', '-9', f'$(lsof -ti:{port})'], shell=True)
        except subprocess.CalledProcessError:
            pass

def find_free_port():
    """Find a free port to use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def authenticate_spotify():
    """Authenticate with Spotify API using environment variables"""
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')

    # Ensure necessary environment variables are set
    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError(
            "SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET and SPOTIPY_REDIRECT_URI environment variables must be set.")

    # Find a free port or use the default
    redirect_port = 9090
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', redirect_port))
        sock.close()
    except socket.error:
        logging.warning(f"Port {redirect_port} is in use. Finding a free port...")
        redirect_port = find_free_port()
        redirect_uri = f'http://127.0.0.1:{redirect_port}/callback'
        os.environ['SPOTIPY_REDIRECT_URI'] = redirect_uri

    logging.info(f"Using redirect URI: {redirect_uri}")

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-read-recently-played user-library-read user-top-read playlist-read-private playlist-read-collaborative",
        open_browser=False
    )

    return spotipy.Spotify(auth_manager=auth_manager)

# --- Load CSV files ---

def load_csv_files(file_paths):
    """Load CSV files and return list of dataframes"""
    dataframes = []
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path, low_memory=False)
            dataframes.append(df)
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
    return dataframes

# --- Extract track IDs ---

def get_track_ids_from_uris(track_uris):
    """Extract track IDs from Spotify URIs"""
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
    """Fetch audio features for track IDs with rate limiting and retries"""
    audio_features_list = []
    batch_start = 0

    while batch_start < len(track_ids):
        batch_ids = [id for id in track_ids[batch_start:batch_start + batch_size] if id]
        if not batch_ids:
            batch_start += batch_size
            continue

        success = False
        for attempt in range(retries):
            try:
                features_batch = sp.audio_features(tracks=batch_ids)
                if features_batch:
                    audio_features_list.extend(features_batch)
                    success = True
                    break

            except spotipy.SpotifyException as e:
                if e.http_status == 429:  # Rate limit
                    wait_time = int(e.headers.get('Retry-After', retry_delay))
                    logging.warning(f"Rate limit exceeded. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Spotify API error: {str(e)}")
                    time.sleep(retry_delay)
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                time.sleep(retry_delay)

        if not success:
            audio_features_list.extend([None] * len(batch_ids))

        batch_start += batch_size

    return audio_features_list

# --- Process CSV files ---

def process_csv_files(sp, dataframes):
    """Process CSV files and add audio features"""
    for i, df in enumerate(dataframes):
        if 'spotify_track_uri' not in df.columns:
            logging.error(
                f"'spotify_track_uri' column is missing in file {file_paths[i]}. Cannot add audio features.")
            continue

        df['track_id'] = get_track_ids_from_uris(df['spotify_track_uri'])
        audio_features = fetch_audio_features(sp, df['track_id'].tolist())
        audio_features_df = pd.DataFrame(audio_features)
        df_with_audio_features = pd.concat([df, audio_features_df], axis=1)

        output_file_path = f'processed_data/spotify_history_part_{i+1}_processed.csv'
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        df_with_audio_features.to_csv(output_file_path, index=False)
        logging.info(f"Data saved to {output_file_path}")

def merge_processed_files():
    """Merge all processed CSV files into one combined dataset"""
    processed_files = [f for f in os.listdir('processed_data') if f.endswith('_processed.csv')]
    dfs = []

    for file in processed_files:
        df = pd.read_csv(f'processed_data/{file}', low_memory=False)
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_csv('processed_data/spotify_history_combined.csv', index=False)
    logging.info("Merged dataset saved to processed_data/spotify_history_combined.csv")

# --- Main Execution ---

def main():
    try:
        # Create processed_data directory if it doesn't exist
        os.makedirs('processed_data', exist_ok=True)

        # Load CSV files first
        logging.info("Loading CSV files...")
        dataframes = load_csv_files(file_paths)
        if not dataframes:
            logging.error("No data files were loaded successfully.")
            return

        # Authenticate only if we have data to process
        logging.info("Authenticating with Spotify...")
        sp = authenticate_spotify()

        # Process data
        logging.info("Processing CSV files...")
        process_csv_files(sp, dataframes)

        logging.info("Merging processed files...")
        merge_processed_files()

        logging.info("Processing completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
