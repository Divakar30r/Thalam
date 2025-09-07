# Java MongoDB Integration with Spring Boot

This project demonstrates how to integrate MongoDB with a Spring Boot application using Java. It includes a complete setup for connecting to a MongoDB replica set, performing CRUD operations, and executing complex queries and aggregations.

## 🚀 Features

- **MongoDB ReplicaSet Connection**: Establishes connection to a MongoDB replica set for high availability
- **Spring Boot Integration**: Utilizes Spring Boot for dependency injection and web services
- **CRUD Operations**: Implements Create, Read, Update, and Delete operations for MongoDB documents
- **Complex Queries**: Demonstrates advanced query capabilities including filtering, sorting, and pagination
- **Aggregation Pipeline**: Shows how to use MongoDB's powerful aggregation framework
- **Multi-Collection Support**: Works with multiple collections (feeds, tokens, users)
- **RESTful API**: Exposes MongoDB operations through a RESTful API

## 📋 Prerequisites

- Java 21+
- Maven
- MongoDB server (configured as a replica set)
- Spring Boot 3.2.0+

## 🔧 Configuration

The application is configured to connect to a MongoDB replica set running on:
- localhost:27030
- localhost:27031
- localhost:27032

Configuration is stored in `application.properties`:

```properties
spring.data.mongodb.uri=mongodb://localhost:27030,localhost:27031,localhost:27032/yourdb?replicaSet=rs0
spring.data.mongodb.database=yourdb
```

## 📦 Project Structure

```
src/main/java/code/
├── Main.java                 # Application entry point
├── mongo/
│   ├── MongoConfig.java      # MongoDB connection configuration
│   ├── MongoController.java  # REST endpoints for MongoDB operations
│   └── MongoService.java     # Service for MongoDB operations
```

## 🏗️ Class Descriptions

### MongoConfig

Sets up the MongoDB client and database connection using properties from the application configuration.

### MongoService

Provides MongoDB operations for a specific collection:
- Basic CRUD operations
- Complex queries with multiple criteria
- Sorting and pagination
- Field projections
- Aggregation operations

### MongoController

Exposes REST endpoints for MongoDB operations:
- Inserting documents
- Retrieving all documents
- Finding specific documents
- Updating documents
- Deleting documents

## 🚀 Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/MrDay2Day/Java-MongoDB.git
   ```

2. Configure MongoDB connection in `application.properties`:
   ```
   server.port=3077
   server.tomcat.max-http-header-size=1048576
   
   
   spring.data.mongodb.uri=mongodb://localhost:27030,localhost:27031,localhost:27032/?replicaSet=rs0
   spring.data.mongodb.database=your_database_name
   
   mongodb.collection.name=dummy
   ```

3. Build the project:
   ```
   mvn clean package
   ```

4. Run the application:
   ```
   java -jar target/Java-MongoDB-1.0-SNAPSHOT.jar
   ```

## 🔍 API Endpoints

   | Method | Endpoint | Description |
   |--------|----------|-------------|
   | POST | /mongo/insert | Insert a new document |
   | GET | /mongo/all | Get all documents from the feeds collection |
   | GET | /mongo/all-tokens | Get all documents from the tokens collection |
   | GET | /mongo/all-users | Get all documents from the users collection |
   | GET | /mongo/find | Find a document by key-value pair |
   | PUT | /mongo/update | Update a document |
   | DELETE | /mongo/delete | Delete a document |

## 📝 Examples

See the [EXAMPLES.md](EXAMPLES.md) file for detailed examples of:
- Complex queries
- Aggregation operations
- Controller usage examples
- Working with filters

## 🛠️ Troubleshooting

If you encounter issues with bean dependency injection, ensure that:
1. You have properly defined all required beans
2. Your MongoDB connection properties are correct
3. The MongoDB replica set is properly configured and running

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
