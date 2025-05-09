# LOT Radio Alerts

A tool that compares artists playing on The LOT Radio with your Spotify top artists and sends alerts when there's a match.

## Features

- Scrapes The LOT Radio website for upcoming shows
- Matches artists with your Spotify listening history
- Sends email alerts when artists you like are playing
- Runs automatically on a schedule in the cloud

## Setup

### Prerequisites

- Docker and Docker Compose
- Spotify Developer Account (for API access)
- Email account for sending alerts

### Configuration

1. Create a Spotify Developer application at https://developer.spotify.com/dashboard/
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```
3. Edit `.env` with your Spotify API credentials and email settings
   - For Gmail, you'll need to create an App Password (not your regular password)

### Running Locally

To run the scraper once locally:

```bash
python lotradioscraper.py
```

To update your Spotify top artists:

```bash
python spotify-stats.py
```

### Docker Deployment

Build and run the Docker container:

```bash
docker-compose up -d
```

This will:
- Update your Spotify stats every 2 weeks on Sunday at 1am
- Check LOT Radio once a week on Monday at 10am
- Send email alerts when artists match

## Cloud Deployment Options

### AWS ECS (Elastic Container Service)

1. Create a repository in ECR (Elastic Container Registry)
2. Build and push your Docker image
3. Create an ECS Task Definition with your image
4. Set up an ECS Service with your task
5. Configure environment variables in the task definition

### Digital Ocean

1. Create a new Droplet
2. Install Docker and Docker Compose
3. Clone this repo and follow the Docker setup steps

### Google Cloud Run

1. Build and push your Docker image to Google Container Registry
2. Deploy as a Cloud Run service with the appropriate environment variables

## Troubleshooting

Check the logs for any issues:

```bash
docker-compose logs
```

Logs are also stored in the `./logs` directory.

## License

MIT