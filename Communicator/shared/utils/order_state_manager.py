# Order State Manager - Centralized order state management
# Decouples order lifecycle from gRPC stream lifecycle

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from shared.models.order_models import ProcessorOrderReqObj

logger = logging.getLogger(__name__)


class OrderStateManager:
    """
    Centralized manager for ProcessorOrderReqObj instances.
    
    Provides shared state between HTTP endpoints and gRPC streaming server.
    Order lifecycle is independent of gRPC stream connection state.
    """
    
    def __init__(self):
        # In-memory storage for order requests (in production, use Redis or similar)
        self.processor_order_req_id_list: Dict[str, ProcessorOrderReqObj] = {}
        self._lock = asyncio.Lock()
    
    def get_or_create_order(
        self, 
        order_req_id: str, 
        expiry_minutes: int = 30,
        session: str = ""
    ) -> ProcessorOrderReqObj:
        """
        Get an existing order or create a new one if it doesn't exist (lazy init).
        
        This allows HTTP endpoints and gRPC streams to both initialize orders,
        supporting HTTP-first, gRPC-first, or mixed flows.
        
        Args:
            order_req_id: Unique order request ID
            expiry_minutes: Minutes until order expires (default from settings)
            session: Session ID (optional)
        
        Returns:
            ProcessorOrderReqObj instance (existing or newly created)
        """
        if order_req_id not in self.processor_order_req_id_list:
            expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            
            order_obj = ProcessorOrderReqObj(
                order_req_id=order_req_id,
                session=session,
                seller_dict_arr=[],
                proposal_dict_arr=[],
                notes_dict_arr=[],
                expiry=int(expiry_time.timestamp() * 1000)  # milliseconds
            )
            
            self.processor_order_req_id_list[order_req_id] = order_obj
            logger.info(f"Created new order state for {order_req_id} (expiry: {expiry_minutes} min)")
        
        return self.processor_order_req_id_list[order_req_id]
    
    def get_order(self, order_req_id: str) -> Optional[ProcessorOrderReqObj]:
        """
        Get an existing order without creating it.
        
        Args:
            order_req_id: Order request ID
        
        Returns:
            ProcessorOrderReqObj if exists, None otherwise
        """
        return self.processor_order_req_id_list.get(order_req_id)
    
    def has_order(self, order_req_id: str) -> bool:
        """Check if an order exists in state"""
        return order_req_id in self.processor_order_req_id_list
    
    def remove_order(self, order_req_id: str) -> bool:
        """
        Remove an order from state (called by sweeper on expiry).
        
        Args:
            order_req_id: Order to remove
        
        Returns:
            True if removed, False if didn't exist
        """
        if order_req_id in self.processor_order_req_id_list:
            del self.processor_order_req_id_list[order_req_id]
            logger.info(f"Removed order state for {order_req_id}")
            return True
        return False
    
    def get_all_orders(self) -> Dict[str, ProcessorOrderReqObj]:
        """Get all orders (for sweeper/admin)"""
        return self.processor_order_req_id_list
    
    def get_expired_orders(self) -> list[str]:
        """
        Get list of expired order_req_ids.
        
        Returns:
            List of order_req_ids that have passed their expiry time
        """
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        expired = [
            oid for oid, obj in self.processor_order_req_id_list.items()
            if obj and getattr(obj, 'expiry', 0) and now_ms >= obj.expiry
        ]
        return expired
    
    def get_stats(self) -> dict:
        """Get order state statistics"""
        return {
            'total_orders': len(self.processor_order_req_id_list),
            'order_ids': list(self.processor_order_req_id_list.keys()),
            'orders_with_proposals': sum(
                1 for obj in self.processor_order_req_id_list.values()
                if obj.proposal_dict_arr
            )
        }


# Global order state manager instance
order_state_manager = OrderStateManager()
