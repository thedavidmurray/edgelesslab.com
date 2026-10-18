#!/usr/bin/env bun
/**
 * Production MCP Server Template -- Stateful Hub
 *
 * A durable message router that maintains state across requests using
 * SQLite (WAL mode) with prepared statements and a lease/ack lifecycle.
 *
 * Use cases:
 *   - Inter-session message bus for multi-agent systems
 *   - Job queue with at-least-once delivery semantics
 *   - Persistent inbox/outbox between MCP clients
 *
 * Usage:
 *   bun run src/index.ts
 *
 *   # Or, if Bun is not available, transpile and use Node 20+ with better-sqlite3:
 *   #   npm i && npm run dev:node
 *
 * Environment:
 *   HUB_PORT          -- HTTP health endpoint port (default: 9800)
 *   HUB_DB            -- SQLite path (default: ./hub.db)
 *   HUB_LEASE_MS      -- Lease duration before message returns to pending (default: 30000)
 *   HUB_MSG_TTL_MS    -- Hard TTL before message moves to dead-letter (default: 86400000)
 *   HUB_SWEEP_MS      -- Background sweep interval (default: 5000)
 */

import { Database } from "bun:sqlite";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// ============================================================
// CONFIG
// ============================================================

const HUB_PORT = parseInt(process.env.HUB_PORT || "9800", 10);
const HUB_DB = process.env.HUB_DB || "./hub.db";
const LEASE_MS = parseInt(process.env.HUB_LEASE_MS || "30000", 10);
const MSG_TTL_MS = parseInt(process.env.HUB_MSG_TTL_MS || `${24 * 60 * 60 * 1000}`, 10);
const SWEEP_MS = parseInt(process.env.HUB_SWEEP_MS || "5000", 10);
const MAX_ATTEMPTS = parseInt(process.env.HUB_MAX_ATTEMPTS || "5", 10);

const startedAt = Date.now();

// ============================================================
// DB BOOTSTRAP
// ============================================================

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemaPath = join(__dirname, "schema.sql");
const schema = readFileSync(schemaPath, "utf8");

const db = new Database(HUB_DB, { create: true });
db.exec(schema);

// ============================================================
// PREPARED STATEMENTS
// ============================================================

const stmts = {
  ensureSession: db.prepare(
    "INSERT OR IGNORE INTO sessions (name) VALUES (?)"
  ),
  touchSession: db.prepare(
    "UPDATE sessions SET last_seen = datetime('now') WHERE name = ?"
  ),
  insertMessage: db.prepare(`
    INSERT INTO messages (id, session_id, sender, payload, expires_at)
    VALUES (?, ?, ?, ?, datetime('now', '+' || ? || ' seconds'))
  `),
  // Atomically lease the next pending message for a session.
  // RETURNING gives us the row in a single round-trip.
  leaseNext: db.prepare(`
    UPDATE messages
       SET status     = 'leased',
           leased_at  = datetime('now'),
           leased_by  = ?,
           attempts   = attempts + 1
     WHERE id = (
       SELECT id FROM messages
        WHERE session_id = ?
          AND status = 'pending'
          AND datetime(expires_at) > datetime('now')
        ORDER BY created_at ASC
        LIMIT 1
     )
   RETURNING *
  `),
  ackMessage: db.prepare(`
    UPDATE messages
       SET status   = 'acked',
           acked_at = datetime('now')
     WHERE id = ? AND status = 'leased'
   RETURNING id
  `),
  nackMessage: db.prepare(`
    UPDATE messages
       SET status     = 'pending',
           leased_at  = NULL,
           leased_by  = NULL,
           last_error = ?
     WHERE id = ? AND status = 'leased'
   RETURNING id
  `),
  // Sweep: any leased message past its lease window goes back to pending
  // (or to dead-letter if attempts >= MAX_ATTEMPTS).
  expireLeases: db.prepare(`
    UPDATE messages
       SET status     = 'pending',
           leased_at  = NULL,
           leased_by  = NULL,
           last_error = 'lease_expired'
     WHERE status = 'leased'
       AND leased_at IS NOT NULL
       AND datetime(leased_at, '+' || ? || ' seconds') < datetime('now')
       AND attempts < ?
  `),
  deadLetterExpired: db.prepare(`
    INSERT INTO dead_letters (id, session_id, sender, payload, reason)
    SELECT id, session_id, sender, payload,
           CASE WHEN attempts >= ? THEN 'max_attempts' ELSE 'ttl_expired' END
      FROM messages
     WHERE (datetime(expires_at) <= datetime('now') AND status != 'acked')
        OR (status = 'leased' AND attempts >= ?)
  `),
  deleteExpired: db.prepare(`
    DELETE FROM messages
     WHERE (datetime(expires_at) <= datetime('now') AND status != 'acked')
        OR (status = 'leased' AND attempts >= ?)
        OR status = 'acked'
  `),
  pendingCount: db.prepare(
    "SELECT COUNT(*) AS c FROM messages WHERE status = 'pending'"
  ),
  leasedCount: db.prepare(
    "SELECT COUNT(*) AS c FROM messages WHERE status = 'leased'"
  ),
  deadLetterCount: db.prepare(
    "SELECT COUNT(*) AS c FROM dead_letters"
  ),
};

// ============================================================
// CORE OPS
// ============================================================

function genId(): string {
  // Bun has crypto.randomUUID; fall back to a small hex if not.
  // @ts-ignore
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

function send(sessionId: string, sender: string, payload: unknown): string {
  stmts.ensureSession.run(sessionId);
  const id = genId();
  const ttlSec = Math.floor(MSG_TTL_MS / 1000);
  stmts.insertMessage.run(id, sessionId, sender, JSON.stringify(payload), ttlSec);
  return id;
}

function lease(sessionId: string, leaseHolder: string): unknown | null {
  stmts.touchSession.run(sessionId);
  const row = stmts.leaseNext.get(leaseHolder, sessionId) as any;
  if (!row) return null;
  return {
    id: row.id,
    session_id: row.session_id,
    sender: row.sender,
    payload: JSON.parse(row.payload),
    attempts: row.attempts,
    leased_at: row.leased_at,
  };
}

function ack(messageId: string): boolean {
  const row = stmts.ackMessage.get(messageId) as any;
  return !!row;
}

function nack(messageId: string, reason: string): boolean {
  const row = stmts.nackMessage.get(messageId, reason) as any;
  return !!row;
}

function sweep(): { expired: number; deadLettered: number } {
  const expiredRes = stmts.expireLeases.run(Math.floor(LEASE_MS / 1000), MAX_ATTEMPTS);
  // Move expired to dead-letter, then delete from messages.
  stmts.deadLetterExpired.run(MAX_ATTEMPTS, MAX_ATTEMPTS);
  const dl = stmts.deadLetterCount.get() as { c: number };
  const del = stmts.deleteExpired.run(MAX_ATTEMPTS);
  return {
    expired: Number(expiredRes.changes ?? 0),
    deadLettered: dl.c,
  };
}

// Background sweeper: keeps the lease/ack lifecycle honest even if no
// client touches the hub for a while.
const sweeper = setInterval(() => {
  try {
    sweep();
  } catch (err) {
    console.error("[hub] sweep error:", err);
  }
}, SWEEP_MS);

// ============================================================
// HEALTH ENDPOINT (Bun.serve on /health)
// ============================================================

// Use Bun.serve. If running under Node, this branch is skipped.
// @ts-ignore -- Bun is a global at runtime
const isBun = typeof Bun !== "undefined";
let httpServer: { stop?: () => void } | null = null;

if (isBun) {
  // @ts-ignore
  httpServer = Bun.serve({
    port: HUB_PORT,
    fetch(req: Request) {
      const url = new URL(req.url);
      if (url.pathname === "/health") {
        const dbOk = (() => {
          try {
            db.prepare("SELECT 1").get();
            return true;
          } catch {
            return false;
          }
        })();
        const pending = (stmts.pendingCount.get() as { c: number }).c;
        const leased = (stmts.leasedCount.get() as { c: number }).c;
        const dead = (stmts.deadLetterCount.get() as { c: number }).c;
        return Response.json({
          status: dbOk ? "ok" : "degraded",
          uptime_ms: Date.now() - startedAt,
          pending,
          leased,
          dead_letters: dead,
          db: HUB_DB,
        }, { status: dbOk ? 200 : 503 });
      }
      if (url.pathname === "/metrics") {
        const pending = (stmts.pendingCount.get() as { c: number }).c;
        const leased = (stmts.leasedCount.get() as { c: number }).c;
        const dead = (stmts.deadLetterCount.get() as { c: number }).c;
        const lines = [
          "# HELP hub_messages_pending Pending messages awaiting lease",
          "# TYPE hub_messages_pending gauge",
          `hub_messages_pending ${pending}`,
          "# HELP hub_messages_leased Currently leased messages",
          "# TYPE hub_messages_leased gauge",
          `hub_messages_leased ${leased}`,
          "# HELP hub_dead_letters Total dead-lettered messages",
          "# TYPE hub_dead_letters counter",
          `hub_dead_letters ${dead}`,
        ].join("\n");
        return new Response(lines, { headers: { "content-type": "text/plain" } });
      }
      return new Response("not found", { status: 404 });
    },
  });
  console.error(`[hub] health on http://localhost:${HUB_PORT}/health`);
}

// ============================================================
// MCP SERVER
// ============================================================

const server = new Server(
  { name: "stateful-hub", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "send",
      description: "Send a message to a session mailbox",
      inputSchema: {
        type: "object",
        properties: {
          session_id: { type: "string", description: "Target session/mailbox name" },
          sender: { type: "string", description: "Sender identifier" },
          payload: { description: "Arbitrary JSON payload" },
        },
        required: ["session_id", "sender", "payload"],
      },
    },
    {
      name: "lease",
      description: "Lease the next pending message for a session",
      inputSchema: {
        type: "object",
        properties: {
          session_id: { type: "string" },
          lease_holder: { type: "string", description: "Consumer identifier" },
        },
        required: ["session_id", "lease_holder"],
      },
    },
    {
      name: "ack",
      description: "Acknowledge a leased message (mark complete)",
      inputSchema: {
        type: "object",
        properties: { message_id: { type: "string" } },
        required: ["message_id"],
      },
    },
    {
      name: "nack",
      description: "Negative-ack a leased message (return to pending)",
      inputSchema: {
        type: "object",
        properties: {
          message_id: { type: "string" },
          reason: { type: "string" },
        },
        required: ["message_id", "reason"],
      },
    },
    {
      name: "stats",
      description: "Get hub statistics (pending, leased, dead-letters)",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const a = (args ?? {}) as Record<string, any>;

  try {
    switch (name) {
      case "send": {
        const id = send(String(a.session_id), String(a.sender), a.payload);
        return { content: [{ type: "text", text: JSON.stringify({ id }) }] };
      }
      case "lease": {
        const msg = lease(String(a.session_id), String(a.lease_holder));
        return { content: [{ type: "text", text: JSON.stringify(msg) }] };
      }
      case "ack": {
        const ok = ack(String(a.message_id));
        return { content: [{ type: "text", text: JSON.stringify({ ok }) }] };
      }
      case "nack": {
        const ok = nack(String(a.message_id), String(a.reason ?? "unspecified"));
        return { content: [{ type: "text", text: JSON.stringify({ ok }) }] };
      }
      case "stats": {
        const pending = (stmts.pendingCount.get() as { c: number }).c;
        const leased = (stmts.leasedCount.get() as { c: number }).c;
        const dead = (stmts.deadLetterCount.get() as { c: number }).c;
        return {
          content: [
            { type: "text", text: JSON.stringify({ pending, leased, dead_letters: dead }) },
          ],
        };
      }
      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${(err as Error).message}` }],
      isError: true,
    };
  }
});

// ============================================================
// LIFECYCLE
// ============================================================

function shutdown(signal: string) {
  console.error(`[hub] received ${signal}, draining...`);
  clearInterval(sweeper);
  try { httpServer?.stop?.(); } catch {}
  try {
    // Final sweep so we don't leave leaked leases on disk.
    sweep();
  } catch {}
  try { db.close(); } catch {}
  process.exit(0);
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

const transport = new StdioServerTransport();
await server.connect(transport);

// Exported for tests
export { db, send, lease, ack, nack, sweep };
