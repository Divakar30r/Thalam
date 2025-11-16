// Production environment configuration
const DOCS_BASE_URL = (import.meta.env as Record<string, any>).VITE_DOCS_BASE_URL || 'http://localhost:8000';

export const config = {
  API_BASE_URL: (import.meta.env as Record<string, any>).VITE_API_BASE_URL || 'https://api.production.com',
  PRESIGNED_URL_CONFIG_NAME: (import.meta.env as Record<string, any>).VITE_PRESIGNED_CONFIG_NAME || 'PRESIGNED URL',
  PRESIGNED_URL_ENDPOINT: (import.meta.env as Record<string, any>).VITE_PRESIGNED_URL_ENDPOINT || '',
  PRESIGNED_STATUS_ENDPOINT: `${DOCS_BASE_URL}/api/v1/status`,
  PRESIGNED_DOCS_ENDPOINT: `${DOCS_BASE_URL}/api/v1/documents/`,
  PRESIGNED_PUBLIC_URL_ENDPOINT: `${DOCS_BASE_URL}/api/v1/public-url/`,
  PRESIGNED_ATTACH_ENDPOINT: `${DOCS_BASE_URL}/api/v1/assign-to-order/`,
};
