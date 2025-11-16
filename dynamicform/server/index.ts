import express from 'express';
import cookieParser from 'cookie-parser';
import axios from 'axios';
import jwt from 'jsonwebtoken';
import jwksRsa from 'jwks-rsa';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

// Load .env and then .env.local (if present) so local dev overrides used by Vite are available to the backend too
dotenv.config();
const localEnv = path.resolve(process.cwd(), '.env.development');
if (fs.existsSync(localEnv)) {
  dotenv.config({ path: localEnv });
}

import crypto from 'crypto';

const app = express();
app.use(express.json());
app.use(cookieParser());

const KEYCLOAK_BASE = process.env.KEYCLOAK_BASE || 'https://keycloak.drapps.dev';
const REALM = process.env.KEYCLOAK_REALM || 'OrderMgmt';
const ORDMGMT_CLIENT_ID = process.env.KEYCLOAK_ORDMGMT_CLIENT_ID;
const ORDMGMT_CLIENT_SECRET = process.env.KEYCLOAK_ORDMGMT_CLIENT_SECRET;
// ORDERFORM_CLIENT_ID is configured below (server-side-only usage)
const ORDERFORM_CLIENT_SECRET = process.env.KEYCLOAK_ORDERFORM_CLIENT_SECRET;
// Optional: comma-separated list of additional Keycloak client IDs whose roles
// we may fetch on-demand via the Admin API. Example: "ORDMGMT""
const MANAGED_CLIENTS = (process.env.KEYCLOAK_MANAGED_CLIENTS || `${ORDMGMT_CLIENT_ID}`).split(',').map(s => s.trim()).filter(Boolean);

// Order form client id (server-side only). Keep this in backend env only.
const ORDERFORM_CLIENT_ID = process.env.KEYCLOAK_ORDERFORM_CLIENT_ID || '';

// Admin credentials (optional). If provided, backend can call Keycloak Admin API to
// fetch role mappings for other clients that are not present in the access token.
const KEYCLOAK_ADMIN_CLIENT_ID = process.env.KEYCLOAK_ADMIN_CLIENT_ID || '';
const KEYCLOAK_ADMIN_CLIENT_SECRET = process.env.KEYCLOAK_ADMIN_CLIENT_SECRET || '';
const KEYCLOAK_ADMIN_TOKEN = process.env.KEYCLOAK_ADMIN_TOKEN || ''; // optional pre-provisioned token

const TOKEN_URL = `${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/token`;
const AUTH_COOKIE = process.env.AUTH_COOKIE_NAME || 'AUTH_SESSION';
const REDIRECT_URI = process.env.KEYCLOAK_REDIRECT_URI || `http://localhost:${process.env.PORT || 8002}/auth/callback`;

// JWKS client for Keycloak public keys
const JWKS_URI = `${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/certs`;
const jwksClient = jwksRsa({
  jwksUri: JWKS_URI,
  cache: true,
  cacheMaxEntries: 5,
  cacheMaxAge: 10 * 60 * 1000, // 10m
});

const DISABLE_JWT_VERIFY = process.env.DISABLE_JWT_VERIFY === 'true';

// Simple in-memory cache to reduce Admin API calls for role/permission checks in dev/prod.
// Keyed by a string (e.g. `${username}|client:${clientId}|check`) -> { expires, value }
const PERMISSION_CACHE_TTL_MS = Number(process.env.PERMISSION_CACHE_TTL || '120') * 1000; // default 120s
const permissionCache: Map<string, { expires: number; value: any }> = new Map();

function cacheGet(key: string) {
  const e = permissionCache.get(key);
  if (!e) return null;
  if (Date.now() > e.expires) {
    permissionCache.delete(key);
    return null;
  }
  return e.value;
}

function cacheSet(key: string, value: any, ttlMs = PERMISSION_CACHE_TTL_MS) {
  permissionCache.set(key, { expires: Date.now() + ttlMs, value });
}

// Health check endpoint
app.get('/', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'Auth BFF',
    endpoints: ['/auth/start', '/auth/callback', '/auth/login', '/auth/me', '/auth/check-role', '/auth/logout']
  });
});

async function verifyToken(token: string | undefined): Promise<any> {
  if (!token) throw new Error('no token');
  if (DISABLE_JWT_VERIFY) {
    // Development mode: decode without verifying signature
    const decoded = jwt.decode(token) as any;
    if (!decoded) throw new Error('invalid token');
    return decoded;
  }

  // Verify signature using jwks-rsa to fetch signing key by kid
  const getKey = (header: any, callback: jwt.SigningKeyCallback) => {
    if (!header || !header.kid) return callback(new Error('No kid in token header'));
    jwksClient.getSigningKey(header.kid, (err, key) => {
      if (err) return callback(err as any);
      const signingKey = (key as any).getPublicKey ? (key as any).getPublicKey() : (key as any).publicKey;
      callback(null, signingKey as string);
    });
  };

  return new Promise((resolve, reject) => {
    jwt.verify(token as string, getKey as any, { algorithms: ['RS256'] }, (err, decoded) => {
      if (err) return reject(err);
      resolve(decoded);
    });
  });
}

app.post('/auth/login', async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ ok: false, message: 'username/password required' });
  }

  try {
    const params = new URLSearchParams();
    params.append('grant_type', 'password');
    params.append('client_id', ORDMGMT_CLIENT_ID);
    params.append('username', username);
    params.append('password', password);
    if (ORDMGMT_CLIENT_SECRET) params.append('client_secret', ORDMGMT_CLIENT_SECRET);

    const tokenResp = await axios.post(TOKEN_URL, params.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const tokenData = tokenResp.data;
    const accessToken = tokenData?.access_token;
    if (!accessToken) {
      return res.status(401).json({ ok: false, message: 'authentication failed', detail: tokenData });
    }

    let claims: any = {};
    try {
      claims = await verifyToken(accessToken);
    } catch (err) {
      // fall back to decode-only in dev mode
      if (DISABLE_JWT_VERIFY) {
        claims = jwt.decode(accessToken) as any;
      } else {
        throw err;
      }
    }
    const usernameClaim = claims.preferred_username || claims.sub;
    const name = claims.name;

    // Set HttpOnly cookies with consistent configuration
    const cookieOptions = {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax' as const,
      path: '/',
    };

    res.cookie(AUTH_COOKIE, accessToken, cookieOptions);
    // Also set access_token cookie for presigned URL service compatibility
    res.cookie('access_token', accessToken, cookieOptions);

    // Note: refresh_token not available in password grant by default
    const refreshToken = tokenData?.refresh_token;
    if (refreshToken) {
      res.cookie('AUTH_REFRESH', refreshToken, cookieOptions);
      res.cookie('refresh_token', refreshToken, cookieOptions);
    }

    return res.json({ ok: true, user: { username: usernameClaim, name } });
  } catch (err: any) {
    const status = err?.response?.status || 500;
    const data = err?.response?.data || err?.message || String(err);
    return res.status(status).json({ ok: false, message: 'authentication failed', detail: data });
  }
});

// === PKCE / Authorization Code flow helpers ===
function base64UrlEncode(buffer: Buffer) {
  return buffer.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function generateCodeVerifier() {
  return base64UrlEncode(crypto.randomBytes(32));
}

function generateCodeChallenge(verifier: string) {
  const hash = crypto.createHash('sha256').update(verifier).digest();
  return base64UrlEncode(hash);
}

// Start OIDC Authorization Code + PKCE flow. Client should redirect user to this endpoint
// optionally with ?returnTo=/app to return after sign-in
app.get('/auth/start', (req, res) => {
  console.log('\n[AUTH START] Initiating PKCE flow...');
  const returnTo = String(req.query.returnTo || '/');
  console.log('[AUTH START] Return URL:', returnTo);
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = generateCodeChallenge(codeVerifier);
  console.log('[AUTH START] PKCE code_challenge generated (verifier stored in cookie)');

  // state: encode returnTo + nonce
  const stateObj = { returnTo, ts: Date.now(), nonce: base64UrlEncode(crypto.randomBytes(8)) };
  const state = base64UrlEncode(Buffer.from(JSON.stringify(stateObj)));

  // Store verifier in secure HttpOnly cookie (short lived)
  res.cookie('PKCE_VERIFIER', codeVerifier, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 5 * 60 * 1000, // 5 minutes
    path: '/auth',
  });

  const authUrl = new URL(`${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/auth`);
  authUrl.searchParams.set('client_id', ORDMGMT_CLIENT_ID);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', 'openid profile email');
  authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('code_challenge', codeChallenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');

  console.log('[AUTH START] Redirecting to Keycloak:', authUrl.hostname);
  return res.redirect(authUrl.toString());
});

// Callback endpoint for OIDC PKCE flow
app.get('/auth/callback', async (req, res) => {
  console.log('\n[AUTH CALLBACK] ✓ Received callback from Keycloak');
  const { code, state } = req.query as any;
  if (!code) {
    console.log('[AUTH CALLBACK] ✗ ERROR: Missing authorization code');
    return res.status(400).send('Missing code');
  }
  console.log('[AUTH CALLBACK] ✓ Authorization code received');

  const codeVerifier = req.cookies['PKCE_VERIFIER'];
  if (!codeVerifier) {
    console.log('[AUTH CALLBACK] ✗ ERROR: PKCE verifier cookie missing');
    return res.status(400).send('PKCE verifier missing (start flow again)');
  }
  console.log('[AUTH CALLBACK] ✓ PKCE verifier retrieved from cookie');

  // decode state
  let returnTo = '/';
  try {
    if (state) {
      const decoded = JSON.parse(Buffer.from(String(state), 'base64').toString('utf8'));
      returnTo = decoded.returnTo || '/';
    }
  } catch (err) {
    // ignore
  }

  try {
    console.log('[AUTH CALLBACK] Exchanging authorization code for tokens...');
    const params = new URLSearchParams();
    params.append('grant_type', 'authorization_code');
    params.append('code', String(code));
    params.append('redirect_uri', REDIRECT_URI);
    params.append('client_id', ORDMGMT_CLIENT_ID);
    params.append('code_verifier', codeVerifier);
    if (ORDMGMT_CLIENT_SECRET) params.append('client_secret', ORDMGMT_CLIENT_SECRET);

    const tokenResp = await axios.post(TOKEN_URL, params.toString(), { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
    console.log('[AUTH CALLBACK] ✓ Token exchange successful');
    const tokenData = tokenResp.data;
    const accessToken = tokenData?.access_token;
    const refreshToken = tokenData?.refresh_token;
    if (!accessToken) {
      console.log('[AUTH CALLBACK] ✗ ERROR: No access token in response');
      return res.status(401).send('Token exchange failed');
    }
    console.log('[AUTH CALLBACK] ✓ Access token received');
    if (refreshToken) console.log('[AUTH CALLBACK] ✓ Refresh token received');

    // Verify token signature now
    console.log('[AUTH CALLBACK] Verifying token signature with JWKS...');
    let claims: any;
    try {
      claims = await verifyToken(accessToken);
      console.log('[AUTH CALLBACK] ✓✓✓ TOKEN SIGNATURE VERIFIED via JWKS ✓✓✓');
      console.log('[AUTH CALLBACK] User:', claims.preferred_username || claims.sub);
    } catch (err) {
      if (DISABLE_JWT_VERIFY) {
        console.log('[AUTH CALLBACK] ⚠ Token verification DISABLED (dev mode) - decoding only');
        claims = jwt.decode(accessToken) as any;
      } else {
        console.log('[AUTH CALLBACK] ✗✗✗ TOKEN VERIFICATION FAILED ✗✗✗');
        throw err;
      }
    }

    // Set cookies (HttpOnly)
    console.log('[AUTH CALLBACK] Setting auth cookies (HttpOnly)...');
    // Cookie options: use 'lax' for same-site, works for localhost cross-port in dev
    const cookieOptions = {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax' as const,
      path: '/',
    };

    res.cookie(AUTH_COOKIE, accessToken, cookieOptions);
    // Also set access_token cookie for presigned URL service compatibility
    res.cookie('access_token', accessToken, cookieOptions);
    if (refreshToken) {
      res.cookie('AUTH_REFRESH', refreshToken, cookieOptions);
      // Also set refresh_token cookie for presigned URL service compatibility
      res.cookie('refresh_token', refreshToken, cookieOptions);
    }

    
    // Clear PKCE_VERIFIER cookie
    res.clearCookie('PKCE_VERIFIER', { path: '/auth' });

    // Redirect back to client
    console.log('[AUTH CALLBACK] ✓✓✓ AUTHENTICATION COMPLETE ✓✓✓');
    console.log('[AUTH CALLBACK] Session established for:', claims.preferred_username || claims.sub);
    console.log('[AUTH CALLBACK] Redirecting to:', returnTo);
    return res.redirect(returnTo as string);
  } catch (err: any) {
    console.error('[AUTH CALLBACK] ✗✗✗ FATAL ERROR ✗✗✗');
    console.error('[AUTH CALLBACK] Error:', err?.response?.data || err.message || err);
    const errorDetail = JSON.stringify(err?.response?.data || { message: err.message || String(err) });
    return res.status(500).send(`Auth callback failed: ${errorDetail}`);
  }
});

app.get('/auth/me', async (req, res) => {
  const token = req.cookies[AUTH_COOKIE];
  if (!token) return res.status(401).json({ error: 'not authenticated' });
  let claims: any;
  try {
    claims = await verifyToken(token);
  } catch (err) {
    if (DISABLE_JWT_VERIFY) {
      claims = jwt.decode(token) as any;
    } else {
      return res.status(401).json({ error: 'invalid token' });
    }
  }

  // Build roles grouped by source: realm and per-client
  const rolesByClient: Record<string, string[]> = {};
  const realmRoles = (claims.realm_access && claims.realm_access.roles) || [];
  rolesByClient['realm'] = Array.isArray(realmRoles) ? realmRoles.slice() : [];

  const resourceAccess = claims.resource_access || {};
  // For initial /auth/me we only include realm roles and roles for the primary client(s)
  for (const clientId of MANAGED_CLIENTS) {
    const clientInfo = resourceAccess[clientId] || {};
    rolesByClient[clientId] = Array.isArray(clientInfo.roles) ? clientInfo.roles.slice() : [];
  }

  // Keep a legacy flat array for backward compatibility (combines realm + primary client roles)
  const flattened: string[] = [];
  if (rolesByClient['realm'] && rolesByClient['realm'].length) flattened.push(...rolesByClient['realm']);
  for (const c of MANAGED_CLIENTS) {
    const cr = rolesByClient[c] || [];
    for (const r of cr) flattened.push(`${c}:${r}`);
  }

  const user = {
    username: claims.preferred_username || claims.sub,
    name: claims.name,
    // legacy: flat list (realm + primary client roles)
    roles: flattened,
    // structured: roles organized by client (realm + per-client arrays)
    roles_by_client: rolesByClient,
  };
  return res.json({ user });
});


// --- Helpers to call Keycloak Admin API on-demand ---
const KC_ADMIN_BASE = `${KEYCLOAK_BASE}/admin/realms/${REALM}`;

async function getAdminAccessToken(): Promise<string> {
  if (KEYCLOAK_ADMIN_TOKEN) return KEYCLOAK_ADMIN_TOKEN;
  if (!KEYCLOAK_ADMIN_CLIENT_ID || !KEYCLOAK_ADMIN_CLIENT_SECRET) throw new Error('no admin credentials');

  const params = new URLSearchParams();
  params.append('grant_type', 'client_credentials');
  params.append('client_id', KEYCLOAK_ADMIN_CLIENT_ID);
  params.append('client_secret', KEYCLOAK_ADMIN_CLIENT_SECRET);

  const resp = await axios.post(`${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/token`, params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return resp.data.access_token;
}

async function findUserIdByUsername(adminToken: string, username: string): Promise<string | null> {
  const resp = await axios.get(`${KC_ADMIN_BASE}/users`, { params: { username }, headers: { Authorization: `Bearer ${adminToken}` } });
  if (Array.isArray(resp.data) && resp.data.length > 0) return resp.data[0].id;
  return null;
}

async function findClientUuid(adminToken: string, clientId: string): Promise<string | null> {
  const resp = await axios.get(`${KC_ADMIN_BASE}/clients`, { params: { clientId }, headers: { Authorization: `Bearer ${adminToken}` } });
  if (Array.isArray(resp.data) && resp.data.length > 0) return resp.data[0].id;
  return null;
}

async function getUserClientRolesViaAdmin(adminToken: string, userId: string, clientUuid: string): Promise<string[]> {
  const resp = await axios.get(`${KC_ADMIN_BASE}/users/${userId}/role-mappings/clients/${clientUuid}`, { headers: { Authorization: `Bearer ${adminToken}` } });
  if (!Array.isArray(resp.data)) return [];
  return resp.data.map((r: any) => r.name).filter(Boolean);
}

// List managed clients configured in the backend
app.get('/auth/clients', (req, res) => {
  return res.json({ clients: MANAGED_CLIENTS });
});

// Fetch roles for a specific client on-demand. First try to read from token claims
// (fast path). If not present and admin credentials are configured, call the
// Keycloak Admin API to fetch the user's role mappings for that client.
app.get('/auth/me/client/:clientId', async (req, res) => {
  const clientId = String(req.params.clientId || '');
  if (!clientId) return res.status(400).json({ ok: false, message: 'clientId required' });

  const token = req.cookies[AUTH_COOKIE];
  if (!token) return res.status(401).json({ ok: false, message: 'not authenticated' });

  let claims: any;
  try {
    claims = await verifyToken(token);
  } catch (err) {
    if (DISABLE_JWT_VERIFY) claims = jwt.decode(token) as any;
    else return res.status(401).json({ ok: false, message: 'invalid token' });
  }

  // Try fast path: roles present in access token under resource_access
  const username = claims.preferred_username || claims.sub;
  const cacheKey = `${username}|client:${clientId}|roles`;
  const cached = cacheGet(cacheKey);
  if (cached) {
    return res.json({ ok: true, client: clientId, roles: cached.roles, source: 'cache' });
  }

  // Try fast path: roles present in access token under resource_access
  const resourceAccess = claims.resource_access || {};
  const clientInfo = resourceAccess[clientId] || {};
  const clientRoles = Array.isArray(clientInfo.roles) ? clientInfo.roles.slice() : [];
  if (clientRoles.length > 0) {
    // cache token-derived roles briefly
    try { cacheSet(cacheKey, { roles: clientRoles }); } catch (e) { /* ignore cache errors */ }
    return res.json({ ok: true, client: clientId, roles: clientRoles, source: 'token' });
  }

  // If no roles in token, and we have admin creds, call admin API
  try {
    const adminToken = await getAdminAccessToken();
    const username = claims.preferred_username || claims.sub;
    const userId = await findUserIdByUsername(adminToken, username);
    if (!userId) return res.status(404).json({ ok: false, message: 'user not found in Keycloak' });
    const clientUuid = await findClientUuid(adminToken, clientId);
    if (!clientUuid) return res.status(404).json({ ok: false, message: 'client not found in Keycloak' });
  const roles = await getUserClientRolesViaAdmin(adminToken, userId, clientUuid);
  try { cacheSet(cacheKey, { roles }); } catch (e) { /* ignore */ }
  return res.json({ ok: true, client: clientId, roles, source: 'admin' });
  } catch (err: any) {
    console.warn('fetch client roles via admin failed:', err?.message || err);
    return res.status(500).json({ ok: false, message: 'failed to fetch roles', detail: err?.message || String(err) });
  }
});

// Check whether the current user has order-edit permissions on the configured order form client.
// This endpoint uses the backend-configured KEYCLOAK_ORDERFORM_CLIENT_ID and does not require
// the frontend to know the client id.
app.get('/auth/check-order-permission', async (req, res) => {
  if (!ORDERFORM_CLIENT_ID) return res.status(500).json({ ok: false, message: 'order form client not configured on server' });
  const token = req.cookies[AUTH_COOKIE];
  if (!token) return res.status(401).json({ ok: false, message: 'not authenticated' });

  let claims: any;
  try {
    claims = await verifyToken(token);
  } catch (err) {
    if (DISABLE_JWT_VERIFY) claims = jwt.decode(token) as any;
    else return res.status(401).json({ ok: false, message: 'invalid token' });
  }

  const allowedRoles = ['ORDER_EDIT', 'ORDER_PROPOSAL'];

  // Fast path: check token resource_access for the ORDERFORM_CLIENT_ID
  const username = claims.preferred_username || claims.sub;
  const cacheKey = `${username}|client:${ORDERFORM_CLIENT_ID}|check-order`;
  const cached = cacheGet(cacheKey);
  if (cached) {
    return res.json({ ok: true, allowed: cached.allowed, roles: cached.roles, source: 'cache' });
  }

  const resourceAccess = claims.resource_access || {};
  const clientInfo = resourceAccess[ORDERFORM_CLIENT_ID] || {};
  const clientRoles = Array.isArray(clientInfo.roles) ? clientInfo.roles.slice() : [];
  if (clientRoles.length > 0) {
    const normalized = clientRoles.map((r: string) => String(r).toUpperCase());
    const allowed = normalized.some((r: string) => allowedRoles.includes(r));
    try { cacheSet(cacheKey, { allowed, roles: clientRoles }); } catch (e) { /* ignore */ }
    return res.json({ ok: true, allowed, roles: clientRoles, source: 'token' });
  }

  // Fallback: use Admin API if configured
  try {
    const adminToken = await getAdminAccessToken();
    const username = claims.preferred_username || claims.sub;
    const userId = await findUserIdByUsername(adminToken, username);
    if (!userId) return res.status(404).json({ ok: false, message: 'user not found in Keycloak' });
    const clientUuid = await findClientUuid(adminToken, ORDERFORM_CLIENT_ID);
    if (!clientUuid) return res.status(404).json({ ok: false, message: 'client not found in Keycloak' });
  const roles = await getUserClientRolesViaAdmin(adminToken, userId, clientUuid);
  const normalized = roles.map(r => String(r).toUpperCase());
  const allowed = normalized.some(r => allowedRoles.includes(r));
  try { cacheSet(cacheKey, { allowed, roles }); } catch (e) { /* ignore */ }
  return res.json({ ok: true, allowed, roles, source: 'admin' });
  } catch (err: any) {
    console.warn('check-order-permission failed via admin:', err?.message || err);
    return res.status(500).json({ ok: false, message: 'failed to verify permissions', detail: err?.message || String(err) });
  }
});

app.get('/auth/check-role', async (req, res) => {
  const client = String(req.query.client || '');
  const contains = String(req.query.contains || '');
  const token = req.cookies[AUTH_COOKIE];
  if (!token) return res.status(401).json({ ok: false, message: 'not authenticated' });
  let claims: any;
  try {
    claims = await verifyToken(token);
  } catch (err) {
    if (DISABLE_JWT_VERIFY) {
      claims = jwt.decode(token) as any;
    } else {
      return res.status(401).json({ ok: false, message: 'invalid token' });
    }
  }

  const resourceAccess = claims.resource_access || {};
  const clientRoles = (client && resourceAccess[client] && resourceAccess[client].roles) || [];

  let ok = false;
  if (contains) {
    ok = Array.isArray(clientRoles) && clientRoles.some((r: string) => r.includes(contains));
  } else {
    ok = Array.isArray(clientRoles) && clientRoles.length > 0;
  }

  return res.json({ ok, client_roles: clientRoles });
});

app.post('/auth/logout', (req, res) => {
  console.log('[AUTH LOGOUT] User logging out');

  // Get token for Keycloak logout
  const token = req.cookies[AUTH_COOKIE];
  let keycloakLogoutUrl = null;

  if (token) {
    try {
      const claims = jwt.decode(token) as any;
      if (claims) {
        const username = claims.preferred_username || claims.sub;

        // Clear all cache entries for this user
        for (const [key] of permissionCache.entries()) {
          if (key.startsWith(`${username}|`)) {
            permissionCache.delete(key);
          }
        }
        console.log('[AUTH LOGOUT] Cleared cache for user:', username);

        // Build Keycloak logout URL to end SSO session
        const logoutEndpoint = `${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/logout`;
        const redirectUri = encodeURIComponent(req.query.returnTo as string || 'http://localhost:3000');
        keycloakLogoutUrl = `${logoutEndpoint}?redirect_uri=${redirectUri}`;
      }
    } catch (err) {
      console.warn('[AUTH LOGOUT] Cache cleanup warning:', err);
    }
  }

  // Clear all auth-related cookies
  res.clearCookie(AUTH_COOKIE, { path: '/' });
  res.clearCookie('AUTH_REFRESH', { path: '/' });
  res.clearCookie('PKCE_VERIFIER', { path: '/auth' });
  // Also clear presigned URL service cookies
  res.clearCookie('access_token', { path: '/' });
  res.clearCookie('refresh_token', { path: '/' });

  console.log('[AUTH LOGOUT] ✓ Logout complete');

  // Return Keycloak logout URL so frontend can redirect
  res.json({
    ok: true,
    message: 'Logged out successfully',
    keycloakLogoutUrl
  });
});

const port = Number(process.env.PORT || 8002);

// Startup debug: print Keycloak-related configuration so we can diagnose missing client ids
console.log('[AUTH BFF] Starting with configuration:');
console.log('  KEYCLOAK_BASE=', KEYCLOAK_BASE);
console.log('  REALM=', REALM);
console.log('  ORDMGMT_CLIENT_ID=', ORDMGMT_CLIENT_ID || '(not set)');
console.log('  ORDERFORM_CLIENT_ID=', ORDERFORM_CLIENT_ID || '(not set)');
app.listen(port, () => console.log(`Auth BFF listening on http://0.0.0.0:${port}`));

export default app;
