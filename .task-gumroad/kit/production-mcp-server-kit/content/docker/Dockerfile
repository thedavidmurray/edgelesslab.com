# Production Dockerfile for the Stateful Hub MCP server.
#
# This Dockerfile targets templates/stateful-hub, which is the only shipped
# template that exposes an HTTP /health endpoint (via Bun.serve on port 9800).
# The other templates (typed-server, api-proxy) speak stdio only and should
# be wrapped with a process-supervisor or run inline by an MCP client.
#
# Build (from product root):
#   docker build -f content/docker/Dockerfile \
#                -t mcp-stateful-hub \
#                content/templates/stateful-hub
#
# Or, with the docker-compose.yml in this directory:
#   docker compose -f content/docker/docker-compose.yml up --build

FROM oven/bun:1.1 AS builder
WORKDIR /app
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile || bun install
COPY src/ src/
COPY tsconfig.json* ./

FROM oven/bun:1.1-slim
WORKDIR /app

# curl is required for HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/src ./src
COPY --from=builder /app/package.json ./

# Persistent SQLite volume
VOLUME ["/data"]
ENV HUB_DB=/data/hub.db \
    HUB_PORT=9800

EXPOSE 9800

# /health is served by Bun.serve inside src/index.ts
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:9800/health || exit 1

# Non-root user
RUN adduser --disabled-password --gecos '' mcp \
  && chown -R mcp:mcp /app /data
USER mcp

CMD ["bun", "run", "src/index.ts"]
