# My Fullstack App - Frontend

This is the frontend part of the My Fullstack App project, built using React. The frontend interacts with a Spring Boot backend to manage records stored in a MongoDB database.

## Project Structure

- **public/index.html**: The main HTML file that serves as the entry point for the React application.
- **src/App.js**: The main component that sets up routing and renders the application layout.
- **src/components/RecordForm.js**: A component for creating and editing records.
- **src/components/RecordList.js**: A component that displays a list of records fetched from the backend.
- **src/index.js**: The entry point for the React application that renders the App component.
- **package.json**: Configuration file for npm, listing dependencies and scripts.

## Getting Started

To get started with the frontend application, follow these steps:

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd my-fullstack-app/frontend
   ```

2. **Install dependencies**:
   ```
   npm install
   ```

3. **Run the application**:
   ```
   npm start
   ```

   This will start the React application in development mode. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## API Integration

The frontend communicates with the backend API to perform CRUD operations on records. Ensure that the backend server is running before starting the frontend application.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.