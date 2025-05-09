import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email_alert(subject, body):
    """
    Send an email alert with the matching artists information using AWS SES
    
    Args:
        subject (str): Email subject
        body (str): Email body with the match information
    """
    # Email configuration from environment variables
    sender_email = os.getenv('EMAIL_SENDER')  # Verified sender email address
    receiver_email = os.getenv('EMAIL_RECEIVER')
    smtp_username = os.getenv('SMTP_USERNAME')  # AWS SES SMTP username
    smtp_password = os.getenv('SMTP_PASSWORD')  # AWS SES SMTP password
    smtp_server = os.getenv('SMTP_SERVER', 'mail-smtp.us-east-2.amazonaws.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    # Validate AWS SES requirements
    if not all([sender_email, receiver_email, smtp_username, smtp_password, smtp_server]):
        print("Missing required AWS SES configuration. Please check your .env file.")
        return
    
    # Create message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    
    # Add body to email
    message.attach(MIMEText(body, 'plain'))
    
    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        # AWS SES SMTP authentication
        try:
            server.login(smtp_username, smtp_password)
        except smtplib.SMTPAuthenticationError:
            print("AWS SES Authentication failed. Please check your SMTP credentials.")
            print("Note: Make sure you're using SES SMTP credentials, not your AWS console password.")
            return
            
        server.send_message(message)
        server.quit()
        print("Email alert sent successfully via AWS SES")
    except Exception as e:
        print(f"Failed to send email via AWS SES: {e}")
        print("Common issues:")
        print("1. Verify sender email is confirmed in SES")
        print("2. If in sandbox mode, verify recipient email")
        print("3. Check if you're using the correct AWS region in SMTP server address")

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

def compare_artist_lists(csv_path, radio_url, send_alerts=True):
    # Read CSV file with Spotify artists
    spotify_df = pd.read_csv(csv_path)
    spotify_artists = set(spotify_df['name'].str.lower())

    # Set up headless Chrome/Chromium browser for containerized environments
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    
    # Use environment variable paths if available (for Docker)
    chrome_path = os.environ.get('CHROME_BIN')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    
    if chrome_path:
        options.binary_location = chrome_path
        
    # In newer Selenium versions, service object is used instead of executable_path
    from selenium.webdriver.chrome.service import Service
    
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    
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
        common_artists = {}  # Dictionary to store radio_title -> matching_spotify_artist
        for radio_title in radio_titles:
            for spotify_artist in spotify_artists:
                if spotify_artist in radio_title:
                    common_artists[radio_title] = spotify_artist
                    break
        
        spotify_only = spotify_artists - set(common_artists.values())
        radio_only = radio_titles - set(common_artists.keys())
        
        # Prepare the output
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        output = f"LOT Radio Artist Matches - {current_date}\n\n"
        output += f"Artists in both lists: {len(common_artists)}\n\n"
        output += "Common artists with schedule:\n"
        
        matches_schedule = []
        for time, artist in radio_titles_with_times:
            if artist in common_artists:
                spotify_match = common_artists[artist]
                matches_schedule.append(f"- {time}: {artist} (matched with Spotify artist: {spotify_match})")
                
        output += "\n".join(matches_schedule) + "\n"
            
        # Print results for local debugging
        print(output)
        
        # Send alert if matches found and alerts are enabled
        if common_artists and send_alerts:
            subject = f"LOT Radio Alert: {len(common_artists)} artists you like are playing!"
            send_email_alert(subject, output)
        elif send_alerts:
            print("No matching artists found, no alert sent")
            
        return common_artists, radio_titles_with_times
            
    finally:
        driver.quit()

# For standalone usage and testing
if __name__ == "__main__":
    # Get the most recent CSV file by date in the filename
    csv_files = [f for f in os.listdir('.') if f.startswith('spotify_top_artists_') and f.endswith('.csv')]
    if not csv_files:
        print("No Spotify artist CSV files found. Run spotify-stats.py first.")
        exit(1)
        
    # Sort by date in filename (format: spotify_top_artists_YYYYMMDD.csv)
    latest_csv = sorted(csv_files)[-1]
    print(f"Using latest Spotify data: {latest_csv}")
    
    radio_url = "https://www.thelotradio.com/"
    compare_artist_lists(latest_csv, radio_url, send_alerts=True)