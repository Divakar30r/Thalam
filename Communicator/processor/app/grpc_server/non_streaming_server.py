import logging
from typing import List, Dict, Any
from datetime import datetime
import grpc
from grpc import aio
from shared.proto.generated import order_service_pb2_grpc, order_service_pb2

from ..core.config import settings
from ..core.exceptions import GRPCServiceException
from ..services import ProposalService, ExternalAPIService


logger = logging.getLogger(__name__)

class NonStreamingServerService(order_service_pb2_grpc.OrderNonStreamingServiceServicer):
    """gRPC non-streaming server implementation (gRPC_NS) as per grpcdesign.yaml"""
    
    def __init__(self):
        self.proposal_service = ProposalService()
        self.external_api_service = ExternalAPIService()
    
    async def ProcessFollowUp(
        self, 
        request: order_service_pb2.FollowUpRequest, 
        context: grpc.aio.ServicerContext
    ) -> order_service_pb2.FollowUpResponse:
        """
        Implementation of gRPC_NS (non-streaming) from grpcdesign.yaml
        
        Args:
            request: FollowUpRequest with OrderReqID, Audience (List of ProposalIDs), FollowUpID
            context: gRPC service context
        
        Returns:
            FollowUpResponse with NS_FollowUpResp list containing Audience (ProposalID), Status, AddedTime
        """
        order_req_id = request.order_req_id
        audience = list(request.audience)  # List of ProposalIDs
        order_follow_up_id = request.order_follow_up_id

        logger.info(f"Processing follow-up for order: {order_req_id}, audience: {audience}, follow_up_id: {order_follow_up_id}")

        try:
            ns_follow_up_resp = []
            
            # Process each entry in request.audience (ProposalIDs)
            for proposal_id in audience: # Need loop to process multi proposals in audience to attach the single follow_up_id
                try:
                    follow_up_resp_item = await self._process_proposal_follow_up_Iterator(
                        proposal_id, 
                        order_follow_up_id
                    )
                    ns_follow_up_resp.append(follow_up_resp_item)
                    
                except Exception as e:
                    logger.error(f"Error processing follow-up for proposal {proposal_id}: {str(e)}")
                    # Add error response
                    error_item = order_service_pb2.FollowUpResponseItem(
                        audience=proposal_id,
                        status="Error",
                        added_time=""
                    )
                    ns_follow_up_resp.append(error_item)
            
            # Create response
            response = order_service_pb2.FollowUpResponse(
                ns_follow_up_resp=ns_follow_up_resp
            )
            
            logger.info(f"Completed follow-up processing for order: {order_req_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in follow-up processing for order {order_req_id}: {str(e)}")
            await context.abort(grpc.StatusCode.INTERNAL, f"Follow-up processing error: {str(e)}")
    
    async def _process_proposal_follow_up_Iterator(
        self, 
        proposal_id: str, 
        order_follow_up_id: str
    ) -> order_service_pb2.FollowUpResponseItem:
        """
        Process follow-up for a single proposal
        
        Args:
            proposal_id: Proposal ID to process
            order_follow_up_id: Order Follow-up ID
        
        Returns:
            FollowUpResponseItem with audience (ProposalID), status, and added_time
        """
        try:
            # Check if proposal status is 'EditLock'
            proposal_details = await self.proposal_service.get_proposal_details(proposal_id)
            proposal_status = proposal_details.get("ProposalStatus") if proposal_details else None
            
            if proposal_status == 'EDITLOCK':
                # Update NS_FollowUpResp[].Status = 'EditLock' and NS_FollowUpResp[].Audience = ProposalID
                return order_service_pb2.FollowUpResponseItem(
                    audience=proposal_id,
                    status="EditLock",
                    added_time=""
                )
            
            else:
                # Call _UpdateProposals(mode = "UserEdits")
                # Create a mock proposal dict array for the update call
                from shared.models.proposal_models import ProposalDictObj

                proposal_dict = ProposalDictObj(
                    ProposalID=proposal_id,
                    Price="",
                    DeliveryDate=""
             

                )
                
                update_response = await self.proposal_service.update_proposals(
                    order_req_id="",  # Not needed for UserEdits mode
                    proposal_dict=proposal_dict,
                    mode="UserEdits",
                    order_follow_up_id=order_follow_up_id
                )
                
                # If successful, update NS_FollowUpResp[].AddedTime = mongo compatible current timestamp
                if update_response:
                    current_timestamp = datetime.utcnow().isoformat() + "Z"
                    
                    return order_service_pb2.FollowUpResponseItem(
                        audience=proposal_id,
                        status="Updated",
                        added_time=current_timestamp
                    )
                else:
                    return order_service_pb2.FollowUpResponseItem(
                        audience=proposal_id,
                        status="Failed",
                        added_time=""
                    )
                    
        except Exception as e:
            logger.error(f"Error processing proposal follow-up for {proposal_id}: {str(e)}")
            return order_service_pb2.FollowUpResponseItem(
                audience=proposal_id,
                status="Error",
                added_time=""
            )
    
    async def health_check(self) -> bool:
        """
        Health check for the non-streaming gRPC service
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Perform basic health checks
            # Check external API connectivity
            api_health = await self.external_api_service.health_check_external_apis()
            
            # Check if all critical APIs are healthy
            critical_apis = ["base_api"]
            for api in critical_apis:
                if not api_health.get(api, False):
                    logger.warning(f"Critical API {api} is not healthy")
                    return False
            
            logger.info("Non-streaming gRPC service health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
