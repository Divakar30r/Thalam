# Dockerfile for Processor service

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared components first (for better layer caching)
COPY shared/ ./shared/

# Copy processor application
COPY processor/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p logs

# Expose ports (FastAPI + gRPC)
EXPOSE 8001 50051

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

# Run the application
CMD ["python", "main.py"]