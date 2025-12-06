"""
Role-based permission classes for Keycloak authentication
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
import logging
from typing import List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ServiceAccountMixin:
    """
    Mixin to handle service account detection and user override
    """
    
    def _handle_service_account(self, request):
        """
        Detect service account and override request.user with admin API response
        Returns True if service account was detected and handled, False otherwise
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        # Check if this is a service account request
        current_email = getattr(request.user, 'email', None) or (request.user.get('email') if hasattr(request.user, 'get') else None)
        # print the current email for debugging
        logger.debug(f"Current request user email: {current_email}")
        service_account_email = getattr(settings, 'KEYCLOAK_SERVICE_ACCOUNT_EMAIL', 'sb.docadmin@drworkplace.microsoft.com')

        if current_email == service_account_email:
            try:
                from .service import keycloak_service
                # Get target user email from request context
                target_user_email = self._get_target_user_email(request)

                # Build a proxy 'effective user' rather than mutating request.user (some frameworks
                # expose read-only properties). We'll attach it to request._effective_user and
                # permission checks should read from that when present.
                from types import SimpleNamespace

                if target_user_email:
                    effective_attrs = {}
                    target_user_info = keycloak_service.get_user_info_with_roles_admin(target_user_email)
                    if target_user_info:
                        # Create a SimpleNamespace with fields from admin_user_info and fallback to
                        # original request.user attributes when missing
                        
                        # Copy a few well-known attributes
                        effective_attrs['is_authenticated'] = True
                        effective_attrs['email'] = target_user_info.get('email')
                        effective_attrs['roles'] = target_user_info.get('roles', [])
                        effective_attrs['sub'] = target_user_info.get('sub')
                        effective_attrs['preferred_username'] = target_user_info.get('preferred_username')
                        # include any remaining items for convenience
                        for k, v in target_user_info.items():
                            if k not in effective_attrs:
                                effective_attrs[k] = v


                        #request._effective_user = SimpleNamespace(**effective_attrs)
                        request.user = SimpleNamespace(**effective_attrs)
                        # print request.user
                        logger.info(f"Service account request processed for target user: {target_user_email}")
                        

                
                else: # Service account without specific target user - keep service account privileges
                    
                    
                    effective_attrs = {
                        'is_authenticated': True,
                        'email': service_account_email,
                        'roles': getattr(request.user, 'roles', []),
                        'sub': getattr(request.user, 'sub', None),
                        'preferred_username': getattr(request.user, 'preferred_username', None)
                    }
                request._effective_user = SimpleNamespace(**effective_attrs)
                # print the request
                logger.info(f"Service account request processed with service account privileges: {request._effective_user}")
                
                return True

            except Exception as e:
                logger.error(f"Failed to handle service account request: {e}")
                return False

        return False
        return False
    
    def _get_target_user_email(self, request):
        """
        Extract target user email from request context
        Override in subclasses if needed for specific logic
        """
        # Try to get from query parameters first
        if hasattr(request, 'query_params'):
            # Accept both camelCase and snake_case query parameters
            target_email = request.query_params.get('userEmail') or request.query_params.get('user_email')
            if target_email:
                return target_email
                
        # Try to get from request data
        if hasattr(request, 'data') and request.data:
            # Accept both camelCase and snake_case in request body
            target_email = request.data.get('userEmail') or request.data.get('user_email')
            if target_email:
                return target_email
                
        return None
    
    


class KeycloakRolePermission(BasePermission, ServiceAccountMixin):
    """
    Base permission class that checks Keycloak roles
    """
    required_roles = []  # Override in subclasses
    
    def has_permission(self, request, view):
        """
        Check if user has required roles
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Handle service account detection and user override
        self._handle_service_account(request)
        
        # Use standard frontend user logic pattern
        user_roles = getattr(request.user, 'roles', [])
        
        # If no roles required, just check if authenticated
        if not self.required_roles:
            return True
            
        # Check if user has any of the required roles
        has_role = any(role in user_roles for role in self.required_roles)
        
        if not has_role:
            logger.warning(
                f"User {getattr(request.user, 'username', 'unknown')} "
                f"lacks required roles {self.required_roles}. "
                f"User roles: {user_roles}"
            )
            
        return has_role

    def get_order_interested_roles(self, order_req_id: str) -> Optional[List[str]]:
        """
        Get interested roles for an order request from external API
        
        Args:
            order_req_id: Order request ID
            
        Returns:
            List of interested role strings or None if not found
        """
        try:
            from ..attachments.dbHandling.order_requests_service import order_requests_service
            
            # Get order request data from external API
            order_data = order_requests_service.get_order_request(order_req_id)
            
            if order_data and 'Interested_Roles' in order_data:
                interested_roles = order_data['Interested_Roles']
                if isinstance(interested_roles, list):
                    logger.info(f"Retrieved {len(interested_roles)} interested roles for order: {order_req_id}")
                    return interested_roles
                else:
                    logger.warning(f"Interested_Roles is not a list for order: {order_req_id}")
                    return None
            else:
                logger.info(f"No Interested_Roles found for order: {order_req_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get interested roles for order {order_req_id}: {e}")
            return None


class InterestedRolesAccess(BasePermission, ServiceAccountMixin):
    """
    Permission that checks if user has interested roles for the order or is document owner
    In AND combination with other permissions, allows access if:
    - User has admin access (DOC_VIEWALL or DOC_UPLALL)
    - User's email matches the request userEmail/user_email parameter
    - User has interested roles for the order (checked in has_object_permission)
    """

    def has_permission(self, request, view):
        """
        Basic authentication check and user email matching
        Returns True if authenticated and either:
        - Is admin, OR
        - No userEmail parameter provided (defaults to current user), OR
        - userEmail matches current user's email
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        # Handle service account detection and user override
        self._handle_service_account(request)

        current_user_email = getattr(request.user, 'email', None)
        user_roles = getattr(request.user, 'roles', [])

        # Check if user has admin access (DOC_VIEWALL or DOC_UPLALL)
        if any(role in user_roles for role in ['DOC_VIEWALL', 'DOC_UPLALL']):
            return True

        # Check if userEmail parameter matches current user (or not provided)
        request_user_email = None
        if hasattr(request, 'query_params'):
            request_user_email = request.query_params.get('userEmail') or request.query_params.get('user_email')
        elif hasattr(request, 'data') and request.data:
            request_user_email = request.data.get('userEmail') or request.data.get('user_email')

        # If no userEmail specified in request, allow (defaults to current user)
        if not request_user_email:
            return True

        # If userEmail matches current user, allow
        if request_user_email == current_user_email:
            return True

        # Otherwise deny
        logger.warning(
            f"User {current_user_email} attempted to access documents for {request_user_email}"
        )
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has interested roles for order or is document owner
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        # Handle service account detection and user override
        self._handle_service_account(request)

        current_user_email = getattr(request.user, 'email', None)
        user_roles = getattr(request.user, 'roles', [])

        # Check if user has admin access (DOC_VIEWALL or DOC_UPLALL)
        if any(role in user_roles for role in ['DOC_VIEWALL', 'DOC_UPLALL']):
            logger.debug(f"User has admin access roles: {user_roles}")
            return True

        # Check if user is document owner
        if hasattr(obj, 'user_email') and obj.user_email == current_user_email:
            return True

        # Check interested roles for order
        order_req_id = None
        if hasattr(obj, 'order_req_id'):
            order_req_id = obj.order_req_id
        elif hasattr(request, 'data') and request.data:
            order_req_id = request.data.get('order_req_id') or request.data.get('orderReqId')

        if order_req_id:
            try:
                # Get interested roles for the order
                permission_checker = KeycloakRolePermission()
                interested_roles = permission_checker.get_order_interested_roles(order_req_id)

                if interested_roles:
                    # Check if user has any of the interested roles
                    has_interested_role = any(role in interested_roles for role in user_roles)
                    if has_interested_role:
                        return True

            except Exception as e:
                logger.error(f"Failed to check interested roles for order {order_req_id}: {e}")


        logger.warning(
            f"User {getattr(request.user, 'username', 'unknown')} "
            f"denied access - not document owner and no interested roles for order {order_req_id}"
        )
        return False


class UploadAccess(KeycloakRolePermission):
    """
    Permission for upload operations - requires DOC_UPL or DOC_UPLALL roles
    """
    required_roles = ['DOC_UPL', 'DOC_UPLALL']


class ViewAccess(KeycloakRolePermission):
    """
    Permission for view operations - requires DOC_VIEW or DOC_VIEWALL roles
    """
    required_roles = ['DOC_VIEW', 'DOC_VIEWALL']


class AdminAccess(KeycloakRolePermission):
    """
    Permission for admin operations - requires DOC_UPLALL or DOC_VIEWALL roles
    """
    required_roles = ['DOC_UPLALL', 'DOC_VIEWALL']


class OwnerOrAdminPermission(BasePermission, ServiceAccountMixin):
    """
    Permission that allows access to resource owner or admin/manager roles
    """
    
    def has_permission(self, request, view):
        """Basic authentication check"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Handle service account detection and user override
        self._handle_service_account(request)
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is owner of the object or has admin/manager role
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Handle service account detection and user override
        self._handle_service_account(request)
        
        current_user_email = getattr(request.user, 'email', None)
        current_user_id = getattr(request.user, 'sub', None)
        
        # Use standard frontend user logic pattern
        user_roles = getattr(request.user, 'roles', [])
        
        # Check if user is owner (use email if available, fallback to user_id)
        obj_user_email = getattr(obj, 'user_email', None)
        obj_user_id = getattr(obj, 'user_id', None)
        
        if obj_user_email and obj_user_email == current_user_email:
            return True
        elif obj_user_id and obj_user_id == current_user_id:
            return True
            
        logger.warning(
            f"User {getattr(request.user, 'username', 'unknown')} "
            f"denied access to object owned by {obj_user_email or obj_user_id}"
        )
        return False


class DocumentOwnerPermission(BasePermission, ServiceAccountMixin):
    """
    Permission for document-specific ownership checks
    """
    
    def has_permission(self, request, view):
        """Basic authentication check"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Handle service account detection and user override
        self._handle_service_account(request)
        return True
        
    def check_document_access(self, request, document):
        """
        Check if user can access the document
        Returns True if access allowed, False otherwise
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Handle service account detection and user override
        self._handle_service_account(request)
        
        # Prefer a non-mutating "effective user" if the service-account handler set one.
        eff_user = getattr(request, '_effective_user', None) or getattr(request, 'user', None)

        current_user_email = getattr(eff_user, 'email', None)
        current_user_id = getattr(eff_user, 'sub', None)
        # Use roles from the effective user when present
        user_roles = getattr(eff_user, 'roles', [])

        # Users with global admin/view-all roles may access any document
        if any(r in user_roles for r in ('DOC_VIEWALL', 'DOC_UPLALL')):
            return True

        # Document owner can access (use email if available, fallback to user_id)
        document_user_email = getattr(document, 'user_email', None)
        document_user_id = getattr(document, 'user_id', None)

        if document_user_email and document_user_email == current_user_email:
            return True
        if document_user_id and document_user_id == current_user_id:
            return True

        return False


