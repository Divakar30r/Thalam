package com.DRDiv.keycloakMicroservice.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.security.oauth2.client.*;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.stereotype.Service;

import com.nimbusds.jwt.JWTParser;
import com.nimbusds.jwt.SignedJWT;

import java.util.HashMap;
import java.util.List;
import java.util.Map;


@Service
public class AccessTokenfunctions {

      
    public List<String> extractRealmRolesforUser(String userAccessToken, String clientId) {
        try {
            SignedJWT jwt = (SignedJWT) JWTParser.parse(userAccessToken);
            Map<String, Object> claims = jwt.getJWTClaimsSet().getClaims();
            List<String> allRoles = new java.util.ArrayList<>();

        // Realm roles
        Map<String, Object> realmAccess = (Map<String, Object>) claims.get("realm_access");
        if (realmAccess != null && realmAccess.containsKey("roles")) {
            Object rolesObj = realmAccess.get("roles");
            if (rolesObj instanceof List<?> rolesList) {
                rolesList.forEach(role -> allRoles.add(role.toString()));
            }
        }

        // Client roles
        Map<String, Object> resourceAccess = (Map<String, Object>) claims.get("resource_access");
        if (resourceAccess != null && resourceAccess.containsKey(clientId)) {
            Map<String, Object> clientRoles = (Map<String, Object>) resourceAccess.get(clientId);
            Object rolesObj = clientRoles.get("roles");
            if (rolesObj instanceof List<?> rolesList) {
                rolesList.forEach(role -> allRoles.add(role.toString()));
            }
        }

        // Group roles (if mapped in token)
        Object groupsObj = claims.get("groups");
        if (groupsObj instanceof List<?> groupsList) {
            groupsList.forEach(group -> allRoles.add(group.toString()));
        }

        // Remove duplicates
        return allRoles.stream().distinct().toList();
        } catch (Exception e) {
            e.printStackTrace();
        }
        return List.of(); // empty list if no roles found
    }   

    public List<String> getRolesFromClientIDAccessToken(String accessToken, String clientId) {
        try {
            SignedJWT jwt = (SignedJWT) JWTParser.parse(accessToken);
            Map<String, Object> claims = jwt.getJWTClaimsSet().getClaims();

            Map<String, Object> resourceAccess = (Map<String, Object>) claims.get("resource_access");
            if (resourceAccess != null && resourceAccess.containsKey(clientId)) {
                Map<String, Object> clientRoles = (Map<String, Object>) resourceAccess.get(clientId);
                Object rolesObj = clientRoles.get("roles");
                if (rolesObj instanceof List<?> rolesList) {
                    return rolesList.stream().map(Object::toString).distinct().toList();
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return List.of(); // empty list if no roles found
    }
}
