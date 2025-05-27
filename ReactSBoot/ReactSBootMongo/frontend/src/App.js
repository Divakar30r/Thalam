import React, { useEffect, useState } from 'react';
import RecordForm from './components/RecordForm';
import RecordList from './components/RecordList';

function App() {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    const response = await fetch('/api/records');
    const data = await response.json();
    setRecords(data);
  };

  const addRecord = async (record) => {
   
    await fetch('/api/records', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(record),
    });
    fetchRecords();
  };

  const deleteRecord = async (id) => {
    await fetch(`/api/records/${id}`, {
      method: 'DELETE',
    });
    fetchRecords();
  };
 

  return (
    <div>
      <h1>Record Management</h1>
      <RecordForm onSubmit={addRecord}  />
      <RecordList records={records} deleteRecord={deleteRecord} />
    </div>
  );
}

export default App;