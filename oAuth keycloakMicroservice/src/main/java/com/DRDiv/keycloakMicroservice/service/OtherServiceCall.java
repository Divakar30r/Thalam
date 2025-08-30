package com.DRDiv.keycloakMicroservice.service;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.nimbusds.jwt.JWTParser;
import com.nimbusds.jwt.SignedJWT;

import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;

@Service
public class OtherServiceCall {

    RestTemplate rest;
    @Value("${service2.url}")
    private String otherService;

    // generate @value string for property spring.security.oauth2.client.registration.SignedJWTprops.client-id
    @Value("${spring.security.oauth2.client.registration.SignedJWTprops.client-id}")
    private String clientId;

    @Autowired
    private JWTSigner jwtSigner;

    @Autowired
    AccessTokenfunctions accessTokenfunctions;

    public ResponseEntity invokeServerService(){
        
        // For user based access token
        var authentication = SecurityContextHolder.getContext().getAuthentication();
        var jwtSignertoken = jwtSigner.getAccessToken();
        if (authentication instanceof JwtAuthenticationToken jwtAuth) {
              if (jwtSignertoken != null) {
                // compare two List<String> and return matching List
                List<String> userRoles = accessTokenfunctions.extractRealmRolesforUser(jwtAuth.getToken().getTokenValue(), clientId);
                List<String> clientRoles = accessTokenfunctions.getRolesFromClientIDAccessToken(jwtSignertoken, clientId);
                List<String> matchingRoles = userRoles.stream()
                        .filter(clientRoles::contains)
                        .toList();
                if (!matchingRoles.isEmpty()) {
                    return ResponseEntity.ok(jwtSignertoken + "  Matching roles " + matchingRoles.toString() + " User:" + userRoles.toString() + "  Client:" + clientRoles.toString()
                            + " User accesstoken:" + jwtAuth.getToken().getTokenValue() + " Client accesstoken:" + jwtSignertoken
                    );
                } else {

                    return ResponseEntity.ok("No matching roles " + "User:" + userRoles.toString() + "  Client:" + clientRoles.toString()
                            + " User accesstoken:" + jwtAuth.getToken().getTokenValue() + " Client accesstoken:" + jwtSignertoken
                    );

            }
            

        }
           return ResponseEntity.ok("No access token found for client ");

 
    }
 return ResponseEntity.ok("No access token found for  user");
    
}
}

