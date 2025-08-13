package com.DRDiv.DocMgmt.security;

import com.nimbusds.jose.*;
import com.nimbusds.jose.crypto.*;
import com.nimbusds.jose.jwk.source.JWKSource;
import com.nimbusds.jose.jwk.source.RemoteJWKSet;
import com.nimbusds.jose.proc.JWSVerificationKeySelector;
import com.nimbusds.jose.proc.SecurityContext;
import com.nimbusds.jose.util.DefaultResourceRetriever;
import com.nimbusds.jwt.*;
import com.nimbusds.jwt.proc.ConfigurableJWTProcessor;
import com.nimbusds.jwt.proc.DefaultJWTProcessor;

import lombok.val;

import java.io.FileInputStream;
import java.net.URI;
import java.net.URL;
import java.nio.file.*;
import java.security.*;
import java.security.spec.*;
import java.time.Instant;
import java.util.*;

import org.apache.kafka.common.protocol.types.Field.Str;
import org.aspectj.apache.bcel.classfile.annotation.NameValuePair;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.util.ResourceUtils;
import org.springframework.web.client.RestTemplate;

import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Instant;

@Component
public class JwtSigner {

     

    @Autowired
    KeycloakJwtValidator keycloakJwtValidator; 

    @Value("${keycloak.privatekey.keystorepath}")
    private  String privatekeyp12path;

    @Value("${keycloak.privatekey.key-store-password}")
    private  String privatekeyp12pwd;

    @Value("${keycloak.privatekey.keyStoreType}")
    private  String privatekeyStoreType;
    
    @Value("${keycloak.privatekey.keyAlias}")
    private  String privatekeyAlias;

    @Value("${keycloak.auth-server-url}")
    private  String keycloakauthserverurl;
    
    @Value("${keycloak.realm}")
    private  String keycloakrealm;
    
    @Value("${keycloak.client-id}")
    private  String keycloakclientid;

    @Value("${keycloak.token-uri}")
    private String keycloaktokenuri;

    @Value("${keycloak.jwt.algorithm}")
    private String keycloakjwtalgo;

    @Value("${keycloak.jwt.keysource)")
    private String keycloakcertsurl;
    

        public   PrivateKey loadPrivateKeyFromP12() throws Exception {
            System.out.println("Checking props:"+privatekeyp12path + " "+ privatekeyp12pwd);
               KeyStore keyStore = KeyStore.getInstance("PKCS12");
                try (FileInputStream fis = new FileInputStream(ResourceUtils.getFile(privatekeyp12path))) {
                System.out.println("Desc: "+fis.getFD().toString());
                keyStore.load(fis, privatekeyp12pwd.toCharArray());
               }catch(Exception e){ throw e;}
                return (PrivateKey) keyStore.getKey(privatekeyAlias, privatekeyp12pwd.toCharArray());
       }

        public   String generateSignedJwt() throws Exception {
         // Prepare JWT claims
        Instant now = Instant.now();
        JWTClaimsSet claims = new JWTClaimsSet.Builder()
            .issuer(keycloakclientid)
            .subject(keycloakclientid)
            .audience(keycloaktokenuri)
            .issueTime(Date.from(now))
            .expirationTime(Date.from(now.plusSeconds(300)))
            .jwtID(UUID.randomUUID().toString())
            .build();

        // Create signed JWT with PS256
        JWSHeader header = new JWSHeader.Builder(JWSAlgorithm.PS256)
            .type(JOSEObjectType.JWT)
            .build();

        SignedJWT signedJWT = new SignedJWT(header, claims);
        RSASSASigner signer = new RSASSASigner(loadPrivateKeyFromP12());
        signedJWT.sign(signer);

        return signedJWT.serialize();
    }

        public   String sendKeycloak(String serializedsignedJWT){
        
          
       RestTemplate restTemplate = new RestTemplate();

        // Prepare headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        // Prepare body
        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("client_id", keycloakclientid);
        body.add("grant_type", "client_credentials");
        body.add("client_assertion_type",  "urn:ietf:params:oauth:client-assertion-type:jwt-bearer");
        body.add("client_assertion",   serializedsignedJWT);

        HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(body, headers);

        // Send POST request
        ResponseEntity<String> response = restTemplate.postForEntity(keycloaktokenuri, request, String.class);

        return response.getBody();

    }

        public  boolean validateJWTtoken(String bearerToken) {
            
            System.out.println("triggered access token flow for JWT");
            String token = bearerToken.replace("Bearer ", "");
    
            if (keycloakJwtValidator.isTokenValid(token)) {
                // Process valid token
                return true;
            } else {
                // Invalid token - return 401
                return false;
            }
        }
}
