FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install the small runtime surface used by the service and healthcheck.
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create audio cache directory
RUN mkdir -p /audio /models

# Create non-root user
RUN useradd --create-home --shell /bin/bash tts \
    && chown -R tts:tts /app /audio /models
USER tts

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", 8001"]
