# AWS MSK Kafka Client for messaging

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from ..models import MSKMessage, MSKTopic, MSKMessageKey
from ..config import get_settings

logger = logging.getLogger(__name__)

class KafkaClient:
    """AWS MSK Kafka client for messaging between services"""
    
    def __init__(self):
        self.settings = get_settings()
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._producer_started = False
        
    async def start_producer(self):
        """Start the Kafka producer"""
        if not self._producer_started:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()
            self._producer_started = True
            logger.info("Kafka producer started")
    
    async def stop_producer(self):
        """Stop the Kafka producer"""
        if self.producer and self._producer_started:
            await self.producer.stop()
            self._producer_started = False
            logger.info("Kafka producer stopped")
    
    async def send_message(
        self, 
        topic: MSKTopic, 
        message: MSKMessage, 
        key: MSKMessageKey
    ) -> bool:
        """
        Send a message to MSK topic
        
        Args:
            topic: MSK topic name
            message: Message object to send
            key: Message key for partitioning
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            if not self._producer_started:
                await self.start_producer()
            
            message_data = message.dict()
            
            await self.producer.send_and_wait(
                topic.value,
                value=message_data,
                key=key.value
            )
            
            logger.info(f"Message sent to topic {topic.value} with key {key.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {topic.value}: {str(e)}")
            return False
    
    async def send_buyer_acknowledgement(
        self, 
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send buyer acknowledgement message"""
        msk_message = MSKMessage(
            OrderReqID=order_req_id,
            Session=session,
            message=message
        )
        
        return await self.send_message(
            MSKTopic.BUYER_ACKNOWLEDGEMENTS,
            msk_message,
            MSKMessageKey.ORD_SUBMISSION
        )
    
    async def send_buyer_notification(
        self, 
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send buyer notification message"""
        msk_message = MSKMessage(
            OrderReqID=order_req_id,
            Session=session,
            message=message
        )
        
        return await self.send_message(
            MSKTopic.BUYER_NOTIFY,
            msk_message,
            MSKMessageKey.ORD_UPDATES
        )
    
    async def send_seller_acknowledgement(
        self, 
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send seller acknowledgement message"""
        msk_message = MSKMessage(
            OrderReqID=order_req_id,
            Session=session,
            message=message
        )
        
        return await self.send_message(
            MSKTopic.SELLER_ACKNOWLEDGEMENTS,
            msk_message,
            MSKMessageKey.PRP_SUBMISSION
        )
    
    async def send_seller_notification(
        self, 
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send seller notification message"""
        msk_message = MSKMessage(
            OrderReqID=order_req_id,
            Session=session,
            message=message
        )
        
        return await self.send_message(
            MSKTopic.SELLER_NOTIFY,
            msk_message,
            MSKMessageKey.PRP_REQUEST
        )
    
    async def send_failure_notification(
        self, 
        topic: MSKTopic,
        key: MSKMessageKey,
        order_req_id: str, 
        session: str, 
        message: str
    ) -> bool:
        """Send failure notification message"""
        msk_message = MSKMessage(
            OrderReqID=order_req_id,
            Session=session,
            message=message
        )
        
        return await self.send_message(topic, msk_message, key)

# Global Kafka client instance
kafka_client = KafkaClient()