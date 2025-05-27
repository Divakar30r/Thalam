import React, { useState, useEffect } from 'react';

const RecordForm = ({ record, onSubmit }) => {
    const [formData, setFormData] = useState({
        name: '',
        address: '',
        landmark: '',
        taluk: '',
        pincode: '',
        geolocation: {
            collectioncentre: '',
            proximity: '',
            coordinates: {
                latitude: '',
                longitude: ''
            }
        }
    });

    useEffect(() => {
        if (record) {
            setFormData(record);
        }
    }, [record]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prevData) => ({
            ...prevData,
            [name]: value
        }));
    };

    /*
    const handleGeolocationChange = (e) => {
        const { name, value } = e.target;
        const [key, subKey] = name.split('.');
        console.log(name + " ** "+ key + " ** "+ subKey+ " ** "+ value);
        setFormData((prevData) => ({
            ...prevData,
            [key]: {
                ...prevData[key],
                [subKey]: value
            }
        }));
    };
    */

    const handleGeolocationChange = (e) => {
        const { name, value } = e.target;
        const keys = name.split('.');
    
        setFormData((prevData) => {
            // Create a deep copy of prevData
            const newData = { ...prevData };
            let current = newData;
    
            // Traverse to the correct nested object
            for (let i = 0; i < keys.length - 1; i++) {
                // If the key doesn't exist, create an empty object
                if (!current[keys[i]]) current[keys[i]] = {};
                current = current[keys[i]];
            }
    
            // Set the value at the deepest level
            current[keys[keys.length - 1]] = value;
            return newData;
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit}>
            <input type="text" name="name" value={formData.name} onChange={handleChange} placeholder="Name" required />
            <input type="text" name="address" value={formData.address} onChange={handleChange} placeholder="Address" required />
            <input type="text" name="landmark" value={formData.landmark} onChange={handleChange} placeholder="Landmark" />
            <input type="text" name="taluk" value={formData.taluk} onChange={handleChange} placeholder="Taluk" />
            <input type="number" name="pincode" value={formData.pincode} onChange={handleChange} placeholder="Pincode" required />
            <input type="text" name="geolocation.collectioncentre" value={formData.geolocation.collectioncentre} onChange={handleGeolocationChange} placeholder="Collection Centre" />
            <input type="text" name="geolocation.proximity" value={formData.geolocation.proximity} onChange={handleGeolocationChange} placeholder="Proximity" />
            <input type="number" name="geolocation.coordinates.latitude" value={formData.geolocation.coordinates.latitude} onChange={handleGeolocationChange} placeholder="Latitude" required />
            <input type="number" name="geolocation.coordinates.longitude" value={formData.geolocation.coordinates.longitude} onChange={handleGeolocationChange} placeholder="Longitude" required />
            <button type="submit">Submit</button>
        </form>
    );
};

export default RecordForm;