import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
    return {
      root: path.resolve(__dirname, '..'),
      server: {
        port: 3000,
        host: '0.0.0.0',
        proxy: {
          '/auth': {
            target: 'http://localhost:8002',
            changeOrigin: true,
            secure: false,
            ws: true,
            cookieDomainRewrite: 'localhost',
            rewrite: (path) => path, // Keep the path as-is
          },
          '/api/v1/documents': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            cookieDomainRewrite: 'localhost',
          },
          '/api/v1/public-url': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            cookieDomainRewrite: 'localhost',
          },
          '/api/v1/presigned-upload': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            cookieDomainRewrite: 'localhost',
          },
          '/api/v1/status': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            cookieDomainRewrite: 'localhost',
          },
          '/api/v1/assign-to-order': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            cookieDomainRewrite: 'localhost',
          },
        },
        // Ensure /auth routes are not handled by the SPA
        middlewareMode: false,
      },
      // Add a tiny logging plugin so incoming /auth requests show up in the Vite terminal.
      // This helps verify the dev-server proxy is seeing the request before forwarding it.
      plugins: [
        // simple logger plugin
        {
          name: 'vite:log-auth-requests',
          configureServer(server) {
            server.middlewares.use((req, res, next) => {
              try {
                if (req && req.url && req.url.startsWith('/auth')) {
                  console.log('[VITE] proxied request ->', req.method, req.url);
                }
              } catch (e) {
                // ignore
              }
              next();
            });
          },
        },
        react(),
      ],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        // expose Order Form client id to the frontend build (use VITE_ORDERFORM_CLIENT_ID in .env)
  // Only expose VITE_ORDERFORM_CLIENT_ID if explicitly provided (do NOT leak server-only KEYCLOAK vars)
  'process.env.VITE_ORDERFORM_CLIENT_ID': JSON.stringify(env.VITE_ORDERFORM_CLIENT_ID || ''),
  'import.meta.env.VITE_ORDERFORM_CLIENT_ID': JSON.stringify(env.VITE_ORDERFORM_CLIENT_ID || ''),
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '../src'),
          '@components': path.resolve(__dirname, '../src/components'),
          '@pages': path.resolve(__dirname, '../src/pages'),
          '@services': path.resolve(__dirname, '../src/services'),
          '@hooks': path.resolve(__dirname, '../src/hooks'),
          '@utils': path.resolve(__dirname, '../src/utils'),
          '@types': path.resolve(__dirname, '../src/types'),
          '@config': path.resolve(__dirname, '../src/config'),
          '@assets': path.resolve(__dirname, '../src/assets'),
        }
      }
    };
});
