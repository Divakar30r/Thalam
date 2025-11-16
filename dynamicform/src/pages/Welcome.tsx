import React, { useEffect, useState } from 'react';

// Normalize a role string that may include a client prefix like "CLIENT:ROLE" or "CLIENT/ROLE"
// Returns the last segment upper-cased, e.g. "ORDMGMT:ORDER_EDIT" -> "ORDER_EDIT".
function normalizeRoleString(role: string | undefined | null) {
  if (!role) return '';
  const parts = String(role).split(/[:\\/]/);
  return parts[parts.length - 1].toUpperCase();
}

interface UserInfo {
  username?: string;
  name?: string;
  roles?: string[];
}

export const Welcome: React.FC<{ onOpenApp?: () => void; onViewSubmittedOrders?: () => void }> = ({ onOpenApp, onViewSubmittedOrders }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        // include credentials so HttpOnly cookies set by the auth backend are sent
        const resp = await fetch('/auth/me', { credentials: 'include' });
        if (!resp.ok) throw new Error('Not authenticated');
        const data = await resp.json();
        setUser(data.user || data);
      } catch (err: any) {
        setError(err?.message || 'Failed to fetch user');
      }
    };
    fetchMe();
  }, []);

  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!user) return <div className="p-6">Loading...</div>;

  const hasRole = (r: string) => {
    const target = r.toUpperCase();
    return (user.roles || []).some(rr => normalizeRoleString(rr) === target || (rr || '').toUpperCase() === target);
  };

  // any role that, after normalization, contains the substring 'FORM'
  const anyFormRole = (user.roles || []).some(rr => normalizeRoleString(rr).includes('FORM'));

  const handleLogout = async () => {
    try {
      const response = await fetch('/auth/logout?returnTo=' + encodeURIComponent(window.location.origin), {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();

      // If Keycloak logout URL provided, redirect there to end SSO session
      if (data.keycloakLogoutUrl) {
        window.location.href = data.keycloakLogoutUrl;
      } else {
        // Fallback: just redirect to home
        window.location.href = '/';
      }
    } catch (err) {
      console.error('Logout failed:', err);
      // Force redirect anyway
      window.location.href = '/';
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-2xl font-semibold">Welcome{user.name ? `, ${user.name}` : ''}</h2>
          <p className="text-sm text-gray-600">Username: {user.username}</p>
        </div>
        <button
          onClick={handleLogout}
          className="py-2 px-4 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
        >
          Logout
        </button>
      </div>

      <div className="mt-6 space-x-2">
        {hasRole('BUY') && (
          <>
            <CreateEditButton onOpenApp={onOpenApp} />
            <ViewSubmittedOrdersButton onViewSubmittedOrders={onViewSubmittedOrders} />
          </>
        )}
        {anyFormRole && (
          <button onClick={() => onOpenApp?.()} className="py-2 px-3 bg-indigo-600 text-white rounded">Open Dynamic Form</button>
        )}
      </div>
    </div>
  );
};

export default Welcome;

// Small sub-component to handle on-demand client-role check before opening the app
const CreateEditButton: React.FC<{ onOpenApp?: () => void }> = ({ onOpenApp }) => {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleClick = async () => {
    setErr(null);
    setLoading(true);
    try {
      const resp = await fetch(`/auth/check-order-permission`, { credentials: 'include' });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        setErr(body?.message || `Failed to fetch client roles (${resp.status})`);
        setLoading(false);
        return;
      }
      const data = await resp.json();
      const roles: string[] = data.roles || [];
      const normalized = roles.map(r => String(r || '').toUpperCase());
      const allowed = ['ORDER_EDIT'];
      // backend already indicates allowed, but double-check locally
      const ok = Boolean(data.allowed) || normalized.some(r => allowed.includes(r));
      if (ok) {
        onOpenApp?.();
      } else {
        setErr('You do not have permission to create/edit orders.');
      }
    } catch (e: any) {
      setErr(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button onClick={handleClick} disabled={loading} className={`py-2 px-3 bg-green-600 text-white rounded ${loading ? 'opacity-60 cursor-wait' : ''}`}>
        {loading ? 'Checking...' : 'Create / Edit Order'}
      </button>
      {err && <div className="text-sm text-red-600 mt-2">{err}</div>}
    </>
  );
};

// Button to view submitted orders
const ViewSubmittedOrdersButton: React.FC<{ onViewSubmittedOrders?: () => void }> = ({ onViewSubmittedOrders }) => {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      // Future: Add any permission checks or data fetching here if needed
      onViewSubmittedOrders?.();
    } catch (e: any) {
      console.error('Error opening submitted orders:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={`py-2 px-3 bg-blue-600 text-white rounded ${loading ? 'opacity-60 cursor-wait' : 'hover:bg-blue-700'}`}
    >
      {loading ? 'Loading...' : 'View Submitted Orders'}
    </button>
  );
};
