# Queue Integration for Proposal Messages

## Overview

The processor now uses `QueueManager` from `shared/utils/queue_manager.py` to handle proposal and follow-up messages. Each order has its own queue identified by `order_req_id`.

## Architecture

### Queue Storage
- **Location**: `QueueManager.order_queues: Dict[str, asyncio.Queue]`
- **Key**: `order_req_id` (e.g., "SB1029436")
- **Value**: `asyncio.Queue` instance for that order
- **Separation**: These order-specific queues are separate from the `priority_queue` used for gRPC concurrency

### Message Flow

```
Proposal API Endpoints → queue_manager.add_to_order_queue(order_req_id, message)
                                          ↓
                         QueueManager.order_queues[order_req_id]
                                          ↓
               streaming_server._stream_responses() polls queue
                                          ↓
                    _process_queue_message() processes message
                                          ↓
                      Yields OrderStreamResponse to client
```

## Message Formats

### 1. New Proposal Submission
**Endpoint**: `POST /proposals/proposal-submissions`

**Message Format**: `{proposal_id}/New`

**Example**: `PROP123/New`

**Processing**: 
- Triggers `_handle_proposal_message()` with code="New"
- Returns `OrderStreamResponse` with `streaming_response_status="NewProposal"`

### 2. Proposal Follow-Up
**Endpoint**: `POST /proposals/Proposalfollowup`

**Message Format**: `{proposal_id}.{follow_up_id}/Update`

**Example**: `PROP123.FU001/Update`

**Processing**:
- Triggers `_handle_followup_message()` with code="Update"
- Returns `OrderStreamResponse` with `streaming_response_status="ProposalUpdate"`

### 3. Edit Lock
**Endpoint**: `POST /proposals/edit-lock`

**Message Format**: `{proposal_id}/EditLock`

**Example**: `PROP123/EditLock`

**Processing**:
- Triggers `_handle_proposal_message()` with code="EditLock"
- Returns `OrderStreamResponse` with `streaming_response_status="EditLock"`

## Code Changes

### 1. ProcessorOrderReqObj Model
**File**: `shared/models/order_models.py`

**Removed**:
```python
queue_name: Optional[str] = Field(default=None, alias="Queuename")
```

**Rationale**: Queue is now managed by `QueueManager` using `order_req_id` directly

### 2. Streaming Server
**File**: `processor/app/grpc_server/streaming_server.py`

**Changes**:
- Removed `queue_name` from `ProcessorOrderReqObj` initialization
- Changed `get_message(queue_name, timeout)` → `get_from_order_queue(order_req_id, timeout)`
- Removed queue cleanup (handled by garbage collection)

### 3. Proposals API
**File**: `processor/app/api/v1/proposals.py`

**Added**:
```python
from shared.utils.queue_manager import queue_manager
```

**Updated Endpoints**:

#### proposal_submissions
```python
# Old (just logging)
logger.info(f"Adding queue message: {proposal_id}/New")

# New (actually adds to queue)
await queue_manager.add_to_order_queue(order_req_id, f"{proposal_id}/New")
logger.info(f"Added queue message: {proposal_id}/New to order queue {order_req_id}")
```

#### ProposalFollowup
```python
# Old (just logging)
logger.info(f"Adding queue message: {request.follow_up_id}/Update")

# New (actually adds to queue)
queue_message = f"{proposal_id}.{request.follow_up_id}/Update"
await queue_manager.add_to_order_queue(order_req_id, queue_message)
logger.info(f"Added queue message: {queue_message} to order queue {order_req_id}")
```

#### edit_lock
```python
# Old (just logging)
logger.info(f"Adding queue message: {proposal_id}/EditLock")

# New (actually adds to queue)
await queue_manager.add_to_order_queue(order_req_id, f"{proposal_id}/EditLock")
logger.info(f"Added queue message: {proposal_id}/EditLock to order queue {order_req_id}")
```

## QueueManager API

### Methods Used

#### add_to_order_queue
```python
async def add_to_order_queue(self, order_req_id: str, message: str)
```
- Creates queue if it doesn't exist
- Adds message to order-specific queue
- Logs the addition

#### get_from_order_queue
```python
async def get_from_order_queue(
    self, 
    order_req_id: str, 
    timeout: Optional[float] = None
) -> Optional[str]
```
- Retrieves message from order-specific queue
- Returns `None` on timeout
- Blocks until message available if no timeout

#### get_order_queue
```python
def get_order_queue(self, order_req_id: str) -> asyncio.Queue
```
- Gets or creates queue for order
- Automatically managed by QueueManager

## Separation of Concerns

### Priority Queue (gRPC Concurrency)
**Purpose**: Manage concurrent gRPC streaming tasks

**Type**: `asyncio.PriorityQueue`

**Key**: `task_id`

**Used by**: 
- `requestor/app/services/grpc_client_service.py`
- Background task execution with priority levels

### Order Queues (Proposal Messages)
**Purpose**: Deliver proposal/follow-up messages to streaming clients

**Type**: `Dict[str, asyncio.Queue]`

**Key**: `order_req_id`

**Used by**:
- `processor/app/api/v1/proposals.py` (producers)
- `processor/app/grpc_server/streaming_server.py` (consumer)

**No Confusion**: These are completely separate systems:
- Priority queue manages task execution
- Order queues manage message delivery

## Testing

### Test Proposal Submission
```bash
# Submit proposal
curl -X POST http://localhost:8005/api/v1/proposals/proposal-submissions \
  -H "Content-Type: application/json" \
  -d '{
    "order_req_id": "SB1029436",
    "seller_id": "SELLER001",
    "proposal": {
      "proposal_id": "PROP123",
      "price": 1000,
      "delivery_date": "2025-11-01T00:00:00",
      "notes_arr": []
    }
  }'

# Check processor logs:
# "Added queue message: PROP123/New to order queue SB1029436"

# Check gRPC streaming client should receive:
# OrderStreamResponse(streaming_response_status="NewProposal", proposal_id="PROP123")
```

### Test Follow-Up
```bash
# Submit follow-up
curl -X POST http://localhost:8005/api/v1/proposals/Proposalfollowup \
  -H "Content-Type: application/json" \
  -d '{
    "order_req_id": "SB1029436",
    "proposal_id": "PROP123",
    "follow_up_id": "FU001",
    "message": {
      "urls": [],
      "message_type": "text",
      "message": "Can you deliver earlier?"
    }
  }'

# Check processor logs:
# "Added queue message: PROP123.FU001/Update to order queue SB1029436"

# Check gRPC streaming client should receive:
# OrderStreamResponse(streaming_response_status="ProposalUpdate", proposal_id="PROP123", follow_up_id="FU001")
```

## Lifecycle

### 1. Order Initiated
- Client calls `/initiate` on requestor
- Requestor starts gRPC streaming to processor
- Processor creates `ProcessorOrderReqObj` in `processor_order_req_id_list`
- QueueManager automatically creates queue when first message is added

### 2. Proposals Received
- Seller posts to `/proposal-submissions`
- Message `{proposal_id}/New` added to order queue
- Streaming server polls queue, gets message
- Processes message and yields `OrderStreamResponse`
- Requestor receives response and notifies buyer

### 3. Follow-Ups
- Seller/Buyer posts to `/Proposalfollowup`
- Message `{proposal_id}.{follow_up_id}/Update` added to order queue
- Same streaming/processing flow as proposals

### 4. Order Expiry
- After 30 minutes (configurable)
- Streaming server detects expiry in `_stream_responses`
- Sends final `OrderPaused` response
- Cleanup removes order from `processor_order_req_id_list`
- Queue is garbage collected automatically

## Benefits

1. **Real Message Delivery**: Messages now actually flow through queues instead of just logging
2. **Async-Safe**: Uses `asyncio.Queue` for async/await compatibility
3. **Auto-Cleanup**: Queues are garbage collected when orders are removed
4. **Clear Separation**: Order queues separate from priority queue
5. **Scalable**: Each order has independent queue
6. **Simple API**: Easy to add messages with `add_to_order_queue()`

## Monitoring

Check queue stats:
```python
stats = queue_manager.get_queue_stats()
# Returns:
# {
#     'priority_queue_size': 0,
#     'active_tasks': 2,
#     'order_queues': 5,  # Number of active order queues
#     'completed_tasks': 10
# }
```

## Notes

- Queues are **in-memory only** - lost on service restart
- For production, consider using Redis or RabbitMQ for persistence
- Current implementation is sufficient for local/dev testing
- Queue timeouts set to 1.0 second in streaming loop
- Messages are processed in FIFO order per queue
