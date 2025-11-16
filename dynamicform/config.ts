// Centralized config for the app. Reads Vite environment variable VITE_API_BASE_URL
// and falls back to localhost if not provided.

export const API_BASE_URL = (import.meta.env as Record<string, any>).VITE_API_BASE_URL || 'http://127.0.0.1:8001';

// Name used by backend to identify which presigned URL configuration to use.
export const PRESIGNED_URL_CONFIG_NAME = (import.meta.env as Record<string, any>).VITE_PRESIGNED_CONFIG_NAME || 'PRESIGNED URL';

// Endpoint to request a presigned POST payload. Can be overridden via Vite env.
export const PRESIGNED_URL_ENDPOINT = (import.meta.env as Record<string, any>).VITE_PRESIGNED_URL_ENDPOINT || `${API_BASE_URL}/api/v1/dochandler/presigned`;

// Base URL for document service (default: localhost:8000)
const DOCS_BASE_URL = (import.meta.env as Record<string, any>).VITE_DOCS_BASE_URL || 'http://localhost:8000';

// Endpoint to update document status after upload
export const PRESIGNED_STATUS_ENDPOINT = `${DOCS_BASE_URL}/api/v1/status`;

// Endpoint to list documents
export const PRESIGNED_DOCS_ENDPOINT = `${DOCS_BASE_URL}/api/v1/documents/`;

// Endpoint to get public download URL
export const PRESIGNED_PUBLIC_URL_ENDPOINT = `${DOCS_BASE_URL}/api/v1/public-url/`;

// Order form Keycloak client id used by the backend to fetch client-specific roles on demand
// Note: ORDERFORM client id is intentionally kept server-side (KEYCLOAK_ORDERFORM_CLIENT_ID).
// Frontend should call /auth/check-order-permission to ask the backend whether the
// current user has order-edit permissions.
