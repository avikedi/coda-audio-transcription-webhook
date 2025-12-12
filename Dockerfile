FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create temp directory for audio files
RUN mkdir -p /tmp/audio

# Create empty static directory and collect static files
RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run the application with gunicorn
# Use shell form to allow PORT variable expansion
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 transcription_service.wsgi:application
