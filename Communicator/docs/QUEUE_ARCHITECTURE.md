# Queue Architecture - Separation of Concerns

## Overview

The queue system has been refactored into separate, focused modules to improve maintainability and clarity:

```
shared/utils/
├── priority_queue_manager.py   # gRPC concurrency control
├── order_queue_manager.py      # Proposal message delivery
└── queue_manager.py            # Unified interface (backward compatible)
```

## Architecture

### 1. Priority Queue Manager (`priority_queue_manager.py`)

**Purpose**: Manages concurrent gRPC streaming tasks with priority-based execution.

**Key Components**:
- `TaskPriority` enum: HIGH, MEDIUM, LOW
- `PriorityTask` dataclass: Task wrapper with priority and metadata
- `PriorityQueueManager` class: Orchestrates task execution

**Responsibilities**:
- Maintain `asyncio.PriorityQueue` for task ordering
- Enforce `max_concurrent_tasks` limit
- Execute tasks via worker coroutine pool
- Track active tasks and results
- Handle task lifecycle (start, stop, cleanup)

**Usage**:
```python
from shared.utils.priority_queue_manager import priority_queue_manager, TaskPriority

# Start the manager
await priority_queue_manager.start()

# Add a priority task
task_id = await priority_queue_manager.add_priority_task(
    order_req_id="ORD123",
    task_func=my_async_function,
    priority=TaskPriority.HIGH,
    param1="value1"
)

# Get result
result = priority_queue_manager.get_task_result(task_id)
```

**Key Methods**:
- `start()`: Start the worker coroutine
- `stop()`: Stop and cleanup all tasks
- `add_priority_task()`: Add task to priority queue
- `get_task_result()`: Retrieve completed task result
- `get_queue_stats()`: Get priority queue statistics
- `cleanup_old_results()`: Remove old task results

---

### 2. Order Queue Manager (`order_queue_manager.py`)

**Purpose**: Manages per-order message queues for proposal delivery to streaming clients.

**Key Components**:
- `OrderQueueManager` class: Manages dictionary of order-specific queues
- `order_queues` dict: Maps `order_req_id` → `asyncio.Queue`

**Responsibilities**:
- Create/retrieve queues per order_req_id
- Add proposal messages to order queues
- Retrieve messages for streaming clients
- Track queue statistics
- Cleanup queues when orders complete

**Usage**:
```python
from shared.utils.order_queue_manager import order_queue_manager

# Add message to order queue
await order_queue_manager.add_to_order_queue("ORD123", "PROP456/New")

# Get message from order queue (with timeout)
message = await order_queue_manager.get_from_order_queue("ORD123", timeout=1.0)

# Check if queue exists
if order_queue_manager.has_order_queue("ORD123"):
    # Remove queue when order completes
    order_queue_manager.remove_order_queue("ORD123")
```

**Key Methods**:
- `get_order_queue()`: Get or create queue for order
- `add_to_order_queue()`: Add message to queue
- `get_from_order_queue()`: Retrieve message (with optional timeout)
- `remove_order_queue()`: Delete queue for completed order
- `has_order_queue()`: Check queue existence
- `get_queue_stats()`: Get order queue statistics

---

### 3. Unified Queue Manager (`queue_manager.py`)

**Purpose**: Provides backward-compatible unified interface to both queue systems.

**Key Components**:
- `QueueManager` class: Delegates to specialized managers
- Re-exports: `TaskPriority`, `PriorityTask`, managers

**Usage** (backward compatible):
```python
from shared.utils.queue_manager import queue_manager

# Priority queue operations
await queue_manager.start()
task_id = await queue_manager.add_priority_task(...)
result = queue_manager.get_task_result(task_id)

# Order queue operations
await queue_manager.add_to_order_queue("ORD123", "PROP456/New")
message = await queue_manager.get_from_order_queue("ORD123", timeout=1.0)

# Combined statistics
stats = queue_manager.get_queue_stats()
# Returns: {
#   'priority_queue_size': 5,
#   'active_tasks': 3,
#   'completed_tasks': 10,
#   'order_queues_count': 2,
#   'order_queue_details': {'ORD123': 3, 'ORD456': 1}
# }
```

---

## Why Separate Files?

### Benefits

1. **Separation of Concerns**
   - Priority queue logic isolated from order queue logic
   - Each manager has single, clear responsibility
   - Reduces cognitive load when maintaining code

2. **Independent Testing**
   - Test gRPC concurrency separately from message delivery
   - Mock one system without affecting the other
   - Easier to write focused unit tests

3. **Code Clarity**
   - No confusion between `priority_queue` and `order_queues`
   - Clear file names indicate purpose
   - Better IDE navigation and code discovery

4. **Flexibility**
   - Can use specialized managers directly
   - Swap implementations independently
   - Add features to one without impacting other

5. **Backward Compatibility**
   - Existing code using `queue_manager` still works
   - Gradual migration to specialized managers possible
   - No breaking changes to existing integrations

### Design Principles

- **Priority Queue Manager**: For **task concurrency** in requestor
- **Order Queue Manager**: For **message delivery** in processor
- **Unified Manager**: For **convenience** and **compatibility**

---

## Integration Points

### Requestor Usage (Priority Queue)
```python
# requestor/app/services/grpc_client_service.py
from shared.utils.priority_queue_manager import priority_queue_manager

await priority_queue_manager.start()
task_id = await priority_queue_manager.add_priority_task(
    order_req_id=order_req_id,
    task_func=self._stream_handler,
    priority=TaskPriority.MEDIUM,
    w_request=request
)
```

### Processor Usage (Order Queue)
```python
# processor/app/api/v1/proposals.py
from shared.utils.order_queue_manager import order_queue_manager

await order_queue_manager.add_to_order_queue(order_req_id, f"{proposal_id}/New")

# processor/app/grpc_server/streaming_server.py
from shared.utils.order_queue_manager import order_queue_manager

message = await order_queue_manager.get_from_order_queue(order_req_id, timeout=1.0)
```

---

## Migration Guide

### For New Code
Use specialized managers directly:
```python
# For gRPC concurrency
from shared.utils.priority_queue_manager import priority_queue_manager

# For proposal messages
from shared.utils.order_queue_manager import order_queue_manager
```

### For Existing Code
No changes required - unified manager still works:
```python
# Backward compatible
from shared.utils.queue_manager import queue_manager
```

### Recommended Approach
- **Processor**: Use `order_queue_manager` directly
- **Requestor**: Use `priority_queue_manager` directly
- **Shared/Utils**: Keep unified interface for convenience

---

## Statistics and Monitoring

### Priority Queue Stats
```python
stats = priority_queue_manager.get_queue_stats()
# Returns:
# {
#   'priority_queue_size': 5,      # Tasks waiting
#   'active_tasks': 3,              # Tasks executing
#   'completed_tasks': 10           # Tasks finished
# }
```

### Order Queue Stats
```python
stats = order_queue_manager.get_queue_stats()
# Returns:
# {
#   'order_queues_count': 2,
#   'queues': {
#     'ORD123': 3,  # 3 messages waiting
#     'ORD456': 1   # 1 message waiting
#   }
# }
```

### Combined Stats (via QueueManager)
```python
stats = queue_manager.get_queue_stats()
# Returns merged statistics from both managers
```

---

## Testing

### Unit Tests (Priority Queue)
```python
async def test_priority_execution():
    mgr = PriorityQueueManager(max_concurrent_tasks=2)
    await mgr.start()
    
    task_id = await mgr.add_priority_task(
        order_req_id="TEST",
        task_func=my_func,
        priority=TaskPriority.HIGH
    )
    
    await asyncio.sleep(0.5)
    result = mgr.get_task_result(task_id)
    assert result['success'] == True
```

### Unit Tests (Order Queue)
```python
async def test_order_message_delivery():
    mgr = OrderQueueManager()
    
    await mgr.add_to_order_queue("ORD123", "PROP456/New")
    message = await mgr.get_from_order_queue("ORD123", timeout=1.0)
    
    assert message == "PROP456/New"
```

---

## Summary

The refactored architecture provides:
- **Clear separation** between gRPC concurrency and message delivery
- **Backward compatibility** through unified interface
- **Better maintainability** with focused, single-responsibility modules
- **Flexible usage** - use specialized managers or unified interface
- **No breaking changes** to existing code

Both systems work independently and can be tested, modified, and scaled separately while maintaining a convenient unified interface for existing integrations.
