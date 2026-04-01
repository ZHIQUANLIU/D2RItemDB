# Use official Python slim image for a small footprint
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONMENT production

# Set working directory
WORKDIR /app

# Install system dependencies (libmagic is required for python-magic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for persistent data if not exists
RUN mkdir -p static/uploads

# Expose the application port
EXPOSE 5000

# Start the application using Gunicorn
# --bind: listen on all interfaces at port 5000
# --workers: rule of thumb is 2 * (number of cores) + 1
# --access-logfile: log requests to stdout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "app:app"]
