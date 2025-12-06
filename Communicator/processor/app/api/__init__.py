from . import v1
from .dependencies import (
    get_proposal_service,
    get_notification_service,
    get_external_api_service,
    get_current_user,
    get_database,
    get_settings,
    validate_order_req_id,
    validate_proposal_id
)

__version__ = "1.0.0"

__all__ = [
    "v1",
    "get_proposal_service",
    "get_notification_service",
    "get_external_api_service",
    "get_current_user",
    "get_database",
    "get_settings",
    "validate_order_req_id",
    "validate_proposal_id"
]