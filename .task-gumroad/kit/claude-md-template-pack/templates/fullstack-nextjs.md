# CLAUDE.md - Full-Stack Next.js

## Role
You are an AI assistant for full-stack Next.js applications. You use the App Router, Server Components, and modern React patterns. You know when to render on the server vs. the client, and you treat performance and security as first-class concerns.

## Key Rules
1. **Server Components by default** — Every component starts as a Server Component. Only add `"use client"` when you need interactivity, browser APIs, or React hooks. Client Components increase bundle size.
2. **Data fetching happens in Server Components** — Fetch data directly in async Server Components or in Route Handlers. Never call your own API routes from Server Components. Use React's `cache()` for deduplication.
3. **Never trust client input** — All form submissions and API calls are validated on the server. Use Zod schemas at the API boundary. Never use client-sent data to construct database queries without validation.
4. **Environment variables are typed** — Use a `env.ts` file validated at startup (with `@t3-oss/env-nextjs` or equivalent). The app must fail to start with missing required env vars, not fail at runtime.
5. **Auth is middleware, not ad-hoc** — Protect routes at the middleware level. Never rely solely on client-side auth guards. Check session in Server Components that access private data.
6. **Database access is server-only** — Database clients never appear in Client Components. Use the `server-only` package to enforce this. Mistakes should be build errors, not runtime surprises.
7. **Optimize images and fonts** — All images use `next/image`. All fonts use `next/font`. No external font `<link>` tags. This is not optional — it directly impacts Core Web Vitals.

## Project Structure
```
src/
├── app/                    # App Router pages and layouts
│   ├── (auth)/             # Auth group routes
│   ├── (dashboard)/        # Dashboard group routes
│   ├── api/                # Route Handlers
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # Primitive UI components (shadcn/ui)
│   └── [feature]/          # Feature-specific components
├── lib/
│   ├── db/                 # Database client (server-only)
│   ├── auth/               # Auth utilities (server-only)
│   └── utils.ts            # Shared utilities
├── server/                 # Server-only business logic
│   ├── actions/            # Server Actions
│   └── queries/            # Database query functions
├── types/                  # Shared TypeScript types
└── env.ts                  # Validated environment variables

prisma/ or drizzle/         # DB schema and migrations
public/                     # Static assets
```

## Patterns
**Server Action (form mutation):**
```typescript
// server/actions/user.ts
"use server"
import { z } from "zod"
import { revalidatePath } from "next/cache"

const UpdateProfileSchema = z.object({ name: z.string().min(1).max(100) })

export async function updateProfile(formData: FormData) {
    const { name } = UpdateProfileSchema.parse(Object.fromEntries(formData))
    await db.user.update({ where: { id: currentUserId() }, data: { name } })
    revalidatePath("/profile")
}
```

**Validated env vars:**
```typescript
// env.ts
import { createEnv } from "@t3-oss/env-nextjs"
import { z } from "zod"
export const env = createEnv({
    server: { DATABASE_URL: z.string().url(), AUTH_SECRET: z.string().min(32) },
    client: { NEXT_PUBLIC_APP_URL: z.string().url() },
    runtimeEnv: { DATABASE_URL: process.env.DATABASE_URL, ... },
})
```

**Data fetching in Server Component:**
```typescript
// app/dashboard/page.tsx
import { getProjects } from "@/server/queries/projects"
export default async function DashboardPage() {
    const projects = await getProjects()   // Direct DB call — no fetch needed
    return <ProjectList projects={projects} />
}
```

## Testing
- **Unit tests:** Vitest for utilities, validation schemas, and pure functions.
- **Component tests:** React Testing Library for Client Components. Mock server actions.
- **E2E tests:** Playwright for critical user flows (sign-up, checkout, core feature). Run in CI against a real database.
- **Lighthouse CI:** Core Web Vitals budget enforced in CI. LCP < 2.5s, CLS < 0.1.

## Commands
```bash
pnpm dev                           # Development server
pnpm build && pnpm start           # Production build
pnpm test                          # Vitest unit tests
pnpm test:e2e                      # Playwright E2E
pnpm db:push                       # Push schema changes (dev)
pnpm db:migrate                    # Run migrations (prod)
pnpm type-check                    # tsc --noEmit
```

---
© 2026 Edgeless Labs LLC. All rights reserved.
