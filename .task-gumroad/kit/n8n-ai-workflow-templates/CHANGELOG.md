# Changelog

## 1.1.0 (2026-04-07)

Quality pass: workflows are now genuinely import-and-go.

- **Fixed**: docker-compose now actually wires n8n to the bundled Postgres (added `DB_TYPE=postgresdb` and 5 `DB_POSTGRESDB_*` env vars). The 1.0.0 release shipped a Postgres container that n8n ignored, falling back to SQLite.
- **Fixed**: pinned n8n image to `n8nio/n8n:1.70.0` (was `:latest`).
- **Fixed**: removed deprecated `N8N_BASIC_AUTH_USER/PASSWORD` from `.env.example`. n8n 1.x uses owner-setup wizard.
- **Fixed**: all 5 workflows now read `GOOGLE_GEMINI_API_KEY` directly from env via `?key={{ $env.GOOGLE_GEMINI_API_KEY }}` query param. No node editing required after import.
- **Fixed**: `rss-intelligence-feed.json` now ships with a Telegram send node wired to the format step (was a dangling stub).
- **Fixed**: `content-digest-generator.json` now ships with an `emailSend` node wired to the HTML compile step (was a dangling stub).
- **Fixed**: `health-check-alerts.json` IF node now has both branches wired (Telegram alert on true, no-op on false). Added `./health-state` volume mount so failure counters survive container restarts.
- **Fixed**: `ai-code-review-webhook.json` now uses `GITHUB_TOKEN` env var directly instead of requiring an n8n credential setup.
- **Fixed**: `start.sh` now validates `GOOGLE_GEMINI_API_KEY` and `POSTGRES_PASSWORD` before starting Docker, fails fast with a clear message if either is missing or still a placeholder.
- **Added**: Postgres healthcheck and n8n healthcheck blocks in docker-compose.yml.
- **Expanded**: guide.md grew from ~1,900 words to ~5,000 words. New chapters: Credentials Walkthrough (with three failure modes per credential), LLM Swapping (concrete JSON snippets for OpenAI, Anthropic, Ollama), Troubleshooting (10 real failure modes), Why We Pin n8n, Going to Production, Observability, and Scope.
- **Added**: 5 mermaid diagrams in guide.md (architecture, credential flow, YouTube workflow, RSS workflow, health-check state machine).

## 1.0.0 (2026-04-02)

Initial release.

- 5 importable n8n workflow JSON files
- Docker Compose setup with Postgres
- 8-chapter guide covering setup, customization, and troubleshooting
- Environment template with all required variables
- Start script with health check verification
