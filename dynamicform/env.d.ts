/// <reference types="vite/client" />

// Provide minimal typings for Vite environment variables used in this project.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
