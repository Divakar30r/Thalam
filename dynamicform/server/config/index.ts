// Server configuration with environment-based selection
const env = process.env.NODE_ENV || 'development';

// Import appropriate config based on environment
const configModule = env === 'production'
  ? await import('./prod.js')
  : await import('./dev.js');

export const serverConfig = configModule.config;
