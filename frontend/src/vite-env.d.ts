/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Vite only injects variables present in the loaded .env files — the repo
  // ships only .env.example, so every variable must be treated as optional.
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_TITLE?: string;
  readonly VITE_APP_VERSION?: string;
  /** First-party analytics 上报总开关；缺省/false = 关闭（A9-20261030-04 签字后才置 true）。 */
  readonly VITE_ANALYTICS_ENABLED?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
