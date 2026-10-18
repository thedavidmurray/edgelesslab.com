# CLAUDE.md - Monorepo

## Role
You are an AI assistant for a monorepo containing multiple packages and applications. You enforce package boundaries, shared tooling standards, and coordinated release workflows. You understand that changes can have cross-package effects.

## Key Rules
1. **Understand the dependency graph first** — Before modifying any package, check what depends on it (`pnpm why <package>` or `nx graph`). A change in a shared utility affects every consumer.
2. **Package boundaries are strict** — Packages must not import from sibling apps directly. All shared code lives in `packages/`. Never use relative paths that cross package boundaries.
3. **One version policy** — All packages in the repo share the same version for internal deps. Avoid peer-dependency drift. Run the dep-check script before any PR.
4. **Changesets for releases** — Every PR that changes user-facing behavior needs a changeset (`pnpm changeset`). Never manually bump `package.json` versions.
5. **Affected-only CI** — Only run tests/builds for packages affected by the diff. Use `nx affected` or Turborepo filtering to keep CI fast.
6. **Shared config is the source of truth** — ESLint, TypeScript, Prettier configs live in `packages/config-*`. Individual packages extend them, never override them.
7. **Document cross-package APIs** — When a package exports a public API, it must have a JSDoc comment and appear in that package's `README.md`.

## Project Structure
```
monorepo/
├── apps/                   # Deployable applications
│   ├── web/                # Web application
│   ├── api/                # API server
│   └── admin/              # Admin dashboard
├── packages/               # Shared libraries
│   ├── ui/                 # Shared component library
│   ├── utils/              # Shared utilities
│   ├── types/              # Shared TypeScript types
│   ├── config-eslint/      # Shared ESLint config
│   ├── config-typescript/  # Shared tsconfig bases
│   └── config-tailwind/    # Shared Tailwind config
├── tooling/                # Internal build tools, scripts
├── .changeset/             # Changeset files
├── pnpm-workspace.yaml     # Workspace definition
├── turbo.json              # Turborepo pipeline config
└── package.json            # Root package (no prod deps)
```

## Patterns
**Adding a new package:**
1. `mkdir packages/my-pkg && cd packages/my-pkg`
2. `pnpm init` with `name: "@org/my-pkg"`
3. Add to `pnpm-workspace.yaml` if needed (wildcard usually covers it)
4. Extend shared configs: `"extends": ["@org/config-eslint"]`
5. Add to `turbo.json` pipeline if it has a build step

**Cross-package change workflow:**
1. Identify all affected packages with `nx graph` or `turbo run build --dry`
2. Make changes in dependency order (lowest-level package first)
3. Write a changeset: `pnpm changeset` — select all affected packages
4. Run `pnpm turbo run test --filter=...[HEAD^1]` to verify

**Dependency updates:** Use `pnpm update --recursive --latest` for minor bumps. For major bumps, update one package at a time and run affected tests.

## Testing
- **Unit tests:** Each package runs its own tests in isolation with `pnpm --filter @org/utils test`.
- **Integration tests:** Cross-package integration tests live in `apps/` or a dedicated `e2e/` package.
- **Type-check all:** `pnpm turbo run type-check` must pass across the entire graph.
- **CI strategy:** On PR, run `turbo run test lint build --filter=...[origin/main]`.

## Commands
```bash
pnpm turbo run build                                   # Build all
pnpm turbo run test --filter=...[HEAD^1]               # Test affected
pnpm --filter @org/ui dev                              # Dev single package
pnpm changeset                                         # Create changeset
pnpm changeset version                                 # Bump versions
pnpm changeset publish                                 # Publish to registry
```

---
© 2026 Edgeless Labs LLC. All rights reserved.
