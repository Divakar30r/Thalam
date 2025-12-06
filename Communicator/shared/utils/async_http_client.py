# Asynchronous HTTP Client for Google APIs using httpx

import asyncio
import httpx
import logging
from typing import Dict, Any, Optional, List
from ..config import get_settings

logger = logging.getLogger(__name__)

class AsyncHTTPClient:
    """Asynchronous HTTP client for Google API calls"""
    
    def __init__(self):
        self.settings = get_settings()
        self.google_bot_url = self.settings.api_google_bot_url
        self.google_chat_url = self.settings.api_google_chat_url
        self.timeout = self.settings.http_timeout
        
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make async HTTP request
        
        Args:
            method: HTTP method
            url: Full URL
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                )
                
                response.raise_for_status()
                
                logger.info(f"Async {method} {url} - Status: {response.status_code}")
                
                if response.content:
                    return response.json()
                return {"success": True}
                
        except httpx.TimeoutException:
            logger.error(f"Timeout for async {method} {url}")
        except httpx.ConnectError:
            logger.error(f"Connection error for async {method} {url}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for async {method} {url}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error for async {method} {url}: {str(e)}")
        
        return None
    
    async def get_distance_matrix(
        self, 
        origins: List[str], 
        destinations: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Get distance matrix from Google Distance Matrix API via GBOT
        
        Args:
            origins: List of origin locations
            destinations: List of destination locations
            
        Returns:
            Distance matrix response
        """
        url = f"{self.google_bot_url}/Distance"
        data = {
            "origins": origins,
            "destinations": destinations
        }
        
        return await self._make_request("GET", url, params=data)
    
    async def send_gchat_notification(
        self, 
        recipient: str, 
        message: str
    ) -> bool:
        """
        Send Google Chat notification
        
        Args:
            recipient: Recipient Google account
            message: Message to send
            
        Returns:
            bool: True if notification sent successfully
        """
        url = f"{self.google_chat_url}/Notify"
        data = {
            "recipient": recipient,
            "message": message
        }
        
        result = await self._make_request("GET", url, params=data)
        return result is not None
    
    async def send_multiple_gchat_notifications(
        self, 
        notifications: List[Dict[str, str]]
    ) -> List[bool]:
        """
        Send multiple Google Chat notifications concurrently
        
        Args:
            notifications: List of {recipient, message} dicts
            
        Returns:
            List of success indicators
        """
        tasks = [
            self.send_gchat_notification(notif["recipient"], notif["message"])
            for notif in notifications
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to False
        return [
            result if isinstance(result, bool) else False 
            for result in results
        ]
    
    async def calculate_seller_distances(
        self, 
        buyer_location: str, 
        seller_locations: List[str]
    ) -> Dict[str, float]:
        """
        Calculate distances between buyer and multiple sellers
        
        Args:
            buyer_location: Buyer's terminal location
            seller_locations: List of seller terminal locations
            
        Returns:
            Dict mapping seller_location to distance in km
        """
        distance_data = await self.get_distance_matrix(
            origins=[buyer_location],
            destinations=seller_locations
        )
        
        distances = {}
        if distance_data and "distances" in distance_data:
            for i, seller_loc in enumerate(seller_locations):
                try:
                    # Extract distance value from response
                    distance_km = distance_data["distances"][0][i]["distance"]["value"] / 1000
                    distances[seller_loc] = distance_km
                except (IndexError, KeyError, TypeError):
                    logger.warning(f"Could not parse distance for {seller_loc}")
                    distances[seller_loc] = float('inf')
        
        return distances

# Global async HTTP client instance
async_http_client = AsyncHTTPClient()