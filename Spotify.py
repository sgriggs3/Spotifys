import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
import logging
from dotenv import load_dotenv
from spotify_mcp_client import SpotifyMCPClient

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


def authenticate_spotify():
    """Authenticate with Spotify API using environment variables"""
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.environ.get(
        'SPOTIPY_REDIRECT_URI', 'http://localhost:8080')

    # Ensure necessary environment variables are set
    if not all([client_id, client_secret]):
        raise ValueError(
            "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables must be set.")

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-recently-played user-library-read streaming user-top-read user-library-modify user-read-email",
        show_dialog=True,
        cache_path=".cache"
    )

    return spotipy.Spotify(auth_manager=auth_manager)

# --- Test Authentication and API ---


def test_spotify_connection(sp):
    """Test Spotify connection and API functionality"""
    try:
        # Test 1: Get user profile
        user = sp.current_user()
        logging.info(f"Successfully connected as user: {user['display_name']}")

        # Test 2: Get audio features for a known track (Bohemian Rhapsody)
        track_id = '3z8h0TU7ReDPLIbEnYhWZb'
        features = sp.audio_features([track_id])[0]
        logging.info("Successfully fetched audio features:")
        for key, value in features.items():
            logging.info(f"{key}: {value}")

        return True
    except Exception as e:
        logging.error(f"Error testing Spotify connection: {str(e)}")
        return False

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


def fetch_audio_features(sp, track_ids, batch_size=50, retries=3, retry_delay=5, use_mcp=True):
    """Fetch audio features for track IDs with optional MCP support"""
    if use_mcp:
        try:
            mcp_client = SpotifyMCPClient(batch_size=batch_size)
            return mcp_client.get_audio_features(track_ids)
        except Exception as e:
            logging.error(f"MCP fetch failed, falling back to traditional method: {str(e)}")
            # Fall back to traditional method if MCP fails
            return fetch_audio_features(sp, track_ids, batch_size, retries, retry_delay, use_mcp=False)
    
    # Traditional spotipy method
    audio_features_list = []
    batch_start = 0

    while batch_start < len(track_ids):
        batch_ids = [
            id for id in track_ids[batch_start:batch_start + batch_size] if id]
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
                    logging.warning(
                        f"Rate limit exceeded. Waiting {wait_time}s...")
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


def process_csv_files(sp, dataframes, use_mcp=True):
    """Process CSV files and add audio features with optional MCP support"""
    for i, df in enumerate(dataframes):
        if 'spotify_track_uri' not in df.columns:
            logging.error(
                f"'spotify_track_uri' column is missing in file {file_paths[i]}. Cannot add audio features.")
            continue

        df['track_id'] = get_track_ids_from_uris(df['spotify_track_uri'])
        audio_features = fetch_audio_features(sp, df['track_id'].tolist(), use_mcp=use_mcp)
        audio_features_df = pd.DataFrame(audio_features)
        df_with_audio_features = pd.concat([df, audio_features_df], axis=1)

        output_file_path = f'processed_data/spotify_history_part_{i+1}_processed.csv'
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        df_with_audio_features.to_csv(output_file_path, index=False)
        logging.info(f"Data saved to {output_file_path}")


def merge_processed_files():
    """Merge all processed CSV files into one combined dataset"""
    processed_files = [f for f in os.listdir(
        'processed_data') if f.endswith('_processed.csv')]
    dfs = []

    for file in processed_files:
        df = pd.read_csv(f'processed_data/{file}', low_memory=False)
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_csv(
        'processed_data/spotify_history_combined.csv', index=False)
    logging.info(
        "Merged dataset saved to processed_data/spotify_history_combined.csv")

# --- Main Execution ---


def main():
    try:
        # Authenticate with Spotify
        logging.info("Authenticating with Spotify...")
        sp = authenticate_spotify()

        # Test the connection and API functionality
        logging.info("Testing Spotify connection and API functionality...")
        if not test_spotify_connection(sp):
            logging.error("Failed to verify Spotify connection")
            return

        # If testing is successful, proceed with data processing
        logging.info(
            "Connection test successful, proceeding with data processing...")

        # Create processed_data directory if it doesn't exist
        os.makedirs('processed_data', exist_ok=True)

        # Load CSV files
        logging.info("Loading CSV files...")
        dataframes = load_csv_files(file_paths)
        if not dataframes:
            logging.error("No data files were loaded successfully.")
            return

        # Process data using MCP by default
        logging.info("Processing CSV files...")
        process_csv_files(sp, dataframes, use_mcp=True)

        logging.info("Merging processed files...")
        merge_processed_files()

        logging.info("Processing completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
