# TopicAI Frontend

React 19, TypeScript 6, Vite, MUI, and Zustand frontend for the v2-only TopicAI workspace.

The active product routes are Today, Content, Opportunities, Materials, and Me. Removed tool routes are not redirected and render the normal Not Found view.

## Development

```powershell
npm.cmd install
npm.cmd run dev
```

The Vite development server is available at `http://127.0.0.1:5173` and calls `/api/v2`.

## Quality Gates

```powershell
npm.cmd run lint
npm.cmd test -- --run
npm.cmd run build
```

Authentication tokens are obtained and refreshed through `/api/v2/auth/*` only.
