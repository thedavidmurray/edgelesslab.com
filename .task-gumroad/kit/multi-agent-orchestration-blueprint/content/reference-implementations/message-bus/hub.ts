/**
 * Agent Bus Hub -- SQLite-backed message router
 *
 * Usage: bun run hub.ts
 *
 * Environment:
 *   AGENT_BUS_PORT=9800
 *   AGENT_BUS_DB=hub.db
 *   AGENT_BUS_LEASE_TTL=30       (seconds)
 *   AGENT_BUS_CLEANUP_INTERVAL=60 (seconds)
 */

import { Database } from "bun:sqlite";
import { readFileSync } from "fs";

const PORT = parseInt(process.env.AGENT_BUS_PORT ?? "9800");
const DB_PATH = process.env.AGENT_BUS_DB ?? "hub.db";
const LEASE_TTL = parseInt(process.env.AGENT_BUS_LEASE_TTL ?? "30");
const CLEANUP_INTERVAL = parseInt(process.env.AGENT_BUS_CLEANUP_INTERVAL ?? "60");

// Initialize database
const db = new Database(DB_PATH);
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA busy_timeout = 5000");
db.exec(readFileSync(new URL("schema.sql", import.meta.url), "utf8"));

// Prepared statements
const insertSession = db.prepare(
  `INSERT INTO sessions (name) VALUES (?)
   ON CONFLICT(name) DO UPDATE SET last_seen = datetime('now')`
);

const insertMessage = db.prepare(
  `INSERT INTO messages (mailbox, from_sender, content, type, expires_at)
   VALUES (?, ?, ?, ?, datetime('now', '+' || ? || ' seconds'))`
);

const pollMessages = db.prepare(
  `UPDATE messages
   SET status = 'leased', leased_at = datetime('now')
   WHERE mailbox = ? AND status = 'pending'
   RETURNING *`
);

const ackMessage = db.prepare(
  `UPDATE messages
   SET status = 'acked', acked_at = datetime('now')
   WHERE id = ? AND status = 'leased'`
);

const releaseStaleLeases = db.prepare(
  `UPDATE messages
   SET status = 'pending', leased_at = NULL
   WHERE status = 'leased'
     AND leased_at < datetime('now', '-' || ? || ' seconds')`
);

const expireOldMessages = db.prepare(
  `DELETE FROM messages
   WHERE expires_at < datetime('now') AND status != 'acked'`
);

const listSessions = db.prepare(
  `SELECT name, connected_at, last_seen FROM sessions
   ORDER BY last_seen DESC`
);

const touchSession = db.prepare(
  `UPDATE sessions SET last_seen = datetime('now') WHERE name = ?`
);

// Cleanup loop
setInterval(() => {
  releaseStaleLeases.run(LEASE_TTL);
  expireOldMessages.run();
}, CLEANUP_INTERVAL * 1000);

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    const path = url.pathname;

    // Health check
    if (path === "/health" && req.method === "GET") {
      const count = db.prepare("SELECT COUNT(*) as n FROM messages WHERE status = 'pending'").get() as { n: number };
      return jsonResponse({ status: "ok", pending_messages: count.n });
    }

    // Register session
    if (path === "/register" && req.method === "POST") {
      const body = await req.json() as { name: string };
      if (!body.name) return jsonResponse({ error: "name required" }, 400);
      insertSession.run(body.name);
      return jsonResponse({ registered: body.name });
    }

    // Send message
    if (path === "/send" && req.method === "POST") {
      const body = await req.json() as {
        from: string; to: string; content: string; type?: string; ttl?: number
      };
      if (!body.from || !body.to || !body.content) {
        return jsonResponse({ error: "from, to, content required" }, 400);
      }
      const ttl = body.ttl ?? 86400; // Default 24h
      insertMessage.run(body.to, body.from, body.content, body.type ?? "request", ttl);
      touchSession.run(body.from);
      return jsonResponse({ sent: true });
    }

    // Broadcast
    if (path === "/broadcast" && req.method === "POST") {
      const body = await req.json() as { from: string; content: string; type?: string };
      if (!body.from || !body.content) {
        return jsonResponse({ error: "from, content required" }, 400);
      }
      const sessions = listSessions.all() as { name: string }[];
      let count = 0;
      for (const session of sessions) {
        if (session.name !== body.from) {
          insertMessage.run(session.name, body.from, body.content, body.type ?? "broadcast", 3600);
          count++;
        }
      }
      touchSession.run(body.from);
      return jsonResponse({ broadcast: true, recipients: count });
    }

    // Poll for messages
    if (path.startsWith("/poll/") && req.method === "GET") {
      const name = path.split("/poll/")[1];
      if (!name) return jsonResponse({ error: "name required" }, 400);
      touchSession.run(name);
      const messages = pollMessages.all(name);
      return jsonResponse(messages);
    }

    // Acknowledge message
    if (path === "/ack" && req.method === "POST") {
      const body = await req.json() as { id: string };
      if (!body.id) return jsonResponse({ error: "id required" }, 400);
      const result = ackMessage.run(body.id);
      return jsonResponse({ acked: result.changes > 0 });
    }

    // List sessions
    if (path === "/sessions" && req.method === "GET") {
      const sessions = listSessions.all();
      return jsonResponse(sessions);
    }

    return jsonResponse({ error: "not found" }, 404);
  },
});

console.log(`Agent Bus Hub running on port ${PORT}`);
console.log(`Database: ${DB_PATH}`);
console.log(`Lease TTL: ${LEASE_TTL}s | Cleanup: every ${CLEANUP_INTERVAL}s`);
