import pandas as pd
import logging
from Spotify import authenticate_spotify, process_csv_files

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_pipeline.log')
    ]
)

def create_test_csv():
    """Create a small test CSV with known track URIs"""
    test_data = {
        'spotify_track_uri': [
            'spotify:track:3z8h0TU7ReDPLIbEnYhWZb',  # Bohemian Rhapsody
            'spotify:track:4cOdK2wGLETKBW3PvgPWqT',  # Never Gonna Give You Up
            'spotify:track:4gphxUgq0JSFv2BCLhNDiE'   # Smells Like Teen Spirit
        ],
        'timestamp': [
            '2024-03-15 10:00:00',
            '2024-03-15 10:05:00',
            '2024-03-15 10:10:00'
        ]
    }
    
    df = pd.DataFrame(test_data)
    df.to_csv('test_spotify_history.csv', index=False)
    return df

def test_pipeline():
    """Test the full pipeline with MCP integration"""
    try:
        # Create test data
        logging.info("Creating test data...")
        create_test_csv()
        
        # Authenticate with Spotify
        logging.info("Authenticating with Spotify...")
        sp = authenticate_spotify()
        
        # Process the test file
        logging.info("Processing test file with MCP...")
        test_df = pd.read_csv('test_spotify_history.csv')
        process_csv_files(sp, [test_df], use_mcp=True)
        
        # Verify results
        logging.info("Verifying results...")
        result_df = pd.read_csv('processed_data/spotify_history_part_1_processed.csv')
        
        # Check if audio features were fetched
        required_features = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness',
            'liveness', 'valence', 'tempo'
        ]
        
        missing_features = [feat for feat in required_features if feat not in result_df.columns]
        if missing_features:
            logging.error(f"Missing audio features: {missing_features}")
        else:
            logging.info("All required audio features present in results")
            
        # Display sample results
        logging.info("\nSample results:")
        logging.info(result_df[['spotify_track_uri'] + required_features].to_string())
        
    except Exception as e:
        logging.error(f"Pipeline test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_pipeline()