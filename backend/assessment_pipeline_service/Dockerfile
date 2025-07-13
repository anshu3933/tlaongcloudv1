FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy common package first
COPY backend/common /app/common

# Copy the entire assessment_pipeline_service as a package
COPY backend/assessment_pipeline_service /app/assessment_pipeline_service
COPY backend/special_education_service /app/special_education_service

# Install dependencies
RUN pip install --no-cache-dir -r assessment_pipeline_service/requirements.txt && \
    pip install --no-cache-dir sqlalchemy==2.0.25 asyncpg==0.29.0 email-validator==2.1.0.post1 backoff==2.2.1 "numpy<2.0" httpx==0.26.0

# Create directory for GCP credentials
RUN mkdir -p /app/credentials

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# Run the service
CMD ["uvicorn", "assessment_pipeline_service.main:app", "--host", "0.0.0.0", "--port", "8006"]