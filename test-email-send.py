import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))
sender = os.getenv('EMAIL_SENDER')
password = os.getenv('EMAIL_PASSWORD')

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    print("Login successful!")
    server.quit()
except Exception as e:
    print(f"Error: {e}")