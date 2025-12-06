# API Prefix Configuration

## Overview

The FastAPI Order Management application now supports configurable API path prefixes via the `API_PREFIX` environment variable. This allows you to have different URL structures for development and production environments.

## How It Works

### Development Mode (with prefix)
- **API_PREFIX**: `/api/v1`
- **Endpoints**:
  - `http://localhost:8001/api/v1/order-req/`
  - `http://localhost:8001/api/v1/order-proposal/`
  - `http://localhost:8001/api/v1/users/`
  - `http://localhost:8001/health` (no prefix)

### Production Mode (without prefix)
- **API_PREFIX**: `` (empty string)
- **Endpoints**:
  - `http://localhost:8001/order-req/`
  - `http://localhost:8001/order-proposal/`
  - `http://localhost:8001/users/`
  - `http://localhost:8001/health` (no prefix)

## Why Remove Prefix in Production?

When deploying behind an API Gateway (like AWS API Gateway, Kong, or Nginx with custom routing), the gateway typically:
1. Handles the `/api/v1` prefix at the gateway level
2. Routes requests to the appropriate backend service
3. Strips the prefix before forwarding to the backend

This means:
- **Gateway receives**: `https://drapps.dev/api/v1/order-req/123`
- **Gateway routes to**: FastAPI service based on `/api/v1` prefix
- **FastAPI receives**: `/order-req/123` (prefix already stripped)

## Configuration

### Development (.env or .env.example)
```bash
API_PREFIX="/api/v1"
```

### Production (.env.production or docker-compose)
```bash
API_PREFIX=""
```

### In Code (app/core/config.py)
```python
class Settings(BaseSettings):
    api_prefix: str = "/api/v1"  # Default for development
```

### In main.py
```python
# Routers automatically use the configured prefix
app.include_router(
    order_req_router.router,
    prefix=settings.api_prefix,  # Uses "" in production, "/api/v1" in dev
    dependencies=[]
)
```

## Health Endpoint

The `/health` endpoint is **NOT** affected by the API prefix:
- Always accessible at: `http://localhost:8001/health`
- Returns: `{"status": "healthy", "service": "ordermgmt-fastapi"}`

This ensures load balancers and monitoring tools can always check health without worrying about the prefix.

## Example Logs

### Development (with prefix)
```
INFO: 127.0.0.1:50952 - "GET /api/v1/order-req/SB1029435 HTTP/1.1" 200 OK
INFO: 127.0.0.1:50953 - "POST /api/v1/order-proposal/ HTTP/1.1" 201 Created
```

### Production (without prefix)
```
INFO: 127.0.0.1:50952 - "GET /order-req/SB1029435 HTTP/1.1" 200 OK
INFO: 127.0.0.1:50953 - "POST /order-proposal/ HTTP/1.1" 201 Created
```

## API Gateway Routing Example

### AWS API Gateway / Custom Domain
```
Client Request:
  https://drapps.dev/api/v1/order-req/123

API Gateway:
  - Matches route: /api/v1/order-req/{proxy+}
  - Backend: http://ec2-instance:8001/order-req/{proxy+}
  - Strips /api/v1 prefix

FastAPI receives:
  GET /order-req/123
```

### Nginx Configuration
```nginx
# Gateway handles /api/v1 prefix
location /api/v1/order-req {
    # Strip /api/v1 and forward to FastAPI
    rewrite ^/api/v1/order-req/(.*) /order-req/$1 break;
    proxy_pass http://localhost:8001;
}
```

## Testing

### Test with prefix (development)
```bash
# Set environment
export API_PREFIX="/api/v1"

# Start app
uvicorn app.main:app --reload

# Test endpoint
curl http://localhost:8001/api/v1/order-req/
curl http://localhost:8001/health
```

### Test without prefix (production)
```bash
# Set environment
export API_PREFIX=""

# Start app
uvicorn app.main:app

# Test endpoint
curl http://localhost:8001/order-req/
curl http://localhost:8001/health
```

## GitLab CI/CD Variable

Add to your GitLab CI/CD variables:
- **Variable**: `API_PREFIX`
- **Value**: `` (empty for production)
- **Type**: Variable
- **Protected**: No
- **Masked**: No

## Docker Compose

The `docker-compose.yml` is already configured:
```yaml
environment:
  API_PREFIX: ${API_PREFIX:-}  # Default to empty string
```

## Migration Guide

If you're migrating from hardcoded `/api/v1` prefix:

1. **Update .env files**: Set `API_PREFIX=""` for production
2. **Update Nginx/Gateway**: Remove prefix stripping if not needed
3. **Update client applications**: Ensure they use the correct URLs
4. **Test thoroughly**: Verify all endpoints work with new configuration

## Benefits

1. **Flexibility**: Easy to switch between prefixed and non-prefixed URLs
2. **Gateway-friendly**: Works seamlessly with API Gateways
3. **Development-friendly**: Keep `/api/v1` for local testing
4. **No code changes**: Just update environment variables
5. **Backward compatible**: Can keep prefix in production if needed
