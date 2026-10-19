# Novoya web

React + TypeScript + Vite, with TanStack Router (file-based routes), TanStack Query and TanStack Form. See [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).

How `src/` is organised:

- Screens, in Atomic Design: [docs/ATOMIC.md](docs/ATOMIC.md)
- Business rules (`src/domain/`): [docs/DOMAIN.md](docs/DOMAIN.md)
- React hooks (`src/hooks/`): [docs/HOOKS.md](docs/HOOKS.md)

## Run locally

Needs Node 22.22.2+ (or 24.15+) and pnpm. The API should run on http://localhost:8000: the dev server proxies `/api` to it (set `API_PROXY_TARGET` otherwise), so the browser only talks to http://localhost:5173 ([ADR 0011](../../docs/adr/0011-same-origin-api-proxy.md)).

```bash
cp .env.example .env
pnpm install
pnpm dev
```

The app runs on http://localhost:5173.

## Generated code

Both are created by `pnpm gen`, which `dev`, `build`, `typecheck` and `test` run first. They are not committed.

- `src/api/generated/`: the typed API client and TanStack Query helpers, from `../api/openapi.json`.
- `src/routeTree.gen.ts`: the route tree, from the files in `src/routes/`.

To call an endpoint, use the generated query options:

```tsx
import { useQuery } from '@tanstack/react-query'
import { getHealthOptions } from '../api/generated/@tanstack/react-query.gen'

const { data } = useQuery(getHealthOptions())
```

## Checks

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```
