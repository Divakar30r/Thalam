from typing import Dict, Any, Optional
import logging
 
from shared.utils.http_client import HTTPClient

from ..core.config import settings
from ..core.exceptions import ExternalAPIException


logger = logging.getLogger(__name__)

class ExternalAPIService:
    """Service for handling external API integrations"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.google_chat_url = settings.api_google_chat_url
        self.google_bot_url = settings.api_google_bot_url
    
    async def send_gchat_notification(self, message: str) -> bool:
        """
        Send notification to Google Chat
        
        Args:
            message: Message to send
        
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending GChat notification: {message}")
            
            url = f"{self.google_chat_url}/Notify"
            data = {"message": message}
            
            # http_client.get() is synchronous, no await needed
            response = self.http_client.get(url, params=data)
            
            # Assuming successful response indicates notification was sent
            if response:
                logger.info("GChat notification sent successfully")
                return True
            else:
                logger.warning("GChat notification failed - no response")
                return False
                
        except Exception as e:
            logger.warning(f"Google Chat API unavailable - notification not sent: {str(e)}")
            # Return False but don't raise exception - allows processing to continue
            return False
    
    async def get_distance(self, origin: str, destination: str) -> float:
        """
        Get distance between two locations using Google Distance Matrix API through GBOT
        
        Args:
            origin: Origin location
            destination: Destination location
        
        Returns:
            Distance in kilometers (defaults to 5.0 if API unavailable)
        """
        try:
            logger.info(f"Getting distance from {origin} to {destination}")
            
            url = f"{self.google_bot_url}/Distance"
            params = {
                "origin": origin,
                "destination": destination
            }
            
            # http_client.get() is synchronous, no await needed
            response = self.http_client.get(url, params=params)
            
            if not response:
                logger.warning("No distance data returned from GBOT API, using default 5 km")
                return 5.0
            
            # Assuming response contains distance in kilometers
            distance_km = response.get("distance_km")
            if distance_km is None:
                logger.warning("Distance not found in GBOT API response, using default 5 km")
                return 5.0
            
            logger.info(f"Distance from {origin} to {destination}: {distance_km} km")
            return float(distance_km)
            
        except Exception as e:
            logger.warning(
                f"Google Distance Matrix API unavailable: {str(e)}. "
                f"Using default distance of 5 km for {origin} to {destination}"
            )
            # Return default distance instead of raising exception
            return 5.0
    
    async def health_check_external_apis(self) -> Dict[str, bool]:
        """
        Perform health checks on external APIs
        
        Returns:
            Dictionary mapping API names to health status
        """
        health_status = {}
        
        # Check Google Chat API (synchronous, no await)
        try:
            url = f"{self.google_chat_url}/health"
            response = self.http_client.get(url)
            health_status["google_chat"] = bool(response)
        except Exception as e:
            logger.warning(f"Google Chat API health check failed: {str(e)}")
            health_status["google_chat"] = False
        
        # Check Google Bot API (synchronous, no await)
        try:
            url = f"{self.google_bot_url}/health"
            response = self.http_client.get(url)
            health_status["google_bot"] = bool(response)
        except Exception as e:
            logger.warning(f"Google Bot API health check failed: {str(e)}")
            health_status["google_bot"] = False
        
        # Check Base API (synchronous, no await)
        try:
            url = f"{settings.api_base_url}/health"
            response = self.http_client.get(url)
            health_status["base_api"] = bool(response)
        except Exception as e:
            logger.warning(f"Base API health check failed: {str(e)}")
            health_status["base_api"] = False
        
        return health_status
