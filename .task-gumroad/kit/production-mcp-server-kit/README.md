# Production MCP Server Kit

Take MCP servers past the tutorial stage. Auth, rate limiting, Docker, health checks, and error handling from running 4+ servers in production.

## What's Inside

- **guide.md / guide.pdf** -- 8-chapter guide covering typed servers, stateful hubs, API proxies, subprocess bridges, fallback patterns, Docker deployment, and testing
- **templates/** -- 2 production server templates (Effect-TS typed server, API proxy with auth/caching/rate limiting)
- **scripts/** -- Python subprocess IPC bridge
- **docker/** -- Dockerfile + Compose for containerized deployment

## Quick Start

### Typed Server (Effect-TS)
```bash
cd templates/typed-server
bun install
bun run dev
```

### API Proxy
```bash
cd templates/api-proxy
bun install
EXTERNAL_API_KEY=your-key bun run dev
```

### Docker Deployment
```bash
cd docker
docker compose up -d
curl http://localhost:9800/health
```

## Prerequisites

- Bun 1.1+ or Node.js 20+ with tsx
- Docker (for containerized deployment)

## Version

1.0.0 -- Initial release, April 2026
