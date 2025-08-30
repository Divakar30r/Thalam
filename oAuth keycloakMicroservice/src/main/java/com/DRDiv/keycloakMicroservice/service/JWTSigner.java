package com.DRDiv.keycloakMicroservice.service;


import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
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

import com.nimbusds.oauth2.sdk.auth.PrivateKeyJWT;
 
import java.io.FileInputStream;
import java.net.URI;
import java.net.URL;
import java.nio.file.*;
import java.security.*;
import java.security.spec.*;
import java.time.Instant;
import java.util.*;


import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ssl.NoSuchSslBundleException;
import org.springframework.boot.ssl.SslBundle;
import org.springframework.boot.ssl.SslBundles;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.*;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.web.DefaultOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.web.OAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.OAuth2AuthorizationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.endpoint.OAuth2AccessTokenResponse;
import org.springframework.security.oauth2.core.endpoint.OAuth2ParameterNames;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
 
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

    @Component
    public class JWTSigner {

        @Value("${spring.ssl.bundle.jks.privatekeyprops.key.alias}")
        private  String privatekeyAlias;

        @Value("${spring.ssl.bundle.jks.privatekeyprops.keystore.password}")
        private  String privatekeyp12pwd;

         @Value("${spring.ssl.bundle.jks.privatekeyprops.keystore.location}")
        private String keycloakcertsurl;
         
        private ClientRegistrationRepository clientRegistrationRepository;

        @Autowired
        private OAuth2AuthorizedClientRepository authorizedClientRepository;

        @Autowired
        private OAuth2AuthorizedClientManager authorizedClientManager;

        @Autowired
        SslBundles sslBundles;

        public JWTSigner(ClientRegistrationRepository clientRegistrationRepository) {
            this.clientRegistrationRepository = clientRegistrationRepository;
            
        }
        

        
        @Bean
        PrivateKey jwtSigningKey() throws UnrecoverableKeyException, KeyStoreException, NoSuchAlgorithmException, NoSuchSslBundleException {
                 
                 return (PrivateKey) sslBundles.getBundle("privatekeyprops")
                        .getStores()
                        .getKeyStore()
                        .getKey("imapi-gateway", "killer".toCharArray());
        }

         
         
        public  String generateSignedJwt() throws Exception {

            // Prepare JWT claims
            Instant now = Instant.now();
            ClientRegistration clientRegistration_ClientwithSignedJWT = clientRegistrationRepository.findByRegistrationId("SignedJWTprops");

            JWTClaimsSet claims = new JWTClaimsSet.Builder()
                    .issuer(clientRegistration_ClientwithSignedJWT.getClientId())
                    .subject(clientRegistration_ClientwithSignedJWT.getClientId())
                    .audience(clientRegistration_ClientwithSignedJWT.getProviderDetails().getTokenUri())
                    .issueTime(Date.from(now))
                    .expirationTime(Date.from(now.plusSeconds(300)))
                    .jwtID(UUID.randomUUID().toString())
                    .build();

            // Create signed JWT with PS256
            JWSHeader header = new JWSHeader.Builder(JWSAlgorithm.PS256)
                    .type(JOSEObjectType.JWT)
                    .build();

            SignedJWT signedJWT = new SignedJWT(header, claims);
            RSASSASigner signer = new RSASSASigner(jwtSigningKey());
            signedJWT.sign(signer);

            System.out.println("Serialized JWT " + signedJWT.serialize());
            return signedJWT.serialize();
        }

    public String getAccessToken() {
        
        ClientRegistration clientRegistration_ClientwithSignedJWT = clientRegistrationRepository.findByRegistrationId("SignedJWTprops");

        RestTemplate restTemplate = new RestTemplate();
        try {
            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

            // Prepare body
            MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
            body.add("client_id", clientRegistration_ClientwithSignedJWT.getClientId());
            body.add("grant_type", "client_credentials");
            body.add("client_assertion_type",  "urn:ietf:params:oauth:client-assertion-type:jwt-bearer");
            body.add("client_assertion",   generateSignedJwt());

            HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(body, headers);

            // Send POST request
            ResponseEntity<String> response = restTemplate.postForEntity(clientRegistration_ClientwithSignedJWT.getProviderDetails().getTokenUri(), request, String.class);
            System.out.println("Response: " + response.getBody());
            ObjectMapper mapper = new ObjectMapper();
            JsonNode node = mapper.readTree(response.getBody());
            return node.has("access_token") ? node.get("access_token").asText() : null;
        }catch(Exception e){
            e.printStackTrace();
            return null;
        }
    }
    
}
