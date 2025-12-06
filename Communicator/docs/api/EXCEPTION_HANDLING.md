# Exception Handling for AWS MSK and Google APIs

This document describes the exception handling implemented for unconfigured external services.

## Summary

Both **Requestor** and **Processor** applications now gracefully handle exceptions when AWS MSK (Kafka) and Google APIs are unavailable.

---

## Requestor Application

### AWS MSK (Kafka) Handling

**Location**: `requestor/main.py`, `requestor/app/services/notification_service.py`

**Behavior**:
- Application startup continues even if Kafka connection fails
- All MSK notification methods return `True` to continue processing
- Warnings are logged instead of errors
- No exceptions are raised to the caller

**Modified Methods**:
1. `main.py::lifespan()` - Wraps `kafka_client.start_producer()` in try-except
2. `notification_service.py::send_buyer_acknowledgement()` - Returns True on failure
3. `notification_service.py::send_buyer_notification()` - Returns True on failure
4. `notification_service.py::send_failure_notification()` - Returns True on failure
5. `notification_service.py::send_custom_message()` - Returns True on failure

**Example**:
```python
try:
    await kafka_client.start_producer()
    logger.info("Kafka client started successfully")
except Exception as e:
    logger.warning(f"AWS MSK/Kafka not available: {str(e)}. Continuing without messaging support.")
```

---

## Processor Application

### AWS MSK (Kafka) Handling

**Location**: `processor/app/services/notification_service.py`

**Behavior**:
- All MSK message sending operations log warnings instead of raising exceptions
- Returns `False` on failure but doesn't block processing
- Allows order processing to continue even without messaging

**Modified Methods**:
1. `notification_service.py::send_msk_message()` - Returns False instead of raising exception
2. `notification_service.py::notify_gchat()` - Returns False instead of raising exception

### Google Chat API Handling

**Location**: `processor/app/services/external_api_service.py`, `processor/app/services/notification_service.py`

**Behavior**:
- Google Chat notifications are non-blocking
- Logs warnings when API is unavailable
- Returns `False` but doesn't raise exceptions
- Order processing continues regardless of notification success

**Modified Methods**:
1. `external_api_service.py::send_gchat_notification()` - Returns False on failure (no exception)
2. `notification_service.py::notify_gchat()` - Returns False on failure (no exception)

### Google Distance Matrix API Handling

**Location**: `processor/app/services/external_api_service.py`, `processor/app/services/seller_service.py`

**Behavior**:
- **Default distance**: 5 km when API is unavailable
- Sellers are still included in selection with default distance
- Logs warnings instead of errors
- Order processing continues with default values

**Modified Methods**:
1. `external_api_service.py::get_distance()` - Returns 5.0 km as default
2. `seller_service.py::_filter_sellers_by_proximity()` - Uses default distance on exception

**Example**:
```python
try:
    distance_km = await self.external_api_service.get_distance(origin, destination)
except Exception as e:
    logger.warning(f"Google Distance Matrix API unavailable: {str(e)}. Using default distance of 5 km.")
    distance_km = 5  # Default distance when API is unavailable
```

---

## Configuration

### Environment Variables

The following environment variables are used but the application continues if services are unavailable:

**Requestor** (`.env.local`):
```bash
# Kafka Configuration (Optional - graceful degradation)
KAFKA_BOOTSTRAP_SERVERS=["localhost:9092"]
```

**Processor** (`.env.local`):
```bash
# Google API URLs (Optional - graceful degradation)
API_GOOGLE_CHAT_URL=http://localhost:8006
API_GOOGLE_BOT_URL=http://localhost:8007

# AWS MSK Configuration (Optional - graceful degradation)
AWS_MSK_BOOTSTRAP_SERVERS=localhost:9092
AWS_MSK_SECURITY_PROTOCOL=PLAINTEXT
```

---

## Testing Without External Services

You can test the applications without AWS MSK or Google APIs configured:

1. **Start Requestor**:
   ```powershell
   cd requestor
   venv\Scripts\activate.bat
   python main.py
   ```
   Expected: Application starts with warning about Kafka unavailability

2. **Start Processor**:
   ```powershell
   cd processor
   venv\Scripts\activate.bat
   python main.py
   ```
   Expected: Application starts normally

3. **Test Order Initiation**:
   ```powershell
   curl -X POST http://localhost:8004/api/v1/initiate -H "Content-Type: application/json" -d '{"order_req_id": "test123", "session_id": "session1", "notification_type": "email"}'
   ```
   Expected: Order processes successfully with warnings logged about unavailable services

---

## Logging Examples

### When AWS MSK is unavailable:
```
WARNING - AWS MSK/Kafka not available: Connection refused. Continuing without messaging support.
WARNING - AWS MSK unavailable - acknowledgement not sent: [Errno 111] Connection refused
```

### When Google Chat API is unavailable:
```
WARNING - Google Chat API unavailable - notification not sent: Connection timeout
```

### When Google Distance Matrix API is unavailable:
```
WARNING - Google Distance Matrix API unavailable: HTTP 404. Using default distance of 5 km for origin to destination
```

---

## Benefits

1. **Resilience**: Applications continue to function even when external services are down
2. **Development**: Easier local development without full infrastructure setup
3. **Graceful Degradation**: Core business logic executes regardless of notification/messaging status
4. **Clear Logging**: Warnings indicate which services are unavailable without failing requests
5. **Default Values**: Sensible defaults (5 km distance) allow order processing to continue

---

## Future Enhancements

Consider implementing:
1. Circuit breaker pattern for external API calls
2. Retry mechanisms with exponential backoff
3. Health check endpoints that report external service status
4. Metrics/monitoring for external service availability
5. Feature flags to completely disable external service calls
