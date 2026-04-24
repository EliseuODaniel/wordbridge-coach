FROM python:3.11-slim

ARG INSTALL_ARGOS=false

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-argos.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_ARGOS" = "true" ]; then \
        pip install --no-cache-dir -r requirements-argos.txt; \
    fi

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
