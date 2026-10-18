# traffic-1000 decisions

## Consent gate broke visitor measurement (09-12-2026)

**Root cause:** Commit 8da20f800 made analytics opt-in only. `posthog.init`
runs only when localStorage `edgeless.analytics-consent.v1` === "accepted".
PostHog daily events dropped from 40-61/week to 0-1.

**Fix:** Cookieless pre-consent tracking. `posthog.init` always runs with
`cookieless_mode: "always"`, `persistence: "memory"`, `capture_pageview: false`.
Every route change sends an anonymous `$pageview` with `site=main`. No cookies,
no localStorage, no identifiers — no consent needed.

After Accept: full mode with `capture_pageview: true`, `cross_subdomain_cookie: true`.
Reject: cookieless only, never zero.

**Caveat for traffic_scoreboard.py:** Cookieless unique counting uses a daily
hash, not PostHog `distinct_id`. Counts may differ from consented distinct_id
metrics. Read the scoreboard as anonymous pageview count, not unique visitors.