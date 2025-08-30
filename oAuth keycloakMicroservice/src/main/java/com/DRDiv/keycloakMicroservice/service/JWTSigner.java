package com.DRDiv.keycloakMicroservice.service;


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
import org.springframework.boot.ssl.SslBundle;
import org.springframework.boot.ssl.SslBundles;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.oauth2.client.*;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.util.ResourceUtils;
import org.springframework.web.client.RestTemplate;

import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Instant;

    @Component
    public class JWTSigner {

        @Value("${spring.ssl.bundle.jks.privatekeyprops.key.alias}")
        private  String privatekeyAlias;

        @Value("${spring.ssl.bundle.jks.privatekeyprops.key.alias.keystore.password}")
        private  String privatekeyp12pwd;

         @Value("${keycloak.jwt.keysource}")
        private String keycloakcertsurl;

        @Autowired
        ClientRegistration clientRegistration_ClientwithSignedJWT;

        @Autowired
        ClientRegistrationRepository clientRegistrationRepository;

        clientRegistration_ClientwithSignedJWT = clientRegistrationRepository.findByRegistrationId("SignedJWTprops");



        public OAuth2AuthorizedClientService auth2AuthorizedClientService(ClientRegistrationRepository
                                                                                  clientRegistrationRepository){
            return new InMemoryOAuth2AuthorizedClientService(clientRegistrationRepository);
        }

        //  Creating a manager (helps manage token request)

        public OAuth2AuthorizedClientManager auth2AuthorizedClientManager(ClientRegistrationRepository repos, OAuth2AuthorizedClientService clientService) {

            AuthorizedClientServiceOAuth2AuthorizedClientManager manager = new AuthorizedClientServiceOAuth2AuthorizedClientManager(repos, clientService);

            OAuth2AuthorizedClientProvider provider = OAuth2AuthorizedClientProviderBuilder.builder()
                    .clientCredentials(builder -> builder.accessTokenRequestCustomizer(customizer -> {
                        ClientRegistration registration = customizer.getClientRegistration();
                        String jwt = generateClientAssertion(registration, keyPair);

                        customizer.getHeaders().setContentType(MediaType.APPLICATION_FORM_URLENCODED);
                        customizer.getBody().add("client_assertion_type",
                                "urn:ietf:params:oauth:client-assertion-type:jwt-bearer");
                        customizer.getBody().add("client_assertion", jwt);
                    }))
                    .build();



            OAuth2AuthorizedClientProvider provider = OAuth2AuthorizedClientProviderBuilder.builder().clientCredentials().build();
            manager.setAuthorizedClientProvider(provider);
            return manager;
        }

        @Autowired
        OAuth2AuthorizedClientManager oAuth2AuthorizedClientManager1;


        public String retreiver(){
            //keycloakprops is the suffix used in the property
            var authRequest = OAuth2AuthorizeRequest.withClientRegistrationId ("keycloakprops").principal("TEST").build();

            OAuth2AuthorizedClient oAuth2AuthorizedClient =  oAuth2AuthorizedClientManager1.authorize(authRequest);
            return oAuth2AuthorizedClient.getAccessToken().getTokenValue();

        }

        @Bean
        KeyPair jwtSigningKeyPair(SslBundles sslBundles) {
            return sslBundles.getBundle("privatekeyprops")
                    .getStores()
                    .getKeyStore()
                    .getKey(privatekeyAlias,String.);
        }
        /*
        public   PrivateKey loadPrivateKeyFromP12() throws Exception {
            System.out.println("Checking props:"+privatekeyp12path + " "+ privatekeyp12pwd);
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            try (FileInputStream fis = new FileInputStream(ResourceUtils.getFile(privatekeyp12path))) {
                System.out.println("Desc: "+fis.getFD().toString());
                keyStore.load(fis, privatekeyp12pwd.toCharArray());
            }catch(Exception e){ throw e;}
            return (PrivateKey) keyStore.getKey(privatekeyAlias, privatekeyp12pwd.toCharArray());
        }
        */
         */

        public   String generateSignedJwt() throws Exception {
            // Prepare JWT claims
            Instant now = Instant.now();
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
            //RSASSASigner signer = new RSASSASigner(loadPrivateKeyFromP12());
            RSASSASigner signer = new RSASSASigner(jwtSigningKeyPair().getPrivate());
            signedJWT.sign(signer);

            return signedJWT.serialize();
        }

        public   String sendKeycloak(String serializedsignedJWT) {




            RestTemplate restTemplate = new RestTemplate();

            // Prepare headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

            // Prepare body
            MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
            body.add("client_id", keycloakjwtclientid);
            body.add("grant_type", "client_credentials");
            body.add("client_assertion_type",  "urn:ietf:params:oauth:client-assertion-type:jwt-bearer");
            body.add("client_assertion",   serializedsignedJWT);

            HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(body, headers);

            // Send POST request
            ResponseEntity<String> response = restTemplate.postForEntity(keycloaktokenuri, request, String.class);

            return response.getBody();

        }


        /*
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

         */
    }

}
