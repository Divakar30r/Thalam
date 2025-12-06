from typing import List, Dict, Any, Optional
import logging

from shared.models.order_models import ProcessorOrderReqObj
from shared.utils.http_client import HTTPClient

from ..core.config import settings
from ..core.exceptions import SellerSelectionException, ExternalAPIException
 
from .external_api_service import ExternalAPIService

logger = logging.getLogger(__name__)

class SellerService:
    """Service for handling seller selection as per _SelectSellers method"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.external_api_service = ExternalAPIService()
        self.base_url = settings.api_base_url
        self.max_sellers = settings.find_max_sellers
    
    async def select_sellers(self, order_req_id: str, processor_order_req_obj: ProcessorOrderReqObj) -> List[Dict[str, Any]]:
        """
        Implementation of _SelectSellers method from grpcdesign.yaml
        
        Args:
            order_req_id: Order request ID
            processor_order_req_obj: Processor order request object to update
        
        Returns:
            List of selected sellers with SellerID and Distance
        
        Raises:
            SellerSelectionException: If seller selection fails
        """
        try:
            logger.info(f"Selecting sellers for order: {order_req_id}")
            
            # Step 1: Get order details to retrieve industry and requestor email ID
            order_details = await self._get_order_details(order_req_id)
            industry = order_details.get("Industry")
            requestor_email_id = order_details.get("RequestorEmailID")
            
            if not industry or not requestor_email_id:
                raise SellerSelectionException(
                    f"Missing industry or requestor email ID for order: {order_req_id}"
                )
            
            # Step 2: Get buyer terminal location coordinates
            buyer_terminal_coords = await self._get_buyer_location(requestor_email_id)
            
            if not buyer_terminal_coords:
                raise SellerSelectionException(
                    f"Could not retrieve buyer terminal location for order: {order_req_id}"
                )
            
            # Step 3: Get sellers list based on industry with their terminal locations
            sellers_list = await self._get_sellers_by_industry(industry)
            
            if not sellers_list:
                logger.warning(f"No sellers found for industry: {industry}")
                return []
            
            # Step 4: Filter sellers based on terminal proximity with buyer terminal locations
            # and calculate distances using Google Distance Matrix API
            selected_sellers = await self._filter_sellers_by_proximity(
                sellers_list, 
                buyer_terminal_coords
            )
            
            # Step 5: Update ProcessorOrderReqObj.SellersDictArr with max of n entries
            limited_sellers = selected_sellers[:self.max_sellers]
            processor_order_req_obj.seller_dict_arr = limited_sellers
            
            logger.info(f"Selected {len(limited_sellers)} sellers for order: {order_req_id}")
            return limited_sellers
            
        except Exception as e:
            logger.error(f"Error selecting sellers for order {order_req_id}: {str(e)}")
            raise SellerSelectionException(f"Failed to select sellers: {str(e)}")
    
    async def _get_order_details(self, order_req_id: str) -> Dict[str, Any]:
        """
        Get order details through GET /api/v1/order-req/{order-req-id}
        
        Returns:
            Dictionary containing order details as returned by API (with original key names)
        """
        try:
            # http_client.get() is synchronous and already prepends base_url
            # Just pass the endpoint path
            endpoint = f"/api/v1/order-req/{order_req_id}"
            logger.info(f"Fetching order details from endpoint: {endpoint}")
            response = self.http_client.get(endpoint)
            
            if not response:
                raise ExternalAPIException(f"No data returned for order: {order_req_id}")
            
            # Return response as-is without converting keys
            return response
            
        except Exception as e:
            logger.error(f"Error fetching order details for {order_req_id}: {str(e)}")
            raise ExternalAPIException(f"Failed to fetch order details: {str(e)}")
    
    async def _get_buyer_location(self, requestor_email_id: str) -> Optional[List[float]]:
        """
        Get buyer terminal location coordinates
        
        Steps:
        1. Prefix requestor email ID with "BUY_" to create role_id
        2. Call /api/v1/roles/role-id/{role_id}
        3. Extract Location.coordinates from response
        
        Args:
            requestor_email_id: Requestor's email ID
        
        Returns:
            List of coordinates [longitude, latitude] or None if not found
        """
        try:
            # Step 1: Create role_id with BUY_ prefix
            role_id = f"BUY_{requestor_email_id}"
            
            # Step 2: Get buyer role details (synchronous call, no await)
            endpoint = f"/api/v1/roles/role-id/{role_id}"
            print(f"Fetching buyer role details from endpoint: {endpoint}")
            response = self.http_client.get(endpoint)
            
            if not response:
                logger.warning(f"No role data found for buyer: {role_id}")
                return None
            
            # Step 3: Extract Location.coordinates
            location = response.get("Location")
            if not location:
                logger.warning(f"No Location found in buyer role data: {role_id}")
                return None
            
            coordinates = location.get("coordinates")
            if not coordinates or not isinstance(coordinates, list) or len(coordinates) != 2:
                logger.warning(f"Invalid coordinates format for buyer: {role_id}")
                return None
            
            logger.info(f"Retrieved buyer location for {role_id}: {coordinates}")
            return coordinates
            
        except Exception as e:
            logger.error(f"Error fetching buyer location for {requestor_email_id}: {str(e)}")
            return None
    
    async def _get_sellers_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Get sellers list based on industry with location coordinates
        
        Args:
            industry: Industry type to filter sellers
        
        Returns:
            List of seller dictionaries with seller_id and coordinates
        """
        try:
            # Call roles endpoint to get sellers by industry (synchronous, no await)
            endpoint = f"/api/v1/roles/Industry/{industry}"
    
            
            response = self.http_client.get(endpoint)
            
            if not response:
                logger.warning(f"No sellers found for industry: {industry}")
                return []
            
            # Extract sellers from response
            sellers_raw = response if isinstance(response, list) else response.get("sellers", [])
            
            # Process each seller to extract coordinates from Location field
            sellers_list = []
            for seller in sellers_raw:
                #print sellers_raw to debug
                print(f"Seller raw data: {seller}")
                seller_id = seller.get("RoleID")
                location = seller.get("Location")
                
                if not seller_id or not location:
                    logger.warning(f"Skipping seller with missing ID or Location: {seller}")
                    continue
                
                coordinates = location.get("coordinates")
                if not coordinates or not isinstance(coordinates, list) or len(coordinates) != 2:
                    logger.warning(f"Invalid coordinates for seller {seller_id}")
                    continue
                
                sellers_list.append({
                    "seller_id": seller_id,
                    "coordinates": coordinates  # [longitude, latitude]
                })
            
            print(f"Sellers list: {sellers_list}")
            logger.info(f"Found {len(sellers_list)} sellers with valid locations for industry: {industry}")
            return sellers_list
            
        except Exception as e:
            logger.error(f"Error fetching sellers for industry {industry}: {str(e)}")
            raise ExternalAPIException(f"Failed to fetch sellers: {str(e)}")
    
    async def _filter_sellers_by_proximity(
        self, 
        sellers_list: List[Dict[str, Any]], 
        buyer_coords: List[float]
    ) -> List[Dict[str, str]]:
        """
        Filter sellers based on terminal proximity using Google Distance Matrix API
        
        Args:
            sellers_list: List of seller objects with seller_id and coordinates
            buyer_coords: Buyer's terminal location coordinates [longitude, latitude]
        
        Returns:
            List of SellerDictObj with SellerID and Distance
        """
        try:
            selected_sellers = []
            
            # Format buyer coordinates as "lat,lng" string for Google API
            buyer_location_str = f"{buyer_coords[1]},{buyer_coords[0]}"  # latitude,longitude
            
            for seller in sellers_list:
                seller_id = seller.get("seller_id")  # Use lowercase key from sellers_list
                seller_coords = seller.get("coordinates")

                if not seller_id or not seller_coords:
                    logger.warning(f"Skipping seller with missing data: {seller}")
                    continue

                # Remove the prefix "SEL_" from seller_id
                seller_id = seller_id.split("SEL_")[-1]
                
                # Format seller coordinates as "lat,lng" string for Google API
                seller_location_str = f"{seller_coords[1]},{seller_coords[0]}"  # latitude,longitude
                
                # Get distance using Google Distance Matrix API through GBOT
                # Default to 5km if API is unavailable
                try:
                    distance_km = await self.external_api_service.get_distance(
                        origin=buyer_location_str,
                        destination=seller_location_str
                    )
                except Exception as e:
                    logger.warning(
                        f"Google Distance Matrix API unavailable for seller {seller_id}: {str(e)}. "
                        f"Using default distance of 5 km."
                    )
                    distance_km = 5  # Default distance when API is unavailable
                
                # Create SellerDictObj
                seller_dict = {
                    "seller_id": seller_id,
                    "distance": str(distance_km)
                }
                
                selected_sellers.append(seller_dict)
            
            # Sort by distance (ascending) to get closest sellers first
            selected_sellers.sort(key=lambda x: float(x["distance"]))
            
            return selected_sellers
            
        except Exception as e:
            logger.error(f"Error filtering sellers by proximity: {str(e)}")
            raise SellerSelectionException(f"Failed to filter sellers: {str(e)}")
