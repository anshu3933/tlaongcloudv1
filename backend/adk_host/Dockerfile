FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY adk_host/src /app/adk_host/src
COPY common/src /app/common/src

# Set Python path to include the src directory
ENV PYTHONPATH=/app

# Run the server
CMD ["uvicorn", "adk_host.src.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"] 