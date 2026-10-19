# Novoya web

React + TypeScript + Vite, with TanStack Router (file-based routes), TanStack Query and TanStack Form. See [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).

How `src/` is organised:

- Screens, in Atomic Design: [docs/ATOMIC.md](docs/ATOMIC.md)
- Business rules (`src/domain/`): [docs/DOMAIN.md](docs/DOMAIN.md)
- React hooks (`src/hooks/`): [docs/HOOKS.md](docs/HOOKS.md)
- Translations, English and French (`src/i18n/`): [docs/I18N.md](docs/I18N.md)

## Styling

Tailwind CSS 4, with the design tokens from the Figma Make mockup in `src/index.css` (`@theme`): colours (`ink`, `ivory`, `paper`, `sand`, `coral`, `sage`, `muted`, `line`), the fonts (DM Sans for text, Gloock for headings) and shadows. Use the tokens (`bg-ink`, `text-muted`, `font-serif`), not raw hex values.

shadcn/ui components live in `src/components/ui/` (`components.json` is set up). Add one with `pnpm dlx shadcn@latest add <name>`, then check its imports use `@/lib/utils`. They are for interactive parts that need keyboard and screen-reader support (menus, tabs); our own atoms, molecules and organisms are built on top.

`@/` points to `src/`.

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
