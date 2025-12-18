"""
Configuration file for Google Chat API with Keycloak Workload Identity Federation
"""

# Keycloak Configuration
KEYCLOAK_CONFIG = {
    "server_url": "http://localhost:9090",  # Update with your actual Keycloak server URL
    "realm": "OrderMgmt",  # Update with your actual realm name
    "client_id": "Googlechat-api-client",
    "client_secret": "wqq",  # Replace with actual secret
    "token_endpoint": "http://localhost:9090/realms/OrderMgmt/protocol/openid-connect/token"
}

# Google Cloud Project Configuration
GOOGLE_CLOUD_CONFIG = {
    "project_number": "2112",  # Replace with your GCP project number
    "project_id": "OrderManagement",  # Replace with your GCP project ID
    "service_account_email": "21unning-crane-22-v6.iam.gserviceaccount.com",  # Update with actual SA email
    "workload_identity_pool_id": "keycloak-pool",
    "workload_identity_provider_id": "keycloak",
    "location": "global"
}

# Google Chat API Configuration
GOOGLE_CHAT_CONFIG = {
    "api_endpoint": "https://chat.googleapis.com/v1",
    "user_email": "divakar30@drapps.dev",
    "scopes": [
        "https://www.googleapis.com/auth/chat.bot",
        "https://www.googleapis.com/auth/chat.messages",
        "https://www.googleapis.com/auth/chat.spaces"
    ]
}

# Workload Identity Federation Configuration
WIF_CONFIG = {
    "audience": f"//iam.googleapis.com/projects/{GOOGLE_CLOUD_CONFIG['project_number']}/locations/{GOOGLE_CLOUD_CONFIG['location']}/workloadIdentityPools/{GOOGLE_CLOUD_CONFIG['workload_identity_pool_id']}/providers/{GOOGLE_CLOUD_CONFIG['workload_identity_provider_id']}",
    "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
    "token_url": "https://sts.googleapis.com/v1/token"
}

# File paths
WIF_CONFIG_FILE = "wif-config.json"
CREDENTIALS_FILE = "credentials.json"
