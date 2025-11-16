// Production server configuration
export const config = {
  port: parseInt(process.env.PORT || '8002', 10),
  keycloak: {
    base: process.env.KEYCLOAK_BASE || 'https://keycloak.production.com',
    realm: process.env.KEYCLOAK_REALM || 'OrderMgmt',
  },
  disableJwtVerify: false, // Always verify tokens in production
  permissionCacheTTL: parseInt(process.env.PERMISSION_CACHE_TTL || '300', 10), // seconds
};
