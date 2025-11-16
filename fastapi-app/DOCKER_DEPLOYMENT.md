# Docker Deployment Guide

This guide covers deploying the FastAPI Order Management application on AWS EC2 using Docker and GitLab CI/CD.

## Architecture Overview

```
Cloudflare Proxy
       |
    Nginx (Reverse Proxy on EC2)
       |
    ├─ Port 8000 → DocHandler
    ├─ Port 8001 → FastAPI Order Management (This service)
    ├─ Port 8002 → DynamicForm Backend
    └─ Port 3000 → DynamicForm Frontend
```

## Prerequisites

1. AWS EC2 instance with Docker and Docker Compose installed
2. GitLab repository with CI/CD enabled
3. MongoDB instance (can be on EC2, MongoDB Atlas, or separate server)
4. Nginx configured as reverse proxy
5. Cloudflare proxy configured

## Files Created

- `Dockerfile` - Multi-stage build for optimized production image
- `docker-compose.yml` - Docker Compose configuration with environment variables
- `.env.production` - Production environment template
- `.dockerignore` - Files to exclude from Docker build

## Environment Variables Setup

### Required Variables (Set in GitLab CI/CD > Settings > CI/CD > Variables)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `MONGODB_URL` | Protected | MongoDB connection string | `mongodb://user:pass@host:27017` |
| `DATABASE_NAME` | Variable | Database name | `CP_OrderManagement` |
| `CORS_ORIGINS` | Variable | Allowed CORS origins | `["https://drapps.dev"]` |
| `API_PREFIX` | Variable | API path prefix | `/api/v1` (dev) or `` (prod) |

### Optional Variables (with defaults)

- `APP_NAME` - Application name (default: "dCent CP Order Management API")
- `APP_VERSION` - Application version (default: "1.0.0")
- `ENVIRONMENT` - Environment name (default: "production")
- `DEBUG` - Debug mode (default: "false")
- `LOG_LEVEL` - Logging level (default: "INFO")
- `MIN_POOL_SIZE` - MongoDB min pool size (default: "10")
- `MAX_POOL_SIZE` - MongoDB max pool size (default: "100")

## Local Testing

### 1. Create a `.env` file

```bash
cp .env.production .env
# Edit .env with your local values
```

### 2. Build and run

```bash
# Build the image
docker build -t fastapi-order-management:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:8001/health
```

### 3. Stop and clean up

```bash
docker-compose down
docker-compose down -v  # Remove volumes too
```

## AWS EC2 Deployment

### 1. EC2 Instance Setup

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### 2. Deploy Application

Your GitLab CI/CD pipeline will handle deployment. The pipeline should:

1. Build the Docker image
2. Push image to container registry (optional)
3. SSH into EC2
4. Pull latest code/image
5. Create `.env` file from GitLab variables
6. Run `docker-compose up -d`

### 3. Nginx Configuration

Create Nginx configuration for reverse proxy:

```nginx
# /etc/nginx/sites-available/drapps.dev

upstream fastapi_order_management {
    server localhost:8001;
}

upstream dochandler {
    server localhost:8000;
}

upstream dynamicform_backend {
    server localhost:8002;
}

upstream dynamicform_frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name drapps.dev www.drapps.dev;

    # Increase timeouts for long-running requests
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    # Order Management API (no /api/v1 prefix as it's handled by API Gateway)
    # Note: Set API_PREFIX="" in production .env to remove the prefix
    location /order-req {
        proxy_pass http://fastapi_order_management/order-req;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /order-proposal {
        proxy_pass http://fastapi_order_management/order-proposal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Order Management Health Check
    location /health {
        proxy_pass http://fastapi_order_management/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # DocHandler
    location /dochandler {
        proxy_pass http://dochandler;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # DynamicForm Backend
    location /api/forms {
        proxy_pass http://dynamicform_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # DynamicForm Frontend
    location / {
        proxy_pass http://dynamicform_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/drapps.dev /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## GitLab CI/CD Integration

Your `.gitlab-ci.yml` should include a deploy stage. Example integration:

```yaml
deploy:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
    - ssh-keyscan $EC2_HOST >> ~/.ssh/known_hosts
  script:
    # SSH into EC2 and deploy
    - ssh $EC2_USER@$EC2_HOST "
        cd /home/$EC2_USER/fastapi-app &&
        git pull origin main &&

        # Create .env file from GitLab variables
        cat > .env << EOF
        APP_NAME=${APP_NAME}
        APP_VERSION=${APP_VERSION}
        ENVIRONMENT=${ENVIRONMENT}
        DEBUG=${DEBUG}
        HOST=${HOST}
        PORT=${PORT}
        HOST_PORT=${HOST_PORT}
        MONGODB_URL=${MONGODB_URL}
        DATABASE_NAME=${DATABASE_NAME}
        SECRET_KEY=${SECRET_KEY}
        CORS_ORIGINS=${CORS_ORIGINS}
        API_DOMAIN=${API_DOMAIN}
        API_BASE_URL=${API_BASE_URL}
        LOG_LEVEL=${LOG_LEVEL}
        EOF

        # Deploy with docker-compose
        docker-compose down &&
        docker-compose up -d --build &&
        docker-compose logs --tail=50
      "
  only:
    - main
```

## Health Checks

The application includes health check endpoints:

```bash
# Application health
curl http://localhost:8001/health

# API info
curl http://localhost:8001/

# API documentation
curl http://localhost:8001/docs
```

## Monitoring and Logs

### View logs

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f fastapi-app
```

### Monitor resources

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Check environment variables
docker-compose config

# Recreate container
docker-compose down -v
docker-compose up -d
```

### Connection refused

1. Check if container is running: `docker ps`
2. Check port mapping: `docker port fastapi-order-management`
3. Check firewall rules on EC2 security group
4. Check Nginx configuration: `sudo nginx -t`

### Database connection issues

1. Verify MONGODB_URL is correct
2. Check MongoDB is accessible from EC2
3. Verify security groups allow MongoDB port (27017)
4. Test connection: `docker-compose exec fastapi-app curl -v $MONGODB_URL`

## Security Best Practices

1. **Never commit `.env` files** - Use GitLab CI/CD variables
2. **Use Protected Variables** - For sensitive data like SECRET_KEY and MONGODB_URL
3. **Keep images updated** - Regularly rebuild with latest base images
4. **Limit container resources** - Set memory and CPU limits in docker-compose.yml
5. **Use non-root user** - Already configured in Dockerfile
6. **Enable HTTPS** - Configure SSL/TLS with Cloudflare and Nginx
7. **Rotate secrets regularly** - Update SECRET_KEY periodically
8. **Monitor logs** - Set up log aggregation and monitoring

## Scaling

### Horizontal Scaling

To run multiple instances:

```yaml
services:
  fastapi-app:
    # ... existing config ...
    deploy:
      replicas: 3  # Run 3 instances
```

Update Nginx to load balance:

```nginx
upstream fastapi_order_management {
    least_conn;
    server localhost:8001;
    server localhost:8011;
    server localhost:8021;
}
```

### Vertical Scaling

Adjust resource limits in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

## Backup and Recovery

### Backup MongoDB

```bash
# Create backup
docker exec mongodb mongodump --uri="$MONGODB_URL" --out=/backup

# Restore backup
docker exec mongodb mongorestore --uri="$MONGODB_URL" /backup
```

### Backup Application

```bash
# Backup entire application directory
tar -czf fastapi-app-backup-$(date +%Y%m%d).tar.gz /home/ubuntu/fastapi-app/
```

## Support

For issues or questions:
1. Check application logs: `docker-compose logs`
2. Verify environment variables: `docker-compose config`
3. Test endpoints: `curl http://localhost:8001/health`
4. Review GitLab CI/CD pipeline logs
