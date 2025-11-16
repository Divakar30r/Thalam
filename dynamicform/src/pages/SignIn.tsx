import React, { useState } from 'react';

// Simple SignIn component that posts username/password to the backend BFF
// Endpoint: POST /auth/login

export const SignIn: React.FC<{ onSuccess?: () => void }> = ({ onSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!resp.ok) {
        const text = await resp.text().catch(() => '');
        throw new Error(text || `Login failed: ${resp.status}`);
      }
      // backend sets AUTH_SESSION cookie (HttpOnly). Backend also returns user info.
      const data = await resp.json();
      if (data?.ok) {
        onSuccess?.();
      } else {
        setError(data?.message || 'Login failed');
      }
    } catch (err: any) {
      setError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Sign in</h2>
      {error && <div className="mb-3 text-red-600">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="block text-sm font-medium">Username</label>
          <input value={username} onChange={e => setUsername(e.target.value)} className="mt-1 block w-full border rounded p-2" />
        </div>
        <div className="mb-3">
          <label className="block text-sm font-medium">Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1 block w-full border rounded p-2" />
        </div>
        <div className="flex justify-end">
          <button type="submit" disabled={loading} className="py-2 px-3 bg-indigo-600 text-white rounded">
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SignIn;
