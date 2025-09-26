package com.example.signup.service;

import com.example.signup.dto.SignupRequest;
import com.example.signup.dto.CreateGroupRequest;
import com.example.signup.dto.LinkUserRequest;
// ...existing imports...
import lombok.RequiredArgsConstructor;


import org.keycloak.admin.client.Keycloak;
import org.keycloak.admin.client.KeycloakBuilder;
import org.keycloak.admin.client.resource.RealmResource;
import org.keycloak.admin.client.resource.UsersResource;
import org.keycloak.admin.client.resource.RolesResource;
import org.keycloak.admin.client.resource.ClientsResource;
import org.keycloak.representations.idm.ClientRepresentation;
import org.keycloak.representations.idm.RoleRepresentation;
import org.keycloak.representations.idm.CredentialRepresentation;
import org.keycloak.representations.idm.UserRepresentation;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import com.example.signup.exception.AlreadyExistsException;
import jakarta.ws.rs.core.Response;
import java.util.*;
import java.util.stream.Collectors;
import com.example.signup.dto.DelinkUserRequest;

@Service
@RequiredArgsConstructor
public class SignupService {

    // Simplified configuration (legacy keycloak.* adapter removed)
    @Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}") private String issuerUri; // http://host:port/realms/<realm>
    @Value("${provision.admin.client-id}") private String adminClientId; // admin client (admin-cli or service acct)
    @Value("${provision.admin.client-secret}") private String adminClientSecret;
    @Value("${provision.admin.realm}") private String adminRealm; // realm where admin client resides (master or managed realm)
    @Value("${provision.admin.grant-type:client_credentials}") private String admingrantType; // usually client_credentials
    // Application client whose roles are assigned to new users (use the standard Spring registration client id)    
    @Value("${provision.managed.realm:${PROVISION_MANAGED_REALM:TeamMgmt}}") private String managedRealm; // target realm for users/groups
    @Value("${provision.default.realm-roles}") private String defaultRealmRolesCsv;
    
    @Value("${provision.fail-if-exists}") private boolean failIfExists;
    @Value("${provision.email-verified}") private boolean emailVerified;
    @Value("${provision.user-enabled}") private boolean userEnabled;
    @Value("${provision.fail-if-group-exists}") private boolean failIfGroupExists;
    @Value("${provision.group.name.pattern}") private String groupNamePattern;

    @Value("${spring.security.oauth2.client.registration.keycloak.client-id}") private String registrationClientId;
    @Value("${registration.client.default-roles:${REGISTRATION_CLIENT_DEFAULT_ROLES:}}") private String newClientRolesCsv;
     
    // No transactional logic needed
    public void signup(SignupRequest request) {
        System.out.println("Signup request received for email: " + request.getEmail());
    Keycloak keycloak = buildAdministrativeKeycloak();
    RealmResource realmResource = keycloak.realm(managedRealm);
        UsersResource users = realmResource.users();
        String email = request.getEmail();

        if (!users.search(email, true).isEmpty()) {
            if (failIfExists) {
                throw new AlreadyExistsException("User already exists: " + email);
            }
            System.out.println("User already exists, skipping create: " + email);
            return;
        }

        UserRepresentation user = new UserRepresentation();
        user.setUsername(email);
        user.setEmail(email);
        user.setEnabled(userEnabled);
        user.setEmailVerified(emailVerified);

        CredentialRepresentation credential = new CredentialRepresentation();
        credential.setType(CredentialRepresentation.PASSWORD);
        credential.setValue(request.getPassword());
        credential.setTemporary(false);
        user.setCredentials(Collections.singletonList(credential));

        Response createResponse = users.create(user);
        if (createResponse.getStatus() >= 300) {
            throw new RuntimeException("Failed to create user. Status: " + createResponse.getStatus());
        }
        String userId = extractCreatedId(createResponse);
        System.out.println("Created user ID: " + userId);

        assignDefaultRoles(realmResource, userId);
    }

    public record LinkResult(int status, String body) {}

    /**
     * Link user to a group with status semantics:
     * 206 - user already linked to requested group (body: groupName)
     * 200 - user linked to a DIFFERENT group already (body: existing group name) - no change (was 204, changed so body is not stripped)
     * 201 - user was not linked to any group and now linked (body: groupName)
     * 400 - invalid input
     * 409 - Conflict , with another group
     * 500 - unexpected handled in controller
     */


    public LinkResult linkuser(LinkUserRequest request) {
        if (request == null || request.getUserId() == null || request.getUserId().isBlank() ||
            request.getGroupName() == null || request.getGroupName().isBlank()) {
            throw new IllegalArgumentException("userId and groupName are required");
        }
        if (!request.getGroupName().matches(groupNamePattern)) {
            throw new IllegalArgumentException("Invalid group name. Must match pattern: " + groupNamePattern);
        }
        try (Keycloak keycloak = buildAdministrativeKeycloak()) {
            RealmResource realm = keycloak.realm(managedRealm);

            var internaltargetGroup = resolveGroup(realm, request.getGroupName());
            String internalUserId = resolveUserId(realm, request.getUserId());
            var userResource = realm.users().get(internalUserId);
            var userGroups = userResource.groups();

            if (userGroups == null || userGroups.isEmpty()) {
                userResource.joinGroup(internaltargetGroup.getId());
                return new LinkResult(201, internaltargetGroup.getName());
            }

            boolean alreadyInTarget = userGroups.stream().anyMatch(g -> g.getId().equals(internaltargetGroup.getId()));
            if (alreadyInTarget) {
                return new LinkResult(206, internaltargetGroup.getName());
            }
            String existing = userGroups.get(0).getName();
             
      
            return new LinkResult(409, existing);
        }
    }

    /**
     * Delink user from a group with status semantics:
     * 201 - user was in the group and now removed (body: groupName)
     * 206 - user not in any group (body: none)
     * 200 - user belongs to a different group (body: existing group name) - no change (was 204, changed so body is not stripped)
     * 400 - invalid input
     * 409 - Conflict , with another group
     
     */
    public LinkResult delinkuser(DelinkUserRequest request) {
        if (request == null || request.getUserId() == null || request.getUserId().isBlank() ||
            request.getGroupName() == null || request.getGroupName().isBlank()) {
            throw new IllegalArgumentException("userId and groupName are required");
        }
        if (!request.getGroupName().matches(groupNamePattern)) {
            throw new IllegalArgumentException("Invalid group name. Must match pattern: " + groupNamePattern);
        }
        try (Keycloak keycloak = buildAdministrativeKeycloak()) {
            RealmResource realm = keycloak.realm(managedRealm);
            var internaltargetGroup = resolveGroup(realm, request.getGroupName());
            String internalUserId = resolveUserId(realm, request.getUserId());
            var userResource = realm.users().get(internalUserId);
            var userGroups = userResource.groups();

            if (userGroups == null || userGroups.isEmpty()) {
                return new LinkResult(206, "none");
            }

            boolean inTarget = userGroups.stream().anyMatch(g -> g.getId().equals(internaltargetGroup.getId()));
            if (!inTarget) {
                String existing = userGroups.get(0).getName();
                // Use 409 so the existing group name is preserved in the response body
                return new LinkResult(409, existing);
            }
            userResource.leaveGroup(internaltargetGroup.getId());
            return new LinkResult(201, internaltargetGroup.getName());
        }
    }

    /**
     * Create a realm group if it does not exist.
     * Name is required. Optionally a path can be supplied (Keycloak usually derives it as /<name>). 
     * Idempotent: if group exists returns silently unless failIfGroupExists=true.
     */
    public void CreateGroup(CreateGroupRequest request) {
        if (request == null || request.getName() == null || request.getName().isBlank()) {
            throw new IllegalArgumentException("Group name is required");
        }
        if (!request.getName().matches(groupNamePattern)) {
            throw new IllegalArgumentException("Invalid group name. Must match pattern: " + groupNamePattern);
        }
    Keycloak keycloak = buildAdministrativeKeycloak();
    RealmResource realmResource = keycloak.realm(managedRealm);
        var realmgroups = realmResource.groups();
        
        // Check existence (Keycloak doesn't supply direct find-by-name so we filter client-side)
        boolean exists = realmgroups.groups().stream().anyMatch(g -> request.getName().equalsIgnoreCase(g.getName()));
        if (exists) {
            if (failIfGroupExists) {
                throw new IllegalArgumentException("Group already exists: " + request.getName());
            }
            return; // silently succeed
        }

        var rep = new org.keycloak.representations.idm.GroupRepresentation();
        rep.setName(request.getName());
        if (request.getPath() != null && !request.getPath().isBlank()) {
            rep.setPath(request.getPath());
        }
        Response resp = realmgroups.add(rep);
        if (resp.getStatus() >= 300) {
            throw new RuntimeException("Failed to create group. Status: " + resp.getStatus());
        }
    }

    private Keycloak buildAdministrativeKeycloak() {
        // issuer-uri form: http(s)://base/realms/<realm>
        String base = issuerUri.substring(0, issuerUri.indexOf("/realms/"));
        return KeycloakBuilder.builder()
            .serverUrl(base)
            .realm(adminRealm)
            .clientId(adminClientId)
            .clientSecret(adminClientSecret)
            .grantType(admingrantType)
            .build();
    }

    private void assignDefaultRoles(RealmResource realmResource, String userId) {
        List<String> realmRoles = csvToList(defaultRealmRolesCsv);
    // Determine client roles from new property first; if empty, use deprecated one
    String effectiveClientRolesCsv = newClientRolesCsv;
    List<String> clientRoles = csvToList(effectiveClientRolesCsv);

        // Realm roles
        if (!realmRoles.isEmpty()) {
            RolesResource rolesRsc = realmResource.roles();
            List<RoleRepresentation> roleReps = realmRoles.stream()
                .map(rn -> {
                    try { return rolesRsc.get(rn).toRepresentation(); } catch (Exception e) { return null; }
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
            if (!roleReps.isEmpty()) {
                realmResource.users().get(userId).roles().realmLevel().add(roleReps);
            }
        }

        // Client roles
        if (!clientRoles.isEmpty()) {
            ClientsResource clients = realmResource.clients();
            List<ClientRepresentation> clientList = clients.findByClientId(registrationClientId);
            if (!clientList.isEmpty()) {
                String appClientId = clientList.get(0).getId();
                var clientRoleMapping = realmResource.users().get(userId).roles().clientLevel(appClientId);
                List<RoleRepresentation> clientRoleReps = clientRoles.stream()
                    .map(cr -> {
                        try { return clients.get(appClientId).roles().get(cr).toRepresentation(); } catch (Exception e) { return null; }
                    })
                    .filter(Objects::nonNull)
                    .collect(Collectors.toList());
                if (!clientRoleReps.isEmpty()) {
                    clientRoleMapping.add(clientRoleReps);
                }
            }
        }
    }

    private List<String> csvToList(String csv) {
        if (csv == null || csv.isBlank()) return Collections.emptyList();
        return Arrays.stream(csv.split(","))
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .collect(Collectors.toList());
    }

    private String extractCreatedId(Response response) {
        String location = response.getHeaderString("Location");
        if (location == null) return null;
        int idx = location.lastIndexOf('/');
        return idx != -1 ? location.substring(idx + 1) : location;
    }

    // Resolve supplied user identifier (UUID, username, or email) to internal Keycloak UUID
    private String resolveUserId(RealmResource realm, String supplied) {
        if (supplied.matches("^[0-9a-fA-F-]{32,36}$")) {
            try {
                realm.users().get(supplied).toRepresentation();
                return supplied; // valid UUID
            } catch (Exception ignored) { /* fall through to search */ }
        }
        var results = realm.users().search(supplied, true);
        if (results == null || results.isEmpty()) {
            throw new IllegalArgumentException("User not found: " + supplied);
        }
        return results.stream()
            .filter(u -> supplied.equalsIgnoreCase(Optional.ofNullable(u.getUsername()).orElse(""))
                      || supplied.equalsIgnoreCase(Optional.ofNullable(u.getEmail()).orElse("")))
            .map(UserRepresentation::getId)
            .findFirst()
            .orElse(results.get(0).getId());
    }

    // Resolve group by name (case-insensitive) or treat supplied value as ID if direct retrieval works
    private org.keycloak.representations.idm.GroupRepresentation resolveGroup(RealmResource realm, String groupIdOrName) {
        // Attempt direct fetch if it looks like an ID (UUID) and Keycloak returns something
        if (groupIdOrName.matches("^[0-9a-fA-F-]{32,36}$")) {
            try {
                var grp = realm.groups().group(groupIdOrName).toRepresentation();
                if (grp != null && grp.getId() != null) {
                    return grp;
                }
            } catch (Exception ignored) { /* fallback to name search */ }
        }
        var all = realm.groups().groups();
        return all.stream()
            .filter(g -> groupIdOrName.equalsIgnoreCase(g.getName()))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException("Group not found: " + groupIdOrName));
    }
}
