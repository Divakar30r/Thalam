    # Multi-stage build for Django S3 Document Service
    FROM python:3.12-slim as builder

    # Set environment variables
    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PIP_NO_CACHE_DIR=1 \
        PIP_DISABLE_PIP_VERSION_CHECK=1

    # Install system dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        && rm -rf /var/lib/apt/lists/*

    # Create application directory
    WORKDIR /app

    # Copy requirements and install Python dependencies
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Final stage
    FROM python:3.12-slim

    # Set environment variables
    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1

    # Create non-root user
    RUN groupadd -r django && useradd -r -g django django

    # Create application directory
    WORKDIR /app

    # Copy Python packages from builder
    COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
    COPY --from=builder /usr/local/bin /usr/local/bin

    # Copy application code
    COPY . .

    # Create necessary directories and set permissions
    RUN mkdir -p /app/staticfiles /app/media /app/logs && \
        chown -R django:django /app

    # Switch to non-root user
    USER django

    # Expose port
    EXPOSE 8000

    # Health check
    HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
        CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/${API_PREFIX:-api/v1/}health/').read()" || exit 1

    # Run gunicorn
    CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "django_s3_app.wsgi:application"]
