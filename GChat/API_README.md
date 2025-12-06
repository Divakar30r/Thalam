# Google Chat Notification API

FastAPI endpoint for receiving notification requests and sending them to Google Chat.

## Features

- RESTful API endpoint to receive notification parameters
- Pydantic models with CamelCase aliases for external API (snake_case internally)
- Automatic API documentation with FastAPI
- Health check endpoints

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python api_server.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### POST /notify

Receive notification parameters for processing.

**Request Body (JSON):**
```json
{
  "mailID": "user@example.com",
  "s3Link": "https://s3.amazonaws.com/bucket/file.pdf",
  "notificationCardTemplate": "standard",
  "message": "Your document is ready for review"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification request received and queued for processing",
  "notificationID": null
}
```

### GET /health

Health check endpoint to verify service status.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "api": "ok",
    "auth": "pending_check",
    "google_chat": "pending_check"
  }
}
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| mailID | string (email) | Yes | Email address of the recipient |
| s3Link | string (URL) | Yes | S3 link to the resource |
| notificationCardTemplate | string | No | Card template type for formatting |
| message | string | Yes | Message content to send |

## Testing with cURL

```bash
# Send a notification
curl -X POST "http://localhost:8000/notify" \
  -H "Content-Type: application/json" \
  -d '{
    "mailID": "user@example.com",
    "s3Link": "https://s3.amazonaws.com/bucket/file.pdf",
    "notificationCardTemplate": "standard",
    "message": "Your document is ready"
  }'

# Health check
curl http://localhost:8000/health
```

## Testing with Python

```python
import requests

# Send notification
response = requests.post(
    "http://localhost:8000/notify",
    json={
        "mailID": "user@example.com",
        "s3Link": "https://s3.amazonaws.com/bucket/file.pdf",
        "notificationCardTemplate": "standard",
        "message": "Your document is ready"
    }
)

print(response.json())
```

## Next Steps (TODO)

The endpoint currently receives and validates requests. Implementation pending:

1. **User/Space Resolution**: Find or create DM space with user based on mailID
2. **Message Formatting**: Build card/message based on notificationCardTemplate
3. **Content Integration**: Include s3Link and message in the notification
4. **Delivery**: Send to Google Chat via the GoogleChatClient
5. **Error Handling**: Robust error handling and retry logic
6. **Logging**: Comprehensive logging for debugging
7. **Authentication**: Add API key or OAuth for securing the endpoint

## Architecture

```
External API Request (CamelCase)
    ↓
FastAPI Endpoint
    ↓
Pydantic Model (converts to snake_case)
    ↓
[TODO] Business Logic
    ↓
GoogleChatClient
    ↓
Google Chat API
```
