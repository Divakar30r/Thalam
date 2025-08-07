import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';  
import RecordForm from './components/RecordForm';
import RecordList from './components/RecordList';
import WelcomePage from './components/WelcomePage';
import axios from 'axios';

function App() {

    const handleRecordSubmit = async (formData) => {
    try {
      const response = await axios.post('/api/records', formData);
      console.log("Record created:", response.data);
      // Optionally, you might want to refresh the record list or update state.
    } catch (error) {
      console.error("Error creating record:", error);
    }
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/records" element={
          <div style={{ margin: '20px' }}>
            <h1>Record Management</h1>
            <RecordForm onSubmit={handleRecordSubmit}/>
            <RecordList />
          </div>
        }/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;