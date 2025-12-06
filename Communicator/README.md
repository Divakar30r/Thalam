# dCent Communicator

A sophisticated microservices architecture demonstrating gRPC server streaming, FastAPI REST endpoints, and AWS MSK messaging between **Requestor** and **Processor** applications.

## Architecture Overview

```
┌─────────────────┐         gRPC Streaming         ┌─────────────────┐
│   Requestor     │◄──────────────────────────────►│   Processor     │
│                 │                                │                 │
│ FastAPI:8000    │         gRPC Non-Stream        │ FastAPI:8001    │
│ gRPC Client     │◄──────────────────────────────►│ gRPC Server     │
└─────────────────┘                                └─────────────────┘
         │                                                   │
         │                    AWS MSK                        │
         └─────────────────────────────────────────────────┘
                           Kafka Topics
```

## Key Features

- **Dual Protocol Support**: FastAPI (HTTP/1.1) + gRPC (HTTP/2) on different ports
- **Mixed HTTP Patterns**: Sync requests for API_BASE_URL, async httpx for Google APIs  
- **Advanced Concurrency**: asyncio.create_task() with priority queues for gRPC streaming
- **Synchronization**: asyncio.Lock() and asyncio.Semaphore() for coordinated operations
- **Messaging**: AWS MSK Kafka for inter-service communication
- **Modern Python**: Pydantic v2, FastAPI, asyncio, grpcio

## Project Structure

```
dCent/Communicator/
├── shared/                          # Shared components
│   ├── proto/                       # gRPC protocol definitions
│   ├── models/                      # Pydantic models
│   ├── utils/                       # Utilities (Kafka, HTTP, Queue management)
│   └── config/                      # Configuration management
├── requestor/                       # Requestor FastAPI application
│   ├── main.py                      # FastAPI + gRPC client
│   ├── app/api/v1/                  # REST endpoints (/initiate, /followup)
│   ├── app/services/                # Business logic (_UpdateRequests)
│   └── app/grpc_client/             # gRPC streaming client (gRPC_SS, gRPC_NS)
├── processor/                       # Processor FastAPI + gRPC application
│   ├── main.py                      # FastAPI + gRPC server
│   ├── app/api/v1/                  # REST endpoints (/proposal-submissions, /followup, /edit-lock)
│   ├── app/services/                # Business logic (_UpdateProposals, _SelectSellers, _NotifyGChat)
│   └── app/grpc_server/             # gRPC server implementation
├── deployment/                      # Docker, scripts, deployment configs
├── tests/                          # Test suites
└── docs/                           # Documentation
```

## Services

### Requestor Service (Port 8000)

**REST Endpoints:**
- `POST /api/v1/initiate` - Initiate order processing
- `POST /api/v1/followup` - Add follow-up to existing order
- `PUT /api/v1/finalize/{order_req_id}` - Finalize order
- `PUT /api/v1/pause/{order_req_id}` - Pause order

**gRPC Client Functions:**
- **gRPC_SS**: Server streaming for real-time order updates
- **gRPC_NS**: Non-streaming for follow-up processing

**Business Logic:**
- `_UpdateRequests`: Order status management (RequestSubmissions, RequestFollowUp, OrderFinalised, OrderPaused)
- AWS MSK messaging for buyer notifications

### Processor Service (Port 8001)

**REST Endpoints:**
- `POST /api/v1/proposal-submissions` - Submit new proposals
- `POST /api/v1/followup` - Add follow-up to proposals
- `POST /api/v1/edit-lock` - Lock proposal for editing

**gRPC Server Functions:**
- **gRPC_SS**: Streams proposal updates to requestor
- **gRPC_NS**: Handles follow-up requests from requestor

**Business Logic:**
- `_SelectSellers`: Find sellers by location/industry + Google Distance Matrix
- `_UpdateProposals`: Proposal management (ProposalSubmissions, ProposalUpdate, ProposalClosed, EditLock, etc.)
- `_NotifyGChat`: Google Chat notifications to sellers
- Priority queue management for concurrent order processing

## Quick Start

### Prerequisites
- Python 3.9+
- Docker (optional)
- Kafka/AWS MSK cluster

### 1. Install Dependencies

```bash
# Requestor service
cd requestor
pip install -r requirements.txt

# Processor service  
cd ../processor
pip install -r requirements.txt
```

### 2. Generate gRPC Code

```bash
# Windows
cd deployment/scripts
generate_proto.bat

# Linux/Mac
cd deployment/scripts
chmod +x generate_proto.sh
./generate_proto.sh
```

### 3. Configure Environment

```bash
# Copy and edit environment files
cp requestor/.env.example requestor/.env.local
cp processor/.env.example processor/.env.local

# Edit the .env.local files with your configuration
```

### 4. Start Services

```bash
# Terminal 1 - Start Processor (gRPC server + FastAPI)
cd processor
python main.py

# Terminal 2 - Start Requestor (gRPC client + FastAPI)  
cd requestor
python main.py
```

### 5. Test the Services

```bash
# Initiate an order
curl -X POST "http://localhost:8000/api/v1/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "OrderReqId": "ORD-001",
    "SessionID": "SESSION-123", 
    "Notification type": "GChat"
  }'

# Submit a proposal (to processor)
curl -X POST "http://localhost:8001/api/v1/proposal-submissions" \
  -H "Content-Type: application/json" \
  -d '{
    "OrderReqID": "ORD-001",
    "Seller": "SELLER-001",
    "ProposalDictObj": {
      "ProposalID": "PROP-001",
      "Price": 1000.0,
      "DeliveryDate": "2025-11-01T00:00:00Z"
    }
  }'

# Add follow-up
curl -X POST "http://localhost:8000/api/v1/followup" \
  -H "Content-Type: application/json" \
  -d '{
    "OrderReqID": "ORD-001",
    "Audience": ["PROP-001"],
    "Message": {
      "content": {
        "URLs": [],
        "MessageType": "text",
        "Message": "Please clarify delivery terms"
      }
    }
  }'
```

## Configuration

### Environment Variables

Key configuration options:

```bash
# API Endpoints
API_BASE_URL=http://localhost:8080          # Main API base URL
API_GOOGLE_BOT_URL=http://localhost:8081    # Google Distance Matrix API
API_GOOGLE_CHAT_URL=http://localhost:8082   # Google Chat API

# gRPC Settings
GRPC_SERVER_PORT=50051                      # gRPC server port
GRPC_MAX_WORKERS=10                         # Max gRPC workers

# Kafka/MSK
KAFKA_BOOTSTRAP_SERVERS=["localhost:9092"]  # Kafka brokers

# Queue Management
MAX_CONCURRENT_TASKS=10                     # Max concurrent gRPC tasks
ORDER_EXPIRY_MINUTES=30                     # Order expiry time

# Seller Selection
FIND_MAX_SEL=10                            # Max sellers to find
```

## AWS MSK Topics

| Topic | Key | Purpose |
|-------|-----|---------|
| `BUYER_ACKNOWLEDGEMENTS` | `ORD_SUBMISSION` | Order submission confirmations |
| `BUYER_NOTIFY` | `ORD_UPDATES` | Order status notifications |
| `REQ_failures` | `ORD_SUBMISSION`, `ORD_UPDATES` | Request failure notifications |
| `SELLER_ACKNOWLEDGEMENTS` | `PRP_SUBMISSION` | Proposal submission confirmations |
| `SELLER_NOTIFY` | `PRP_REQUEST` | New order notifications to sellers |
| `PRP_FAILURES` | `PRP_SUBMISSION` | Proposal failure notifications |

## gRPC Services

### OrderStreamingService (Server Streaming)
```protobuf
service OrderStreamingService {
    rpc ProcessOrderStream(OrderStreamRequest) returns (stream OrderStreamResponse);
}
```

### OrderNonStreamingService (Simple RPC)
```protobuf
service OrderNonStreamingService {
    rpc ProcessFollowUp(FollowUpRequest) returns (FollowUpResponse);
}
```

## Key Technologies

- **FastAPI**: Modern Python web framework
- **gRPC**: High-performance RPC framework  
- **asyncio**: Asynchronous programming
- **Pydantic**: Data validation and parsing
- **aiokafka**: Async Kafka client
- **httpx**: Async HTTP client
- **uvicorn**: ASGI server

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific service tests  
pytest tests/requestor/
pytest tests/processor/
```

### Code Generation
```bash
# Generate gRPC code from proto files
python scripts/proto_compile.py

# Generate requirements.txt
python scripts/generate_requirements.py
```

### Docker Development
```bash
# Build and run with Docker Compose
cd deployment/docker
docker-compose up --build
```

## Production Deployment

### Docker
```bash
# Build images
docker build -f deployment/docker/requestor.dockerfile -t dcent-requestor .
docker build -f deployment/docker/processor.dockerfile -t dcent-processor .

# Run containers
docker run -p 8000:8000 dcent-requestor
docker run -p 8001:8001 -p 50051:50051 dcent-processor
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f deployment/kubernetes/
```

## API Documentation

- **Requestor API**: http://localhost:8000/docs
- **Processor API**: http://localhost:8001/docs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please open an issue in the GitHub repository.