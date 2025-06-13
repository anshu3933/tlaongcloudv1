# Multi-stage Docker build for Authentication Service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r authuser && useradd -r -g authuser authuser

WORKDIR /app

# Copy common package first (if needed)
COPY backend/common /app/common

# Copy service requirements and install dependencies
COPY backend/auth_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY backend/auth_service/src /app/src
COPY backend/auth_service/alembic.ini .
COPY backend/auth_service/scripts /app/scripts

# Change ownership to non-root user
RUN chown -R authuser:authuser /app

# Switch to non-root user
USER authuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Production command with multiple workers
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "4"]
