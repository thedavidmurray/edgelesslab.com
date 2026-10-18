-- SQLite schema for Claude Code hook observability
-- Used by: post-tool-tracker.py, trading-observer.py, sandbox-observer.py

-- Enable WAL mode for concurrent writes
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Tool usage tracking (post-tool-tracker.py)
CREATE TABLE IF NOT EXISTS tool_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    tool_name TEXT NOT NULL,
    tool_input TEXT,
    success INTEGER DEFAULT 1,
    duration_ms INTEGER,
    session_id TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_usage(tool_name);
CREATE INDEX IF NOT EXISTS idx_timestamp ON tool_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_session ON tool_usage(session_id);

-- Tool usage patterns (aggregated)
CREATE TABLE IF NOT EXISTS tool_patterns (
    tool_name TEXT PRIMARY KEY,
    total_uses INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    avg_duration_ms REAL DEFAULT 0.0,
    last_used TEXT
);

-- Trading events (trading-observer.py)
CREATE TABLE IF NOT EXISTS trading_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    agent TEXT NOT NULL,
    action TEXT NOT NULL,  -- buy, sell, swap, approve
    token TEXT,
    amount REAL,
    price REAL,
    risk_level TEXT,  -- low, medium, high, critical
    session_id TEXT,
    success INTEGER DEFAULT 1,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_trading_agent ON trading_events(agent);
CREATE INDEX IF NOT EXISTS idx_trading_timestamp ON trading_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_trading_risk ON trading_events(risk_level);

-- Trading session aggregates
CREATE TABLE IF NOT EXISTS trading_sessions (
    session_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    start_time TEXT NOT NULL DEFAULT (datetime('now')),
    end_time TEXT,
    total_trades INTEGER DEFAULT 0,
    total_volume REAL DEFAULT 0.0,
    max_single_trade REAL DEFAULT 0.0,
    alerts_triggered INTEGER DEFAULT 0,
    pnl REAL DEFAULT 0.0
);

-- Trading alerts
CREATE TABLE IF NOT EXISTS trading_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    agent TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    amount REAL,
    token TEXT,
    action TEXT,
    message TEXT,
    acknowledged INTEGER DEFAULT 0
);

-- Sandbox execution events (sandbox-observer.py)
CREATE TABLE IF NOT EXISTS sandbox_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    agent TEXT,
    language TEXT,
    code_preview TEXT,  -- first 500 chars
    duration_ms INTEGER,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    session_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_sandbox_agent ON sandbox_events(agent);

-- Useful queries --

-- Most used tools today
-- SELECT tool_name, COUNT(*) as uses
-- FROM tool_usage
-- WHERE timestamp > date('now')
-- GROUP BY tool_name ORDER BY uses DESC;

-- Failed operations in last hour
-- SELECT timestamp, tool_name, error_message
-- FROM tool_usage
-- WHERE success = 0 AND timestamp > datetime('now', '-1 hour');

-- Trading volume by agent
-- SELECT agent, SUM(amount) as volume, COUNT(*) as trades
-- FROM trading_events
-- GROUP BY agent ORDER BY volume DESC;

-- High-risk trades
-- SELECT * FROM trading_alerts
-- WHERE risk_level IN ('high', 'critical')
-- AND acknowledged = 0;
