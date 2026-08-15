/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Vite only injects variables present in the loaded .env files — the repo
  // ships only .env.example, so every variable must be treated as optional.
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_TITLE?: string;
  readonly VITE_APP_VERSION?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
