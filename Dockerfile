FROM python:3.11-slim

# Install Chromium and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chromium path for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml uv.lock ./

# Install pip and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY *.py ./
# Copy env example if available
COPY .env.example ./

# Set up cron for scheduling
RUN apt-get update && apt-get install -y cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add crontab file
COPY crontab /etc/cron.d/lotradio-cron
RUN chmod 0644 /etc/cron.d/lotradio-cron && \
    crontab /etc/cron.d/lotradio-cron

# Add health check script
COPY healthcheck.sh /app/
RUN chmod +x /app/healthcheck.sh

# Expose port for health checks
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Run script on container start
CMD ["python", "scheduler.py"]