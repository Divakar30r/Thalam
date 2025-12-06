# Queue Manager - Unified Interface for Priority Queue and Order Queues
# This module provides a unified interface to both queue systems:
# - PriorityQueueManager: For gRPC streaming concurrency control
# - OrderQueueManager: For proposal message delivery per order
# - OrderStateManager: For centralized order state management

from shared.utils.priorityTask_queue_manager import (
    PriorityQueueManager,
    priority_queue_manager,
    TaskPriority,
    PriorityTask
)

from shared.utils.Message_queue_manager import (
    OrderQueueManager,
    order_queue_manager
)

from shared.utils.order_state_manager import (
    OrderStateManager,
    order_state_manager
)


class QueueManager:
    """
    Unified Queue Manager - combines Priority Queue, Order Queue, and Order State
    
    This is a backward-compatible wrapper that delegates to:
    - PriorityQueueManager: For gRPC streaming concurrency control
    - OrderQueueManager: For proposal message delivery per order
    - OrderStateManager: For centralized order state (ProcessorOrderReqObj instances)
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.priority_mgr = PriorityQueueManager(max_concurrent_tasks)
        self.order_mgr = OrderQueueManager()
        self.state_mgr = OrderStateManager()
        
    # Priority Queue methods (delegate to PriorityQueueManager)
    async def start(self):
        """Start the priority queue manager"""
        await self.priority_mgr.start()
    
    async def stop(self):
        """Stop the priority queue manager"""
        await self.priority_mgr.stop()
    
    async def add_priority_task(self, order_req_id: str, task_func: callable, 
                               priority = None, **kwargs):
        """Add a task to the priority queue"""
        if priority is None:
            priority = TaskPriority.MEDIUM
        return await self.priority_mgr.add_priority_task(
            order_req_id, task_func, priority, **kwargs
        )
    
    def get_task_result(self, task_id: str):
        """Get the result of a completed task"""
        return self.priority_mgr.get_task_result(task_id)
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """Cleanup old task results"""
        self.priority_mgr.cleanup_old_results(max_age_hours)
    
    # Order Queue methods (delegate to OrderQueueManager)
    def get_order_queue(self, order_req_id: str):
        """Get or create a queue for a specific order"""
        return self.order_mgr.get_order_queue(order_req_id)
    
    async def add_to_order_queue(self, order_req_id: str, message: str):
        """Add a message to an order-specific queue"""
        await self.order_mgr.add_to_order_queue(order_req_id, message)
    
    async def get_from_order_queue(self, order_req_id: str, timeout = None):
        """Get a message from an order-specific queue"""
        return await self.order_mgr.get_from_order_queue(order_req_id, timeout)
    
    def remove_order_queue(self, order_req_id: str):
        """Remove an order queue"""
        self.order_mgr.remove_order_queue(order_req_id)
    
    def has_order_queue(self, order_req_id: str) -> bool:
        """Check if an order queue exists"""
        return self.order_mgr.has_order_queue(order_req_id)
    
    # Order State methods (delegate to OrderStateManager)
    def get_or_create_order(self, order_req_id: str, expiry_minutes: int = 30, session: str = ""):
        """Get or create an order state (lazy init)"""
        return self.state_mgr.get_or_create_order(order_req_id, expiry_minutes, session)
    
    def get_order(self, order_req_id: str):
        """Get an existing order without creating it"""
        return self.state_mgr.get_order(order_req_id)
    
    def has_order(self, order_req_id: str) -> bool:
        """Check if an order exists in state"""
        return self.state_mgr.has_order(order_req_id)
    
    def remove_order(self, order_req_id: str) -> bool:
        """Remove an order from state"""
        return self.state_mgr.remove_order(order_req_id)
    
    def get_all_orders(self):
        """Get all orders"""
        return self.state_mgr.get_all_orders()
    
    def get_expired_orders(self):
        """Get list of expired order IDs"""
        return self.state_mgr.get_expired_orders()
    
    # Combined stats
    def get_queue_stats(self):
        """Get statistics for both queue systems"""
        priority_stats = self.priority_mgr.get_queue_stats()
        order_stats = self.order_mgr.get_queue_stats()
        state_stats = self.state_mgr.get_stats()
        
        return {
            **priority_stats,
            'order_queues_count': order_stats['order_queues_count'],
            'order_queue_details': order_stats['queues'],
            **state_stats
        }


# Global queue manager instance (backward compatible)
queue_manager = QueueManager()

# Re-export for backward compatibility
__all__ = [
    'QueueManager',
    'queue_manager',
    'PriorityQueueManager',
    'priority_queue_manager',
    'OrderQueueManager',
    'order_queue_manager',
    'OrderStateManager',
    'order_state_manager',
    'TaskPriority',
    'PriorityTask'
]
