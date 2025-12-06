# Order Tracking Service for Requestor App

import logging
from typing import Dict, Optional
from datetime import datetime

from shared.models.order_models import OrderReqObj, NotesDictObj, MessageContent

logger = logging.getLogger(__name__)

class OrderTrackingService:
    """
    Service to manage in-memory order request tracking
    
    Maintains order_req_id_list with OrderReqObj instances for each active order
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
        """
        Add new order to tracking list
        
        Args:
            order_req_id: Order request ID
            session: Session ID
            
        Returns:
            Created OrderReqObj instance
        """
        if self.has_order(order_req_id):
            logger.warning(f"Order {order_req_id} already exists in tracking list")
            return self.order_req_id_list[order_req_id]
        
        order_req_obj = OrderReqObj(
            order_req_id=order_req_id,
            session=session,
            notes_dict_arr=[]
        )
        
        self.order_req_id_list[order_req_id] = order_req_obj
        logger.info(f"Added order {order_req_id} to tracking list")
        
        return order_req_obj
    
    def get_order(self, order_req_id: str) -> Optional[OrderReqObj]:
        """Get order from tracking list"""
        return self.order_req_id_list.get(order_req_id)
    
    def add_follow_up_note(
        self, 
        order_req_id: str, 
        follow_up_id: str,
        audience: list,
        message_content: Dict[str, any]
    ) -> bool:
        """
        Add follow-up note to order's notes_dict_arr
        
        Args:
            order_req_id: Order request ID
            follow_up_id: Follow-up ID
            audience: List of audience IDs
            message_content: Message content dict with urls, message_type, message
            
        Returns:
            bool: True if added successfully
        """
        order_req_obj = self.get_order(order_req_id)
        
        if not order_req_obj:
            logger.error(f"Order {order_req_id} not found in tracking list")
            return False
        
        try:
            # Create MessageContent
            content = MessageContent(
                urls=message_content.get("urls", []),
                message_type=message_content.get("message_type", "text"),
                message=message_content.get("message", "")
            )
            
            # Create NotesDictObj
            note = NotesDictObj(
                follow_up_id=follow_up_id,
                audience=audience,
                content=content
                #added_time=datetime.utcnow()
            )
            
            # Add to order's notes_dict_arr
            order_req_obj.notes_dict_arr.append(note)
            
            logger.info(
                #f"Added follow-up note {follow_up_id} to order {order_req_id}. "
                f"Total notes: {len(order_req_obj.notes_dict_arr)}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding follow-up note to {order_req_id}: {str(e)}")
            return False
    
    def mark_stream_active(self, order_req_id: str):
        """Mark gRPC streaming as active for this order"""
        self.active_grpc_streams[order_req_id] = True
        logger.info(f"Marked gRPC stream as active for order {order_req_id}")
    
    def mark_stream_inactive(self, order_req_id: str):
        """Mark gRPC streaming as inactive for this order"""
        self.active_grpc_streams[order_req_id] = False
        logger.info(f"Marked gRPC stream as inactive for order {order_req_id}")
    
    def remove_order(self, order_req_id: str) -> bool:
        """
        Remove order from tracking list
        
        Args:
            order_req_id: Order request ID
            
        Returns:
            bool: True if removed successfully
        """
        if order_req_id in self.order_req_id_list:
            del self.order_req_id_list[order_req_id]
            
            if order_req_id in self.active_grpc_streams:
                del self.active_grpc_streams[order_req_id]
            
            logger.info(f"Removed order {order_req_id} from tracking list")
            return True
        
        logger.warning(f"Order {order_req_id} not found in tracking list")
        return False
    
    def get_all_orders(self) -> Dict[str, OrderReqObj]:
        """Get all tracked orders"""
        return self.order_req_id_list.copy()
    
    def get_order_count(self) -> int:
        """Get count of tracked orders"""
        return len(self.order_req_id_list)
    
    def get_active_stream_count(self) -> int:
        """Get count of active gRPC streams"""
        return sum(1 for active in self.active_grpc_streams.values() if active)

# Global singleton instance
_order_tracking_service = OrderTrackingService()

def get_order_tracking_service() -> OrderTrackingService:
    """Get global order tracking service instance"""
    return _order_tracking_service
