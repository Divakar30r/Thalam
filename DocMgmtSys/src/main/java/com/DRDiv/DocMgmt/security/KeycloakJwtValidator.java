package com.DRDiv.DocMgmt.security;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.spec.RSAPublicKeySpec;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;


@Component
public class KeycloakJwtValidator implements InitializingBean{
    Logger log = LoggerFactory.getLogger(KeycloakJwtValidator.class);

    @Override
    public void afterPropertiesSet() {
        loadPublicKeys();
    }   
     

    @Value("${keycloak.jwt.keycertsurl}")
    private String keycloakcertsurl;
    

    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final Map<String, PublicKey> publicKeyCache = new ConcurrentHashMap<>();

    @PostConstruct
    public void postConstructLoading() {
        loadPublicKeys();
    }

     

    /**
     * Validates the JWT access token
     * @param accessToken JWT token string
     * @return Claims if valid, null if invalid
     */
    public Claims KeyCloakJWTinternalvalidator(String accessToken) {

        System.out.println("KeyCloakJWTinternalvalidator Begin "+ accessToken);
        try {
            // Parse JWT header to get key ID
            String[] tokenParts = accessToken.split("\\.");
            if (tokenParts.length != 3) {
                return null;
            }

            String header = new String(Base64.getUrlDecoder().decode(tokenParts[0]));
            JsonNode headerJson = objectMapper.readTree(header);
            String kid = headerJson.get("kid").asText();

            // Get public key for this key ID
            PublicKey publicKey = publicKeyCache.get(kid);
            if (publicKey == null) {
                // Refresh keys and try again
                loadPublicKeys();
                publicKey = publicKeyCache.get(kid);
                if (publicKey == null) {
                    throw new RuntimeException("Public key not found for kid: " + kid);
                }
            }

            // Validate and parse JWT
            Claims claims = Jwts.parserBuilder()
                    .setSigningKey(publicKey)
                    .build()
                    .parseClaimsJws(accessToken)
                    .getBody();

            // Additional validations
            if (claims.getExpiration().before(new java.util.Date())) {
                throw new RuntimeException("Token expired");
            }

            System.out.println("KeyCloakJWTinternalvalidator");

            return claims;

        } catch (Exception e) {
            System.err.println("Token validation failed: " + e.getMessage());
            return null;
        }
    }

    public Map<String, Object> getJWTClaimsInfo(String accessToken) {
        Claims claims = KeyCloakJWTinternalvalidator(accessToken);
        if (claims == null) {
            return null;
        }

        Map<String, Object> userInfo = new HashMap<>();
        userInfo.put("subject", claims.getSubject());
        userInfo.put("username", claims.get("preferred_username"));
        userInfo.put("email", claims.get("email"));
        userInfo.put("roles", claims.get("realm_access"));
        userInfo.put("clientRoles", claims.get("resource_access"));
        userInfo.put("issuer", claims.getIssuer());
        userInfo.put("expiration", claims.getExpiration());

        return userInfo;
    }
    /**
     * Load public keys from Keycloak certs endpoint
     */
    private void loadPublicKeys() {
        log.info("Cert url "+keycloakcertsurl+ " - ");
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(keycloakcertsurl))
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(request, 
                    HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonNode certsJson = objectMapper.readTree(response.body());
                JsonNode keys = certsJson.get("keys");

                for (JsonNode key : keys) {
                    String kid = key.get("kid").asText();
                    String kty = key.get("kty").asText();
                    
                    if ("RSA".equals(kty)) {
                        PublicKey publicKey = buildRSAPublicKey(
                            key.get("n").asText(),
                            key.get("e").asText()
                        );
                        publicKeyCache.put(kid, publicKey);
                    }
                }
                
                System.out.println("Loaded " + publicKeyCache.size() + " public keys");
            }

        } catch (Exception e) {
            throw new RuntimeException("Failed to load public keys", e);
        }
    }

    /**
     * Build RSA public key from modulus and exponent
     */
    private PublicKey buildRSAPublicKey(String modulus, String exponent) throws Exception {
        byte[] nBytes = Base64.getUrlDecoder().decode(modulus);
        byte[] eBytes = Base64.getUrlDecoder().decode(exponent);

        java.math.BigInteger n = new java.math.BigInteger(1, nBytes);
        java.math.BigInteger e = new java.math.BigInteger(1, eBytes);

        RSAPublicKeySpec spec = new RSAPublicKeySpec(n, e);
        KeyFactory factory = KeyFactory.getInstance("RSA");
        return factory.generatePublic(spec);
    }

    /**
     * Utility method to check if token is valid (boolean response)
     */
    public boolean isTokenValid(String accessToken) {
        return KeyCloakJWTinternalvalidator(accessToken) != null;
    }

    /**
     * Get user info from token claims
     */
    
}