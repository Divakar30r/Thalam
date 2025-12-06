# Notification Service - AWS MSK messaging

import logging
from typing import Optional

from shared.utils import kafka_client
from shared.models import MSKTopic, MSKMessageKey, MSKMessage
from ..core.exceptions import NotificationServiceError

logger = logging.getLogger(__name__)

class NotificationService:
    """AWS MSK messaging service for notifications"""
    
    def __init__(self):
        self.kafka_client = kafka_client
    
    async def send_buyer_acknowledgement(
        self, 
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send buyer acknowledgement message"""
        try:
            return await self.kafka_client.send_buyer_acknowledgement(
                order_req_id, session, message
            )
        except Exception as e:
            logger.warning(f"AWS MSK unavailable - acknowledgement not sent: {str(e)}")
            # Return True to continue processing even if MSK is unavailable
            return True
    
    async def send_buyer_notification(
        self, 
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send buyer notification message"""
        try:
            return await self.kafka_client.send_buyer_notification(
                order_req_id, session, message
            )
        except Exception as e:
            logger.warning(f"AWS MSK unavailable - notification not sent: {str(e)}")
            # Return True to continue processing even if MSK is unavailable
            return True
    
    async def send_failure_notification(
        self, 
        topic: MSKTopic,
        key: MSKMessageKey,
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send failure notification message"""
        try:
            return await self.kafka_client.send_failure_notification(
                topic, key, order_req_id, session, message
            )
        except Exception as e:
            logger.warning(f"AWS MSK unavailable - failure notification not sent: {str(e)}")
            # Return True to continue processing even if MSK is unavailable
            return True
    
    async def send_custom_message(
        self,
        topic: MSKTopic,
        key: MSKMessageKey,
        order_req_id: str,
        session: str,
        message: str
    ) -> bool:
        """Send custom message to specified topic"""
        try:
            msk_message = MSKMessage(
                OrderReqID=order_req_id,
                Session=session,
                message=message
            )
            
            return await self.kafka_client.send_message(topic, msk_message, key)
            
        except Exception as e:
            logger.warning(f"AWS MSK unavailable - custom message not sent: {str(e)}")
            # Return True to continue processing even if MSK is unavailable
            return True