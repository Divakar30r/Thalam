# Application Flow & Login Guide

## Official Login Page

**Start URL:** http://localhost:3000

This is your official entry point. The app will:
1. Check if you're authenticated
2. If not → Show clean login page
3. If yes → Show Welcome page

## User Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User visits http://localhost:3000                        │
└────────────────────┬────────────────────────────────────────┘
                     │
              ┌──────┴──────┐
              │             │
         Not logged in   Logged in
              │             │
              ▼             ▼
┌──────────────────────┐  ┌────────────────────────────────┐
│ Login Page           │  │ Welcome Page                   │
│ - Clean design       │  │ - Shows user name & roles      │
│ - "Sign in with      │  │ - Create/Edit Order button     │
│    Keycloak" button  │  │ - Logout button (top-right)    │
└──────┬───────────────┘  └────────┬───────────────────────┘
       │                           │
       │ Click sign in             │ Click Create/Edit Order
       │                           │
       ▼                           ▼
┌──────────────────────┐  ┌────────────────────────────────┐
│ Redirects to         │  │ Permission check:              │
│ /auth/start          │  │ /auth/check-order-permission   │
│ (Keycloak login)     │  └────────┬───────────────────────┘
└──────┬───────────────┘           │
       │                    ┌──────┴──────┐
       ▼                    │             │
┌──────────────────────┐   Has roles  No roles
│ Keycloak Login       │   │             │
│ - Enter credentials  │   ▼             ▼
│ - Redirects back to  │  ┌─────────┐  ┌──────────────┐
│   /auth/callback     │  │ Order   │  │ Error:       │
└──────┬───────────────┘  │ Form    │  │ No permission│
       │                  │ Page    │  └──────────────┘
       │                  │         │
       ▼                  │ Logout  │
┌──────────────────────┐  │ button  │
│ Sets AUTH_SESSION    │  │ (header)│
│ cookie & redirects   │  └─────────┘
│ back to home         │
└──────────────────────┘
```

## Pages

### 1. Login Page (http://localhost:3000)
- **Route:** `/` (when not authenticated)
- **Features:**
  - Clean, centered design
  - Single "Sign in with Keycloak" button
  - No manual redirect needed - just visit the root URL

**What happens when you click "Sign in":**
1. Redirects to `/auth/start?returnTo=http://localhost:3000`
2. Backend initiates PKCE flow with Keycloak
3. User enters credentials in Keycloak
4. Keycloak redirects to `/auth/callback`
5. Backend sets `AUTH_SESSION` cookie
6. User redirected back to Welcome page

### 2. Welcome Page
- **Route:** `/` (when authenticated)
- **Features:**
  - Shows user name and username
  - Lists all user roles
  - "Create/Edit Order" button (if user has ORDER_EDIT or ORDER_PROPOSAL role)
  - "Logout" button in top-right corner

**Logout button:**
- Calls `/auth/logout` endpoint
- Clears all cookies (AUTH_SESSION, AUTH_REFRESH, PKCE_VERIFIER)
- Clears backend permission cache
- Redirects to login page

### 3. Order Form Page (Dynamic Form)
- **Access:** Click "Create/Edit Order" from Welcome page
- **Features:**
  - Full order management interface
  - Header with:
    - "Back to Home" button (returns to Welcome)
    - "Logout" button (clears session and returns to login)
  - Industry selection
  - Product management
  - Delivery date picker
  - Submit/Cancel order buttons

**Header Buttons:**
- **Back to Home:** Returns to Welcome page (stays logged in)
- **Logout:** Clears session and returns to Login page

## Authentication Flow Details

### Login (PKCE + Authorization Code)
```
User → Click "Sign in"
  ↓
Frontend → /auth/start
  ↓
Backend → Generate PKCE verifier & challenge
  ↓
Backend → Redirect to Keycloak /auth endpoint
  ↓
User → Enter credentials in Keycloak
  ↓
Keycloak → Redirect to /auth/callback with code
  ↓
Backend → Exchange code for tokens
  ↓
Backend → Set AUTH_SESSION cookie (HttpOnly)
  ↓
Backend → Redirect to returnTo URL (home page)
  ↓
Frontend → Sees authenticated state → Shows Welcome page
```

### Permission Check (On-Demand)
```
User → Click "Create/Edit Order"
  ↓
Frontend → POST /auth/check-order-permission
  ↓
Backend → Read AUTH_SESSION cookie
  ↓
Backend → Decode JWT token
  ↓
Backend → Look for resource_access.ORDERFORM.roles
  ↓
Backend → Check if ORDER_EDIT or ORDER_PROPOSAL present
  ↓
Backend → Return { ok: true, allowed: true/false }
  ↓
Frontend → If allowed → Open order form
           If not allowed → Show error message
```

### Logout
```
User → Click "Logout"
  ↓
Frontend → POST /auth/logout
  ↓
Backend → Clear AUTH_SESSION cookie
Backend → Clear AUTH_REFRESH cookie
Backend → Clear PKCE_VERIFIER cookie
Backend → Clear permission cache for user
  ↓
Backend → Return { ok: true }
  ↓
Frontend → Redirect to / (login page)
```

## Important Notes

### No Manual Redirects Needed
✅ **Correct:** Just visit `http://localhost:3000`
❌ **Wrong:** Manually navigating to `/auth/start`

The app automatically determines if you're logged in and shows the appropriate page.

### URL Behavior
- Any URL you visit (e.g., `http://localhost:3000/foo`) will:
  - Check authentication
  - Show Login page if not authenticated
  - Show Welcome page if authenticated
  - **Does NOT force redirect to sign-in** for arbitrary URLs

### Cookies Used
- `AUTH_SESSION` - Contains JWT access token (HttpOnly)
- `AUTH_REFRESH` - Refresh token (HttpOnly, optional)
- `PKCE_VERIFIER` - Temporary cookie for PKCE flow (cleared after login)

All cookies are cleared on logout.

### Cache Behavior
Backend caches permission checks for 120 seconds (configurable via `PERMISSION_CACHE_TTL`):
- Keyed by username + client + check type
- Automatically cleared on logout
- Reduces redundant role checks

## Testing the Flow

### 1. Start Fresh
```bash
# Clear browser cookies or use incognito mode
# Visit http://localhost:3000
```

### 2. You Should See
- Login page with "Sign in with Keycloak" button
- No automatic redirects
- Clean, centered design

### 3. After Login
- Welcome page with your name
- List of your roles
- "Create/Edit Order" button (if you have permissions)
- "Logout" button

### 4. Test Logout
- Click "Logout" from Welcome page OR Order form page
- Should return to Login page
- Verify cookies are cleared (DevTools → Application → Cookies)
- Backend logs should show: `[AUTH LOGOUT] ✓ Logout complete`

## Troubleshooting

### "Checking authentication..." shows forever
**Cause:** Backend auth service not running or not responding
**Fix:**
```bash
# Restart auth backend
npm run dev:auth
```

### Login button does nothing
**Cause:** Backend not running on port 8002
**Fix:** Check that `/auth/start` endpoint is accessible:
```bash
curl http://localhost:8002/
# Should return: {"status":"ok","service":"Auth BFF",...}
```

### Logout doesn't clear session
**Cause:** Cookie path mismatch
**Fix:** Backend already configured with `path: '/'` - should work correctly

### User redirected to /auth/start on every page load
**Cause:** This should NOT happen anymore! The app now shows Login page instead.
**Check:** Make sure you're using the updated `src/App.tsx`

## Backend Logs to Watch

### Successful Login
```
[AUTH START] Initiating PKCE flow...
[AUTH START] Return URL: /
[AUTH START] PKCE code_challenge generated
[AUTH START] Redirecting to Keycloak: keycloak.example.com
[AUTH CALLBACK] ✓ Received callback from Keycloak
[AUTH CALLBACK] ✓ Authorization code received
[AUTH CALLBACK] ✓ PKCE verifier retrieved from cookie
[AUTH CALLBACK] Exchanging authorization code for tokens...
[AUTH CALLBACK] ✓ Token exchange successful
[AUTH CALLBACK] ✓✓✓ TOKEN SIGNATURE VERIFIED via JWKS ✓✓✓
[AUTH CALLBACK] ✓✓✓ AUTHENTICATION COMPLETE ✓✓✓
```

### Successful Logout
```
[AUTH LOGOUT] User logging out
[AUTH LOGOUT] Cleared cache for user: testuser@example.com
[AUTH LOGOUT] ✓ Logout complete
```

### Permission Check (Token)
```
[Check shows roles found in token, not using Admin API]
Response: {"ok":true,"allowed":true,"source":"token"}
```

## Summary

**Official Start URL:** http://localhost:3000

**Pages:**
1. Login → Welcome → Order Form
2. Logout button on Welcome and Order Form
3. All cookies and cache cleared on logout
4. No forced redirects - clean page-based navigation

**No more:** Automatic redirects to /auth/start
**Instead:** Clean Login page component renders at root URL
