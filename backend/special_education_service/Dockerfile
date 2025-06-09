FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy common package first
COPY backend/common /app/common

# Copy service code and requirements
COPY backend/special_education_service/requirements.txt .
COPY backend/special_education_service/src /app/src

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for GCP credentials
RUN mkdir -p /app/credentials

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]
