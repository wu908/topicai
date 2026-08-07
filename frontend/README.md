# TopicAI Frontend

React 19, TypeScript 6, Vite, MUI, and Zustand frontend for the v2-only TopicAI workspace.

The active product routes are Today, Content, Opportunities, Materials, and Me. Removed tool routes are not redirected and render the normal Not Found view.

## Development

```powershell
pnpm install --frozen-lockfile
pnpm --dir frontend dev
```

The Vite development server is available at `http://127.0.0.1:5173` and calls `/api/v2`.

## Quality Gates

```powershell
pnpm --dir frontend lint
pnpm --dir frontend test
pnpm --dir frontend build
```

## End-to-End

Start the backend on `127.0.0.1:8765`; Playwright starts Vite on port `5173`.

```powershell
pnpm --dir frontend exec playwright install chromium
pnpm --dir frontend exec playwright test e2e/starter-flow.spec.ts e2e/intent-driven-loop.spec.ts
```

CI uses `playwright install --with-deps chromium`. The current resolved Playwright version is `1.62.0`, so reinstall Chromium after changing the package version.

The E2E suite covers a Starter publication/review, a Growth manual-source verification/adoption flow with Canvas PNG export, offline draft recovery, and all five primary navigation nodes at desktop and mobile widths.

Authentication tokens are obtained and refreshed through `/api/v2/auth/*` only.
