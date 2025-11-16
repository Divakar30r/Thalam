# Quick Keycloak Setup with PostgreSQL (HTTP on Port 9090)

## Start Keycloak with PostgreSQL Database

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f keycloak
```

## Access Keycloak

- **Admin Console:** http://localhost:9090/admin
- **Username:** admin
- **Password:** admin

## Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

## What's Included

✅ **Keycloak 23.0** - Latest stable version
✅ **PostgreSQL 15** - Production-grade database (like RDS)
✅ **HTTP on port 9090** - Non-HTTPS for local development
✅ **Persistent data** - Database survives restarts
✅ **Health checks** - Ensures services are ready

## Database Connection

If you need to connect to PostgreSQL directly:

```bash
# Connection details
Host: localhost
Port: 5432
Database: keycloak
Username: keycloak
Password: keycloak
```

Connect via psql:
```bash
docker exec -it keycloak-postgres psql -U keycloak -d keycloak
```

## First-Time Setup

After starting, you need to create your realm and clients:

### 1. Create Realm
```
Admin Console → Hover over "master" dropdown → Create Realm
Name: OrderMgmt
Save
```

### 2. Create ORDMGMT Client
```
Clients → Create client
Client ID: ORDMGMT
Client Protocol: openid-connect
Save

→ Settings tab:
Access Type: confidential
Valid Redirect URIs: http://localhost:8002/*
Web Origins: http://localhost:3000
Save

→ Credentials tab:
Copy the Client Secret to your .env.development
```

### 3. Create ORDERFORM Client
```
Clients → Create client
Client ID: ORDERFORM
Client Protocol: openid-connect
Save

→ Settings tab:
Access Type: confidential
Valid Redirect URIs: *
Save

→ Credentials tab:
Copy the Client Secret to your .env.development
```

### 4. Create Roles in ORDERFORM
```
Clients → ORDERFORM → Roles → Create Role
Role Name: ORDER_EDIT
Save

Create another:
Role Name: ORDER_PROPOSAL
Save
```

### 5. Create User
```
Users → Create user
Username: testuser
Email: testuser@example.com
First Name: Test
Last Name: User
Email Verified: ON
Save

→ Credentials tab:
Set Password: password
Temporary: OFF
Save

→ Role Mappings:
Client Roles → Select "ORDERFORM"
Available Roles → Select ORDER_EDIT
Add selected
```

### 6. Configure Client Scope (CRITICAL!)
```
Client Scopes → Create client scope
Name: orderform-roles
Protocol: openid-connect
Save

→ Mappers tab → Create
Name: orderform-client-roles
Mapper Type: User Client Role
Client ID: ORDERFORM
Token Claim Name: resource_access.${client_id}.roles
Add to access token: ON
Multivalued: ON
Save

→ Back to Clients → ORDMGMT → Client scopes
Add client scope → orderform-roles → Default → Add
```

## Environment Configuration

Your `.env.development` is already configured:
```bash
KEYCLOAK_BASE=http://localhost:9090
KEYCLOAK_REALM=OrderMgmt
KEYCLOAK_ORDMGMT_CLIENT_ID=ORDMGMT
KEYCLOAK_ORDMGMT_CLIENT_SECRET=<from-step-2>
KEYCLOAK_ORDERFORM_CLIENT_ID=ORDERFORM
KEYCLOAK_ORDERFORM_CLIENT_SECRET=<from-step-3>
KEYCLOAK_REDIRECT_URI=http://localhost:8002/auth/callback
```

## Troubleshooting

### Service won't start
```bash
# Check if port 9090 is already in use
netstat -ano | findstr :9090

# Or change the port in docker-compose.yml
ports:
  - "9091:9090"  # Change external port
```

### Database connection issues
```bash
# Ensure PostgreSQL is healthy
docker-compose logs postgres

# Restart services
docker-compose restart
```

### Reset everything
```bash
# Complete reset (deletes all data!)
docker-compose down -v
docker-compose up -d
```

## Production Notes

For production with AWS RDS:

```yaml
keycloak:
  environment:
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://your-rds-endpoint.amazonaws.com:5432/keycloak
    KC_DB_USERNAME: ${DB_USERNAME}
    KC_DB_PASSWORD: ${DB_PASSWORD}
    KC_HOSTNAME: keycloak.yourdomain.com
    KC_PROXY: edge
    KC_HTTP_ENABLED: "false"  # Use HTTPS in production
```
