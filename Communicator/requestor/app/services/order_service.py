# Order Service - _UpdateRequests implementation

import logging
from typing import List, Dict, Any, Optional

from shared.utils import http_client, sync_utils
from shared.config import UpdateMode, APIEndpoints, MESSAGE_TEMPLATES
from shared.models import MSKTopic, MSKMessageKey
from ..core.exceptions import OrderServiceError

logger = logging.getLogger(__name__)

class OrderService:
    """Order request management service"""
    
    def __init__(self):
        self.http_client = http_client
        self.sync_manager = sync_utils
    
    async def update_request(
        self, 
        order_req_dict: Dict[str, Any], 
        mode: str
    ) -> Any:
        """
        Update single order request based on mode
        
        Args:
            order_req_dict: Dictionary containing:
                - order_req_id: Order request ID (required)
                - notes_list: List of NotesDictObj (optional, for REQUEST_UPDATE mode)
            mode: Update mode (RequestSubmissions, RequestUpdate, RequestFinalised, RequestPaused)
            
        Returns:
            bool for status updates, dict for follow-up updates with FollowUpID
        """
        try:
            # Extract order_req_id from dict
            #print the current mode and order_req_dict
            print(f"Current mode: {mode}, order_req_dict: {order_req_dict}")

            order_req_id = order_req_dict.get("order_req_id")
            if not order_req_id:
                logger.error("order_req_id missing from order_req_dict")
                raise OrderServiceError("order_req_id is required")

            notes_dict = order_req_dict.get("notes_dict", {})

            async with self.sync_manager.synchronized_order_operation(order_req_id):
                if mode == UpdateMode.REQUEST_SUBMISSIONS:
                    return await self._update_order_status(order_req_id, "SUBMITTED")
                
                elif mode == UpdateMode.REQUEST_UPDATE:
                    return await self._update_proposal_followup(order_req_id, notes_dict)

                elif mode == UpdateMode.REQUEST_FINALISED:
                    return await self._update_proposal_status(order_req_id, "FINALISED")
                
                elif mode == UpdateMode.REQUEST_PAUSED:
                    return await self._update_proposal_status(order_req_id, "PAUSED")
                
                else:
                    logger.warning(f"Unknown update mode: {mode}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating order {order_req_dict.get('order_req_id', 'UNKNOWN')}: {str(e)}")
            raise OrderServiceError(f"Failed to update request: {str(e)}")
    
    async def _update_order_status(self, order_req_id: str, status: str) -> bool:
        """Update order request status"""
        try:
            # Use synchronous HTTP client for PUT request
            result = self.http_client.update_order_request_status(order_req_id, status)
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to update order status {order_req_id}: {str(e)}")
            return False
    
    async def _update_proposal_status(self, order_req_id: str, status: str) -> bool:
        """Update order proposal status"""
        try:
            # Note: Using order_req_id as proposal_id for this operation
            # In real implementation, you'd need to map order_req_id to proposal_id
            result = self.http_client.update_order_proposal_status(order_req_id, status)
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to update proposal status {order_req_id}: {str(e)}")
            return False
    
    async def _update_proposal_followup(
        self, 
        order_req_id: str, 
        notes_dict: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """
        Update order with follow-up note (wraps add_follow_up)
        
        Args:
            order_req_id: Order request ID
            notes_dict: Dictionary containing FollowUpID, Audience, Content
            
        Returns:
            Dict with FollowUpID if successful, None otherwise
        """
        try:
            if not notes_dict:
                logger.warning(f"No notes provided for follow-up update to {order_req_id}")
                return None
            
            note = notes_dict
            trn_uuid = note.get("FollowUpID")
            audience = note.get("Audience", [])
            content = note.get("Content", {})
            
            # Prepare payload - already inside synchronized block from update_request
            payload = {
                "FollowUpID": trn_uuid,
                "Audience": audience,
                "Content": content
            }
            
            # Add follow-up via HTTP client (synchronous request)
            result = self.http_client.add_follow_up_to_order(order_req_id, payload)
            
            if result:
                # Extract FollowUpID from response
                returned_id = None
                if isinstance(result, dict):
                    returned_id = result.get("FollowUpID") or result.get("follow_up_id")
                return {"FollowUpID": returned_id or trn_uuid}
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to update proposal follow-up for {order_req_id}: {str(e)}")
            return None
    
    async def add_follow_up(
        self, 
        order_req_id: str, 
        trn_uuid: str,
        audience: List[str], 
        message: Dict[str, Any]
    ) -> Optional[str]:
        """
        Add follow-up to order request (RequestFollowUp mode)
        
        Args:
            order_req_id: Order request ID
            audience: List of audience IDs
            message: Message content
            
        Returns:
            Response with follow_up_id or None if failed
        """
        try:
            async with self.sync_manager.synchronized_order_operation(order_req_id):

                 
                NotesData = {
                    "FollowUpID": trn_uuid,  # Let the server generate FollowUpID
                    "Audience": audience,
                    "Content": message
                }

                # The API that updates an order request should accept a payload
                # that contains the Notes array to append. Wrap the note in a
                # top-level "Notes" field so the server can merge/append it.
                payload = {"Notes": [NotesData]}

                # Add follow-up via HTTP client (synchronous request)
                result = self.http_client.add_follow_up_to_order(order_req_id, payload)

                # If the API succeeds, return the FollowUpID we generated (or
                # the DB-generated value if the API returns one).
                if result:
                    # Prefer any FollowUpID returned by the API
                    returned_id = None
                    if isinstance(result, dict):
                        returned_id = result.get("FollowUpID") or result.get("follow_up_id")
                    return returned_id
                else:
                    return None

        except Exception as e:
            logger.error(f"Error adding follow-up to {order_req_id}: {str(e)}")
            raise OrderServiceError(f"Failed to add follow-up: {str(e)}")
    
    def _get_current_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    async def get_order_details(self, order_req_id: str) -> Optional[Dict[str, Any]]:
        """Get order request details"""
        try:
            result = self.http_client.get_order_request(order_req_id)
            return result
            
        except Exception as e:
            logger.error(f"Error getting order details {order_req_id}: {str(e)}")
            return None