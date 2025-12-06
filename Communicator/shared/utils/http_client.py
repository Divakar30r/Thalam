# Synchronous HTTP Client for $API_BASE_URL requests (CRUD operations)

import requests
import logging
from typing import Dict, Any, Optional, List
from requests.exceptions import RequestException, Timeout, ConnectionError
from ..config import get_settings

logger = logging.getLogger(__name__)

class HTTPClient:
    """Synchronous HTTP client for external API calls"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.base_url = self.settings.api_base_url
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Set timeout
        self.timeout = self.settings.http_timeout
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to API_BASE_URL
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            logger.info(f"{method} {url} - Status: {response.status_code}")
            
            if response.content:
                return response.json()
            return {"success": True}
            
        except Timeout:
            logger.error(f"Timeout for {method} {url}")
        except ConnectionError:
            logger.error(f"Connection error for {method} {url}")
        except RequestException as e:
            logger.error(f"Request failed {method} {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error {method} {url}: {str(e)}")
        
        return None
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Convenience GET method"""
        return self._make_request("GET", url, params=params)
    
    def post(self, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convenience POST method"""
        return self._make_request("POST", url, data=data)
    
    def put(self, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convenience PUT method"""
        return self._make_request("PUT", url, data=data)
    
    def delete(self, url: str) -> Optional[Dict[str, Any]]:
        """Convenience DELETE method"""
        return self._make_request("DELETE", url)
    
    def get_order_request(self, order_req_id: str) -> Optional[Dict[str, Any]]:
        """Get order request details by ID"""
        return self._make_request("GET", f"/api/v1/order-req/{order_req_id}")
    
    def update_order_request_status(
        self, 
        order_req_id: str, 
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Update order request status"""
        data = {"OrderReqStatus": status}
        return self._make_request("PUT", f"/api/v1/order-req/{order_req_id}", data)
    
    def add_follow_up_to_order(
        self, 
        order_req_id: str, 
        NotesData: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Add follow-up notes to order request"""
        return self._make_request("POST", f"/api/v1/order-req/{order_req_id}/notes", NotesData)

    def update_order_proposal_status(
        self, 
        proposal_id: str, 
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Update order proposal status"""
        data = {"status": status}
        return self._make_request("PUT", f"/api/v1/order-proposal", data)
    
    def add_follow_up_to_proposal(
        self, 
        proposal_id: str, 
        ProposalNotesData: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Add follow-up to proposal"""
        return self._make_request("POST", f"/api/v1/order-proposal/{proposal_id}/notes", ProposalNotesData)
    
    def add_user_edits_to_proposal(
        self, 
        proposal_id: str, 
        UserEdits: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Add user edits to proposal"""
        print("UserEdits:", UserEdits)
        return self._make_request("POST", f"/api/v1/order-proposal/{proposal_id}/useredits", UserEdits)

    def get_sellers_by_industry_location(
        self, 
        proposal_id: str, 
        follow_up_id: str
    ) -> Optional[Dict[str, Any]]:
        """Add user edits to proposal"""
        data = {
            "follow_up_id": follow_up_id,
            "added_time": self._get_current_timestamp()
        }
        return self._make_request("PUT", f"/api/v1/order-proposal", data)
    
    def get_sellers_by_industry_location(
        self, 
        industry: str, 
        location: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get sellers by industry and location"""
        params = {"industry": industry, "location": location}
        return self._make_request("GET", "/api/v1/sellers", params=params)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in MongoDB compatible format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

# Global HTTP client instance
http_client = HTTPClient()