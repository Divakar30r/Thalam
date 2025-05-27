# My Fullstack App

This project is a fullstack application that utilizes Spring Boot for the backend and React for the frontend. It allows users to view and edit records stored in a MongoDB database.

## Project Structure

```
my-fullstack-app
├── backend                # Spring Boot backend
│   ├── src
│   │   ├── main
│   │   │   ├── java
│   │   │   │   └── com
│   │   │   │       └── example
│   │   │   │           └── app
│   │   │   │               ├── Application.java
│   │   │   │               ├── controller
│   │   │   │               │   └── RecordController.java
│   │   │   │               ├── model
│   │   │   │               │   └── Record.java
│   │   │   │               └── repository
│   │   │   │                   └── RecordRepository.java
│   │   │   └── resources
│   │   │       └── application.properties
│   └── pom.xml            # Maven configuration
├── frontend               # React frontend
│   ├── public
│   │   └── index.html     # Main HTML file
│   ├── src
│   │   ├── App.js         # Main React component
│   │   ├── components
│   │   │   ├── RecordForm.js  # Form for creating/editing records
│   │   │   └── RecordList.js  # Component to display records
│   │   └── index.js       # Entry point for React app
│   ├── package.json       # npm configuration
└── README.md              # Project documentation
```

## Getting Started

### Prerequisites

- Java 11 or higher
- Maven
- Node.js and npm
- MongoDB

### Backend Setup

1. Navigate to the `backend` directory.
2. Update the `application.properties` file with your MongoDB connection details.
3. Build the project using Maven:

   ```
   mvn clean install
   ```

4. Run the Spring Boot application:

   ```
   mvn spring-boot:run
   ```

### Frontend Setup

1. Navigate to the `frontend` directory.
2. Install the dependencies:

   ```
   npm install
   ```

3. Start the React application:

   ```
   npm start
   ```

### Usage

- Access the frontend application at `http://localhost:3000`.
- Use the form to create or edit records.
- View the list of records displayed on the main page.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes. 

## License

This project is licensed under the MIT License.