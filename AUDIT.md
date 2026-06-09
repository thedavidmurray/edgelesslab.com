# Codebase Audit — edgelesslab.com

Date: 2026-06-09
Scope: full repository — build/deploy pipeline, repo health, source code, tooling.

## Status (updated on this branch)

Fixed in this PR: §P0-1 (deploy race — workflow is manual-only), §P0-2 (PostHog
env wiring; set the `NEXT_PUBLIC_POSTHOG_KEY` repo variable to activate),
§P0-3 (lint works on fresh clones), §P0-4 (AGENTS.md created), stale `out/`
untracked, unreferenced `data/` CSVs removed, junk favicon files deleted, and
**all** §P2 code findings (setState-in-effect refactors, ref-during-render
bug, dead state/imports, playwright → devDependencies, scoped ESLint).
`npm run lint` and `tsc --noEmit` are clean; `set-state-in-effect` is enforced
at error severity again.

Still open (requires owner action): the R2 asset migration (needs a
Cloudflare account — follow `scripts/r2-migration-steps.md`), deleting root
build output after single-sourcing deployment, and the git history rewrite
(§P1 step 4 below — needs a coordinated force-push to `main`).

Verification performed: fresh `npm ci`, `tsc --noEmit` (clean), `eslint`, full
`next build` (succeeds), GitHub Actions run history, and inspection of both the
committed build output and a freshly built `out/`.

---

## P0 — Things that are actively broken or racing

### 1. Two GitHub Pages deployments race on every push

Every push to `main` triggers **both**:

- the legacy branch-based pipeline (`pages build and deployment`, event
  `dynamic`): checks out the branch and publishes the **repo root**;
- the custom workflow (`.github/workflows/deploy.yml`): runs `npm run build`
  and publishes **`out/`**.

On the last push they finished 3 seconds apart (23:11:55 vs 23:11:58 UTC).
Whichever deployment lands last is what visitors see — i.e. the live site
content is **nondeterministic**.

The two artifacts differ materially:

- The branch root contains `pen-plotter/assets/` (69,477 files, 1.2 GB).
- The CI build's `out/` does **not** contain those assets:
  `public/pen-plotter/assets/` is gitignored, so a CI checkout never has them,
  and `out/pen-plotter/` ends up with only the HTML files. The pen-plotter
  pages reference relative `assets/...` URLs, so **when the Actions deploy
  wins the race, every pen-plotter image 404s**.

**Fix:** pick exactly one deployment source.

- *Short term (preserves current content):* set Pages source to
  "Deploy from a branch" explicitly and delete/disable
  `.github/workflows/deploy.yml` — the committed root output is already what
  the agents maintain.
- *Long term (recommended):* finish the Cloudflare R2 asset migration that is
  already half-built (`scripts/deploy-pen-plotter-assets.sh`,
  `scripts/r2-migration-steps.md`), point pen-plotter pages at
  `assets.edgelesslab.com`, switch Pages source to "GitHub Actions", and stop
  committing build output entirely (see §4).

### 2. PostHog analytics is silently dead in production

`src/components/posthog-provider.tsx` reads
`process.env.NEXT_PUBLIC_POSTHOG_KEY` and silently no-ops when it's unset.

- `deploy.yml` passes no env vars to `npm run build`.
- No `phc_…` key exists in the committed build output (`_next/`) **or** in a
  fresh build — so no deployed variant of the site has ever initialized
  PostHog from CI.

**Fix:** add `NEXT_PUBLIC_POSTHOG_KEY` as a repository variable and inject it
in the build step:

```yaml
- run: npm run build
  env:
    NEXT_PUBLIC_POSTHOG_KEY: ${{ vars.NEXT_PUBLIC_POSTHOG_KEY }}
```

(Also applies to whatever machine produces the root-committed build, if the
branch pipeline is kept.)

### 3. `npm run lint` fails on any fresh clone

`lint:voice` calls `../scripts/lint-voice.sh` — a path **outside the
repository** (it exists only on the original dev machine). Same class of
problem: `scripts/deploy-pen-plotter-assets.sh` hardcodes
`/Users/djm/claude-projects/edgeless-website/...`.

**Fix:** vendor `lint-voice.sh` into `scripts/` (or guard the npm script), and
derive the asset path in the deploy script from the repo root.

### 4. `CLAUDE.md` imports a file that doesn't exist

`CLAUDE.md` contains only `@AGENTS.md`, but there is no `AGENTS.md` in the
repo. Agents get zero project instructions. Either restore `AGENTS.md` or put
real instructions in `CLAUDE.md`.

---

## P1 — Repository health (1 GB repo for a 36 MB site)

The git pack is **1.02 GiB** and the repo tracks **71,632 files**, while a
full production build (`out/`) is 36 MB. Breakdown:

| What | Size / count | Notes |
|---|---|---|
| `pen-plotter/assets/` | 1.2 GB, 69,477 files | Generated art specimens; the R2 migration was designed for exactly this and never completed |
| `data/*.csv` | 124 MB (objects.csv 81 MB) | Referenced by nothing in `src/` or `scripts/` — appears to be leftover source data |
| Committed build output at root | `index.html`, `_next/`, `404.html`, `blog/`, `lab/`, `products/`, `projects/`, `__next.*.txt`, `index.txt`, `feed.xml`, `sitemap.xml`, `robots.txt`, … | Required only by the legacy branch deploy (§1) |
| `out/` (354 tracked files) | 13 MB | Gitignored *now* but still tracked — a local build immediately shows them all as deleted/stale |
| Junk files | `favicon.ico?favicon.0x3dzn~oxb6tn.ico` (root **and** `public/`), `src/app/favicon.ico.bak` | Accidental artifacts |

Consequences: slow clones, ~1 GB CI checkouts, GitHub Pages' 1 GB site limit
is already at the wire, and `git status` noise that spawned the
`preserve-standalone.sh` workaround.

**Fixes (in order):**
1. Complete the R2 migration; remove `pen-plotter/assets/` from the working
   tree.
2. `git rm -r --cached out/ data/` (plus the junk files) and commit.
3. Once the deployment is single-sourced via Actions, delete all root-level
   build output.
4. Optionally rewrite history with `git-filter-repo` to actually reclaim the
   1 GB pack. This must be run by the repo owner — it force-pushes `main` and
   invalidates every existing clone. After the R2 migration is live:

   ```bash
   pip install git-filter-repo
   git clone --no-local /path/to/edgelesslab.com edgelesslab-rewrite
   cd edgelesslab-rewrite
   # Drop the heavyweight paths from all history:
   git filter-repo \
     --path pen-plotter/assets --path data --path out \
     --invert-paths
   git remote add origin git@github.com:thedavidmurray/edgelesslab.com.git
   git push --force -u origin main
   ```

   Then have any other machines/agents re-clone (do not pull over an old
   clone). Open PRs based on the old history must be recreated. GitHub may
   need a support request (or repo re-create) to garbage-collect the old
   pack on their side.

### 5. `preserve-standalone.sh` copies 1.2 GB twice per build

`prebuild` rsyncs/tars `pen-plotter/`, `tartanism/`, `total-serialism/`, and
`flow-viz/` to `.standalone-stash/` and back on **every** `npm run build`.
The script exists only because build output is committed alongside source
(its own header says it was created "after tartanism/ was deleted twice by
rebuild commits"). It disappears entirely once §1/§4 are resolved.

---

## P2 — Source code quality

`tsc --noEmit` is clean and the production build succeeds. ESLint on `src/`
reports **14 errors and 14 warnings**:

- **12× "Calling setState synchronously within an effect"** — cascading
  render risk in `ascii-art-generator.tsx`, `attractor-playground.tsx`,
  `blog-article.tsx`, `generative-ascii.tsx`, the five `pretext-*` UI
  components, `use-in-view.ts`, `use-shrink-wrap.ts`, `excalidraw-diagrams`.
  Most are measure-then-set patterns that belong in `useLayoutEffect` or
  should derive state during render.
- **`products-grid.tsx:60` — "Cannot access refs during render"** — a real
  React correctness bug; refs read during render are stale under concurrent
  rendering.
- 2× `prefer-const` (`excalidraw-diagrams.tsx:34`, `generative-ascii.tsx:126`).
- 14 unused-variable warnings, including dead `isPlaying`/`setIsPlaying`,
  `isGenerating`, `canvasRef`, and unused icon imports — dead feature code
  worth deleting.

### Other tooling fixes

- **`playwright` is in `dependencies`** — it's tooling, not a runtime dep of a
  static site. Move to `devDependencies` (and keep
  `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` in CI if browsers aren't needed).
- **ESLint lints committed build artifacts** — running bare `eslint` produces
  ~1,240 problems, almost all from minified bundles in `tartanism/app/assets/`,
  `lab/`, `public/flow-viz/`, `total-serialism/`. Add these standalone dirs to
  `globalIgnores` in `eslint.config.mjs` so real errors aren't buried (the 14
  src errors above were invisible inside 923 KB of lint output).
- `src/app/favicon.ico.bak` — delete.

---

## What's in good shape

- TypeScript strict compile is clean; the build is reproducible and fast
  (~90 s in CI).
- Sensible Next.js static-export config (`trailingSlash`, unoptimized images,
  `optimizePackageImports` for lucide).
- `robots.txt`/`robots.ts` deliberately allow AI crawlers with a sitemap —
  consistent with the site's positioning.
- PostHog provider correctly guards initialization and pageview capture
  (it just never receives a key — §2).
- Deploy workflow uses current action versions (`checkout@v4`,
  `setup-node@v4` with npm cache, `deploy-pages@v4`) and proper concurrency
  grouping.

## Suggested order of operations

1. Decide the single deployment source (§1) — everything else gets simpler
   after this.
2. Fix analytics env injection (§2) and the broken lint script (§3).
3. Repo diet: R2 migration, untrack `out/` + `data/`, delete junk (§P1).
4. Fix the 14 ESLint errors in `src/`, prune dead code, move playwright to
   devDeps, scope ESLint ignores (§P2).
