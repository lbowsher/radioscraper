import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def dump_html_content(radio_url, output_path):
    """
    Fetches HTML content from the radio URL and saves it to a file
    
    Args:
        radio_url (str): URL to fetch HTML from
        output_path (str): Path to save the HTML content to
    """
    # Get HTML content
    response = requests.get(radio_url)
    
    # Determine file extension
    ext = '.html' if output_path.endswith('.html') else '.txt'
    if not (output_path.endswith('.txt') or output_path.endswith('.html')):
        output_path = output_path + ext
        
    # Write content to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"HTML content saved to {output_path}")

def compare_artist_lists(csv_path, radio_url):
    # Read CSV file with Spotify artists
    spotify_df = pd.read_csv(csv_path)
    spotify_artists = set(spotify_df['name'].str.lower())

    # Setup Selenium
    driver = webdriver.Chrome()
    try:
        driver.get(radio_url)
        
        # Wait for calendar div to be present and visible
        wait = WebDriverWait(driver, 10)
        calendar = wait.until(EC.presence_of_element_located((By.ID, "calendar")))
        
        # Find both time and title elements in order
        all_elements = calendar.find_elements(By.CSS_SELECTOR, "td.fc-list-event-time, td.fc-list-event-title")
                
        time_info = None
        radio_titles_with_times = []
        radio_titles = set()
        
        for element in all_elements:
            class_name = element.get_attribute('class')
            if 'fc-list-event-time' in class_name:
                time_info = element.text.strip()
            elif 'fc-list-event-title' in class_name:
                artist_link = element.find_element(By.TAG_NAME, "a")
                artist_name = artist_link.text.strip().lower()
                if artist_name != "restream":
                    radio_titles.add(artist_name)
                    if time_info:
                        radio_titles_with_times.append((time_info, artist_name))
                    time_info = None
        
        # Compare the lists
        common_artists = set()
        for radio_title in radio_titles:
            for spotify_artist in spotify_artists:
                if spotify_artist in radio_title:
                    common_artists.add(radio_title)
                    break
        
        spotify_only = spotify_artists - common_artists
        radio_only = radio_titles - common_artists
        
        # Print results
        print(f"Artists in both lists: {len(common_artists)}")
        print("\nCommon artists:")
        for artist, time in radio_titles_with_times:
            if artist in common_artists:
                print(f"- {time}: {artist}")
            
        # print(f"\nArtists only in your Spotify list: {len(spotify_only)}")
        # print("\nSpotify-only artists:")
        # for artist in sorted(spotify_only):
        #     print(f"- {artist}")
            
        print(f"\nArtists only in radio list: {len(radio_only)}")
        print("\nRadio-only artists:")
        for artist in sorted(radio_only):
            print(f"- {artist}")
            
    finally:
        driver.quit()
# Usage
if __name__ == "__main__":
    csv_path = "spotify_top_artists_20250104.csv"
    radio_url = "https://www.thelotradio.com/"
    # dump_html_content(radio_url=radio_url, output_path="lotradio")
    compare_artist_lists(csv_path, radio_url)