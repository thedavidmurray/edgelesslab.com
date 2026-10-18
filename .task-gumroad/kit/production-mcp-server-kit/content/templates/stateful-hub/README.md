# Stateful Hub MCP Server

A durable, lease/ack message hub for inter-session communication. Built with
Bun + `bun:sqlite` (WAL mode) and the official `@modelcontextprotocol/sdk`.

This is the template that backs the "stateful hub" pattern in the guide. It is
the same architecture used in production by Agent Bus and similar
multi-session message routers.

## What it does

- Persistent SQLite-backed mailboxes (one per session)
- Lease/ack lifecycle so consumers can fail without losing messages
- Background sweeper retries expired leases and dead-letters poison messages
- HTTP `/health` and `/metrics` endpoints on port `9800` (Prometheus-shaped)
- Graceful shutdown on `SIGTERM` (drains, closes the DB)

## MCP tools exposed

| Tool   | Purpose                                              |
|--------|------------------------------------------------------|
| `send` | Push a payload onto a session's mailbox              |
| `lease`| Lease the next pending message (claims it for ~30s)  |
| `ack`  | Mark a leased message complete                       |
| `nack` | Return a leased message to pending with a reason     |
| `stats`| Pending / leased / dead-letter counts                |

## Run it (Bun)

```bash
bun install
bun run src/index.ts
```

The MCP server speaks stdio. The HTTP health server listens on `:9800`:

```bash
curl http://localhost:9800/health
curl http://localhost:9800/metrics
```

## Run it (no Bun)

If `bun` isn't available, the same code runs under Node 20+ via `tsx`, but you
will need to swap `bun:sqlite` for `better-sqlite3` (the API is nearly
identical) and skip the `Bun.serve` health endpoint or substitute `node:http`.

```bash
npm install
npm run dev:node
```

## Inspect the SQLite DB

```bash
sqlite3 ./hub.db ".schema"
sqlite3 ./hub.db "SELECT id, status, attempts FROM messages LIMIT 20;"
sqlite3 ./hub.db "SELECT * FROM dead_letters;"
```

WAL mode means readers don't block writers, so you can run `sqlite3` queries
against the live DB without taking the hub down.

## Environment

| Var              | Default        | Meaning                                |
|------------------|----------------|----------------------------------------|
| `HUB_PORT`       | `9800`         | HTTP health/metrics port               |
| `HUB_DB`         | `./hub.db`     | SQLite path                            |
| `HUB_LEASE_MS`   | `30000`        | Lease duration before retry            |
| `HUB_MSG_TTL_MS` | `86400000`     | Hard TTL before dead-letter (24h)      |
| `HUB_SWEEP_MS`   | `5000`         | Sweeper interval                       |
| `HUB_MAX_ATTEMPTS`| `5`           | Attempts before dead-lettering         |

## Schema

See `src/schema.sql`. The relevant indexes:

- `idx_messages_status`
- `idx_messages_session_id`
- `idx_messages_session_status`
- `idx_messages_expires_at`

These keep the lease query (`SELECT ... WHERE session_id = ? AND status =
'pending' ORDER BY created_at LIMIT 1`) at sub-millisecond latency even with
hundreds of thousands of rows.

## Lease/ack lifecycle

```
                 send()
                   |
                   v
              [pending] <-----+
                   |          |
                lease()       |  nack() / lease expired
                   |          |
                   v          |
              [leased] -------+
                   |
                  ack()
                   |
                   v
              [acked] (eventually swept)

   Past TTL or attempts >= MAX_ATTEMPTS  ->  dead_letters table
```

## License

MIT (same as the rest of the kit).
