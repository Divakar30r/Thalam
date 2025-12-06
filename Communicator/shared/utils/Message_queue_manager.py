# Order Queue Manager for Proposal Message Delivery

import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OrderQueueManager:
    """Queue manager for order-specific proposal message delivery"""
    
    def __init__(self):
        self.order_queues: Dict[str, asyncio.Queue] = {}
        
    def get_order_queue(self, order_req_id: str) -> asyncio.Queue:
        """Get or create a queue for a specific order"""
        if order_req_id not in self.order_queues:
            self.order_queues[order_req_id] = asyncio.Queue()
            logger.info(f"Created new order queue for {order_req_id}")
        return self.order_queues[order_req_id]
    
    async def add_to_order_queue(self, order_req_id: str, message: str):
        """Add a message to an order-specific queue"""
        queue = self.get_order_queue(order_req_id)
        await queue.put(message)
        logger.info(f"Added message to order queue {order_req_id}: {message}")
    
    async def get_from_order_queue(
        self, 
        order_req_id: str, 
        timeout: Optional[float] = None
    ) -> Optional[str]:
        """Get a message from an order-specific queue"""
        queue = self.get_order_queue(order_req_id)
        try:
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()
            return message
        except asyncio.TimeoutError:
            return None
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get order queue statistics"""
        return {
            'order_queues_count': len(self.order_queues),
            'queues': {
                order_id: queue.qsize() 
                for order_id, queue in self.order_queues.items()
            }
        }
    
    def remove_order_queue(self, order_req_id: str):
        """Remove an order queue (called when order is completed/cancelled)"""
        if order_req_id in self.order_queues:
            del self.order_queues[order_req_id]
            logger.info(f"Removed order queue for {order_req_id}")
    
    def has_order_queue(self, order_req_id: str) -> bool:
        """Check if an order queue exists"""
        return order_req_id in self.order_queues

# Global order queue manager instance
order_queue_manager = OrderQueueManager()
