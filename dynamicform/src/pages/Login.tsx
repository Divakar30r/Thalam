import React, { useState, useEffect } from 'react';

const Login: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'ready' | 'error'>('checking');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    // Simple health check - just verify we can reach the auth backend
    // We don't need to check a specific endpoint, just that it's running
    const checkBackend = async () => {
      try {
        // Try to fetch the root auth endpoint
        const response = await fetch('/auth', {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          credentials: 'include'
        });

        // If we get ANY response (even 404), the backend is reachable
        // The proxy is working if we get a response
        if (response.status === 404) {
          // This is expected - /auth route might not exist, but backend is reachable
          setBackendStatus('ready');
        } else if (response.ok) {
          try {
            const data = await response.json();
            if (data.service === 'Auth BFF' || data.status === 'ok') {
              setBackendStatus('ready');
            } else {
              setBackendStatus('ready'); // Backend is responding, so it's ready
            }
          } catch {
            // Can't parse JSON, but got 200 - backend is ready
            setBackendStatus('ready');
          }
        } else {
          setBackendStatus('error');
          setErrorMessage(`Auth service returned HTTP ${response.status}.`);
        }
      } catch (err: any) {
        // Network error - backend is truly unreachable
        setBackendStatus('error');
        setErrorMessage('Cannot connect to auth service. Ensure backend is running (npm run dev:auth).');
      }
    };
    checkBackend();
  }, []);

  const handleKeycloakLogin = () => {
    if (backendStatus !== 'ready') {
      alert('Auth backend is not ready. Please wait or contact support.');
      return;
    }
    // Redirect to Keycloak login via backend
    const returnUrl = encodeURIComponent(window.location.origin);
    window.location.href = `/auth/start?returnTo=${returnUrl}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Order Management System
          </h1>
          <p className="text-gray-600">
            Please sign in to continue
          </p>
        </div>

        {backendStatus === 'error' && (
          <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-400 text-red-700">
            <p className="font-bold">Connection Error</p>
            <p className="text-sm">{errorMessage}</p>
            <p className="text-xs mt-2">Run: <code className="bg-red-100 px-1 py-0.5 rounded">npm run dev:auth</code></p>
          </div>
        )}

        <div className="space-y-4">
          <button
            onClick={handleKeycloakLogin}
            disabled={backendStatus !== 'ready'}
            className={`w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white transition-colors ${
              backendStatus === 'ready'
                ? 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {backendStatus === 'checking' && (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {backendStatus === 'checking' && 'Checking auth service...'}
            {backendStatus === 'ready' && (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                Sign in with Keycloak
              </>
            )}
            {backendStatus === 'error' && 'Auth Service Unavailable'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Secure authentication powered by Keycloak
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
