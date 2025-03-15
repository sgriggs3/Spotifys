# Spotifys

## Setting up the Environment in GitHub Codespaces

1. **Open the repository in GitHub Codespaces:**
   - Navigate to your repository on GitHub.
   - Click on the `Code` button and select `Open with Codespaces`.
   - If you don't have a Codespace already, create a new one.

2. **Configure the Dev Container:**
   - The repository includes a `.devcontainer/devcontainer.json` file that sets up the development environment.
   - This file specifies the necessary Python libraries and extensions for VS Code.

3. **Set Environment Variables:**
   - The Spotify API credentials (client ID and redirect URI) are stored as environment variables.
   - You can set these environment variables in GitHub Codespaces using the `.devcontainer/devcontainer.json` file or by using GitHub secrets.

4. **Install Dependencies:**
   - The `postCreateCommand` in the `devcontainer.json` file ensures that all necessary Python libraries are installed using the `requirements.txt` file.

## Running the Code

1. **Open the `Spotify.py` file:**
   - This file contains the main code for fetching audio features from Spotify.

2. **Run the Script:**
   - You can run the script using the integrated terminal in VS Code.
   - Use the debug configurations provided in the `.vscode/launch.json` file for easy debugging and running the script.

3. **Process the CSV Files:**
   - The code is designed to process multiple CSV files (e.g., `spotify_history_part_1.csv`, `spotify_history_part_2.csv`, etc.).
   - It extracts track IDs from the `spotify_track_uri` column and fetches audio features using the `spotipy` library.
   - The processed data is saved to new CSV files in the `processed_data` directory.

## Additional Information

- **Code Formatting:**
  - The code is formatted according to PEP 8 standards using the `black` formatter.
  - Recommended VS Code settings for Python development are included in the `.vscode/settings.json` file.

- **Error Handling and Logging:**
  - The code includes improved error handling and logging using the `logging` module.
  - Comments are added to explain the purpose of different code sections and variables.

- **Refactoring:**
  - The code is refactored into smaller, more manageable functions for better readability and maintainability.
  - Functions include loading CSV files, authenticating with Spotify, processing a single CSV file, and saving the processed data.

- **Performance Optimization:**
  - The code is optimized for performance where possible, using efficient data structures and algorithms.
  - It handles potential issues such as missing data, invalid track URIs, and Spotify API errors gracefully.

- **Authorization Flow:**
  - The manual URL handling for the authorization code flow is removed.
  - The code uses `SpotifyOAuth` with the PKCE flow for authentication.

## Setting up Spotify Developer Credentials

To use the Spotify API, you need to set up Spotify developer credentials. Follow these steps:

1. **Create a Spotify Developer Account:**
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).
   - Log in with your Spotify account or create a new one if you don't have an account.

2. **Create a New Application:**
   - Click on the "Create an App" button.
   - Fill in the required details such as the app name and description.
   - Click on the "Create" button.

3. **Obtain Client ID and Client Secret:**
   - After creating the application, you will be redirected to the app's dashboard.
   - You will find the `Client ID` and `Client Secret` on this page. Copy these values.

4. **Set Redirect URI:**
   - In the app's dashboard, click on the "Edit Settings" button.
   - In the "Redirect URIs" section, add the following URI: `http://127.0.0.1:9090/callback`.
   - Click on the "Save" button.

5. **Update the `.env` File:**
   - Open the `.env` file in the repository.
   - Replace the placeholders with your actual `Client ID`, `Client Secret`, and `Redirect URI` values:
     ```
     SPOTIPY_CLIENT_ID=your_client_id
     SPOTIPY_CLIENT_SECRET=your_client_secret
     SPOTIPY_REDIRECT_URI=http://127.0.0.1:9090/callback
     ```

6. **Configure Environment Variables in GitHub Codespaces:**
   - Open the `.devcontainer/devcontainer.json` file.
   - Ensure that the environment variables are correctly referenced:
     ```json
     "remoteEnv": {
         "SPOTIPY_CLIENT_ID": "${localEnv:SPOTIPY_CLIENT_ID}",
         "SPOTIPY_CLIENT_SECRET": "${localEnv:SPOTIPY_CLIENT_SECRET}",
         "SPOTIPY_REDIRECT_URI": "${localEnv:SPOTIPY_REDIRECT_URI}"
     }
     ```

By following these steps, you will have successfully set up Spotify developer credentials and configured the environment to use the Spotify API.
