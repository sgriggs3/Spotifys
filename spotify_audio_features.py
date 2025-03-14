import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import csv
import time
import os

def get_track_features(track_ids, client_id, client_secret):
    """
    Fetches audio features for a list of Spotify tracks and writes them to a CSV file.

    Args:
        track_ids (list): A list of Spotify track IDs.
        client_id (str): The Spotify API client ID.
        client_secret (str): The Spotify API client secret.
    """

    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # CSV file setup
        csv_file = open('spotify_track_features.csv', 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)

        # Write header row
        header = ['track_id', 'track_name', 'artist_name']
        # Get audio features for the first track to determine the feature names
        first_track_features = sp.audio_features([track_ids[0]])[0] if track_ids else None
        if first_track_features:
            header.extend(first_track_features.keys())
        csv_writer.writerow(header)

        # Process each track
        for track_id in track_ids:
            try:
                track = sp.track(track_id)
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                features = sp.audio_features([track_id])[0]

                if features:
                    row = [track_id, track_name, artist_name]
                    for h in header[3:]:
                        row.append(features[h])
                    csv_writer.writerow(row)
                    print(f"Successfully fetched features for track ID: {track_id}")
                else:
                    print(f"Could not retrieve audio features for track ID: {track_id}")

            except spotipy.exceptions.SpotifyException as e:
                print(f"Error fetching track {track_id}: {e}")
                time.sleep(10)  # Rate limiting
            except Exception as e:
                print(f"An unexpected error occurred for track {track_id}: {e}")

        csv_file.close()
        print("Track features written to spotify_track_features.csv")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # Replace with your actual credentials and track IDs
    CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
    
    # Read track IDs from a text file (one track ID per line)
    try:
        with open('track_ids.txt', 'r') as f:
            track_ids = [line.strip() for line in f]
    except FileNotFoundError:
        print("Error: track_ids.txt not found. Please create a file with track IDs.")
        track_ids = []

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Please set the SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
    elif track_ids:
        get_track_features(track_ids, CLIENT_ID, CLIENT_SECRET)
    else:
        print("No track IDs to process.")