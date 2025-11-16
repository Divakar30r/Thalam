# Keycloak ORDERFORM Client - Role Configuration Guide

## Overview

Based on your codebase analysis, the **ORDERFORM** Keycloak client requires specific roles to control access to order management features.

## Required Roles for ORDERFORM Client

### 1. **ORDER_EDIT** (Primary Role)
- **Purpose**: Allows users to create, edit, and manage orders
- **Permissions**:
  - Create new orders
  - Edit existing orders
  - Submit orders
  - Cancel orders
  - Upload documents
  - Modify product details and preferences

### 2. **ORDER_PROPOSAL** (Secondary Role)
- **Purpose**: Allows users to work with order proposals
- **Permissions**:
  - View orders
  - Propose changes to orders
  - Access proposal workflow features

## Role Validation in Code

### Backend Validation
Location: `server/index.ts:463`

```typescript
const allowedRoles = ['ORDER_EDIT', 'ORDER_PROPOSAL'];
```

The backend checks these roles via:
- **Endpoint**: `/auth/check-order-permission`
- **Method**: Validates against ORDERFORM client roles
- **Checks**: Both token-based (fast) and Admin API (fallback)

### Frontend Validation
Location: `src/pages/Welcome.tsx:91`

```typescript
const allowed = ['ORDER_EDIT', 'ORDER_PROPOSAL'];
```

The frontend validates permissions before showing the "Create / Edit Order" button.

## Additional Role References (Other Clients)

### ORDMGMT Client Roles
Your application also uses the **ORDMGMT** client for authentication. Common roles might include:
- **BUY** - Referenced in Welcome.tsx:59 for showing order creation buttons
- Other application-specific roles

## How to Configure in Keycloak

### Steps to Recreate ORDERFORM Roles:

1. **Login to Keycloak Admin Console**
   - URL: `https://keycloak.drapps.dev/admin`
   - Realm: `OrderMgmt`

2. **Navigate to ORDERFORM Client**
   ```
   Clients → ORDERFORM → Roles tab
   ```

3. **Create Client Roles**

   **Role 1: ORDER_EDIT**
   - Click "Create Role"
   - Role Name: `ORDER_EDIT`
   - Description: `Allows creating and editing orders`
   - Save

   **Role 2: ORDER_PROPOSAL**
   - Click "Create Role"
   - Role Name: `ORDER_PROPOSAL`
   - Description: `Allows working with order proposals`
   - Save

4. **Assign Roles to Users**
   ```
   Users → [Select User] → Role Mappings
   → Client Roles → Select "ORDERFORM"
   → Available Roles → Select ORDER_EDIT and/or ORDER_PROPOSAL
   → Click "Add selected"
   ```

5. **Verify Role Assignment**
   - Test user login
   - Check `/auth/me` endpoint response
   - Verify roles appear in `resource_access.ORDERFORM.roles` in JWT token

## Token Structure

When properly configured, the JWT access token will contain:

```json
{
  "resource_access": {
    "ORDERFORM": {
      "roles": [
        "ORDER_EDIT",
        "ORDER_PROPOSAL"
      ]
    },
    "ORDMGMT": {
      "roles": [
        "BUY",
        // ... other ORDMGMT roles
      ]
    }
  },
  // ... other claims
}
```

## Testing Role Configuration

### 1. Check Token Contents
```bash
# Get access token
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your-user","password":"your-pass"}'

# Decode JWT at jwt.io to verify roles
```

### 2. Test Permission Endpoint
```bash
curl -X GET http://localhost:8002/auth/check-order-permission \
  --cookie "AUTH_SESSION=your-token" \
  -H "Content-Type: application/json"

# Expected response:
{
  "ok": true,
  "allowed": true,
  "roles": ["ORDER_EDIT", "ORDER_PROPOSAL"],
  "source": "token"
}
```

### 3. Check Frontend Access
1. Login to the application
2. Navigate to Welcome screen
3. Verify "Create / Edit Order" button appears (requires ORDER_EDIT or ORDER_PROPOSAL)
4. Click button - should successfully open the order form

## Role Hierarchy & Permissions

### Recommended Role Assignment Strategy:

| User Type | ORDERFORM Roles | ORDMGMT Roles | Access Level |
|-----------|----------------|---------------|--------------|
| **Buyer** | ORDER_EDIT | BUY | Full order creation and editing |
| **Finance Team** | ORDER_PROPOSAL | BUY | Order proposals and review |
| **Approver** | ORDER_PROPOSAL | - | Review proposals only |
| **Viewer** | - | - | Read-only access |

## Environment Configuration

Ensure your environment files have the correct client configuration:

### `.env.development`
```bash
KEYCLOAK_BASE=https://keycloak.drapps.dev
KEYCLOAK_REALM=OrderMgmt
KEYCLOAK_ORDMGMT_CLIENT_ID=ORDMGMT
KEYCLOAK_ORDMGMT_CLIENT_SECRET=lPWIFaUqi6WoTosxT0QEBSAfaCIrxdlv
KEYCLOAK_ORDERFORM_CLIENT_ID=ORDERFORM
KEYCLOAK_ORDERFORM_CLIENT_SECRET=cSKymAkzHP8pnHSYbXwjuXXctXCHnpgh
```

## Troubleshooting

### Issue: "You do not have permission to create/edit orders"

**Possible causes:**
1. User doesn't have ORDER_EDIT or ORDER_PROPOSAL role assigned
2. Roles assigned to wrong client (check it's ORDERFORM, not ORDMGMT)
3. Token doesn't include ORDERFORM client roles

**Solution:**
- Verify role assignment in Keycloak Admin Console
- Check JWT token contents
- Ensure ORDERFORM client is properly configured
- Clear cookies and re-authenticate

### Issue: Roles not appearing in token

**Possible causes:**
1. Client scope not including roles
2. Client mappers not configured
3. Role mappings not saved

**Solution:**
1. Go to ORDERFORM client → Client Scopes
2. Verify "roles" mapper is enabled
3. Check Client Scopes → Evaluate → Select user → View generated token

## Security Notes

1. **Never expose client secrets** in frontend code
2. **ORDERFORM_CLIENT_ID and SECRET** should only be in backend `.env` files
3. Frontend checks permissions via `/auth/check-order-permission` endpoint
4. Backend validates all permissions server-side
5. Use HTTPS in production to protect tokens

## Additional Roles (Optional)

If you need more granular permissions, consider adding:

- **ORDER_VIEW** - Read-only access to orders
- **ORDER_APPROVE** - Approve order proposals
- **ORDER_ADMIN** - Full administrative access
- **ORDER_REPORT** - Generate and view reports

These would need to be added to both Keycloak configuration and the application code validation logic.

## Summary

**Minimum Required Roles for ORDERFORM Client:**
1. ✅ **ORDER_EDIT** - For order creation and editing
2. ✅ **ORDER_PROPOSAL** - For proposal workflow

**Critical Files:**
- `server/index.ts:463` - Backend role validation
- `src/pages/Welcome.tsx:91` - Frontend role validation
- `.env.development` - Client configuration

**Next Steps:**
1. Login to Keycloak Admin Console
2. Navigate to ORDERFORM client → Roles
3. Create ORDER_EDIT and ORDER_PROPOSAL roles
4. Assign roles to appropriate users
5. Test with `/auth/check-order-permission` endpoint
