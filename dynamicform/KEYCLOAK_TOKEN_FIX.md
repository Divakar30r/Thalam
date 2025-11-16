# Fix: ORDERFORM Roles Not in JWT Token

## Problem
The error `"no admin credentials"` occurs because:
1. ORDERFORM client roles are NOT included in the JWT token
2. Backend tries Admin API as fallback but has no admin credentials
3. `/auth/check-order-permission` endpoint fails

## Root Cause
By default, Keycloak only includes the **authenticating client's roles** (ORDMGMT) in the JWT token. Roles from other clients (like ORDERFORM) must be explicitly configured.

## Solution: Configure Keycloak to Include ORDERFORM Roles in Token

### Step 1: Create a Client Scope for ORDERFORM Roles

1. **Login to Keycloak Admin Console**
   - URL: `http://localhost:9090/admin` (or your Keycloak URL)
   - Realm: `OrderMgmt`

2. **Create Client Scope**
   ```
   Client Scopes → Create
   ```
   - **Name:** `orderform-roles`
   - **Description:** `Include ORDERFORM client roles in token`
   - **Type:** `Default`
   - **Protocol:** `openid-connect`
   - **Display on consent screen:** `OFF`
   - **Include in token scope:** `ON`
   - Click **Save**

### Step 2: Add Mapper to Include ORDERFORM Client Roles

1. **Go to the new client scope**
   ```
   Client Scopes → orderform-roles → Mappers tab
   ```

2. **Create Mapper**
   - Click **Add mapper** → **By configuration** → **User Client Role**

   Configure:
   - **Name:** `orderform-client-roles`
   - **Client ID:** `ORDERFORM`
   - **Token Claim Name:** `resource_access.ORDERFORM.roles`
   - **Claim JSON Type:** `String`
   - **Add to ID token:** `OFF`
   - **Add to access token:** `ON` ✅ (IMPORTANT)
   - **Add to userinfo:** `ON`
   - **Multivalued:** `ON` ✅ (IMPORTANT)

   Click **Save**

### Step 3: Assign Client Scope to ORDMGMT Client

Since ORDMGMT is the authentication client, it needs to request the ORDERFORM roles:

1. **Go to ORDMGMT Client**
   ```
   Clients → ORDMGMT → Client Scopes tab
   ```

2. **Add Client Scope**
   - Click **Add client scope**
   - Select `orderform-roles`
   - Choose **Default** (so it's always included)
   - Click **Add**

### Step 4: Verify Configuration

1. **Test the token**
   - Login to your app
   - Open browser DevTools → Application/Storage → Cookies
   - Copy the `AUTH_SESSION` cookie value

2. **Decode the JWT at jwt.io**

   You should see:
   ```json
   {
     "resource_access": {
       "ORDMGMT": {
         "roles": ["BUY", ...]
       },
       "ORDERFORM": {
         "roles": ["ORDER_EDIT", "ORDER_PROPOSAL"]
       }
     }
   }
   ```

### Step 5: Test the Endpoint

```bash
curl http://localhost:8002/auth/check-order-permission \
  --cookie "AUTH_SESSION=your-token"
```

Expected response:
```json
{
  "ok": true,
  "allowed": true,
  "roles": ["ORDER_EDIT", "ORDER_PROPOSAL"],
  "source": "token"  // ← Should be "token", not "admin"
}
```

---

## Alternative Solution: Configure Admin API Access

If you can't modify token configuration, add admin credentials:

### Option A: Create Service Account

1. **Create Admin Client**
   ```
   Clients → Create
   ```
   - **Client ID:** `admin-api-client`
   - **Client Protocol:** `openid-connect`
   - **Access Type:** `confidential`
   - **Service Accounts Enabled:** `ON`
   - **Authorization Enabled:** `OFF`
   - Save

2. **Assign Admin Roles**
   ```
   Clients → admin-api-client → Service Account Roles tab
   ```
   - Client Roles → `realm-management`
   - Assign: `view-users`, `view-clients`, `query-users`, `query-clients`

3. **Get Credentials**
   ```
   Clients → admin-api-client → Credentials tab
   ```
   - Copy the **Secret**

4. **Add to .env.development**
   ```bash
   KEYCLOAK_ADMIN_CLIENT_ID=admin-api-client
   KEYCLOAK_ADMIN_CLIENT_SECRET=<your-secret>
   ```

### Option B: Use Master Realm Admin

**⚠️ Not recommended for production - use for dev only**

```bash
# Add to .env.development
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN_CLIENT_SECRET=<admin-password>
# Or use a pre-generated token
KEYCLOAK_ADMIN_TOKEN=<admin-access-token>
```

---

## Why This Happens

Keycloak's default behavior:
- ✅ Authenticating client roles (ORDMGMT) → **Automatically included**
- ❌ Other client roles (ORDERFORM) → **Not included by default**

This is by design for security - tokens should only contain what's needed.

## Recommended Approach

**Use Solution 1 (Client Scope)**

Why?
- ✅ More secure - tokens only include specific roles needed
- ✅ Faster - no Admin API calls needed
- ✅ Works offline - no dependency on Admin API
- ✅ Better caching - roles in token are cached by backend
- ✅ Industry standard - proper OAuth2/OIDC pattern

---

## Testing Checklist

After applying Solution 1:

- [ ] Client scope `orderform-roles` created
- [ ] Mapper configured for ORDERFORM client roles
- [ ] Client scope assigned to ORDMGMT as **Default**
- [ ] User has ORDER_EDIT or ORDER_PROPOSAL roles assigned
- [ ] Token decoded at jwt.io shows ORDERFORM roles
- [ ] `/auth/check-order-permission` returns `source: "token"`
- [ ] "Create/Edit Order" button works in Welcome screen

## Troubleshooting

### Roles still not in token after configuration

1. **Clear all sessions:**
   ```
   Keycloak Admin → Sessions → [Your User] → Sign out all sessions
   ```

2. **Clear browser cookies and re-login**

3. **Verify mapper configuration:**
   - Token Claim Name must be: `resource_access.ORDERFORM.roles`
   - Multivalued must be ON
   - Add to access token must be ON

### "source": "admin" instead of "token"

This means roles are coming from Admin API, not token. Check:
- Client scope is assigned as **Default**, not **Optional**
- User logged out and back in after config changes
- Token actually contains the roles (decode at jwt.io)

### Backend still tries Admin API

- Restart the auth backend: `npm run dev:auth`
- Check that ORDERFORM_CLIENT_ID is set correctly in .env
- Verify the client ID matches exactly (case-sensitive)
