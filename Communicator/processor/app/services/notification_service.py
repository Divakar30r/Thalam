from typing import Dict, Any, List, Optional
import logging
import json


from shared.utils.kafka_client import KafkaClient


from ..core.config import settings
from ..core.exceptions import NotificationException
from .external_api_service import ExternalAPIService


logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling notifications - _NotifyGChat and AWS MSK messaging"""
    
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.external_api_service = ExternalAPIService()
    
    async def notify_gchat(self, message: str) -> bool:
        """
        Implementation of _NotifyGChat method from grpcdesign.yaml
        
        Args:
            message: Message to send to Google Chat
        
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending GChat notification: {message}")
            
            # Invoke GChat endpoints through external API service
            success = await self.external_api_service.send_gchat_notification(message)
            
            if success:
                logger.info("GChat notification sent successfully")
            else:
                logger.warning("GChat notification failed")
            
            return success
            
        except Exception as e:
            logger.warning(f"Google Chat API unavailable - notification not sent: {str(e)}")
            # Return False but don't raise exception
            return False
    
    async def notify_sellers_gchat(self, seller_dict_arr: List[Dict[str, str]], order_req_id: str) -> Dict[str, bool]:
        """
        Send GChat notifications to multiple sellers
        
        Args:
            seller_dict_arr: List of seller dictionaries with SellerID
            order_req_id: Order request ID to include in message
        
        Returns:
            Dictionary mapping seller_id to notification success status
        """
        results = {}
        
        for seller_dict in seller_dict_arr:
            seller_id = seller_dict.get("seller_id")
            if not seller_id:
                logger.warning(f"Skipping seller with missing ID: {seller_dict}")
                continue
            
            try:
                message = f"OrderReqId {order_req_id} received"
                success = await self.notify_gchat(message)
                results[seller_id] = success
                
            except Exception as e:
                logger.error(f"Failed to notify seller {seller_id}: {str(e)}")
                results[seller_id] = False
        
        return results
    
    async def send_msk_message(
        self, 
        topic: str, 
        key: str, 
        message: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send message to AWS MSK topic
        
        Args:
            topic: MSK topic name
            key: Message key
            message: Message payload
            headers: Optional message headers
        
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending MSK message to topic {topic} with key {key}")
            
            # Convert message to JSON string
            message_str = json.dumps(message)
            
            # Send message using Kafka client
            success = await self.kafka_client.send_message(
                topic=topic,
                key=key,
                value=message_str,
                headers=headers
            )
            
            if success:
                logger.info(f"MSK message sent successfully to {topic}")
            else:
                logger.warning(f"Failed to send MSK message to {topic}")
            
            return success
            
        except Exception as e:
            logger.warning(f"AWS MSK unavailable - message not sent to {topic}: {str(e)}")
            # Return False but don't raise exception
            return False
    
    # Convenience methods for specific MSK topics
    
    async def send_seller_acknowledgement(
        self, 
        order_req_id: str, 
        session_id: str, 
        message: str
    ) -> bool:
        """
        Send message to SELLER_ACKNOWLEDGEMENTS topic
        """
        return await self.send_msk_message(
            topic=settings.seller_acknowledgements_topic,
            key="PRP_SUBMISSION",
            message={
                "order_req_id": order_req_id,
                "session": session_id,
                "message": message
            }
        )
    
    async def send_seller_notification(
        self, 
        order_req_id: str, 
        message: str,
        key: str = "PRP_REQUEST"
    ) -> bool:
        """
        Send message to SELLER_NOTIFY topic
        """
        return await self.send_msk_message(
            topic=settings.seller_notify_topic,
            key=key,
            message={
                "order_req_id": order_req_id,
                "message": message
            }
        )
    
    async def send_seller_followup(
        self, 
        order_req_id: str, 
        session_id: str, 
        message: str
    ) -> bool:
        """
        Send message to SELLER_FOLLOWUP topic
        """
        return await self.send_msk_message(
            topic=settings.seller_followup_topic,
            key="PRP_UPDATES",
            message={
                "order_req_id": order_req_id,
                "session": session_id,
                "message": message
            }
        )
    
    async def send_failure_notification(
        self, 
        order_req_id: str, 
        session_id: str, 
        message: str,
        key: str
    ) -> bool:
        """
        Send message to PRP_FAILURES topic
        """
        return await self.send_msk_message(
            topic=settings.prp_failures_topic,
            key=key,
            message={
                "order_req_id": order_req_id,
                "session": session_id,
                "message": message
            }
        )
