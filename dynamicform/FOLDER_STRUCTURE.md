# Project Folder Structure

This document describes the reorganized folder structure for the dynamicform application.

## Structure Overview

```
dynamicform/
├── src/                          # Frontend source code
│   ├── components/               # Reusable UI components
│   │   ├── common/              # Common components (buttons, inputs, etc.)
│   │   └── forms/               # Form-specific components
│   ├── pages/                   # Route/page components
│   │   ├── SignIn.tsx
│   │   └── Welcome.tsx
│   ├── services/                # API calls & external services
│   │   └── api/                 # API client, endpoints
│   ├── hooks/                   # Custom React hooks
│   ├── utils/                   # Helper functions
│   │   └── mocks/               # Mock data
│   │       └── mock-data.tsx
│   ├── types/                   # TypeScript type definitions
│   ├── config/                  # App configuration
│   │   ├── index.ts             # Main config with env switching
│   │   ├── dev.ts               # Dev-specific config
│   │   └── prod.ts              # Prod-specific config
│   ├── assets/                  # Images, fonts, static files
│   ├── styles/                  # Global styles, themes
│   ├── App.tsx                  # Main app component
│   └── main.tsx                 # Application entry point
│
├── server/                      # Backend-for-Frontend
│   ├── index.ts                 # Server entry point (auth backend)
│   ├── routes/                  # API routes
│   ├── middleware/              # Auth, logging, etc.
│   ├── services/                # Business logic
│   └── config/                  # Server config (dev/prod)
│       ├── index.ts
│       ├── dev.ts
│       └── prod.ts
│
├── config/                      # Root-level build configs
│   ├── vite.config.ts           # Vite configuration
│   └── tsconfig.json            # TypeScript configuration (at root)
│
├── public/                      # Static assets served directly
│   ├── data.json
│   └── metadata.json
│
├── .env.development             # Dev environment vars
├── .env.production              # Prod environment vars
├── .env.example                 # Template for env vars
├── package.json
├── tsconfig.json
└── index.html
```

## Key Features

### 1. Environment-Based Configuration

**Frontend (`src/config/`):**
- `index.ts` - Dynamically imports dev or prod config based on `import.meta.env.MODE`
- `dev.ts` - Development configuration with localhost URLs
- `prod.ts` - Production configuration reading from environment variables

**Backend (`server/config/`):**
- `index.ts` - Dynamically imports dev or prod config based on `NODE_ENV`
- `dev.ts` - Development server settings
- `prod.ts` - Production server settings

### 2. Path Aliases

Configured in both `tsconfig.json` and `vite.config.ts`:

```typescript
{
  "@/*": "./src/*",
  "@components/*": "./src/components/*",
  "@pages/*": "./src/pages/*",
  "@services/*": "./src/services/*",
  "@hooks/*": "./src/hooks/*",
  "@utils/*": "./src/utils/*",
  "@types/*": "./src/types/*",
  "@config/*": "./src/config/*",
  "@assets/*": "./src/assets/*"
}
```

Usage example:
```typescript
import { Welcome } from '@pages/Welcome';
import { API_BASE_URL } from '@config';
```

### 3. Environment Files

- `.env.development` - Development environment variables
- `.env.production` - Production environment variables
- `.env.example` - Template showing required variables

**Important:** Never commit `.env.development` or `.env.production` with actual credentials.

### 4. Updated Scripts

```json
{
  "dev": "vite --config config/vite.config.ts",
  "dev:auth": "tsx watch server/index.ts",
  "start:auth": "tsx server/index.ts",
  "build": "vite build --config config/vite.config.ts",
  "build:auth": "tsc server/index.ts --outDir dist --module nodenext --moduleResolution nodenext",
  "preview": "vite preview --config config/vite.config.ts"
}
```

## Migration Notes

### What Changed

1. **Frontend:**
   - `index.tsx` → `src/App.tsx` + `src/main.tsx`
   - `config.ts` → `src/config/` (split into dev/prod)
   - `src/SignIn.tsx` → `src/pages/SignIn.tsx`
   - `src/Welcome.tsx` → `src/pages/Welcome.tsx`
   - `mock-data.tsx` → `src/utils/mocks/mock-data.tsx`

2. **Backend:**
   - `auth_backend.ts` → `server/index.ts`

3. **Configuration:**
   - `vite.config.ts` → `config/vite.config.ts`
   - `.env.local` → `.env.development`

4. **Static Assets:**
   - `data.json` → `public/data.json`
   - `metadata.json` → `public/metadata.json`

### Import Updates

All imports in `src/App.tsx` have been updated to use path aliases:
```typescript
// Old
import { INDUSTRY_DATA } from './mock-data.tsx';
import { API_BASE_URL } from './config';

// New
import { INDUSTRY_DATA } from '@/src/utils/mocks/mock-data';
import { API_BASE_URL } from '@/src/config';
```

## Benefits

1. **Clear Separation of Concerns:** Frontend, backend, and configuration are clearly separated
2. **Scalability:** Easy to add new features in appropriate directories
3. **Environment Management:** Single source of truth for dev/prod configurations
4. **Developer Experience:** Path aliases reduce relative path complexity
5. **Industry Best Practices:** Follows React + BFF architecture patterns

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy environment template:
   ```bash
   cp .env.example .env.development
   ```

3. Update `.env.development` with your values

4. Run development servers:
   ```bash
   # Terminal 1: Frontend
   npm run dev

   # Terminal 2: Auth Backend
   npm run dev:auth
   ```

5. Build for production:
   ```bash
   npm run build
   npm run build:auth
   ```
