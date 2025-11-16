# Docker Quick Reference Guide

## Essential Commands for Production

### Build and Deploy

```bash
# Build the Docker image
docker build -t fastapi-order-management:latest .

# Start services in detached mode
docker-compose up -d

# Start with rebuild (after code changes)
docker-compose up -d --build

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Monitoring

```bash
# View logs (real-time)
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs -f fastapi-app

# Check container status
docker ps

# Check resource usage
docker stats

# Inspect container
docker inspect fastapi-order-management
```

### Health Checks

```bash
# Check application health
curl http://localhost:8001/health

# Check API info
curl http://localhost:8001/

# Check from inside container
docker-compose exec fastapi-app curl http://localhost:8001/health
```

### Troubleshooting

```bash
# View environment variables
docker-compose config

# Execute command in running container
docker-compose exec fastapi-app bash

# Restart service
docker-compose restart

# Rebuild without cache
docker-compose build --no-cache

# Remove unused images
docker image prune -f

# Remove everything (containers, networks, images)
docker system prune -a
```

### Debugging

```bash
# Access container shell
docker-compose exec fastapi-app /bin/bash

# Check Python version
docker-compose exec fastapi-app python --version

# Check installed packages
docker-compose exec fastapi-app pip list

# Test MongoDB connection
docker-compose exec fastapi-app python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('$MONGODB_URL').admin.command('ping'))"
```

## Network Commands

```bash
# List networks
docker network ls

# Inspect network
docker network inspect dcent-network

# Check container network connectivity
docker-compose exec fastapi-app ping dochandler
docker-compose exec fastapi-app ping dynamicform-backend
```

## Production Deployment Flow

```bash
# 1. Pull latest code
git pull origin main

# 2. Update .env if needed
nano .env

# 3. Stop existing containers
docker-compose down

# 4. Build and start new containers
docker-compose up -d --build

# 5. Wait for health check
sleep 10

# 6. Verify health
curl http://localhost:8001/health

# 7. Check logs
docker-compose logs --tail=50
```

## Rollback

```bash
# 1. Go to previous git commit
git reset --hard HEAD~1

# 2. Rebuild and restart
docker-compose down
docker-compose up -d --build

# 3. Verify
curl http://localhost:8001/health
```

## Resource Management

```bash
# Check disk usage
docker system df

# Clean up stopped containers
docker container prune -f

# Clean up unused images
docker image prune -a -f

# Clean up unused volumes
docker volume prune -f

# Clean up everything
docker system prune -a --volumes -f
```

## Port Verification

```bash
# Check what's running on port 8001
sudo netstat -tulpn | grep 8001
# or
sudo lsof -i :8001

# Check all application ports
sudo netstat -tulpn | grep -E '8000|8001|8002|3000'
```

## Emergency Fixes

```bash
# Container won't start - check logs
docker-compose logs fastapi-app

# Port conflict - change HOST_PORT in .env
HOST_PORT=8011 docker-compose up -d

# Database connection issues - test manually
docker-compose exec fastapi-app env | grep MONGODB

# Force recreate containers
docker-compose up -d --force-recreate

# Remove and recreate everything
docker-compose down -v
docker-compose up -d --build
```
