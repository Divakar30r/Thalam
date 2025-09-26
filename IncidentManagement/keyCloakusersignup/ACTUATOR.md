# Actuator & Health Endpoints

The service uses Spring Boot Actuator for health and readiness probes.

## Enabled Endpoints
- `/actuator/health` (exposed by default through `management.endpoints.web.exposure.include`)
  - Liveness: `/actuator/health/liveness`
  - Readiness: `/actuator/health/readiness`

## Configuration (Environment Variables)
Environment variable names map to the Spring properties declared in `application.properties`.

| ENV Var | Default | Description |
|---------|---------|-------------|
| `MANAGEMENT_ENDPOINTS_EXPOSURE` | `health` | Comma list of actuator endpoints to expose (e.g. `health,info`) |
| `MANAGEMENT_HEALTH_SHOW_DETAILS` | `always` | Show component details in health (`never`, `when_authorized`, `always`) |
| `MANAGEMENT_SERVER_PORT` | (disabled) | Separate port for management endpoints if set |

Liveness / readiness indicators are auto-enabled via:
```
management.health.livenessState.enabled=true
management.health.readinessState.enabled=true
```
These can be overridden if required.

## Kubernetes / Docker Compose
Add to your deployment configuration:
```
# Docker Compose example healthcheck
healthcheck:
  test: ["CMD", "curl", "-f", "http://service:8091/actuator/health"]
  interval: 30s
  timeout: 3s
  retries: 3
```
For k8s probes:
```
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8091
  initialDelaySeconds: 30
  periodSeconds: 30
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8091
  initialDelaySeconds: 10
  periodSeconds: 15
```

## Security Note
Currently only `health` is exposed. If you expose additional endpoints (e.g. `info`, `metrics`), consider adding authentication or network restrictions.
