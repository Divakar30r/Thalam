# gRPC Streaming Implementation Summary

## Problem Overview

The application experienced issues with gRPC server-streaming where the processor server was receiving incorrect request types instead of properly deserialized protobuf messages.

### Symptoms
1. Server receiving `grpc._cython.cygrpc._MessageReceiver` instead of `OrderStreamRequest`
2. Server receiving raw `bytes` (e.g., `b'\n\tSB1029436'`) instead of deserialized proto messages
3. Unable to access proto message fields due to type mismatch

## Root Cause Analysis

### Issue 1: Interceptor Handler Type Mismatch
**Location**: `processor/app/grpc_server/interceptors.py`

The interceptors were not properly distinguishing between different RPC method types, causing handler type mismatches:

```python
# WRONG - All handlers treated the same way
if behavior.unary_stream:
    return grpc.stream_stream_rpc_method_handler(wrapper)  # Wrong handler type!
```

The code was returning `stream_stream_rpc_method_handler` for unary-stream RPCs, which caused gRPC to pass the wrong type of request object to the servicer.

### Issue 2: Missing Request Deserializer
**Location**: `processor/app/grpc_server/interceptors.py`

Even when handler types were corrected, the interceptors weren't propagating the `request_deserializer` and `response_serializer`:

```python
# WRONG - No deserializers
return grpc.unary_stream_rpc_method_handler(wrapper)
```

Without these, gRPC couldn't deserialize the incoming bytes into protobuf message objects.

### Issue 3: Protobuf Import Issues
**Location**: `shared/proto/generated/order_service_pb2_grpc.py`

The generated code had incorrect imports:
```python
# WRONG
import order_service_pb2 as order__service__pb2

# CORRECT
from . import order_service_pb2 as order__service__pb2
```

## Solutions Implemented

### 1. Fixed Interceptor Handler Types

Updated all three interceptors (LoggingInterceptor, ErrorHandlingInterceptor, MetricsInterceptor) to properly distinguish RPC types:

**File**: `processor/app/grpc_server/interceptors.py`

```python
# LoggingInterceptor - CORRECT pattern
if hasattr(behavior, 'unary_stream') and behavior.unary_stream:
    return grpc.unary_stream_rpc_method_handler(
        wrapper,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer
    )
elif hasattr(behavior, 'stream_stream') and behavior.stream_stream:
    return grpc.stream_stream_rpc_method_handler(
        wrapper,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer
    )
elif hasattr(behavior, 'unary_unary') and behavior.unary_unary:
    return grpc.unary_unary_rpc_method_handler(
        wrapper,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer
    )
elif hasattr(behavior, 'stream_unary') and behavior.stream_unary:
    return grpc.stream_unary_rpc_method_handler(
        wrapper,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer
    )
```

**Key Points**:
- Each RPC type (unary_stream, stream_stream, unary_unary, stream_unary) gets its matching handler factory
- Both `request_deserializer` and `response_serializer` are preserved from the original handler
- This ensures gRPC properly deserializes bytes → proto before passing to servicer

### 2. Separated Processor and Requestor Models

Created distinct Pydantic models to handle different requirements:

**File**: `shared/models/order_models.py`

```python
# Base model for requestor (strict fields)
class OrderReqObj(BaseModel):
    order_req_id: str
    session: str
    notes_dict_arr: List[NotesDictObj] = Field(default_factory=list)

# Extended model for processor (optional fields)
class ProcessorOrderReqObj(OrderReqObj):
    seller_dict_arr: List[SellerDictObj] = Field(default_factory=list)
    proposal_dict_arr: List[ProposalDictObj] = Field(default_factory=list)
    queue_name: Optional[str] = None
    expiry: Optional[datetime] = None

# Strict notes for requestor
class NotesDictObj(BaseModel):
    follow_up_id: str
    audience: list  # Required
    content: MessageContent  # Required
    added_time: Optional[datetime] = None

# Optional notes for processor initialization
class ProcessorNotesDictObj(BaseModel):
    follow_up_id: str
    audience: Optional[list] = None  # Optional during initialization
    content: Optional[MessageContent] = None  # Optional during initialization
    added_time: Optional[datetime] = None
```

**Rationale**:
- Requestor knows all order details upfront (strict validation)
- Processor initializes orders with minimal data, then populates fields (flexible validation)
- Prevents validation errors during order initialization in processor

### 3. Updated Processor to Use Processor Models

**Files Modified**:
- `processor/app/grpc_server/streaming_server.py`
- `processor/app/services/seller_service.py`

**Changes**:
```python
# streaming_server.py
from shared.models.order_models import ProcessorOrderReqObj

class StreamingServer:
    def __init__(self):
        # Renamed from order_req_id_list to processor_order_req_id_list
        self.processor_order_req_id_list: Dict[str, ProcessorOrderReqObj] = {}
    
    async def ProcessOrderStream(self, request, context):
        # Create processor-specific object
        processor_order_req_obj = ProcessorOrderReqObj(
            order_req_id=request.order_req_id,
            session=request.session,
            notes_dict_arr=[]
        )
        
        # Store in dict
        self.processor_order_req_id_list[request.order_req_id] = processor_order_req_obj
        
        # Pass to services
        await self.seller_service.select_sellers(
            request.order_req_id, 
            processor_order_req_obj
        )
```

**Variable Naming Convention**:
- `processor_order_req_id_list`: Dict storage in processor
- `processor_order_req_obj`: Individual instances in processor
- `order_req_id_list`: Dict storage in requestor (see below)
- `order_req_obj`: Individual instances in requestor

### 4. Implemented Requestor Order Tracking

Created in-memory order tracking system for requestor to prevent duplicate gRPC streams and maintain order state.

**New File**: `requestor/app/services/order_tracking_service.py`

```python
class OrderTrackingService:
    """
    Service to manage in-memory order request tracking
    """
    
    def __init__(self):
        # Key: order_req_id (str), Value: OrderReqObj
        self.order_req_id_list: Dict[str, OrderReqObj] = {}
        # Track active gRPC streaming sessions
        self.active_grpc_streams: Dict[str, bool] = {}
    
    def has_order(self, order_req_id: str) -> bool:
        """Check if order exists in tracking list"""
        return order_req_id in self.order_req_id_list
    
    def is_stream_active(self, order_req_id: str) -> bool:
        """Check if gRPC streaming is active for this order"""
        return self.active_grpc_streams.get(order_req_id, False)
    
    def add_order(self, order_req_id: str, session: str) -> OrderReqObj:
        """Add new order to tracking list"""
        order_req_obj = OrderReqObj(
            order_req_id=order_req_id,
            session=session,
            notes_dict_arr=[]
        )
        self.order_req_id_list[order_req_id] = order_req_obj
        return order_req_obj
    
    def add_follow_up_note(
        self, 
        order_req_id: str, 
        follow_up_id: str,
        audience: list,
        message_content: Dict[str, any]
    ) -> bool:
        """Add follow-up note to order's notes_dict_arr"""
        order_req_obj = self.get_order(order_req_id)
        
        if not order_req_obj:
            return False
        
        # Create NotesDictObj and append
        note = NotesDictObj(
            follow_up_id=follow_up_id,
            audience=audience,
            content=MessageContent(**message_content),
            added_time=datetime.utcnow()
        )
        
        order_req_obj.notes_dict_arr.append(note)
        return True
    
    def mark_stream_active(self, order_req_id: str):
        """Mark gRPC streaming as active for this order"""
        self.active_grpc_streams[order_req_id] = True
    
    def mark_stream_inactive(self, order_req_id: str):
        """Mark gRPC streaming as inactive for this order"""
        self.active_grpc_streams[order_req_id] = False

# Global singleton instance
_order_tracking_service = OrderTrackingService()

def get_order_tracking_service() -> OrderTrackingService:
    return _order_tracking_service
```

**Features**:
- In-memory dictionary keyed by `order_req_id`
- Tracks active gRPC streaming sessions
- Stores `OrderReqObj` instances with `notes_dict_arr`
- Provides methods to add follow-up notes
- Singleton pattern for global access

### 5. Updated Requestor API Endpoints

**File**: `requestor/app/api/v1/orders.py`

#### /initiate Endpoint
```python
@router.post("/initiate", response_model=OrderResponse)
async def initiate_order(
    request: InitiateRequest,
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    # 1. Check for duplicate order_req_id
    if order_tracking.has_order(request.order_req_id):
        if order_tracking.is_stream_active(request.order_req_id):
            logger.warning(f"Order {request.order_req_id} already has active gRPC stream")
            return OrderResponse(
                success=True,
                message="Order already being processed"
            )
    
    # 2. Create and store OrderReqObj
    order_req_obj = order_tracking.add_order(request.order_req_id, request.session_id)
    
    # 3. Update status in MongoDB
    update_result = await order_service.update_requests([request.order_req_id], "RequestSubmissions")
    
    if not update_result:
        # Clean up tracking on failure
        order_tracking.remove_order(request.order_req_id)
        raise HTTPException(status_code=500, detail="Failed to update order request status")
    
    # 4. Mark stream as active and start gRPC streaming
    order_tracking.mark_stream_active(request.order_req_id)
    
    background_tasks.add_task(
        grpc_client_service.start_streaming_client,
        request.order_req_id,
        request.notification_type
    )
```

**Benefits**:
- Prevents duplicate gRPC streams for same order_req_id
- Creates OrderReqObj before starting stream
- Cleans up tracking on errors

#### /followup Endpoint
```python
@router.post("/followup", response_model=OrderResponse)
async def follow_up_order(
    request: FollowUpRequest,
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    # 1. Add follow-up to MongoDB
    follow_up_result = await order_service.add_follow_up(
        request.order_req_id,
        request.audience,
        request.message
    )
    
    follow_up_id = follow_up_result.get("follow_up_id")
    
    # 2. Add follow-up note to OrderReqObj in tracking list
    if order_tracking.has_order(request.order_req_id):
        order_tracking.add_follow_up_note(
            request.order_req_id,
            follow_up_id,
            request.audience,
            request.message
        )
    else:
        logger.warning(f"Order {request.order_req_id} not found in tracking list")
    
    # 3. Trigger gRPC non-streaming call
    grpc_response = await grpc_client_service.send_non_streaming_request(...)
```

**Benefits**:
- Updates local `notes_dict_arr` when follow-ups added
- Maintains consistency between MongoDB and in-memory state
- Logs warnings if order not tracked

#### Diagnostic Endpoints
```python
@router.get("/tracking/status")
async def get_tracking_status(
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    """Get order tracking status - diagnostic endpoint"""
    return {
        "total_orders": order_tracking.get_order_count(),
        "active_streams": order_tracking.get_active_stream_count(),
        "tracked_order_ids": list(order_tracking.order_req_id_list.keys())
    }

@router.get("/tracking/{order_req_id}")
async def get_order_tracking_details(
    order_req_id: str,
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    """Get detailed tracking info for specific order"""
    # Returns order details, notes, and stream status
```

### 6. Updated gRPC Client Service Stream Lifecycle

**File**: `requestor/app/services/grpc_client_service.py`

```python
class GRPCClientService:
    def __init__(self):
        self.order_tracking = get_order_tracking_service()
        # ...
    
    async def _handle_streaming_responses(
        self, 
        order_req_id: str, 
        notification_type: str
    ):
        try:
            async for response in self.streaming_client.start_stream(order_req_id, notification_type):
                await self._process_streaming_response(response, order_req_id)
            
            logger.info(f"Stream completed successfully for order {order_req_id}")
            
        except Exception as e:
            logger.error(f"Error in streaming response handler for {order_req_id}: {str(e)}")
            raise
        
        finally:
            # Always mark stream as inactive when done
            self.order_tracking.mark_stream_inactive(order_req_id)
            logger.info(f"Marked stream as inactive for order {order_req_id}")
    
    async def stop_streaming_client(self, order_req_id: str) -> bool:
        """Stop streaming client for specific order"""
        if order_req_id in self.active_streams:
            task = self.active_streams[order_req_id]
            task.cancel()
            
            # Mark stream as inactive in tracking
            self.order_tracking.mark_stream_inactive(order_req_id)
            
            logger.info(f"Stopped streaming client for order {order_req_id}")
            return True
```

**Benefits**:
- Automatically marks streams as inactive when completed or cancelled
- Ensures tracking state stays synchronized with actual stream state
- Uses finally block to guarantee cleanup even on errors

## Architecture Overview

### In-Memory Order Tracking Pattern

Both requestor and processor use similar in-memory tracking:

**Processor**:
```
processor_order_req_id_list: Dict[str, ProcessorOrderReqObj]
├── order_req_id: "SB1029436"
│   ├── session: "session_123"
│   ├── notes_dict_arr: []
│   ├── seller_dict_arr: [...]  # Populated by seller_service
│   ├── proposal_dict_arr: [...] # Populated as proposals arrive
│   ├── queue_name: "order_queue"
│   └── expiry: datetime(...)
```

**Requestor**:
```
order_req_id_list: Dict[str, OrderReqObj]
├── order_req_id: "SB1029436"
│   ├── session: "session_123"
│   └── notes_dict_arr: [
│       ├── NotesDictObj(follow_up_id="FU001", audience=[...], content=...)
│       └── NotesDictObj(follow_up_id="FU002", audience=[...], content=...)
│   ]
```

### gRPC Flow with Tracking

```
1. Client POST /initiate
   ↓
2. Check order_tracking.has_order() and is_stream_active()
   ↓ (if not duplicate)
3. Create OrderReqObj and add to order_req_id_list
   ↓
4. Update MongoDB status to "RequestSubmissions"
   ↓
5. Mark stream as active: order_tracking.mark_stream_active()
   ↓
6. Start gRPC streaming in background
   ↓
7. Stream processes responses
   ↓
8. On completion/error: mark_stream_inactive() in finally block
   ↓
9. Client POST /followup
   ↓
10. Add follow-up to MongoDB
    ↓
11. Add NotesDictObj to order_req_obj.notes_dict_arr
    ↓
12. Send gRPC non-streaming request
```

## Testing and Verification

### 1. Restart Services
After implementing these fixes, restart both services:

```powershell
# Terminal 1 - Processor
cd processor
.\.venv\Scripts\activate
python main.py

# Terminal 2 - Requestor
cd requestor
.\.venv\Scripts\activate
python main.py
```

### 2. Verify gRPC Message Types
Check processor logs for correct request types:
```
Request type: <class 'order_service_pb2.OrderStreamRequest'>  # ✅ CORRECT
```

NOT:
```
Request type: <class 'grpc._cython.cygrpc._MessageReceiver'>  # ❌ WRONG
Request type: <class 'bytes'>  # ❌ WRONG
```

### 3. Test Order Tracking
```bash
# Check tracking status
curl http://localhost:8004/api/v1/orders/tracking/status

# Expected response:
{
  "total_orders": 0,
  "active_streams": 0,
  "tracked_order_ids": []
}

# Initiate order
curl -X POST http://localhost:8004/api/v1/orders/initiate \
  -H "Content-Type: application/json" \
  -d '{"order_req_id": "SB1029436", "session_id": "sess_123", "notification_type": "email"}'

# Check tracking again
curl http://localhost:8004/api/v1/orders/tracking/status
# Should show: "total_orders": 1, "active_streams": 1

# Check specific order
curl http://localhost:8004/api/v1/orders/tracking/SB1029436
# Should show order details with notes_count: 0

# Add follow-up
curl -X POST http://localhost:8004/api/v1/orders/followup \
  -H "Content-Type: application/json" \
  -d '{"order_req_id": "SB1029436", "audience": ["seller1"], "message": {...}}'

# Check order again
curl http://localhost:8004/api/v1/orders/tracking/SB1029436
# Should show notes_count: 1
```

### 4. Test Duplicate Prevention
```bash
# Try to initiate same order twice
curl -X POST http://localhost:8004/api/v1/orders/initiate \
  -d '{"order_req_id": "SB1029436", ...}'

# Should return: "Order already being processed"
```

## Files Modified

### Core gRPC Fixes
1. `processor/app/grpc_server/interceptors.py`
   - Fixed all three interceptors (Logging, ErrorHandling, Metrics)
   - Added proper handler type distinction
   - Added request_deserializer/response_serializer propagation

2. `shared/proto/generated/order_service_pb2_grpc.py`
   - Fixed relative imports

### Model Separation
3. `shared/models/order_models.py`
   - Added `ProcessorOrderReqObj` (extends OrderReqObj)
   - Added `ProcessorNotesDictObj` (optional fields)
   - Kept `OrderReqObj` and `NotesDictObj` strict for requestor

### Processor Updates
4. `processor/app/grpc_server/streaming_server.py`
   - Changed to use `ProcessorOrderReqObj`
   - Renamed `order_req_id_list` → `processor_order_req_id_list`
   - Renamed `order_req_obj` → `processor_order_req_obj`

5. `processor/app/services/seller_service.py`
   - Updated to accept `processor_order_req_obj` parameter
   - Changed type hints to `ProcessorOrderReqObj`

### Requestor Order Tracking (New)
6. `requestor/app/services/order_tracking_service.py` ✨ NEW
   - Implements `OrderTrackingService` with `order_req_id_list`
   - Methods: add_order, get_order, add_follow_up_note, mark_stream_active/inactive
   - Singleton pattern via `get_order_tracking_service()`

7. `requestor/app/api/v1/orders.py`
   - Updated `/initiate` endpoint with duplicate prevention
   - Updated `/followup` endpoint to populate notes_dict_arr
   - Added `/tracking/status` diagnostic endpoint
   - Added `/tracking/{order_req_id}` detail endpoint

8. `requestor/app/services/grpc_client_service.py`
   - Added `order_tracking` instance
   - Updated `_handle_streaming_responses` to mark_stream_inactive in finally block
   - Updated `stop_streaming_client` to mark_stream_inactive

## Key Takeaways

### Critical Patterns
1. **Interceptors MUST match handler types**: unary_stream → `grpc.unary_stream_rpc_method_handler()`
2. **Always propagate deserializers**: `request_deserializer=handler.request_deserializer, response_serializer=handler.response_serializer`
3. **Model separation for different validation needs**: ProcessorOrderReqObj (optional) vs OrderReqObj (strict)
4. **In-memory tracking prevents duplicates**: Check before starting streams
5. **Always cleanup in finally blocks**: Guarantee stream state synchronization

### Common Pitfalls
❌ Using wrong handler type (stream_stream for unary_stream)  
❌ Forgetting to propagate deserializers/serializers  
❌ Using single model for both strict and flexible validation  
❌ Not tracking stream lifecycle  
❌ Starting duplicate streams without checks  

### Best Practices
✅ Match RPC method types precisely in interceptors  
✅ Preserve all handler attributes when wrapping  
✅ Use relative imports in generated protobuf code  
✅ Separate models for different validation requirements  
✅ Track order state in-memory for quick lookups  
✅ Use finally blocks for guaranteed cleanup  
✅ Add diagnostic endpoints for debugging  

## Next Steps

1. **Restart Services**: Apply all changes by restarting requestor and processor
2. **Monitor Logs**: Verify "Request type: <class 'order_service_pb2.OrderStreamRequest'>"
3. **Test Tracking**: Use diagnostic endpoints to verify order tracking
4. **Test Duplicates**: Verify duplicate stream prevention works
5. **Test Follow-ups**: Verify notes_dict_arr updates correctly
6. **Load Testing**: Test with multiple concurrent orders
7. **Port Conflict**: Address port 50051 binding issue (currently using 50052)

## References

- **Protobuf Definition**: `shared/proto/order_service.proto`
- **gRPC Server**: `processor/app/grpc_server/streaming_server.py`
- **gRPC Client**: `requestor/app/grpc_client/streaming_client.py`
- **Order Models**: `shared/models/order_models.py`
- **Interceptors**: `processor/app/grpc_server/interceptors.py`
- **Order Tracking**: `requestor/app/services/order_tracking_service.py`
