import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

def setup_spotify_client():
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET') 
    REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'https://localhost:8888/callback')  # Use default if not set
    
    # Define the scope - we need listening history access
    SCOPE = 'user-read-recently-played user-top-read'
    
    # Create the Spotify client
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))
    return sp

def get_top_artists(sp, num_artists=50, time_range='medium_term'):
    """
    Get user's top artists
    time_range options: short_term (4 weeks), medium_term (6 months), long_term (all time)
    """
    limit = 50
    offset = 0
    artists = []

    while offset < num_artists:
        results = sp.current_user_top_artists(limit=limit, offset=offset, time_range=time_range)

        # If no more results, break
        if not results['items']:
            break

        for item in results['items']:
            artist_info = {
                'name': item['name'],
                'genres': ', '.join(item['genres']),
                'popularity': item['popularity'],
                'time_range': time_range,
                'extracted_at': datetime.now().isoformat()
            }
            artists.append(artist_info)
        offset += limit
    
    return artists

def main():
    try:
        # Setup the client
        sp = setup_spotify_client()
        
        # Get top artists for different time ranges
        # time_ranges = ['short_term', 'medium_term', 'long_term']
        time_ranges = ['medium_term']
        max_artists = 300
        all_artists = []
        
        for time_range in time_ranges:
            artists = get_top_artists(sp, num_artists=max_artists, time_range=time_range)
            all_artists.extend(artists)
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(all_artists)
        filename = f'spotify_top_artists_{datetime.now().strftime("%Y%m%d")}.csv'
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()