#!/usr/bin/env python3
"""
Scheduler for LOT Radio alerts
Runs as the main process in the container and manages the cron service
"""
import os
import time
import subprocess
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/scheduler.log')
    ]
)
logger = logging.getLogger('scheduler')

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs('/app/logs', exist_ok=True)
    logger.info("Directory structure verified")

def start_cron_service():
    """Start the cron service"""
    try:
        subprocess.run(['service', 'cron', 'start'], check=True)
        logger.info("Cron service started")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start cron service: {e}")
        return False

def check_aws_credentials():
    """Verify AWS credentials are working"""
    # Skip AWS credential check for local development
    if os.getenv('SKIP_AWS_CHECK', 'false').lower() == 'true':
        logger.info("Skipping AWS credentials check")
        return True
    
    try:
        sts = boto3.client('sts')
        sts.get_caller_identity()
        logger.info("AWS credentials verified")
        return True
    except Exception as e:
        logger.error(f"AWS credentials check failed: {e}")
        # Continue anyway for local development
        logger.warning("Continuing without AWS credentials")
        return True

def run_initial_checks():
    """Run initial checks to ensure everything is set up correctly"""
    # Check for environment variables
    required_vars = ['EMAIL_SENDER', 'EMAIL_RECEIVER', 'SMTP_USERNAME', 
                     'SMTP_PASSWORD', 'SMTP_SERVER', 'SMTP_PORT']
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    # Check AWS credentials
    if not check_aws_credentials():
        logger.warning("AWS credentials check failed")
        return False
    
    # Check for CSV files, run spotify-stats.py if needed
    csv_files = [f for f in os.listdir('.') if f.startswith('spotify_top_artists_') and f.endswith('.csv')]
    if not csv_files:
        logger.info("No Spotify artist CSV files found. Running spotify-stats.py...")
        try:
            subprocess.run(['python', 'spotify-stats.py'], check=True)
            logger.info("Successfully generated Spotify artist data")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run spotify-stats.py: {e}")
            return False
    
    logger.info("Initial checks completed successfully")
    return True

def main():
    """Main scheduler function"""
    logger.info("Starting LOT Radio Alerts scheduler")
    
    # Create necessary directories
    ensure_directories()
    
    # Run initial checks
    if not run_initial_checks():
        logger.error("Initial checks failed, continuing anyway but service may not work properly")
    
    # Start cron service
    if not start_cron_service():
        logger.error("Failed to start cron service")
        return
    
    # Keep the container running
    logger.info("Scheduler is running. Press Ctrl+C to exit.")
    try:
        while True:
            # Log a heartbeat every hour
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Scheduler heartbeat at {current_time}")
            time.sleep(3600)  # 1 hour
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    main()