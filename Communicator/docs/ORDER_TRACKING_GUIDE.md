# Order Tracking System - Quick Reference

## Overview
The requestor app now maintains an in-memory dictionary of orders to prevent duplicate gRPC streams and track order state.

## OrderTrackingService API

### Storage
```python
order_req_id_list: Dict[str, OrderReqObj]  # Main storage
active_grpc_streams: Dict[str, bool]        # Stream state tracking
```

### Methods

#### Query Methods
```python
# Check if order exists
has_order(order_req_id: str) -> bool

# Check if stream is active
is_stream_active(order_req_id: str) -> bool

# Get order object
get_order(order_req_id: str) -> Optional[OrderReqObj]

# Get all orders
get_all_orders() -> Dict[str, OrderReqObj]

# Get counts
get_order_count() -> int
get_active_stream_count() -> int
```

#### Mutation Methods
```python
# Add new order
add_order(order_req_id: str, session: str) -> OrderReqObj

# Add follow-up note
add_follow_up_note(
    order_req_id: str,
    follow_up_id: str,
    audience: list,
    message_content: Dict
) -> bool

# Mark stream as active/inactive
mark_stream_active(order_req_id: str)
mark_stream_inactive(order_req_id: str)

# Remove order
remove_order(order_req_id: str) -> bool
```

## Usage Examples

### In /initiate Endpoint
```python
from ...services.order_tracking_service import get_order_tracking_service

@router.post("/initiate")
async def initiate_order(request: InitiateRequest):
    order_tracking = get_order_tracking_service()
    
    # 1. Check for duplicates
    if order_tracking.is_stream_active(request.order_req_id):
        return OrderResponse(message="Order already being processed")
    
    # 2. Create order object
    order_req_obj = order_tracking.add_order(
        request.order_req_id, 
        request.session_id
    )
    
    # 3. Update MongoDB status
    await order_service.update_requests([request.order_req_id], "RequestSubmissions")
    
    # 4. Mark stream active and start
    order_tracking.mark_stream_active(request.order_req_id)
    
    background_tasks.add_task(
        grpc_client_service.start_streaming_client,
        request.order_req_id,
        request.notification_type
    )
```

### In /followup Endpoint
```python
@router.post("/followup")
async def follow_up_order(request: FollowUpRequest):
    order_tracking = get_order_tracking_service()
    
    # 1. Add to MongoDB
    result = await order_service.add_follow_up(
        request.order_req_id,
        request.audience,
        request.message
    )
    
    follow_up_id = result["follow_up_id"]
    
    # 2. Update local tracking
    if order_tracking.has_order(request.order_req_id):
        order_tracking.add_follow_up_note(
            request.order_req_id,
            follow_up_id,
            request.audience,
            request.message
        )
```

### In gRPC Client Service
```python
class GRPCClientService:
    def __init__(self):
        self.order_tracking = get_order_tracking_service()
    
    async def _handle_streaming_responses(self, order_req_id: str, notification_type: str):
        try:
            async for response in self.streaming_client.start_stream(...):
                await self._process_streaming_response(response, order_req_id)
        finally:
            # Always mark inactive when done
            self.order_tracking.mark_stream_inactive(order_req_id)
```

## Diagnostic Endpoints

### Get Tracking Status
```bash
curl http://localhost:8004/api/v1/orders/tracking/status
```

**Response**:
```json
{
  "total_orders": 5,
  "active_streams": 3,
  "tracked_order_ids": ["SB1029436", "SB1029437", "SB1029438", ...]
}
```

### Get Order Details
```bash
curl http://localhost:8004/api/v1/orders/tracking/SB1029436
```

**Response**:
```json
{
  "order_req_id": "SB1029436",
  "session": "sess_123",
  "notes_count": 2,
  "is_stream_active": true,
  "notes": [
    {
      "follow_up_id": "FU001",
      "audience": ["seller1", "seller2"],
      "message_type": "text",
      "added_time": "2024-01-15T10:30:00"
    },
    {
      "follow_up_id": "FU002",
      "audience": ["seller3"],
      "message_type": "text",
      "added_time": "2024-01-15T11:45:00"
    }
  ]
}
```

## OrderReqObj Structure

```python
class OrderReqObj(BaseModel):
    order_req_id: str                          # e.g., "SB1029436"
    session: str                                # e.g., "sess_123"
    notes_dict_arr: List[NotesDictObj] = []    # Follow-up notes

class NotesDictObj(BaseModel):
    follow_up_id: str                          # e.g., "FU001"
    audience: list                             # Required: ["seller1", "seller2"]
    content: MessageContent                    # Required: message object
    added_time: Optional[datetime] = None      # Auto-populated
```

## Key Benefits

### 1. Duplicate Prevention
- Prevents starting multiple gRPC streams for same order
- Checks `is_stream_active()` before starting new stream
- Returns early if duplicate detected

### 2. State Management
- Maintains local copy of order state
- Tracks follow-up notes in `notes_dict_arr`
- Synchronizes with MongoDB operations

### 3. Stream Lifecycle Tracking
- Marks streams as active when started
- Automatically marks inactive when completed (via finally block)
- Provides real-time stream status

### 4. Debugging Support
- Diagnostic endpoints for quick status checks
- Detailed order tracking information
- Count active streams and total orders

## Common Patterns

### Check Before Start Stream
```python
if order_tracking.is_stream_active(order_req_id):
    logger.warning(f"Stream already active for {order_req_id}")
    return
```

### Cleanup on Error
```python
try:
    order_tracking.add_order(order_req_id, session)
    await some_operation()
except Exception:
    order_tracking.remove_order(order_req_id)
    raise
```

### Always Mark Inactive
```python
try:
    async for response in stream:
        process(response)
finally:
    order_tracking.mark_stream_inactive(order_req_id)
```

## Testing Checklist

- [ ] Initiate order → verify added to tracking
- [ ] Check tracking status → verify count increases
- [ ] Try duplicate initiate → verify prevented
- [ ] Add follow-up → verify notes_dict_arr updated
- [ ] Stream completes → verify marked inactive
- [ ] Check order details → verify all fields correct
- [ ] Multiple concurrent orders → verify independent tracking
- [ ] Service restart → tracking cleared (in-memory)

## Notes

- **In-Memory Only**: Data lost on service restart (by design)
- **Singleton Pattern**: Single global instance via `get_order_tracking_service()`
- **Thread-Safe**: Used with FastAPI async/await (single-threaded event loop)
- **No Persistence**: MongoDB is source of truth, tracking is for operational state only
