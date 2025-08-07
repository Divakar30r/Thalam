import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import fnkeycloak from './Appkeycloak';
import './index.css';

ReactDOM.render(
  <React.StrictMode>
     <ReactKeycloakProvider authClient={fnkeycloak}   initOptions={{ onLoad: 'login-required' }}>
    <App />
    </ReactKeycloakProvider>
  </React.StrictMode>,
  document.getElementById('root')
);