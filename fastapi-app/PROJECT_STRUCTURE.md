# FastAPI Order Management - Project Structure

## Directory Tree

```
fastapi-app/
│
├── app/                                # Main application package
│   ├── __init__.py
│   ├── main.py                        # FastAPI application entry point
│   │
│   ├── core/                          # Core functionality and configuration
│   │   ├── __init__.py
│   │   ├── config.py                  # Settings & environment configuration
│   │   ├── database.py                # MongoDB connection & Beanie ODM setup
│   │   ├── dependencies.py            # FastAPI dependencies
│   │   ├── exception_handlers.py      # Global exception handlers
│   │   ├── exceptions.py              # Custom exception classes
│   │   ├── health.py                  # Health check endpoints
│   │   ├── logging.py                 # Logging configuration
│   │   └── validation.py              # Custom validators
│   │
│   ├── models/                        # Data models
│   │   ├── __init__.py
│   │   ├── documents.py               # Beanie ODM documents (MongoDB models)
│   │   └── schemas.py                 # Pydantic schemas (API request/response)
│   │
│   ├── routers/                       # API route handlers
│   │   ├── __init__.py
│   │   ├── users.py                   # User management endpoints
│   │   ├── roles.py                   # Role management endpoints
│   │   ├── terminals.py               # Terminal management endpoints
│   │   ├── role_details.py            # Role details endpoints
│   │   ├── order_req.py               # Order request endpoints
│   │   └── order_proposal.py          # Order proposal endpoints
│   │
│   └── services/                      # Business logic layer
│       ├── __init__.py
│       ├── user_service.py            # User business logic
│       ├── role_service.py            # Role business logic
│       ├── terminal_service.py        # Terminal business logic
│       ├── role_details_service.py    # Role details business logic
│       ├── order_req_service.py       # Order request business logic
│       ├── order_proposal_service.py  # Order proposal business logic
│       └── s3 tester.py               # S3 testing utilities
│
├── logs/                              # Application logs
│   ├── app.log                        # General application logs
│   └── error.log                      # Error logs
│
├── venv/                              # Python virtual environment (ignored)
│
├── .env                               # Environment variables (development)
├── .env.example                       # Example environment configuration
├── .env.production                    # Production environment template
├── .dockerignore                      # Docker build exclusions
├── .gitlab-ci-deploy-example.yml      # GitLab CI/CD deployment example
│
├── Dockerfile                         # Docker image definition
├── docker-compose.yml                 # Docker Compose configuration
│
├── requirements.txt                   # Python dependencies
├── run.py                             # Development server launcher
├── setup.bat                          # Windows setup script
├── setup.sh                           # Linux/Mac setup script
├── seed_data.py                       # Database seeding script
│
├── API_PREFIX_CONFIG.md               # API prefix configuration guide
├── DOCKER_COMMANDS.md                 # Docker command reference
├── DOCKER_DEPLOYMENT.md               # Deployment documentation
├── ORDER_PROPOSAL_IMPLEMENTATION.md   # Order proposal feature docs
├── ORDERREQ_UPDATES.md                # Order request updates docs
├── README.md                          # Project README
├── REFACTORING_SUMMARY.md             # Refactoring documentation
│
├── order_proposal_requests.http       # HTTP test requests (Order Proposal)
├── order_req_requests_updated.http    # HTTP test requests (Order Request)
└── roles_requests_updated.http        # HTTP test requests (Roles)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUESTS                              │
│        (DocHandler:8000, DynamicForm:3000/8002, Web Browser)        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CLOUDFLARE PROXY                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   NGINX REVERSE PROXY (EC2)                          │
│  Routes: /order-req, /order-proposal, /health → FastAPI:8001       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION (Port 8001)                   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                     app/main.py                             │    │
│  │  • CORS Middleware                                          │    │
│  │  • Exception Handlers                                       │    │
│  │  • Lifespan Events (startup/shutdown)                       │    │
│  │  • Health Check Endpoint                                    │    │
│  └────────────┬───────────────────────────────────────────────┘    │
│               │                                                      │
│  ┌────────────▼──────────────────────────────────────────────┐     │
│  │                  API ROUTERS (with configurable prefix)     │     │
│  │                                                              │     │
│  │  • /users           → users.py                              │     │
│  │  • /roles           → roles.py                              │     │
│  │  • /terminals       → terminals.py                          │     │
│  │  • /role-details    → role_details.py                       │     │
│  │  • /order-req       → order_req.py                          │     │
│  │  • /order-proposal  → order_proposal.py                     │     │
│  │                                                              │     │
│  └────────────┬───────────────────────────────────────────────┘     │
│               │                                                      │
│  ┌────────────▼──────────────────────────────────────────────┐     │
│  │                   SERVICES LAYER                            │     │
│  │  (Business Logic & Data Processing)                         │     │
│  │                                                              │     │
│  │  • user_service.py                                          │     │
│  │  • role_service.py                                          │     │
│  │  • terminal_service.py                                      │     │
│  │  • role_details_service.py                                  │     │
│  │  • order_req_service.py                                     │     │
│  │  • order_proposal_service.py                                │     │
│  │                                                              │     │
│  └────────────┬───────────────────────────────────────────────┘     │
│               │                                                      │
│  ┌────────────▼──────────────────────────────────────────────┐     │
│  │                   MODELS LAYER                              │     │
│  │                                                              │     │
│  │  schemas.py          documents.py                           │     │
│  │  ┌──────────┐       ┌──────────┐                           │     │
│  │  │ Pydantic │       │  Beanie  │                           │     │
│  │  │ Schemas  │       │   ODM    │                           │     │
│  │  │          │       │Documents │                           │     │
│  │  │ API I/O  │       │ MongoDB  │                           │     │
│  │  └──────────┘       └──────────┘                           │     │
│  │                                                              │     │
│  └────────────┬───────────────────────────────────────────────┘     │
│               │                                                      │
│  ┌────────────▼──────────────────────────────────────────────┐     │
│  │              CORE / DATABASE LAYER                          │     │
│  │                                                              │     │
│  │  • config.py        - Settings & environment vars          │     │
│  │  • database.py      - MongoDB connection & Beanie init     │     │
│  │  • logging.py       - Structured logging                   │     │
│  │  • validation.py    - Custom validators                    │     │
│  │  • exceptions.py    - Custom exception classes             │     │
│  │                                                              │     │
│  └────────────┬───────────────────────────────────────────────┘     │
└───────────────┼──────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MONGODB DATABASE                               │
│                                                                       │
│  Collections:                                                         │
│  • UserBase           - User profiles and location data              │
│  • RolesBase          - Role definitions                             │
│  • TerminalBase       - Terminal information                         │
│  • RoleDetails        - Role detail records                          │
│  • OrderRequest       - Order requests                               │
│  • OrderProposal      - Order proposals                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. CLIENT REQUEST
   │
   ├─→ Cloudflare Proxy
   │
   ├─→ Nginx (strips /api/v1 prefix if present)
   │
   ├─→ FastAPI Main (app/main.py)
   │    ├─→ CORS Middleware
   │    ├─→ Exception Handlers
   │    └─→ Request Timing Middleware
   │
   ├─→ ROUTER (app/routers/*.py)
   │    └─→ Validates request with Pydantic schemas
   │
   ├─→ SERVICE (app/services/*.py)
   │    ├─→ Business logic processing
   │    ├─→ Data transformation
   │    └─→ Error handling
   │
   ├─→ BEANIE ODM (app/models/documents.py)
   │    └─→ Database operations
   │
   ├─→ MONGODB
   │
   ├─→ Response flows back through layers
   │
   └─→ CLIENT RECEIVES JSON RESPONSE
```

## Component Responsibilities

### 1. **app/main.py**
- FastAPI application initialization
- Middleware configuration (CORS, timing, trusted hosts)
- Router registration with configurable API prefix
- Lifespan events (database connection/disconnection)
- Health check endpoint

### 2. **app/core/**
- **config.py**: Environment-based settings using Pydantic
- **database.py**: MongoDB connection management and Beanie ODM initialization
- **health.py**: Health check logic (`{"status": "healthy", "service": "ordermgmt-fastapi"}`)
- **logging.py**: Structured logging configuration
- **validation.py**: Custom validators for email, phone, AADHAR, etc.
- **exceptions.py**: Custom exception classes
- **exception_handlers.py**: Global exception handling

### 3. **app/models/**
- **documents.py**: Beanie ODM document models (MongoDB collections)
  - UserBase, RolesBase, TerminalBase, RoleDetails, OrderReq, OrderProposal
- **schemas.py**: Pydantic schemas for API request/response validation
  - Create, Update, Response schemas for each entity

### 4. **app/routers/**
- HTTP endpoint definitions using FastAPI routers
- Request/response validation using Pydantic schemas
- Delegates business logic to service layer
- Handles HTTP-specific concerns (status codes, headers)

### 5. **app/services/**
- Business logic implementation
- Data transformation and validation
- Database operations via Beanie ODM
- Error handling and logging

### 6. **Docker Files**
- **Dockerfile**: Multi-stage build for optimized production image
- **docker-compose.yml**: Container orchestration with environment variables
- **.dockerignore**: Build optimization

### 7. **Configuration Files**
- **.env**: Development environment variables
- **.env.production**: Production environment template (API_PREFIX="")
- **requirements.txt**: Python dependencies

## Key Features

### ✅ Configurable API Prefix
- **Development**: `API_PREFIX="/api/v1"` → Endpoints at `/api/v1/order-req/`
- **Production**: `API_PREFIX=""` → Endpoints at `/order-req/` (Gateway handles prefix)

### ✅ Health Check
- Endpoint: `/health` (no prefix)
- Response: `{"status": "healthy", "service": "ordermgmt-fastapi"}`

### ✅ MongoDB with Beanie ODM
- Async MongoDB operations
- Schema validation at database and application level
- Connection pooling
- Automatic index creation

### ✅ CORS Support
- Configurable allowed origins
- Supports DocHandler (8000), DynamicForm (3000, 8002)

### ✅ Structured Logging
- Request/response logging
- Error tracking
- Performance monitoring

### ✅ Docker Deployment
- Multi-stage builds for optimization
- Health checks
- Resource limits
- Environment-based configuration

### ✅ GitLab CI/CD Integration
- Automated deployment to EC2
- Environment variable injection
- Health verification

## API Endpoints

```
Health & Info:
  GET  /health                          - Health check
  GET  /                                - API information

Users:
  GET    {prefix}/users                 - List users
  POST   {prefix}/users                 - Create user
  GET    {prefix}/users/{id}            - Get user by ID
  PUT    {prefix}/users/{id}            - Update user
  DELETE {prefix}/users/{id}            - Delete user

Roles:
  GET    {prefix}/roles                 - List roles
  POST   {prefix}/roles                 - Create role
  GET    {prefix}/roles/{id}            - Get role by ID
  PUT    {prefix}/roles/{id}            - Update role
  DELETE {prefix}/roles/{id}            - Delete role

Terminals:
  GET    {prefix}/terminals             - List terminals
  POST   {prefix}/terminals             - Create terminal
  GET    {prefix}/terminals/{id}        - Get terminal by ID
  PUT    {prefix}/terminals/{id}        - Update terminal
  DELETE {prefix}/terminals/{id}        - Delete terminal

Role Details:
  GET    {prefix}/role-details          - List role details
  POST   {prefix}/role-details          - Create role detail
  GET    {prefix}/role-details/{id}     - Get role detail by ID
  PUT    {prefix}/role-details/{id}     - Update role detail
  DELETE {prefix}/role-details/{id}     - Delete role detail

Order Requests:
  GET    {prefix}/order-req             - List order requests
  POST   {prefix}/order-req             - Create order request
  GET    {prefix}/order-req/{id}        - Get order request by ID
  PUT    {prefix}/order-req/{id}        - Update order request
  DELETE {prefix}/order-req/{id}        - Delete order request

Order Proposals:
  GET    {prefix}/order-proposal        - List order proposals
  POST   {prefix}/order-proposal        - Create order proposal
  GET    {prefix}/order-proposal/{id}   - Get order proposal by ID
  PUT    {prefix}/order-proposal/{id}   - Update order proposal
  DELETE {prefix}/order-proposal/{id}   - Delete order proposal

Note: {prefix} = "/api/v1" in development, "" in production
```

## Database Collections

```
UserBase:
  - ShortName (string, min 5 chars)
  - EmailID (email, @drworkplace.microsoft.com)
  - Location (GeoJSON Point)
  - Contact (array of phone numbers)
  - AADHAR (12-digit number, optional)
  - ProximityToTerminal (float)
  - PackagingProximity (float)
  - Status (Active/Inactive)

RolesBase:
  - RoleID (auto-generated: ADM-0001, MGR-0001, etc.)
  - RoleName (Admin, Manager, Operator, TerminalOwner)
  - Description
  - Permissions (array)

TerminalBase:
  - TerminalID (string)
  - Location (GeoJSON Point)
  - Capacity (number)
  - CurrentLoad (number)

RoleDetails:
  - UserID (reference to UserBase)
  - RoleID (reference to RolesBase)
  - AssignedDate
  - Status

OrderRequest:
  - OrderID (string)
  - UserID (reference)
  - ProductDetails (object)
  - Quantity (number)
  - Status (string)

OrderProposal:
  - ProposalID (string)
  - OrderID (reference)
  - SupplierID (string)
  - Price (number)
  - Status (string)
```

## Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| API Prefix | `/api/v1` | `` (empty) |
| Debug Mode | `true` | `false` |
| Reload | `true` | `false` |
| Log Level | `DEBUG` | `INFO` |
| CORS Origins | All localhost ports | `drapps.dev` only |
| Port | 8001 | 8001 |

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Web Server**: Uvicorn 0.24.0
- **Database**: MongoDB with Motor (async driver)
- **ODM**: Beanie 1.23.6
- **Validation**: Pydantic 2.5.0
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitLab CI/CD
- **Cloud**: AWS EC2
- **Proxy**: Nginx + Cloudflare
- **Python**: 3.11

## Deployment Flow

```
GitLab Repository
      │
      ├─→ Git Push to main branch
      │
      ├─→ GitLab CI/CD Pipeline triggers
      │    ├─→ Build Docker image
      │    ├─→ SSH to EC2 instance
      │    ├─→ Pull latest code
      │    ├─→ Create .env from CI/CD variables
      │    ├─→ docker-compose down
      │    └─→ docker-compose up -d --build
      │
      ├─→ Docker builds multi-stage image
      │    ├─→ Install dependencies
      │    ├─→ Copy application code
      │    └─→ Create non-root user
      │
      ├─→ Container starts on port 8001
      │
      ├─→ Health check passes
      │
      └─→ Nginx routes traffic to container
```
