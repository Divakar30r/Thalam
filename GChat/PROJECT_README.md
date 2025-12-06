# Google Chat API with Keycloak Workload Identity Federation

A complete Python project for integrating Google Chat API with Keycloak authentication using Google Cloud Workload Identity Federation.

## 🏗️ Project Structure

```
GChat/
├── src/
│   └── googlechat_keycloak/         # Main package
│       ├── __init__.py              # Package initialization
│       ├── config.py                # Configuration settings
│       ├── auth.py                  # Authentication module
│       ├── client.py                # Google Chat API client
│       ├── setup.py                 # Setup utilities
│       └── cli.py                   # Command line interface
├── scripts/
│   ├── install.py                   # Installation script
│   ├── setup.bat                    # Windows setup script
│   └── setup.sh                     # Linux/macOS setup script
├── tests/                           # Test files (future)
├── docs/                           # Documentation (future)
├── setup.py                        # Package setup configuration
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── .env                            # Environment variables (auto-generated)
└── wif-config.json                 # WIF configuration (auto-generated)
```

## 🚀 Quick Start (Step-by-Step)

### Step 1: Clone or Download the Project

If you have the project files, navigate to the project directory:

```bash
cd "C:\Users\User\Documents\Myliving\dCent\GChat"
```

### Step 2: Run Setup (Windows)

**Option A: Using Batch Script (Recommended for Windows)**
```bash
scripts\setup.bat
```

**Option B: Manual Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Step 3: Configure the Project

Your configuration is already set in `src/googlechat_keycloak/config.py`:
- ✅ Keycloak Server: `http://localhost:9090`
- ✅ Project Number: `327935197605`
- ✅ Project ID: `OrderManagement`
- ✅ Service Account: `gordersrv@stunning-crane-475702-v6.iam.gserviceaccount.com`

### Step 4: Run Initial Setup

```bash
python -m googlechat_keycloak.setup
```

This will:
- Generate WIF configuration file
- Create environment variables
- Verify your configuration

### Step 5: Test Authentication

```bash
python -m googlechat_keycloak.cli test-auth
```

### Step 6: Run Demo

```bash
python -m googlechat_keycloak.cli demo
```

## 📋 Detailed Setup Instructions

### Prerequisites

1. **Python 3.8+** installed
2. **Keycloak server** running (yours is at localhost:9090)
3. **Google Cloud Project** set up
4. **Workload Identity Federation** configured
5. **Google Chat API** enabled

### Installation Methods

#### Method 1: Automated Setup (Recommended)

```bash
# Windows
scripts\setup.bat

# Linux/macOS  
chmod +x scripts/setup.sh
./scripts/setup.sh
```

#### Method 2: Manual Installation

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install package
pip install -e .

# 5. Run setup
python -m googlechat_keycloak.setup
```

## 🎯 Usage Examples

### Command Line Interface

The package provides a comprehensive CLI:

```bash
# Show help
python -m googlechat_keycloak.cli --help

# Run setup
python -m googlechat_keycloak.cli setup

# Test authentication
python -m googlechat_keycloak.cli test-auth

# List available spaces
python -m googlechat_keycloak.cli list-spaces

# Send a message
python -m googlechat_keycloak.cli send-message SPACE_ID "Hello World!"

# Send a notification card
python -m googlechat_keycloak.cli send-card SPACE_ID --title "Alert" --message "System notification"

# Run interactive demo
python -m googlechat_keycloak.cli demo

# Show configuration
python -m googlechat_keycloak.cli config
```

### Python API Usage

```python
from googlechat_keycloak import GoogleChatClient, GoogleChatBot

# Initialize client
client = GoogleChatClient()

# List spaces
spaces = client.list_spaces()

# Send message
message = client.create_message("spaces/SPACE_ID", "Hello from Python!")

# Use high-level bot interface
bot = GoogleChatBot("My Bot")
bot.send_simple_message("spaces/SPACE_ID", "Hello!")
bot.send_notification_card("spaces/SPACE_ID", "Title", "Subtitle", "Message")
```

## 🔧 Configuration

Your current configuration in `src/googlechat_keycloak/config.py`:

```python
KEYCLOAK_CONFIG = {
    "server_url": "http://localhost:9090",
    "realm": "OrderMgmt",
    "client_id": "Googlechat-api-client",
    "client_secret": "Mrf9htbXFOtfVGj8qdANSmEHEPYEdPMv",
    "token_endpoint": "http://localhost:9090/realms/OrderMgmt/protocol/openid-connect/token"
}

GOOGLE_CLOUD_CONFIG = {
    "project_number": "327935197605",
    "project_id": "OrderManagement", 
    "service_account_email": "gordersrv@stunning-crane-475702-v6.iam.gserviceaccount.com",
    "workload_identity_pool_id": "keycloak-pool",
    "workload_identity_provider_id": "keycloak",
    "location": "global"
}

GOOGLE_CHAT_CONFIG = {
    "api_endpoint": "https://chat.googleapis.com/v1",
    "user_email": "divakar30@drapps.dev",
    "scopes": [
        "https://www.googleapis.com/auth/chat.bot",
        "https://www.googleapis.com/auth/chat.messages", 
        "https://www.googleapis.com/auth/chat.spaces"
    ]
}
```

## 🔐 Google Cloud Setup Required

You need to set up the following in Google Cloud Console:

### 1. Enable APIs

```bash
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
gcloud services enable chat.googleapis.com
```

### 2. Workload Identity Federation

```bash
# Create pool
gcloud iam workload-identity-pools create keycloak-pool \
    --location="global" \
    --display-name="Keycloak Pool"

# Create provider
gcloud iam workload-identity-pools providers create-oidc keycloak \
    --location="global" \
    --workload-identity-pool="keycloak-pool" \
    --issuer-uri="http://localhost:9090/realms/OrderMgmt" \
    --attribute-mapping="google.subject=assertion.sub,attribute.client_id=assertion.azp"

# Allow impersonation
gcloud iam service-accounts add-iam-policy-binding \
    gordersrv@stunning-crane-475702-v6.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/327935197605/locations/global/workloadIdentityPools/keycloak-pool/attribute.client_id/Googlechat-api-client"
```

## 🧪 Testing

### Test Authentication

```bash
python -m googlechat_keycloak.cli test-auth
```

Expected output:
```
🔐 Testing authentication...
Starting authentication flow...
Successfully obtained Keycloak token
Successfully set up WIF credentials
Authentication completed successfully
✓ Authentication successful!
Authentication verification successful
✓ Token verification successful!
```

### Test API Access

```bash
python -m googlechat_keycloak.cli list-spaces
```

Expected output:
```
📋 Listing Google Chat spaces...
Found 3 spaces:
 1. General (ROOM)
 2. Development (ROOM)
 3. Testing (ROOM)
```

## 🚨 Troubleshooting

### Common Issues

1. **Keycloak Connection Failed**
   ```
   Error getting Keycloak token: Connection refused
   ```
   - Ensure Keycloak is running at `http://localhost:9090`
   - Check if the realm "OrderMgmt" exists
   - Verify client credentials

2. **WIF Configuration Error**
   ```
   Error setting up WIF credentials
   ```
   - Run setup: `python -m googlechat_keycloak.cli setup`
   - Check Google Cloud Workload Identity Federation setup
   - Verify project number and service account

3. **Chat API Permission Denied**
   ```
   Authentication verification failed: 403
   ```
   - Ensure service account has Chat API permissions
   - Add bot to at least one Chat space
   - Verify API is enabled in Google Cloud Console

### Debug Mode

Run commands with verbose output:

```bash
python -m googlechat_keycloak.cli --verbose test-auth
python -m googlechat_keycloak.cli --verbose demo
```

### Check Configuration

```bash
python -m googlechat_keycloak.cli config --verbose
```

## 📚 API Reference

### GoogleChatClient

Main client for Google Chat API:

- `list_spaces(page_size=100)` - List available spaces
- `create_message(space_name, text, thread_key=None)` - Send message
- `create_card_message(space_name, card_data, thread_key=None)` - Send card
- `list_messages(space_name, page_size=25)` - List messages
- `update_message(message_name, text)` - Update message
- `delete_message(message_name)` - Delete message
- `list_members(space_name)` - List space members
- `create_reaction(message_name, emoji)` - Add reaction

### GoogleChatBot

High-level bot interface:

- `send_simple_message(space_name, message)` - Send text message
- `send_notification_card(space_name, title, subtitle, message)` - Send notification
- `send_interactive_card(space_name, title, buttons)` - Send interactive card

### KeycloakWIFAuth

Authentication handler:

- `authenticate()` - Complete authentication flow
- `get_keycloak_token()` - Get Keycloak access token
- `get_google_access_token()` - Get Google access token via WIF
- `verify_authentication()` - Test authentication

## 🔄 Development Workflow

### 1. Make Changes

Edit files in `src/googlechat_keycloak/`

### 2. Test Changes

```bash
# Test authentication
python -m googlechat_keycloak.cli test-auth

# Test functionality
python -m googlechat_keycloak.cli demo
```

### 3. Install in Development Mode

```bash
pip install -e .
```

## 📦 Distribution

### Build Package

```bash
python setup.py sdist bdist_wheel
```

### Install from Source

```bash
pip install .
```

## 🔒 Security Notes

- Client secrets are in config files (secure in production)
- WIF eliminates need for service account key files
- Use environment variables for sensitive data
- Rotate secrets regularly
- Monitor access logs

## 📞 Support

### Getting Help

1. **Check logs** with verbose mode: `--verbose`
2. **Verify configuration** with: `cli config`
3. **Test authentication** with: `cli test-auth`
4. **Run diagnostics** with: `cli demo`

### Common Commands Summary

```bash
# Setup and test
python -m googlechat_keycloak.cli setup
python -m googlechat_keycloak.cli test-auth
python -m googlechat_keycloak.cli demo

# Daily usage
python -m googlechat_keycloak.cli list-spaces
python -m googlechat_keycloak.cli send-message SPACE_ID "Hello!"
python -m googlechat_keycloak.cli send-card SPACE_ID --title "Alert"
```

---

**🎉 Your Google Chat + Keycloak integration is ready to use!**