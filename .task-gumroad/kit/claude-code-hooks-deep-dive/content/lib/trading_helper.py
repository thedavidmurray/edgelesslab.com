#!/usr/bin/env python3
"""
trading_helper.py - Multi-Agent Trading Observability Helper
Identifies trading agents and provides trading-specific utilities.

AGENTS:
- Pamela: Main trading bot (elizaos-bots/pamela-agent/)
- Toast: Secondary trading bot (elizaos-bots/toast-agent/)
- Manual: Direct trading operations

SECURITY: 2024-12-28
- Sanitizes all agent identifiers
- Validates trading data before logging
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Agent identification patterns
AGENT_PATTERNS = {
    "pamela": [
        "pamela-agent",
        "pamela",
        "elizaos-bots/pamela",
    ],
    "toast": [
        "toast-agent",
        "toast",
        "elizaos-bots/toast",
        "toast-bot-v2",
    ],
    "hummingbot": [
        "hummingbot",
        "hb_gateway",
    ],
}

# Trading-related tool patterns
TRADING_TOOL_PATTERNS = [
    r"trade",
    r"swap",
    r"buy|sell",
    r"order",
    r"position",
    r"portfolio",
    r"balance",
    r"wallet",
    r"dex|cex",
    r"token",
    r"price",
    r"market",
    r"liquidity",
]

# Compiled patterns for efficiency
TRADING_REGEX = re.compile("|".join(TRADING_TOOL_PATTERNS), re.IGNORECASE)


def identify_agent(cwd: Optional[str] = None, env: Optional[Dict] = None) -> str:
    """
    Identify which trading agent is running based on context.

    Args:
        cwd: Current working directory
        env: Environment variables dict

    Returns:
        Agent identifier: 'pamela', 'toast', 'hummingbot', or 'manual'
    """
    cwd = cwd or os.getcwd()
    env = env or dict(os.environ)

    cwd_lower = cwd.lower()

    # Check CWD for agent patterns
    for agent_name, patterns in AGENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in cwd_lower:
                return agent_name

    # Check environment variables
    agent_env = env.get("TRADING_AGENT", "").lower()
    if agent_env in AGENT_PATTERNS:
        return agent_env

    # Check for bot-specific env vars
    if env.get("PAMELA_CONFIG") or env.get("PAMELA_API_KEY"):
        return "pamela"
    if env.get("TOAST_CONFIG") or env.get("TOAST_API_KEY"):
        return "toast"
    if env.get("HUMMINGBOT_CONF_PATH"):
        return "hummingbot"

    return "manual"


def is_trading_operation(tool_name: str, tool_input: Any = None) -> bool:
    """
    Determine if a tool operation is trading-related.

    Args:
        tool_name: Name of the tool being used
        tool_input: Input to the tool

    Returns:
        True if this appears to be a trading operation
    """
    # Check tool name
    if TRADING_REGEX.search(tool_name):
        return True

    # Check input for trading keywords
    if tool_input:
        input_str = str(tool_input).lower()
        trading_keywords = ["swap", "trade", "buy", "sell", "token", "dex", "wallet"]
        if any(kw in input_str for kw in trading_keywords):
            return True

    return False


def extract_trading_metadata(tool_name: str, tool_input: Dict) -> Dict[str, Any]:
    """
    Extract trading-specific metadata from tool input.

    Args:
        tool_name: Name of the tool
        tool_input: Tool input dict

    Returns:
        Dict with trading metadata
    """
    metadata = {
        "is_trading": True,
        "timestamp": datetime.now().isoformat(),
    }

    # Extract common trading fields
    if isinstance(tool_input, dict):
        # Token/Asset info
        if "token" in tool_input:
            metadata["token"] = str(tool_input["token"])[:20]
        if "token_address" in tool_input:
            metadata["token_address"] = str(tool_input["token_address"])[:50]
        if "pair" in tool_input:
            metadata["pair"] = str(tool_input["pair"])[:20]

        # Amount info
        if "amount" in tool_input:
            try:
                metadata["amount"] = float(tool_input["amount"])
            except (ValueError, TypeError):
                pass

        # Price info
        if "price" in tool_input:
            try:
                metadata["price"] = float(tool_input["price"])
            except (ValueError, TypeError):
                pass

        # Action type
        for action in ["buy", "sell", "swap", "transfer"]:
            if action in tool_name.lower() or action in str(tool_input).lower():
                metadata["action"] = action
                break

    return metadata


def calculate_risk_level(metadata: Dict[str, Any]) -> str:
    """
    Calculate risk level for a trading operation.

    Returns: 'low', 'medium', 'high', or 'critical'
    """
    amount = metadata.get("amount", 0)

    if amount > 10000:
        return "critical"
    elif amount > 1000:
        return "high"
    elif amount > 100:
        return "medium"
    return "low"


def format_alert_message(
    agent: str,
    action: str,
    metadata: Dict[str, Any],
    risk_level: str
) -> str:
    """Format an alert message for trading events."""
    icon = {
        "low": "ℹ️",
        "medium": "⚠️",
        "high": "🔶",
        "critical": "🚨"
    }.get(risk_level, "📊")

    token = metadata.get("token", metadata.get("pair", "unknown"))
    amount = metadata.get("amount", "?")

    return f"{icon} [{agent.upper()}] {action.upper()}: {token} amount={amount} (risk={risk_level})"


# Database schema for trading tables
TRADING_SCHEMA = """
-- Trading events table
CREATE TABLE IF NOT EXISTS trading_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    session_id TEXT,
    agent TEXT NOT NULL,
    action TEXT,
    token TEXT,
    token_address TEXT,
    pair TEXT,
    amount REAL,
    price REAL,
    risk_level TEXT,
    success INTEGER,
    tool_name TEXT,
    metadata TEXT
);

-- Trading session performance
CREATE TABLE IF NOT EXISTS trading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    agent TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    total_trades INTEGER DEFAULT 0,
    successful_trades INTEGER DEFAULT 0,
    failed_trades INTEGER DEFAULT 0,
    total_volume REAL DEFAULT 0,
    metadata TEXT
);

-- Trading alerts
CREATE TABLE IF NOT EXISTS trading_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    agent TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    metadata TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trading_events_agent ON trading_events(agent);
CREATE INDEX IF NOT EXISTS idx_trading_events_timestamp ON trading_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_trading_alerts_severity ON trading_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_trading_sessions_agent ON trading_sessions(agent);
"""


def init_trading_tables(conn) -> bool:
    """
    Initialize trading-specific tables in the database.

    Args:
        conn: SQLite connection

    Returns:
        True if successful
    """
    try:
        cursor = conn.cursor()
        cursor.executescript(TRADING_SCHEMA)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error initializing trading tables: {e}")
        return False
