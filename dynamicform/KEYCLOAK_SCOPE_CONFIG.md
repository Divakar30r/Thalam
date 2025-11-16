# Keycloak Configuration: Include ORDERFORM Roles in Login Token

## Design Pattern
Your application uses a **lazy-load permission check** pattern:
1. User logs in with ORDMGMT client → Gets JWT token (stored in `AUTH_SESSION` cookie)
2. User clicks "Create/Edit Order" button
3. Frontend calls `/auth/check-order-permission`
4. Backend reads **existing token from cookie** → Extracts ORDERFORM roles from `resource_access.ORDERFORM.roles`
5. No Admin API needed!

## Current Problem
The JWT token issued at login **does not contain ORDERFORM client roles**, so the backend has nothing to read. This causes it to fallback to Admin API (which you don't want to use).

## Solution: Configure ORDMGMT Client to Request ORDERFORM Roles

You need to tell Keycloak: "When issuing tokens for ORDMGMT authentication, also include ORDERFORM client roles."

### Step-by-Step Configuration

#### Step 1: Login to Keycloak Admin Console
```
URL: http://localhost:9090/admin
Realm: OrderMgmt
```

#### Step 2: Create a Dedicated Client Scope for ORDERFORM Roles

Navigate to:
```
Client Scopes → Create client scope
```

Configuration:
- **Name:** `orderform-roles`
- **Description:** `Include ORDERFORM client roles in access token`
- **Type:** `Default`
- **Protocol:** `openid-connect`
- **Display on consent screen:** `OFF`
- **Include in token scope:** `ON`

Click **Save**

#### Step 3: Add Role Mapper to the Client Scope

Navigate to:
```
Client Scopes → orderform-roles → Mappers → Create
```

Select mapper type: **User Client Role**

Configuration:
- **Name:** `orderform-client-roles`
- **Client ID:** `ORDERFORM` ← The client whose roles you want to include
- **Token Claim Name:** `resource_access.${client_id}.roles`
- **Claim JSON Type:** `String`
- **Add to ID token:** `OFF`
- **Add to access token:** `ON` ✅ **CRITICAL**
- **Add to userinfo:** `ON`
- **Multivalued:** `ON` ✅ **CRITICAL**

Click **Save**

#### Step 4: Assign Client Scope to ORDMGMT Client

Navigate to:
```
Clients → ORDMGMT → Client scopes
```

Click **Add client scope**:
- Select: `orderform-roles`
- Type: **Default** ← This ensures it's always included
- Click **Add**

#### Step 5: Verify the Configuration

1. **Check that ORDERFORM roles are assigned to your user:**
   ```
   Users → [Your User] → Role mappings → Client roles
   → Select "ORDERFORM" client
   → Verify ORDER_EDIT and/or ORDER_PROPOSAL are assigned
   ```

2. **Logout completely from your app**
   - Clear browser cookies
   - Or use incognito mode

3. **Login again**
   - After login, the new token will include ORDERFORM roles

4. **Inspect the token** (optional):
   - Open DevTools → Application → Cookies
   - Copy `AUTH_SESSION` cookie value
   - Go to https://jwt.io and paste the token
   - Verify you see:
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

#### Step 6: Test the Permission Check

Click "Create/Edit Order" button. The backend should now successfully read roles from the token:

Expected response from `/auth/check-order-permission`:
```json
{
  "ok": true,
  "allowed": true,
  "roles": ["ORDER_EDIT", "ORDER_PROPOSAL"],
  "source": "token"  ← Not "admin"!
}
```

---

## How It Works (Flow Diagram)

### Before Configuration ❌
```
1. User logs in
   ↓
2. Keycloak issues token with ONLY ORDMGMT roles
   {
     "resource_access": {
       "ORDMGMT": { "roles": ["BUY"] }
       // ORDERFORM roles missing!
     }
   }
   ↓
3. User clicks "Create/Edit Order"
   ↓
4. Backend reads token → No ORDERFORM roles found
   ↓
5. Backend tries Admin API → ERROR: no admin credentials
```

### After Configuration ✅
```
1. User logs in
   ↓
2. Keycloak issues token with BOTH client roles
   {
     "resource_access": {
       "ORDMGMT": { "roles": ["BUY"] },
       "ORDERFORM": { "roles": ["ORDER_EDIT"] }  ← Now included!
     }
   }
   ↓
3. User clicks "Create/Edit Order"
   ↓
4. Backend reads token → ORDERFORM roles found!
   ↓
5. Backend returns: { ok: true, allowed: true, source: "token" }
   ↓
6. App opens successfully ✅
```

---

## Backend Code Reference

Your backend correctly implements this pattern in `server/index.ts:465-481`:

```typescript
// Fast path: check token resource_access for the ORDERFORM_CLIENT_ID
const resourceAccess = claims.resource_access || {};
const clientInfo = resourceAccess[ORDERFORM_CLIENT_ID] || {};
const clientRoles = Array.isArray(clientInfo.roles) ? clientInfo.roles.slice() : [];

if (clientRoles.length > 0) {
  // ✅ Roles found in token - no Admin API needed!
  const normalized = clientRoles.map((r: string) => String(r).toUpperCase());
  const allowed = normalized.some((r: string) => allowedRoles.includes(r));
  return res.json({ ok: true, allowed, roles: clientRoles, source: "token" });
}

// ❌ Only reaches here if roles NOT in token
// Fallback to Admin API (which you don't want)
```

---

## Why This Design is Better

**Advantages of your approach:**
- ✅ No Admin API dependency
- ✅ No additional network calls
- ✅ Roles cached in token (fast)
- ✅ Works offline
- ✅ Simpler architecture
- ✅ More secure (principle of least privilege)

**Why the configuration is needed:**
- Keycloak doesn't know automatically which other client roles to include
- You must explicitly configure: "When ORDMGMT authenticates, also include ORDERFORM roles"
- This is done via Client Scopes

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Making it Optional
```
Client Scopes → Add client scope → Type: "Optional"
```
**Problem:** Optional scopes require explicit request in the auth flow. Use **Default** instead.

### ❌ Mistake 2: Wrong Token Claim Name
```
Token Claim Name: "orderform_roles"  ← Wrong!
```
**Correct:**
```
Token Claim Name: "resource_access.${client_id}.roles"
```
This is a special pattern that Keycloak understands.

### ❌ Mistake 3: Not Logging Out
The token is issued at login time. If you configure Keycloak but don't logout/login again, the old token (without ORDERFORM roles) is still being used.

**Solution:** Always logout completely after Keycloak configuration changes.

---

## Troubleshooting

### Issue: Still getting "no admin credentials" error

**Checklist:**
1. ☑ Client scope created with correct mapper
2. ☑ Mapper has "Add to access token" = ON
3. ☑ Mapper has "Multivalued" = ON
4. ☑ Client scope assigned to ORDMGMT as **Default**
5. ☑ User has ORDERFORM roles assigned (ORDER_EDIT or ORDER_PROPOSAL)
6. ☑ Logged out completely and logged back in
7. ☑ Auth backend restarted (`npm run dev:auth`)

### Issue: Roles in token but permission check still fails

Check the token claim structure. It should be:
```json
{
  "resource_access": {
    "ORDERFORM": {
      "roles": ["ORDER_EDIT"]
    }
  }
}
```

If it's under a different path, the mapper's Token Claim Name is wrong.

### Issue: Want to verify without decoding JWT

Add debug logging to your backend temporarily:

```typescript
// In server/index.ts around line 473
const resourceAccess = claims.resource_access || {};
console.log('DEBUG: Full resource_access:', JSON.stringify(resourceAccess, null, 2));
const clientInfo = resourceAccess[ORDERFORM_CLIENT_ID] || {};
console.log('DEBUG: ORDERFORM roles:', clientInfo.roles);
```

Restart backend and check logs when clicking the button.

---

## Summary

**What you need to do:**
1. Configure Keycloak Client Scope to include ORDERFORM roles
2. Assign it to ORDMGMT client as **Default**
3. Logout and login again
4. Test the permission check

**What you DON'T need:**
- ❌ Admin API credentials
- ❌ Admin client configuration
- ❌ Service accounts
- ❌ Code changes

The backend code is already correct. It's purely a Keycloak configuration issue!
