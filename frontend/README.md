# Factor Attribution Lens — frontend

React (Vite + TypeScript) + Tailwind CSS + shadcn/ui single-page app.
See the [project root README](../README.md) for how this fits into the
whole app (the FastAPI backend it talks to, dev vs. production run modes,
project layout) and `docs/decisions/0017-phase10h-identity-for-react-stack.md`
/ `docs/decisions/0018-phase10i-react-rebuild.md` for the design/
implementation decisions behind it.

```bash
npm install
npm run dev      # dev server, proxies /api/* to the backend on :8000
npm run build    # production build -> dist/ (served by the FastAPI backend)
npx tsc -b       # typecheck
npm run lint     # oxlint
```
