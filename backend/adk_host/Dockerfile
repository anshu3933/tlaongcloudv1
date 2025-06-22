FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy common package first
COPY backend/common /app/common

# Copy shared requirements and service code
COPY backend/requirements.txt .
COPY backend/adk_host/src /app/adk_host/src

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir email-validator==2.1.0.post1

# Run the server
CMD ["uvicorn", "adk_host.src.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"] 