import { useNavigate } from 'react-router-dom';
import { useKeycloak } from '@react-keycloak/web';
import React from 'react';

const WelcomePage = () => {
  const { keycloak } = useKeycloak();
  const navigate = useNavigate();

  return (
    <div style={{ textAlign: 'center', padding: '40px' }}>
      <div style={{color: 'red', fontWeight: 'bold', fontSize: '20px'}}>DEBUG: WelcomePage is rendering</div>
      {/* React Icon */}
      <img 
        src="https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg" 
        alt="React Icon" 
        style={{ width: '120px', height: '120px' }} 
      />
      <h1>Hello, Welcome to ReactSBoot</h1>
      <button 
        style={{
          padding: '10px 20px',
          marginTop: '20px',
          fontSize: '16px',
          cursor: 'pointer'
        }}
        onClick={() => navigate('/records')}
      >
        View Records
      </button>
    </div>
  );
};

export default WelcomePage;