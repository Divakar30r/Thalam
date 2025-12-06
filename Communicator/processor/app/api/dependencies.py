from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from ..core.config import settings
from ..services import ProposalService, SellerService, NotificationService, ExternalAPIService

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Service dependencies
def get_proposal_service() -> ProposalService:
    """Get proposal service instance"""
    return ProposalService()

def get_seller_service() -> SellerService:
    """Get seller service instance"""
    return SellerService()

def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    return NotificationService()

def get_external_api_service() -> ExternalAPIService:
    """Get external API service instance"""
    return ExternalAPIService()

# Authentication dependency (optional)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from authorization token (placeholder implementation)
    
    Args:
        credentials: HTTP authorization credentials
    
    Returns:
        User information or None if not authenticated
    
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        # For now, allow unauthenticated access
        # In production, you might want to require authentication
        return None
    
    try:
        # Placeholder for token validation
        # In a real implementation, you would:
        # 1. Validate the JWT token
        # 2. Extract user information
        # 3. Check permissions
        
        token = credentials.credentials
        
        # For demo purposes, accept any token that starts with "valid_"
        if token.startswith("valid_"):
            return {
                "user_id": "demo_user",
                "username": "demo",
                "permissions": ["read", "write"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Database dependency (placeholder)
def get_database() -> Generator:
    """
    Get database connection (placeholder)
    
    In a real implementation, this would return a database session
    """
    # Placeholder for database connection
    # In production, you would:
    # 1. Create database session
    # 2. Yield the session
    # 3. Close the session in finally block
    
    try:
        # Mock database connection
        db = {"connection": "mock_db"}
        yield db
    finally:
        # Close database connection
        pass

# Request validation dependencies
def validate_order_req_id(order_req_id: str) -> str:
    """
    Validate order request ID format
    
    Args:
        order_req_id: Order request ID to validate
    
    Returns:
        Validated order request ID
    
    Raises:
        HTTPException: If order request ID is invalid
    """
    if not order_req_id or len(order_req_id.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order request ID cannot be empty"
        )
    
    # Add additional validation rules as needed
    if len(order_req_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order request ID too long"
        )
    
    return order_req_id.strip()

def validate_proposal_id(proposal_id: str) -> str:
    """
    Validate proposal ID format
    
    Args:
        proposal_id: Proposal ID to validate
    
    Returns:
        Validated proposal ID
    
    Raises:
        HTTPException: If proposal ID is invalid
    """
    if not proposal_id or len(proposal_id.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal ID cannot be empty"
        )
    
    # Add additional validation rules as needed
    if len(proposal_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal ID too long"
        )
    
    return proposal_id.strip()

# Configuration dependency
def get_settings() -> dict:
    """
    Get application settings
    
    Returns:
        Dictionary with application settings
    """
    return {
        "api_base_url": settings.api_base_url,
        "grpc_server_host": settings.grpc_server_host,
        "grpc_server_port": settings.grpc_server_port,
        "fastapi_host": settings.fastapi_host,
        "fastapi_port": settings.fastapi_port,
        "find_max_sellers": settings.find_max_sellers,
        "order_expiry_minutes": settings.order_expiry_minutes
    }
