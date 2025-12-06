# 🚀 How to Run the Google Chat Keycloak Integration Project

## 📋 Quick Start Guide

### Option 1: Windows Automated Setup (Recommended)

1. **Open PowerShell** as Administrator in the project directory:
   ```powershell
   cd "C:\Users\User\Documents\Myliving\dCent\GChat"
   ```

2. **Run the setup script**:
   ```powershell
   .\scripts\setup.bat
   ```

3. **Follow the prompts and activate virtual environment**:
   ```powershell
   venv\Scripts\activate
   ```

4. **Run the setup**:
   ```powershell
   python -m googlechat_keycloak.setup
   ```

5. **Test the installation**:
   ```powershell
   python -m googlechat_keycloak.cli demo
   ```

### Option 2: Manual Setup

1. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Run setup**:
   ```powershell
   python -m googlechat_keycloak.setup
   ```

3. **Test authentication**:
   ```powershell
   python -m googlechat_keycloak.cli test-auth
   ```

## 🐳 Docker Setup (Alternative)

### Option 3: Using Docker

1. **Build the Docker image**:
   ```powershell
   docker build -t googlechat-keycloak .
   ```

2. **Run with Docker Compose** (includes Keycloak):
   ```powershell
   docker-compose up -d
   ```

3. **Test the container**:
   ```powershell
   docker exec -it googlechat-keycloak python -m googlechat_keycloak.cli test-auth
   ```

## 🔧 Configuration Check

Your configuration is already set in `src/googlechat_keycloak/config.py`:

- ✅ **Keycloak Server**: `http://localhost:9090`
- ✅ **Realm**: `OrderMgmt`
- ✅ **Client ID**: `Googlechat-api-client`
- ✅ **Client Secret**: `Mrf9htbXFOtfVGj8qdANSmEHEPYEdPMv`
- ✅ **GCP Project**: `OrderManagement` (`327935197605`)
- ✅ **Service Account**: `gordersrv@stunning-crane-475702-v6.iam.gserviceaccount.com`

## 📊 Testing & Verification

### Step 1: Verify Configuration
```powershell
python -m googlechat_keycloak.cli config
```

### Step 2: Test Authentication
```powershell
python -m googlechat_keycloak.cli test-auth
```

### Step 3: List Google Chat Spaces
```powershell
python -m googlechat_keycloak.cli list-spaces
```

### Step 4: Run Full Demo
```powershell
python -m googlechat_keycloak.cli demo
```

## 💬 Using the Application

### Send a Simple Message
```powershell
python -m googlechat_keycloak.cli send-message "spaces/SPACE_ID" "Hello from CLI!"
```

### Send a Notification Card
```powershell
python -m googlechat_keycloak.cli send-card "spaces/SPACE_ID" --title "Alert" --message "System notification"
```
.
### Interactive Python Usage
```python
from googlechat_keycloak import GoogleChatClient, GoogleChatBot

# Initialize client
client = GoogleChatClient()

# List spaces
spaces = client.list_spaces()
print(f"Found {len(spaces.get('spaces', []))} spaces")

# Send message
if spaces.get('spaces'):
    space_id = spaces['spaces'][0]['name']
    message = client.create_message(space_id, "Hello from Python!")
    print("Message sent!")

# Use bot interface
bot = GoogleChatBot("My Bot")
bot.send_notification_card(
    space_id,
    "System Alert",
    "Keycloak Integration",
    "Your integration is working perfectly! 🎉"
)
```

## 🔄 Available CLI Commands

```powershell
# Show all available commands
python -m googlechat_keycloak.cli --help

# Setup and configuration
python -m googlechat_keycloak.cli setup
python -m googlechat_keycloak.cli config

# Authentication testing
python -m googlechat_keycloak.cli test-auth

# Google Chat operations
python -m googlechat_keycloak.cli list-spaces
python -m googlechat_keycloak.cli send-message SPACE_ID "message"
python -m googlechat_keycloak.cli send-card SPACE_ID --title "Title"

# Interactive demo
python -m googlechat_keycloak.cli demo
```

## ⚠️ Prerequisites

### Required Services
1. **Keycloak Server** running at `localhost:9090`
2. **Google Cloud Workload Identity Federation** configured
3. **Google Chat API** enabled
4. **Bot added to Google Chat spaces**

### Google Cloud Setup Commands

If you haven't set up Google Cloud yet:

```bash
# Enable required APIs
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com  
gcloud services enable chat.googleapis.com

# Create Workload Identity Pool
gcloud iam workload-identity-pools create keycloak-pool \
    --location="global" \
    --display-name="Keycloak Pool"

# Create OIDC Provider
gcloud iam workload-identity-pools providers create-oidc keycloak \
    --location="global" \
    --workload-identity-pool="keycloak-pool" \
    --issuer-uri="http://localhost:9090/realms/OrderMgmt" \
    --attribute-mapping="google.subject=assertion.sub,attribute.client_id=assertion.azp"

# Allow service account impersonation
gcloud iam service-accounts add-iam-policy-binding \
    gordersrv@stunning-crane-475702-v6.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/327935197605/locations/global/workloadIdentityPools/keycloak-pool/attribute.client_id/Googlechat-api-client"
```

## 🚨 Troubleshooting

### Common Issues

1. **"Upgrading pip failed" (Safe to ignore)**
   - If you see "Requirement already satisfied: pip" - this is normal
   - The installer now handles this automatically
   - Installation will continue successfully

2. **"Keycloak connection failed"**
   - Ensure Keycloak is running: `http://localhost:9090`
   - Check realm `OrderMgmt` exists
   - Verify client credentials

3. **"WIF configuration error"**
   - Run: `python -m googlechat_keycloak.cli setup`
   - Check Google Cloud setup
   - Verify project numbers match

4. **"Permission denied (403)"**
   - Ensure service account has Chat permissions
   - Add bot to Chat spaces
   - Check API is enabled

### Debug Steps

```powershell
# Enable verbose output
python -m googlechat_keycloak.cli --verbose test-auth

# Check configuration
python -m googlechat_keycloak.cli config --verbose

# Run diagnostics
python -m googlechat_keycloak.cli demo --verbose
```

## 📁 Project Structure Summary

```
GChat/
├── src/googlechat_keycloak/    # Main package
├── scripts/                    # Setup scripts  
├── requirements.txt            # Dependencies
├── setup.py                    # Package setup
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose
└── PROJECT_README.md           # Full documentation
```

## 🎯 Success Indicators

When everything is working, you should see:

```
✓ Authentication successful!
✓ Token verification successful!
✓ Found X spaces
✓ Demo message sent!
✓ Demo card sent!
🎉 Demo completed successfully!
```

---

**🎉 Your Google Chat + Keycloak integration is ready to use!**

For detailed documentation, see `PROJECT_README.md`