# Keycloak Signup Spring Boot Service

This project provides a secure REST API for user signup, integrating with Keycloak (realm: TeamMgmt, clientID: TestCrt, port: 9090) and PostgreSQL. Passwords are validated and stored using BCrypt encryption. OAuth2 and Spring Security are used for authentication best practices.

## Features
- Signup endpoint (`/signup`) accepts email and password
- Validates password strength (min 8 chars, upper/lower/digit/special)
- Registers user in Keycloak and local PostgreSQL DB
- Passwords stored with BCrypt
- OAuth2 login with Keycloak
- Configurable admin provisioning (password or client_credentials grant)
- Automatic default realm & client role assignment on first signup

## Setup
1. **Configure PostgreSQL**
   - Create a database named `keycloak_signup`
   - Set username/password in `src/main/resources/application.properties`
2. **Configure Keycloak**
   - Run Keycloak on port 9090
   - Create realm `TeamMgmt` and client `TestCrt`
   - Set client secret in `application.properties`
3. **Build and Run (Local)**
    - `mvn clean install`
    - `mvn spring-boot:run`

4. **Run via Docker Compose (Example Snippet)**
    ```yaml
    services:
       signup-service:
          image: yourrepo/signup-service:latest
          environment:
             SERVER_PORT: 8091
             KEYCLOAK_AUTH_SERVER_URL: http://keycloak:8080/realms/TeamMgmt
             KEYCLOAK_REALM: TeamMgmt
             KEYCLOAK_CLIENT_ID: TestCrt
             KEYCLOAK_CLIENT_SECRET: change_me
             PROVISION_GRANT_TYPE: password
             PROVISION_ADMIN_USERNAME: realm-admin
             PROVISION_ADMIN_PASSWORD: S3curePass!
             PROVISION_ADMIN_CLIENT_ID: admin-cli
             PROVISION_MASTER_REALM: master
             PROVISION_DEFAULT_REALM_ROLES: basic_user,audit_viewer
             PROVISION_DEFAULT_CLIENT_ROLES: app_user
             PROVISION_EMAIL_VERIFIED: true
             PROVISION_USER_ENABLED: true
             PROVISION_FAIL_IF_EXISTS: false
             SECURITY_PASSWORD_ENCODER_STRENGTH: 12
          ports:
             - "8091:8091"
          depends_on:
             - keycloak
    ```

## API
- `POST /signup` with JSON body:
  ```json
  {
    "email": "user@example.com",
    "password": "StrongP@ssw0rd"
  }
  ```

## Security
- Passwords must be 8-64 chars, contain upper, lower, digit, special char
- All passwords stored with BCrypt (strength 12)
- Only signup endpoint is public; all others require OAuth2 login

## Environment
## Configuration Reference

| Property | Env Var | Purpose | Default |
|----------|---------|---------|---------|
| `server.port` | `SERVER_PORT` | HTTP port | 8091 |
| `keycloak.auth-server-url` | `KEYCLOAK_AUTH_SERVER_URL` | Realm auth URL (with /realms/<realm>) | http://localhost:9090/realms/TeamMgmt |
| `keycloak.realm` | `KEYCLOAK_REALM` | Target realm | TeamMgmt |
| `keycloak.resource` | `KEYCLOAK_CLIENT_ID` | Application (public/confidential) client ID | TestCrt |
| `keycloak.credentials.secret` | `KEYCLOAK_CLIENT_SECRET` | Client secret | example secret |
| `provision.grant-type` | `PROVISION_GRANT_TYPE` | How admin API authenticates (password or client_credentials) | password |
| `provision.admin.username` | `PROVISION_ADMIN_USERNAME` | Realm admin username (password grant) | DivAdmin |
| `provision.admin.password` | `PROVISION_ADMIN_PASSWORD` | Realm admin password | DivAdmin |
| `provision.admin.client-id` | `PROVISION_ADMIN_CLIENT_ID` | Client used for password grant | admin-cli |
| `provision.admin.client-secret` | `PROVISION_ADMIN_CLIENT_SECRET` | Optional secret if client requires it | CHANGEME |
| `provision.master-realm` | `PROVISION_MASTER_REALM` | Master (admin) realm name | master |
| `provision.default.realm-roles` | `PROVISION_DEFAULT_REALM_ROLES` | Comma-separated realm roles to add to new users | basic_user |
| `provision.default.client-roles` | `PROVISION_DEFAULT_CLIENT_ROLES` | Comma-separated client roles (in application client) | app_user |
| `provision.fail-if-exists` | `PROVISION_FAIL_IF_EXISTS` | Throw error if user exists | false |
| `provision.email-verified` | `PROVISION_EMAIL_VERIFIED` | Mark new user email verified | true |
| `provision.user-enabled` | `PROVISION_USER_ENABLED` | Enable new user | true |
| `security.password.encoder.strength` | `SECURITY_PASSWORD_ENCODER_STRENGTH` | BCrypt strength cost factor | 12 |

### Notes
1. Client roles require that the configured application client already has those roles defined.
2. Realm roles must pre-exist; missing roles are silently skipped.
3. For `client_credentials`, your service client must have realm-management permissions adequate to create users and assign roles.
4. Consider vault/secret manager for sensitive values in production.

## Operational Considerations
| Concern | Recommendation |
|---------|---------------|
| Idempotency | Set `PROVISION_FAIL_IF_EXISTS=false` in CI/CD bootstrap runs. |
| Secrets | Mount via Docker/Kubernetes secrets, never bake into image. |
| Auditing | Enable Keycloak admin event logging for traceability. |
| Scaling | Stateless; can scale horizontally. Ensure consistent Keycloak endpoint. |
| Hardening | Restrict network egress; use HTTPS for Keycloak in production; rotate admin credentials. |

- Java 17+
- Spring Boot 3.2+
- PostgreSQL 14+
- Keycloak 22+

---
Replace `REPLACE_WITH_CLIENT_SECRET` in `application.properties` with your Keycloak client secret.



## Prompt
Need a project implemented using springboot with REST endpoint for signup which accepts usermailID and password (complying with standard regulations) and should create the user in keycloak ream

Database: PostGre
Use spring authentication for the signup endpoint with keycloak realm 'TeamMgmt' with clientID 'TestCrt' and use OAuth2 specific classes.

Keycloak port:9090 realm: TeamMgmt
Users required mailID and password need to be set permanently and store it post Bencryption