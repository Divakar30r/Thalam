# Google Chat API with Keycloak Workload Identity Federation

This Python application provides integration between Google Chat API and Keycloak using Workload Identity Federation (WIF) for authentication. The setup allows secure access to Google Chat without storing service account keys.

## 🏗️ Architecture Overview

```
Keycloak (drapps.dev) → Workload Identity Federation → Google Cloud → Google Chat API
```

- **User**: divakar30@drapps.dev
- **Domain**: drapps.dev
- **Keycloak Client**: Googlechat-api-client
- **Authentication Flow**: Client Credentials → OIDC Token → Google Access Token

## 📋 Prerequisites

### Google Cloud Setup
1. **Google Cloud Project** with Chat API enabled
2. **Workload Identity Federation** configured
3. **Service Account** with Chat API permissions
4. **IAM Bindings** for Workload Identity

### Keycloak Setup
1. **Keycloak Realm**: OrderMgmt (or your custom realm)
2. **Client**: Googlechat-api-client
3. **Client Credentials** grant type enabled
4. **OIDC Discovery** endpoint available

### Google Workspace Setup
1. **Google Chat API** enabled for the domain
2. **Bot/App** registered in Google Chat
3. **Appropriate scopes** configured

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Settings

Edit `config.py` and update the following placeholders:

```python
# Keycloak Configuration
KEYCLOAK_CONFIG = {
    "server_url": "https://auth.drapps.dev",  # Your Keycloak server
    "realm": "OrderMgmt",                     # Your realm name
    "client_id": "Googlechat-api-client",
    "client_secret": "YOUR_ACTUAL_SECRET",    # Replace with real secret
    "token_endpoint": "https://auth.drapps.dev/realms/OrderMgmt/protocol/openid-connect/token"
}

# Google Cloud Configuration
GOOGLE_CLOUD_CONFIG = {
    "project_number": "123456789012",         # Your GCP project number
    "project_id": "your-project-id",          # Your GCP project ID
    "service_account_email": "googlechat-sa@your-project-id.iam.gserviceaccount.com"
}
```

### 3. Generate WIF Configuration

```bash
python wif_setup.py
```

This creates:
- `wif-config.json` - Workload Identity Federation configuration
- `.env` - Environment variables file

### 4. Test Authentication

```bash
python auth.py
```

### 5. Run Example

```bash
python example.py
```

## 📁 Project Structure

```
GChat/
├── config.py                 # Configuration settings
├── wif_setup.py              # WIF configuration generator
├── auth.py                   # Authentication module
├── google_chat_client.py     # Google Chat API client
├── example.py                # Usage examples
├── requirements.txt          # Python dependencies
├── wif-config.json           # Generated WIF config (auto-created)
├── .env                      # Environment variables (auto-created)
└── README.md                 # This file
```

## 🔧 Configuration Details

### config.py Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `KEYCLOAK_CONFIG.server_url` | Keycloak server URL | `https://auth.drapps.dev` |
| `KEYCLOAK_CONFIG.realm` | Keycloak realm name | `OrderMgmt` |
| `KEYCLOAK_CONFIG.client_id` | Keycloak client ID | `Googlechat-api-client` |
| `KEYCLOAK_CONFIG.client_secret` | Keycloak client secret | `your-secret-here` |
| `GOOGLE_CLOUD_CONFIG.project_number` | GCP project number | `123456789012` |
| `GOOGLE_CLOUD_CONFIG.project_id` | GCP project ID | `your-project-id` |
| `GOOGLE_CLOUD_CONFIG.service_account_email` | Service account email | `googlechat-sa@project.iam.gserviceaccount.com` |

## 🔐 Google Cloud Setup Steps

### 1. Enable APIs

```bash
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
gcloud services enable chat.googleapis.com
```

### 2. Create Service Account

```bash
gcloud iam service-accounts create googlechat-sa \
    --display-name="Google Chat Service Account"
```

### 3. Grant Permissions

```bash
# Grant Chat API permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:googlechat-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/chat.owner"
```

### 4. Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create keycloak-pool \
    --location="global" \
    --display-name="Keycloak Pool"
```

### 5. Create Workload Identity Provider

```bash
gcloud iam workload-identity-pools providers create-oidc keycloak-oidc \
    --location="global" \
    --workload-identity-pool="keycloak-pool" \
    --issuer-uri="https://auth.drapps.dev/realms/OrderMgmt" \
    --attribute-mapping="google.subject=assertion.sub,attribute.client_id=assertion.azp"
```

### 6. Allow Service Account Impersonation

```bash
gcloud iam service-accounts add-iam-policy-binding \
    googlechat-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/keycloak-pool/attribute.client_id/Googlechat-api-client"
```

## 🔧 Keycloak Setup Steps

### 1. Create Client

1. Go to Keycloak Admin Console
2. Select realm "OrderMgmt"
3. Go to Clients → Create Client
4. Set Client ID: `Googlechat-api-client`
5. Enable "Client authentication"
6. Set "Authentication flow" to "Service accounts roles"

### 2. Configure Client

1. Go to Client → Settings
2. Set "Access Type" to "confidential"
3. Enable "Service Accounts Enabled"
4. Set "Valid Redirect URIs" to appropriate values
5. Save configuration

### 3. Get Client Secret

1. Go to Client → Credentials
2. Copy the "Secret" value
3. Update `config.py` with this secret

## 💻 Usage Examples

### Basic Usage

```python
from google_chat_client import GoogleChatClient

# Initialize client
client = GoogleChatClient()

# List spaces
spaces = client.list_spaces()

# Send message
space_name = spaces['spaces'][0]['name']
message = client.create_message(space_name, "Hello from Keycloak!")
```

### Bot Usage

```python
from google_chat_client import GoogleChatBot

# Initialize bot
bot = GoogleChatBot("My Bot")

# Send notification
bot.send_notification_card(
    space_name,
    title="Alert",
    subtitle="System Status",
    message="All systems operational"
)
```

### Advanced Authentication

```python
from auth import KeycloakWIFAuth

# Initialize auth
auth = KeycloakWIFAuth()

# Get access token
token = auth.authenticate()

# Verify authentication
is_valid = auth.verify_authentication()
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check Keycloak client secret in `config.py`
   - Verify Keycloak server URL and realm
   - Ensure WIF configuration is correct

2. **Permission Denied**
   - Verify service account has Chat API permissions
   - Check IAM bindings for Workload Identity
   - Ensure bot is added to Chat spaces

3. **Token Exchange Failed**
   - Verify Workload Identity Pool configuration
   - Check OIDC provider settings
   - Ensure project number is correct

### Debug Steps

```bash
# Test Keycloak token
python -c "from auth import KeycloakWIFAuth; auth = KeycloakWIFAuth(); print(auth.get_keycloak_token())"

# Test WIF setup
python -c "from auth import KeycloakWIFAuth; auth = KeycloakWIFAuth(); print(auth.setup_wif_credentials())"

# Test full authentication
python auth.py
```

### Log Analysis

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### GoogleChatClient Methods

- `list_spaces()` - List available spaces
- `get_space(space_name)` - Get space details
- `create_message(space_name, text)` - Send text message
- `create_card_message(space_name, card_data)` - Send card message
- `list_messages(space_name)` - List messages in space
- `update_message(message_name, text)` - Update message
- `delete_message(message_name)` - Delete message
- `list_members(space_name)` - List space members
- `create_reaction(message_name, emoji)` - Add reaction

### GoogleChatBot Methods

- `send_simple_message(space_name, message)` - Send text
- `send_notification_card(space_name, title, subtitle, message)` - Send notification
- `send_interactive_card(space_name, title, buttons)` - Send interactive card
- `monitor_space(space_name, callback)` - Monitor for new messages

## 🔒 Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Rotate client secrets** regularly
4. **Monitor access logs** in both Keycloak and Google Cloud
5. **Use least privilege** principle for permissions
6. **Enable audit logging** for compliance

## 📄 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues related to:
- **Keycloak**: Check Keycloak logs and configuration
- **Google Cloud**: Review Cloud Console IAM and API settings
- **Authentication**: Run debug scripts and check tokens
- **API Calls**: Review Google Chat API documentation

---

**Note**: Replace all placeholder values in `config.py` with your actual configuration before running the application.