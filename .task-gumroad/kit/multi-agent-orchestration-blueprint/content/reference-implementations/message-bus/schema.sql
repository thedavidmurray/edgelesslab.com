-- Agent Bus Hub -- SQLite Schema
-- Run: sqlite3 hub.db < schema.sql

CREATE TABLE IF NOT EXISTS sessions (
    name TEXT PRIMARY KEY,
    connected_at TEXT DEFAULT (datetime('now')),
    last_seen TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    mailbox TEXT NOT NULL,
    from_sender TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT DEFAULT 'request' CHECK (type IN ('request', 'response', 'broadcast', 'heartbeat')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'leased', 'acked', 'expired')),
    created_at TEXT DEFAULT (datetime('now')),
    leased_at TEXT,
    acked_at TEXT,
    expires_at TEXT DEFAULT (datetime('now', '+24 hours'))
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_mailbox_status ON messages(mailbox, status);
CREATE INDEX IF NOT EXISTS idx_expires ON messages(expires_at);
CREATE INDEX IF NOT EXISTS idx_from_sender ON messages(from_sender);
CREATE INDEX IF NOT EXISTS idx_created_at ON messages(created_at);

-- Cleanup trigger: auto-expire old messages
CREATE TRIGGER IF NOT EXISTS cleanup_expired
AFTER INSERT ON messages
BEGIN
    DELETE FROM messages
    WHERE expires_at < datetime('now')
    AND status != 'acked';
END;
