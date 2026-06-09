# edgelesslab.com — agent instructions

Personal site for Edgeless Lab, deployed at https://edgelesslab.com via
GitHub Pages.

## Architecture (read before touching anything)

This repo is **two things at once**:

1. A Next.js 16 app (`src/`) configured for static export
   (`output: "export"` in `next.config.ts`).
2. The **deployed site itself**, committed at the repo root: GitHub Pages
   serves the `main` branch root via the branch-based "pages build and
   deployment" pipeline. The root-level `index.html`, `_next/`, `blog/`,
   `products/`, etc. are build output that IS the live site.

Standalone (non-Next.js) content lives alongside the build output and must
never be deleted by a rebuild: `pen-plotter/`, `tartanism/`,
`total-serialism/`, `flow-viz/`. `scripts/preserve-standalone.sh` (wired into
`prebuild`/`postbuild`) stashes and restores them around `next build`.

`.github/workflows/deploy.yml` is **manual-trigger only** — see the comment
in that file before re-enabling it on push.

## Commands

- `npm run dev` — local dev server.
- `npm run build` — static export to `out/` (stashes/restores standalone
  dirs automatically).
- `npm run lint` — ESLint (`src/` and config files only) + experiment lint +
  voice lint. The voice linter is an external tool; `scripts/lint-voice.sh`
  skips gracefully when it isn't present.
- `npx tsc --noEmit` — typecheck.

## Deploying changes

To publish: build, then copy the contents of `out/` over the repo root
(preserving the standalone dirs above), commit, and push to `main`. The
branch-based Pages pipeline deploys the root automatically.

## Gotchas

- `public/pen-plotter/assets/` is gitignored; the canonical copies of those
  69k assets live in root `pen-plotter/assets/` (a Cloudflare R2 migration is
  planned — `scripts/r2-migration-steps.md`).
- Analytics (PostHog) requires `NEXT_PUBLIC_POSTHOG_KEY` at build time; it
  silently no-ops without it.
- Do not commit `node_modules/`, `.next/`, `.standalone-stash/`, or new large
  binary datasets — the repo is already ~1 GB.
- `AUDIT.md` documents known issues and the cleanup plan; check it before
  large structural changes.
- Design language and voice guidelines: `DESIGN.md`.
