from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from shared.models.proposal_models import ProposalDictObj
from shared.utils.http_client import HTTPClient

from ..core.config import settings
from ..core.exceptions import ProposalUpdateException, ExternalAPIException
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class ProposalService:
    """Service for handling proposal operations as per _UpdateProposals method"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.notification_service = NotificationService()
        self.base_url = settings.api_base_url
    
    async def update_proposals(
        self, 
        order_req_id: str,
        proposal_dict: ProposalDictObj, 
        mode: str,
        session_id: Optional[str] = None,
        order_follow_up_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Implementation of _UpdateProposals method from grpcdesign.yaml
        
        Args:
            order_req_id: Order request ID
            proposal_dict_arr: List of proposal objects
            mode: Operation mode (ProposalSubmissions, ProposalUpdate, ProposalClosed, 
                  OrderPaused, EditLock, ProposalLock, UserEdits)
            session_id: Session ID for error messaging
            follow_up_id: Follow up ID for UserEdits mode
        
        Returns:
            Response data from the API call
        """
        try:
            logger.info(f"Updating proposals with mode: {mode} for order: {order_req_id}")
            
            if mode == "ProposalSubmissions":
                return await self._handle_proposal_submissions(proposal_dict, session_id)
            
            elif mode == "ProposalUpdate":
                return await self._handle_proposal_update(proposal_dict, session_id)
            
            elif mode == "ProposalClosed":
                return await self._handle_proposal_closed(proposal_dict, session_id)
            
            elif mode == "OrderPaused":
                return await self._handle_order_paused(proposal_dict, session_id)
            
            elif mode == "EditLock":
                return await self._handle_edit_lock(proposal_dict, session_id)

            elif mode == "ProposalLock":
                return await self._handle_proposal_lock(proposal_dict, session_id)
            
            elif mode == "UserEdits":
                return await self._handle_user_edits(proposal_dict, order_follow_up_id , session_id)
            
            else:
                raise ProposalUpdateException(f"Unknown mode: {mode}")
                
        except Exception as e:
            logger.error(f"Error updating proposals: {str(e)}")
            # Send failure notification to MSK
            await self._send_failure_notification(order_req_id, session_id, f"Proposal update failure: {str(e)}")
            raise ProposalUpdateException(f"Failed to update proposals: {str(e)}")
    
    async def _handle_proposal_submissions(self, proposal_dict: ProposalDictObj, session_id: str) -> Dict[str, Any]:
        """Handle proposal submissions - update status to 'SUBMITTED'"""
        endpoint = f"/api/v1/order-proposal/{proposal_dict.proposal_id}"
        data = {
            "ProposalReqID": proposal_dict.proposal_id,
            "ProposalStatus": "SUBMITTED"
        }
        response = self.http_client.put(endpoint, data)
        return {"result": response}
    
    async def _handle_proposal_update(self, proposal_dict: ProposalDictObj, session_id: str) -> Dict[str, Any]:
        """Handle proposal updates - insert new Notes object"""
        # Create notes object without FollowUpID (will be returned in response)
         
        print(f"Handling proposal update for proposal ID: {proposal_dict}")
        # Convert Pydantic model to dict if notes_arr exists
        notes_data = {}
        if proposal_dict.notes_arr:
            note_obj = proposal_dict.notes_arr[-1]
            # Convert Pydantic model to dict
            notes_dict = note_obj.dict() if hasattr(note_obj, 'dict') else note_obj.model_dump() if hasattr(note_obj, 'model_dump') else note_obj
            
            # Convert to PascalCase for API
            notes_data = {
                "FollowUpID": notes_dict.get("follow_up_id"),
                "Content": notes_dict.get("content")
            }
            print(f"Converted notes data: {notes_data}")
        
        response = self.http_client.add_follow_up_to_proposal(
            proposal_dict.proposal_id,
            notes_data
        )
        print(f"Proposal follow-up response: {response}")
        return {"result": response}

    async def _handle_proposal_closed(self, proposal_dict: ProposalDictObj, session_id: str) -> Dict[str, Any]:
        """Handle proposal closed - update status to 'CLOSED'"""
        endpoint = "/api/v1/order-proposal"
        data = {
            "proposal_id": proposal_dict.proposal_id,
            "status": "CLOSED"
        }
        response = self.http_client.put(endpoint, data)
        
        return {"result": response}
    
    async def _handle_order_paused(self, proposal_dict: ProposalDictObj, session_id: str) -> Dict[str, Any]:
        """Handle order paused - update status to 'PAUSED'"""
        endpoint = "/api/v1/order-proposal"
        data = {
            "proposal_id": proposal_dict.proposal_id,
            "status": "PAUSED"
        }
        response = self.http_client.put(endpoint, data)
        return {"result": response}
    
    async def _handle_edit_lock(self, proposal_dict: ProposalDictObj, session_id: str) -> Dict[str, Any]:
        """Handle edit lock - update status to 'EDITLOCK'"""
        endpoint = "/api/v1/order-proposal"
        data = {
            "proposal_id": proposal_dict.proposal_id,
            "status": "EDITLOCK"
        }
        response = self.http_client.put(endpoint, data)
        return {"result": response}
    
    async def _handle_proposal_lock(self, proposal_dict: ProposalDictObj, session_id: str) -> Dict[str, Any]:
        """Handle proposal lock - update status to 'PROPOSALLOCK'"""
        endpoint = "/api/v1/order-proposal"
        data = {
            "proposal_id": proposal_dict.proposal_id,
            "status": "PROPOSALLOCK"
        }
        response = self.http_client.put(endpoint, data)
        return {"result": response}
    
    async def _handle_user_edits(self, proposal_dict: ProposalDictObj, order_follow_up_id: str, session_id: str) -> Dict[str, Any]:
        """Handle user edits - add UserEdits object with OrderFollowUpID and AddedTime"""
        user_edit_data = {
            "OrderFollowUpID": order_follow_up_id
        }
        response = self.http_client.add_user_edits_to_proposal(proposal_dict.proposal_id, user_edit_data)
        return {"result": response}
    
    async def get_proposal_details(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full proposal details from MongoDB via API_BASE_URL
        
        Args:
            proposal_id: Proposal ID to retrieve
        
        Returns:
            Full proposal data or None if not found
        """
        try:
            logger.info(f"Getting details for proposal: {proposal_id}")
            
            endpoint = f"/api/v1/order-proposal/{proposal_id}"
            response = self.http_client.get(endpoint)
            
            if not response:
                logger.warning(f"No data found for proposal: {proposal_id}")
                return None
            
            logger.info(f"Retrieved details for proposal: {proposal_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting proposal details: {str(e)}")
            return None
    
    async def _send_failure_notification(self, order_req_id: str, session_id: str, message: str):
        """Send failure notification to AWS MSK"""
        try:
            await self.notification_service.send_msk_message(
                topic=settings.prp_failures_topic,
                key="PRP_SUBMISSION",
                message={
                    "order_req_id": order_req_id,
                    "session": session_id,
                    "message": message
                }
            )
        except Exception as e:
            logger.error(f"Failed to send failure notification: {str(e)}")
