-- Stateful Hub MCP Server -- Schema
--
-- Durable message router with lease/ack lifecycle.
-- Run via Bun's bun:sqlite, but the schema is portable.
--
-- Lifecycle:
--   pending -> leased (consumer holds it for LEASE_MS)
--           -> acked (consumer confirmed processing)
--           -> failed (lease expired or explicit nack -> back to pending)
--           -> expired (TTL passed without ack -> dead-letter)

PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA temp_store = MEMORY;

CREATE TABLE IF NOT EXISTS sessions (
  name         TEXT PRIMARY KEY,
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id           TEXT PRIMARY KEY,
  session_id   TEXT NOT NULL REFERENCES sessions(name),
  sender       TEXT NOT NULL,
  payload      TEXT NOT NULL,             -- JSON-serialized body
  -- pending | leased | acked | failed
  status       TEXT NOT NULL DEFAULT 'pending',
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  leased_at    TEXT,
  leased_by    TEXT,
  acked_at     TEXT,
  expires_at   TEXT NOT NULL,
  attempts     INTEGER NOT NULL DEFAULT 0,
  last_error   TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_status      ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_session_id  ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_expires_at  ON messages(expires_at);
CREATE INDEX IF NOT EXISTS idx_messages_session_status
  ON messages(session_id, status);

CREATE TABLE IF NOT EXISTS dead_letters (
  id           TEXT PRIMARY KEY,
  session_id   TEXT NOT NULL,
  sender       TEXT NOT NULL,
  payload      TEXT NOT NULL,
  failed_at    TEXT NOT NULL DEFAULT (datetime('now')),
  reason       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dead_letters_session ON dead_letters(session_id);
