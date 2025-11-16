// Centralized config for the app with environment-based imports
import { config as devConfig } from './dev';
import { config as prodConfig } from './prod';

const env = import.meta.env.MODE || 'development';

// Select config based on environment
const selectedConfig = env === 'production' ? prodConfig : devConfig;

export const { API_BASE_URL, PRESIGNED_URL_CONFIG_NAME, PRESIGNED_URL_ENDPOINT, PRESIGNED_STATUS_ENDPOINT, PRESIGNED_DOCS_ENDPOINT, PRESIGNED_PUBLIC_URL_ENDPOINT, PRESIGNED_ATTACH_ENDPOINT } = selectedConfig;
