# Docker Deployment Guide

Django S3 Document Service - Docker deployment configuration for AWS EC2 with Cloudflare DNS, API Gateway, ALB, and NGINX.

## Architecture

```
Cloudflare DNS → API Gateway → ALB → EC2 (NGINX) → Docker (Django App)
```

## Prerequisites

- Docker and Docker Compose installed on EC2 instance
- AWS credentials configured
- Keycloak authentication server
- MongoDB instance (external FastAPI app)
- `.env` file configured

## Quick Start

### 1. Build and Run

```bash
# Build and start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Build Only Django App (without NGINX)

```bash
docker-compose up -d django-s3-app
```

### 3. Production Build

```bash
# Build with production settings
docker build -t django-s3-document-service:latest .

# Run container
docker run -d \
  --name django-s3-app \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  django-s3-document-service:latest
```

## Configuration

### Environment Variables

Configure these in your `.env` file:

```env
# API Configuration
API_PREFIX=api/v1/

# Django Settings
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_ROLE_ARN=arn:aws:iam::account:role/RoleName
AWS_S3_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1

# Keycloak
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=your-realm
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret

# MongoDB FastAPI App
FASTAPI_APP_BASE_URL=http://fastapi-app:8080

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.com
```

### Changing API Prefix

The API prefix can be configured via environment variable:

```env
# Default: api/v1/
API_PREFIX=api/v2/

# Or custom path
API_PREFIX=documents/api/v1/
```

All endpoints will be available under the configured prefix:
- Health: `http://localhost:8000/${API_PREFIX}health/`
- Upload: `http://localhost:8000/${API_PREFIX}presigned-upload/`

## Health Check

Health check endpoint is available at:
```
GET /{API_PREFIX}health/
```

Response:
```json
{
  "status": "healthy"
}
```

### Docker Health Check

The container includes built-in health checks:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/${API_PREFIX}health/').read()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### ALB Health Check Configuration

Configure your AWS Application Load Balancer:

- **Health Check Path**: `/${API_PREFIX}health/` (e.g., `/api/v1/health/`)
- **Health Check Protocol**: HTTP
- **Health Check Port**: 8000 (or 80 if using NGINX)
- **Healthy Threshold**: 2
- **Unhealthy Threshold**: 3
- **Timeout**: 5 seconds
- **Interval**: 30 seconds
- **Success Codes**: 200

## NGINX Configuration

### With Docker Compose

NGINX is included in `docker-compose.yml` as a reverse proxy:

```bash
# Start with NGINX
docker-compose up -d

# NGINX will be available on port 80
curl http://localhost/api/v1/health/
```

### External NGINX (on EC2)

If you're using NGINX directly on EC2 (not in Docker):

```nginx
upstream django_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /health/ {
        proxy_pass http://django_backend;
    }

    location / {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## AWS EC2 Deployment

### 1. Prepare EC2 Instance

```bash
# Update system
sudo yum update -y  # Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Docker
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd django_s3_app

# Create .env file
vi .env
# Add your environment variables

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f django-s3-app
```

### 3. Configure Security Groups

Allow inbound traffic:
- Port 80 (HTTP) from ALB
- Port 443 (HTTPS) from ALB
- Port 8000 (Django) from ALB only

### 4. Configure ALB Target Group

- **Target Type**: Instance
- **Protocol**: HTTP
- **Port**: 80 (NGINX) or 8000 (direct Django)
- **Health Check Path**: `/api/v1/health/`

## Logging

Logs are stored in:
- Container logs: `docker-compose logs`
- Application logs: `./logs/` directory
- NGINX logs: `/var/log/nginx/` (inside NGINX container)

View logs:
```bash
# All services
docker-compose logs -f

# Django app only
docker-compose logs -f django-s3-app

# NGINX only
docker-compose logs -f nginx
```

## Monitoring

### Container Health

```bash
# Check container status
docker ps

# Check health status
docker inspect --format='{{.State.Health.Status}}' django-s3-document-service
```

### Application Metrics

```bash
# CPU and memory usage
docker stats

# Detailed container info
docker inspect django-s3-document-service
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs django-s3-app

# Check environment variables
docker-compose exec django-s3-app env

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### Health Check Failing

```bash
# Test health endpoint
docker-compose exec django-s3-app curl http://localhost:8000/api/v1/health/

# Check application logs
docker-compose exec django-s3-app tail -f /app/logs/django_s3_app.log
```

### Permission Issues

```bash
# Fix log directory permissions
sudo chown -R 1000:1000 logs/
sudo chmod -R 755 logs/
```

## Scaling

### Horizontal Scaling

```bash
# Scale Django app to 3 instances
docker-compose up -d --scale django-s3-app=3
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  django-s3-app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup

```bash
# Backup environment file
cp .env .env.backup

# Export logs
docker-compose logs > logs_backup_$(date +%Y%m%d).txt
```

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use secrets management** - AWS Secrets Manager or Parameter Store
3. **Enable SSL/TLS** - Use Cloudflare or ACM certificates
4. **Limit container capabilities** - Run as non-root user (already configured)
5. **Keep images updated** - Regularly rebuild with latest base images
6. **Network isolation** - Use Docker networks for service communication

## Support

For issues or questions, check:
- Application logs: `docker-compose logs`
- Health endpoint: `curl http://localhost:8000/api/v1/health/`
- Container status: `docker ps`
