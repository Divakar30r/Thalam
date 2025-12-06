# Application Constants and Enums

from enum import Enum

class UpdateMode(str, Enum):
    """Update operation modes"""
    REQUEST_SUBMISSIONS = "RequestSubmissions"
    REQUEST_UPDATE = "RequestUpdate"
    REQUEST_FOLLOWUP = "RequestFollowUp"
    REQUEST_FINALISED = "RequestFinalised"
    REQUEST_PAUSED = "RequestPaused"
    PROPOSAL_SUBMISSIONS = "ProposalSubmissions"
    PROPOSAL_UPDATE = "ProposalUpdate"
    PROPOSAL_CLOSED = "ProposalClosed"
    EDIT_LOCK = "EditLock"
    PROPOSAL_LOCK = "ProposalLock"
    USER_EDITS = "UserEdits"

class QueueMessageCode(str, Enum):
    """Queue message codes"""
    NEW = "New"
    CLOSED = "Closed"
    UPDATE = "Update"
    EDIT_LOCK = "EditLock"

class APIEndpoints:
    """API endpoint constants"""
    
    # Order Request endpoints
    ORDER_REQ = "/api/v1/order-req"
    ORDER_REQ_BY_ID = "/api/v1/order-req/{order_req_id}"
    
    # Order Proposal endpoints
    ORDER_PROPOSAL = "/api/v1/order-proposal"
    ORDER_PROPOSAL_BY_ID = "/api/v1/order-proposal/proposal/{proposal_req_id}"
    
    # Seller endpoints
    SELLERS = "/api/v1/sellers"
    
    # Google API endpoints
    GOOGLE_DISTANCE = "/Distance"
    GOOGLE_CHAT_NOTIFY = "/Notify"

class TimeConstants:
    """Time-related constants"""
    
    # Default timeouts in seconds
    HTTP_TIMEOUT = 30
    GRPC_TIMEOUT = 30
    QUEUE_TIMEOUT = 1800  # 30 minutes
    
    # Expiry times in minutes
    ORDER_EXPIRY_MINUTES = 30
    TASK_RESULT_CLEANUP_HOURS = 24
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    BACKOFF_FACTOR = 2.0

class ServiceNames:
    """Service name constants"""
    REQUESTOR = "requestor"
    PROCESSOR = "processor"

class LoggerNames:
    """Logger name constants"""
    KAFKA_CLIENT = "kafka_client"
    HTTP_CLIENT = "http_client"
    ASYNC_HTTP_CLIENT = "async_http_client"
    QUEUE_MANAGER = "queue_manager"
    SYNC_UTILS = "sync_utils"
    GRPC_SERVER = "grpc_server"
    GRPC_CLIENT = "grpc_client"
    ORDER_SERVICE = "order_service"
    PROPOSAL_SERVICE = "proposal_service"
    NOTIFICATION_SERVICE = "notification_service"

# Default configuration values
DEFAULT_CONFIG = {
    "find_max_sellers": 10,
    "max_concurrent_tasks": 10,
    "order_expiry_minutes": 30,
    "grpc_server_port": 50051,
    "grpc_max_workers": 10,
    "http_timeout": 30,
    "log_level": "INFO"
}

# Message templates
MESSAGE_TEMPLATES = {
    "order_submitted": "Order Submitted",
    "order_submission_failure": "Order Submission failure",
    "new_proposal_received": "New Proposal received", 
    "proposal_closed": "Proposal closed",
    "proposal_updates": "Proposal updates",
    "choose_one_proposal": "Choose one proposal",
    "proposal_updates_in_progress": "Proposal updates in progress",
    "proposal_submitted": "Proposal Submitted",
    "proposal_submission_failure": "Proposal Submission failure",
    "order_received": "OrderReqId {order_req_id} received"
}