// Development server configuration
export const config = {
  port: 8002,
  keycloak: {
    base: 'https://keycloak.drapps.dev',
    realm: 'OrderMgmt',
  },
  disableJwtVerify: true, // Allow unsigned tokens in dev
  permissionCacheTTL: 120, // seconds
};
