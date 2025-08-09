# Realtime Document Editor – Project Documentation

## 📌 Project Overview

A collaborative document editing platform enabling multiple users to edit documents in real-time using WebSocket communication (STOMP protocol). Built with Spring Boot (backend) and React (frontend), it ensures low latency, data consistency, authentication, and scalability.

## 🎯 Core Objectives

* Enable real-time collaborative editing of documents.
* Support concurrent users working on the same document.
* Ensure data consistency across clients.
* Use caching and queuing for performance and reliability.
* Secure both REST and WebSocket communication.
* Provide proper persistence and recovery mechanisms.

## 🏗️ Architecture Technologies

| Layer / Concern         | Technology / Library                          |
| ----------------------- | --------------------------------------------- |
| Core Framework          | Spring Boot                                   |
| REST API                | Spring Web (spring-boot-starter-web)          |
| Real-time Communication | Spring WebSocket + STOMP                      |
| Authentication          | Spring Security + JWT                         |
| Persistence             | Spring Data JPA + PostgreSQL                  |
| Caching                 | Spring Data Redis                             |
| Messaging Queue         | Apache Kafka or RabbitMQ + Spring Integration |
| Exception Handling      | @ControllerAdvice for global error handling   |
| Logging / AOP           | Spring AOP (spring-boot-starter-aop)          |
| Migrations              | Liquibase                                     |
| Monitoring / Metrics    | Spring Boot Actuator                          |
| Testing                 | Spring Boot Test + JUnit                      |

## 🧱 Architecture Layers

| Layer              | Responsibilities                                                      |
| ------------------ | --------------------------------------------------------------------- |
| Presentation Layer | Expose REST APIs and WebSocket endpoints, secure endpoints with JWT   |
| WebSocket Layer    | Manage real-time document collaboration using STOMP over WebSocket    |
| Service Layer      | Handle business logic for documents, users, conflict resolution, etc. |
| Messaging Layer    | Asynchronously process operations using RabbitMQ or Kafka             |
| Caching Layer      | Store document state for fast retrieval using Redis                   |
| Persistence Layer  | Store durable document and user data in PostgreSQL                    |
| Security Layer     | Handle authentication and authorization using JWT and Spring Security |
| Monitoring/Logging | Track performance, events, and errors using Spring AOP and Actuator   |
| Migration Layer    | Version control of DB schema via Liquibase                            |

## 🧩 Detailed Architecture View

### 1. Client Interaction Layer (React.js)

* Provides the user interface for document editing.
* Connects to backend via REST (for auth, user/doc CRUD) and WebSocket (for real-time collaboration).
* Maintains local editor state and sends delta changes.

### 2. Gateway/API Layer (Spring Boot)

* Exposes JWT-secured REST endpoints for authentication and resource access.
* Exposes WebSocket/STOMP endpoint `/ws` for bi-directional communication.

### 3. WebSocket Handler Layer

* Handles real-time events under `/app/documents/{id}`.
* Routes incoming changes using `@MessageMapping`.
* Broadcasts document updates over `/topic/documents/{id}`.

### 4. Business Logic Layer (Service)

* Verifies permission and document validity.
* Resolves document conflicts (e.g., OT or CRDT algorithms).
* Coordinates with Messaging, Caching, and Persistence layers.

### 5. Messaging Queue Layer

* Accepts queued document changes (via RabbitMQ/Kafka).
* Ensures ordered processing and isolates computation load.
* Re-publishes confirmed changes to WebSocket layer.

### 6. Caching Layer (Redis)

* First read point for document data.
* Updates with every valid change.
* Evicts or syncs back to DB on interval or lifecycle events.

### 7. Persistence Layer (PostgreSQL + JPA)

* Stores user, role, and document metadata.
* Writes committed document states from queue/caching layer.
* Restores latest state on startup.

### 8. Authentication and Authorization

* JWT-based login/registration system.
* Validates JWT during REST and WebSocket handshakes.
* Controls read/write permissions.

### 9. Monitoring and Observability

* Spring Boot Actuator for health and metrics.
* Logs WebSocket lifecycle events.
* Uses AOP to wrap service calls and log errors.

### 10. Infrastructure

* Redis, RabbitMQ, PostgreSQL via Docker containers.
* Spring profiles for local, staging, production.
* Future-proofed for Kubernetes or EC2 scaling.



## 🚀 Milestones Breakdown

### ✅ Milestone 1: Real-Time WebSocket Communication Setup

* STOMP over WebSocket integration
* React client connects via SockJS
* Broadcast document changes using `/topic/documents/{id}`
* `@MessageMapping("/documents/{id}")` to handle incoming edits

### ✅ Milestone 2: Document State Management and Caching

* Setup Redis for caching documents
* On fetch, check Redis → fallback to DB if not found
* Sync cache with DB periodically or on updates

### ⏳ Milestone 3: Operation Queuing and Processing

* Integrate RabbitMQ or Kafka
* Queue incoming edits to ensure sequential handling
* Consume messages and broadcast updated state

### ⏳ Milestone 4: Conflict Resolution with OT or CRDT

* Apply Operational Transformation (OT) or CRDT algorithms
* Merge concurrent edits safely
* Update cache and broadcast final state

### ✅ Milestone 5: Authentication and Token-based Authorization

* Add JWT authentication to REST APIs
* Add JWT to WebSocket handshake headers
* Validate JWT on WebSocket connect/interactions

### ✅ Milestone 6: REST API for Document and User Management

* CRUD for users and documents
* Protect endpoints with JWT
* Store users, roles, documents in PostgreSQL

### ⏳ Milestone 7: Multi-threading and Concurrency Handling

* Use ExecutorService for parallel task handling
* Ensure thread-safe operations on Redis and DB

### ⏳ Milestone 8: Persistence and Recovery

* Persist document changes to DB
* Schedule save on interval or disconnect
* Recover from Redis on server restart

### ⏳ Milestone 9: Monitoring, Logging, and Exception Handling

* Add Spring Boot Actuator for metrics
* Log WebSocket events (connect, disconnect, error)
* Use `@ControllerAdvice` for REST/WebSocket exception handling

### ⏳ Milestone 10: Scalability and Production Readiness

* Redis pub/sub for multi-instance message sync
* Dockerize backend + Redis
* Prepare for Kubernetes or EC2 deployment

## 📦 Backend Code Snapshots (Current)

```java
@MessageMapping("/documents/{id}")
public void getDocumentById(@DestinationVariable String id, @Payload DocumentDTO documentDTO) {
    log.info("Socket request to update document of id '{}' with this payload: {}", id, documentDTO);
    DocumentDTO document = documentService.findOneById(Long.parseLong(id));
    messagingTemplate.convertAndSend("/topic/documents/" + id, document);
}

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic");
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("http://localhost:5173")
                .withSockJS();
    }
}
```

## ✅ Current Progress Summary

* Spring Boot REST APIs with JWT Authentication ✅
* PostgreSQL persistence layer setup ✅
* WebSocket + STOMP working (basic doc fetch & sync) ✅
* React client connected to STOMP endpoint ✅
* Redis caching integrated ✅

## 🔜 Next Steps

* Setup RabbitMQ queue for sequential doc updates
* Broadcast changes post-consumption
* Queue-based reliability improvements
* Move toward OT/CRDT merge resolution logic

## 🗂️ Future Enhancements

* Role-based access (read-only vs. editor)
* Collaborative cursor/selection display
* Version history and rollback
* Offline edit support and sync
