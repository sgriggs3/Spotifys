import os
import sys
import spotipy
from spotipy.exceptions import SpotifyException
import pandas as pd
import time
import logging
import socket
import subprocess
import platform
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spotify_api.log'),
        logging.StreamHandler()
    ]
)

class SpotifyAudioFeaturesError(Exception):
    """Custom exception for audio features processing errors"""
    pass

class RateLimitException(Exception):
    """Custom exception for rate limit errors"""
    def __init__(self, wait_time: int):
        self.wait_time = wait_time
        super().__init__(f"Rate limit exceeded. Wait time: {wait_time}s")

class AudioFeatureValidator:
    """Validates audio feature responses"""
    
    REQUIRED_FEATURES = {
        'danceability', 'energy', 'key', 'loudness', 'mode',
        'speechiness', 'acousticness', 'instrumentalness',
        'liveness', 'valence', 'tempo', 'duration_ms'
    }
    
    @staticmethod
    def validate_features(features: Dict[str, Any]) -> bool:
        """Validate audio features response"""
        if not features:
            return False
            
        return all(
            feature in features and features[feature] is not None
            for feature in AudioFeatureValidator.REQUIRED_FEATURES
        )

class SpotifyAudioFeatures:
    """Handles Spotify audio features processing with improved error handling and efficiency"""
    
    def __init__(self, sp: spotipy.Spotify, batch_size: int = 50):
        self.sp = sp
        self.retry_delay = 5
        self.max_retries = 3
        self.batch_size = min(batch_size, 100)  # Spotify API limit is 100
        self.validator = AudioFeatureValidator()
        
    def get_track_ids_from_uris(self, track_uris: List[str]) -> List[Optional[str]]:
        """Extract track IDs from Spotify URIs with validation"""
        track_ids = []
        for uri in track_uris:
            try:
                if pd.isna(uri):
                    track_ids.append(None)
                    continue
                    
                # Handle both URI and ID formats
                if uri.startswith('spotify:track:'):
                    track_id = uri.split(':')[-1]
                else:
                    track_id = uri
                    
                # Validate track ID format
                if not isinstance(track_id, str) or len(track_id) != 22:
                    logging.warning(f"Invalid track ID format: {track_id}")
                    track_ids.append(None)
                else:
                    track_ids.append(track_id)
                    
            except (AttributeError, IndexError) as e:
                logging.warning(f"Could not extract track ID from URI: {uri} - {str(e)}")
                track_ids.append(None)
                
        return track_ids

    def fetch_audio_features(
        self,
        track_ids: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Fetch audio features for tracks
        
        Args:
            track_ids: List of Spotify track IDs
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of audio features dictionaries or None for failed requests
        """
        audio_features_list = []
        batch_start = 0
        total_tracks = len(track_ids)
        
        while batch_start < total_tracks:
            # Get valid track IDs for current batch
            batch_ids = [id for id in track_ids[batch_start:batch_start + self.batch_size] if id]
            
            if not batch_ids:
                batch_start += self.batch_size
                continue
                
            features_batch = None
            success = False
            retry_count = 0
            
            while not success and retry_count < self.max_retries:
                try:
                    features_batch = self.sp.audio_features(batch_ids)
                    
                    # Validate features
                    if features_batch and all(
                        not f or self.validator.validate_features(f)
                        for f in features_batch
                    ):
                        success = True
                    else:
                        raise SpotifyAudioFeaturesError("Invalid audio features response")
                        
                except SpotifyException as e:
                    if e.http_status == 429:  # Rate limit
                        wait_time = int(e.headers.get('Retry-After', self.retry_delay))
                        logging.warning(f"Rate limit exceeded. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        retry_count += 1
                        if retry_count == self.max_retries:
                            logging.error(f"Spotify API error: {str(e)}")
                            raise SpotifyAudioFeaturesError(f"Failed to fetch audio features: {str(e)}")
                        time.sleep(self.retry_delay * retry_count)
                        
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.max_retries:
                        logging.error(f"Unexpected error: {str(e)}")
                        raise SpotifyAudioFeaturesError(f"Unexpected error: {str(e)}")
                    time.sleep(self.retry_delay * retry_count)
            
            # Add results or None for failed batch
            if success and features_batch:
                audio_features_list.extend(features_batch)
            else:
                audio_features_list.extend([None] * len(batch_ids))
            
            # Update progress
            if progress_callback:
                progress = min((batch_start + self.batch_size) / total_tracks * 100, 100)
                progress_callback(progress)
                
            batch_start += self.batch_size
            
        return audio_features_list

    def process_dataframe(
        self,
        df: pd.DataFrame,
        output_path: str,
        chunk_size: Optional[int] = None
    ) -> None:
