# Queue System Architecture Diagram

## Before Refactoring

```
┌─────────────────────────────────────────────────────────────────┐
│                      queue_manager.py                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             QueueManager Class (230+ lines)              │   │
│  │                                                           │   │
│  │  Priority Queue Logic:                                    │   │
│  │  - priority_queue: asyncio.PriorityQueue                  │   │
│  │  - active_tasks: Dict[str, asyncio.Task]                  │   │
│  │  - task_results: Dict[str, Any]                           │   │
│  │  - add_priority_task()                                    │   │
│  │  - _worker(), _execute_task()                             │   │
│  │  - get_task_result(), cleanup_old_results()               │   │
│  │                                                           │   │
│  │  Order Queue Logic:                                       │   │
│  │  - order_queues: Dict[str, asyncio.Queue]                 │   │
│  │  - get_order_queue()                                      │   │
│  │  - add_to_order_queue()                                   │   │
│  │  - get_from_order_queue()                                 │   │
│  │                                                           │   │
│  │  ⚠️ Mixed Responsibilities                                │   │
│  │  ⚠️ Hard to test independently                            │   │
│  │  ⚠️ Confusing which queue system to use                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## After Refactoring

```
┌───────────────────────────────────────────────────────────────────────┐
│                     shared/utils/ Module Structure                     │
├───────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │         priority_queue_manager.py (217 lines)                    │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │          PriorityQueueManager                            │   │ │
│  │  │                                                           │   │ │
│  │  │  Purpose: gRPC Streaming Concurrency Control             │   │ │
│  │  │                                                           │   │ │
│  │  │  State:                                                   │   │ │
│  │  │  • priority_queue: asyncio.PriorityQueue                 │   │ │
│  │  │  • active_tasks: Dict[str, asyncio.Task]                 │   │ │
│  │  │  • task_results: Dict[str, Any]                          │   │ │
│  │  │  • max_concurrent_tasks: int                             │   │ │
│  │  │                                                           │   │ │
│  │  │  Methods:                                                 │   │ │
│  │  │  • start(), stop()                                        │   │ │
│  │  │  • add_priority_task(order_req_id, task_func, priority)  │   │ │
│  │  │  • get_task_result(task_id)                              │   │ │
│  │  │  • cleanup_old_results(max_age_hours)                    │   │ │
│  │  │  • get_queue_stats()                                      │   │ │
│  │  │                                                           │   │ │
│  │  │  ✅ Single Responsibility                                │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │                                                                  │ │
│  │  Global Instance: priority_queue_manager                        │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │         order_queue_manager.py (68 lines)                        │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │           OrderQueueManager                              │   │ │
│  │  │                                                           │   │ │
│  │  │  Purpose: Per-Order Proposal Message Delivery            │   │ │
│  │  │                                                           │   │ │
│  │  │  State:                                                   │   │ │
│  │  │  • order_queues: Dict[str, asyncio.Queue]                │   │ │
│  │  │                                                           │   │ │
│  │  │  Methods:                                                 │   │ │
│  │  │  • get_order_queue(order_req_id)                         │   │ │
│  │  │  • add_to_order_queue(order_req_id, message)             │   │ │
│  │  │  • get_from_order_queue(order_req_id, timeout)           │   │ │
│  │  │  • remove_order_queue(order_req_id)                      │   │ │
│  │  │  • has_order_queue(order_req_id)                         │   │ │
│  │  │  • get_queue_stats()                                      │   │ │
│  │  │                                                           │   │ │
│  │  │  ✅ Single Responsibility                                │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │                                                                  │ │
│  │  Global Instance: order_queue_manager                           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │         queue_manager.py (99 lines)                              │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │           QueueManager (Unified Interface)               │   │ │
│  │  │                                                           │   │ │
│  │  │  Purpose: Backward Compatibility & Convenience           │   │ │
│  │  │                                                           │   │ │
│  │  │  Composition:                                             │   │ │
│  │  │  • priority_mgr: PriorityQueueManager                    │   │ │
│  │  │  • order_mgr: OrderQueueManager                          │   │ │
│  │  │                                                           │   │ │
│  │  │  Delegation Methods:                                      │   │ │
│  │  │  • start() → priority_mgr.start()                        │   │ │
│  │  │  • add_priority_task() → priority_mgr.add_priority_task()│   │ │
│  │  │  • add_to_order_queue() → order_mgr.add_to_order_queue() │   │ │
│  │  │  • get_from_order_queue() → order_mgr.get_from_order_..()│   │ │
│  │  │  • get_queue_stats() → merged stats from both            │   │ │
│  │  │                                                           │   │ │
│  │  │  ✅ Maintains Backward Compatibility                     │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │                                                                  │ │
│  │  Global Instance: queue_manager                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────────────────────────────────────────────┘
```

## Usage Flow Diagram

### Requestor (gRPC Concurrency)

```
┌─────────────────────────────────────────────────────────────┐
│              Requestor Service                               │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  requestor/app/services/grpc_client_service.py        │  │
│  │                                                         │  │
│  │  from shared.utils.priority_queue_manager import \     │  │
│  │      priority_queue_manager, TaskPriority              │  │
│  │                                                         │  │
│  │  await priority_queue_manager.start()                  │  │
│  │                                                         │  │
│  │  task_id = await priority_queue_manager.add_priority.. │  │
│  │      order_req_id="ORD123",                            │  │
│  │      task_func=_stream_handler,                        │  │
│  │      priority=TaskPriority.HIGH                        │  │
│  │  )                                                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │      PriorityQueueManager                             │  │
│  │                                                         │  │
│  │  • Manages concurrent gRPC streams                     │  │
│  │  • Enforces max_concurrent_tasks limit                 │  │
│  │  • Executes tasks by priority                          │  │
│  │  • Tracks task results                                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Processor (Proposal Message Delivery)

```
┌─────────────────────────────────────────────────────────────┐
│              Processor Service                               │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  processor/app/api/v1/proposals.py                     │  │
│  │                                                         │  │
│  │  from shared.utils.order_queue_manager import \        │  │
│  │      order_queue_manager                               │  │
│  │                                                         │  │
│  │  # New proposal submission                             │  │
│  │  await order_queue_manager.add_to_order_queue(         │  │
│  │      order_req_id="ORD123",                            │  │
│  │      message="PROP456/New"                             │  │
│  │  )                                                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │      OrderQueueManager                                 │  │
│  │                                                         │  │
│  │  order_queues = {                                      │  │
│  │      "ORD123": asyncio.Queue([                         │  │
│  │          "PROP456/New",                                │  │
│  │          "PROP457/New"                                 │  │
│  │      ])                                                │  │
│  │  }                                                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  processor/app/grpc_server/streaming_server.py        │  │
│  │                                                         │  │
│  │  from shared.utils.order_queue_manager import \        │  │
│  │      order_queue_manager                               │  │
│  │                                                         │  │
│  │  # Get messages from queue                             │  │
│  │  message = await order_queue_manager.get_from_order... │  │
│  │      order_req_id="ORD123",                            │  │
│  │      timeout=1.0                                       │  │
│  │  )                                                      │  │
│  │                                                         │  │
│  │  # Parse and yield to gRPC stream                      │  │
│  │  yield _process_queue_message(message)                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Benefits Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    Before Refactoring                        │
├─────────────────────────────────────────────────────────────┤
│  ⚠️  Monolithic 230+ line QueueManager class                │
│  ⚠️  Mixed responsibilities                                  │
│  ⚠️  Hard to test independently                              │
│  ⚠️  Confusion between priority_queue vs order_queues        │
│  ⚠️  Difficult to maintain                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Refactoring
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    After Refactoring                         │
├─────────────────────────────────────────────────────────────┤
│  ✅  Separated into 3 focused modules                        │
│  ✅  Single responsibility per class                         │
│  ✅  Easy to test independently                              │
│  ✅  Clear separation of concerns                            │
│  ✅  Backward compatible                                     │
│  ✅  Can use specialized managers or unified interface       │
│  ✅  Better maintainability                                  │
└─────────────────────────────────────────────────────────────┘
```

## Import Options

### Option 1: Use Specialized Managers (Recommended)
```python
# In Requestor
from shared.utils.priority_queue_manager import priority_queue_manager

# In Processor  
from shared.utils.order_queue_manager import order_queue_manager
```

### Option 2: Use Unified Interface (Backward Compatible)
```python
# Anywhere
from shared.utils.queue_manager import queue_manager
```

### Option 3: Via shared.utils (Package Import)
```python
from shared.utils import (
    priority_queue_manager,
    order_queue_manager,
    queue_manager
)
```

## Clear Separation of Concerns

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  PriorityQueueManager    │         │  OrderQueueManager       │
├──────────────────────────┤         ├──────────────────────────┤
│                          │         │                          │
│  FOR: Task Concurrency   │         │  FOR: Message Delivery   │
│                          │         │                          │
│  USED BY: Requestor      │         │  USED BY: Processor      │
│                          │         │                          │
│  PURPOSE:                │         │  PURPOSE:                │
│  • Limit concurrent      │         │  • Queue proposals for   │
│    gRPC streams          │         │    each order            │
│  • Priority ordering     │         │  • Deliver to streaming  │
│  • Task result tracking  │         │    clients               │
│                          │         │  • Per-order isolation   │
└──────────────────────────┘         └──────────────────────────┘
           │                                    │
           └────────────────┬───────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │     QueueManager              │
            │  (Unified Interface)          │
            ├───────────────────────────────┤
            │  Delegates to both managers   │
            │  Provides backward compat     │
            │  Combines statistics          │
            └───────────────────────────────┘
```
