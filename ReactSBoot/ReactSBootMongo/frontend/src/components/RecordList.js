import React, { useEffect, useState } from 'react';
import axios from 'axios';

const RecordList = () => {
    const [records, setRecords] = useState([]);

    useEffect(() => {
        fetchRecords();
    }, []);

    const fetchRecords = async () => {
        try {
            const response = await axios.get('/api/records');
            setRecords(response.data);
        } catch (error) {
            console.error('Error fetching records:', error);
        }
    };

    const deleteRecord = async (id) => {
        try {
            await axios.delete(`/api/records/${id}`);
            fetchRecords(); // Refresh the list after deletion
        } catch (error) {
            console.error('Error deleting record:', error);
        }
    };

    return (
        <div>
            <h2>Record List</h2>
            <ul>
              
                {records.map(record => (
                    <li key={record.id}>
                        <div>
                            <strong>Name:</strong> {record.name}<br />
                            <strong>Address:</strong> {record.address}<br />
                            <strong>Landmark:</strong> {record.landmark}<br />
                            <strong>Taluk:</strong> {record.taluk}<br />
                            <strong>Pincode:</strong> {record.pincode}<br />
                            <strong>Collection Centre:</strong> {record.geolocation.collectioncentre}<br />
                            <strong>Proximity:</strong> {record.geolocation.proximity}<br />
                            <strong>Coordinates:</strong> {record.geolocation.coordinates.latitude}, {record.geolocation.coordinates.longitude}
                        </div>
                        <button onClick={() => deleteRecord(record.id)}>Delete</button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default RecordList;