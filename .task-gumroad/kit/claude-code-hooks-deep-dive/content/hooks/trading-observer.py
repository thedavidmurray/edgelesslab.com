#!/usr/bin/env python3
"""
trading-observer.py - Multi-Agent Trading Observability Hook
PostToolUse hook for tracking trading operations across agents.

AGENTS MONITORED:
- Pamela: Primary trading bot
- Toast: Secondary trading bot
- Hummingbot: Market making
- Manual: Direct operations

FEATURES:
- Trading event logging with risk levels
- Session performance tracking
- Alert generation for high-risk operations
- Cross-agent correlation

SECURITY: 2024-12-28
- Inherits security from post-tool-tracker
- Additional trading-specific sanitization
"""

import json
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add lib to path
HOOKS_DIR = Path(__file__).parent
LIB_DIR = HOOKS_DIR / "lib"
sys.path.insert(0, str(LIB_DIR))

from trading_helper import (
    identify_agent,
    is_trading_operation,
    extract_trading_metadata,
    calculate_risk_level,
    format_alert_message,
    init_trading_tables,
)

# Configuration
DB_PATH = HOOKS_DIR / "events.db"
LOG_PATH = HOOKS_DIR / "trading.log"
MAX_INPUT_SIZE = 50000

# Alert thresholds
ALERT_ON_RISK_LEVELS = ["high", "critical"]


def get_connection():
    """Get database connection with trading tables initialized."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    init_trading_tables(conn)
    return conn


def log_trading_event(conn, event_data: dict) -> int:
    """Log a trading event to the database."""
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trading_events
        (timestamp, session_id, agent, action, token, token_address,
         pair, amount, price, risk_level, success, tool_name, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_data.get("timestamp", datetime.now().isoformat()),
        event_data.get("session_id"),
        event_data.get("agent", "unknown"),
        event_data.get("action"),
        event_data.get("token"),
        event_data.get("token_address"),
        event_data.get("pair"),
        event_data.get("amount"),
        event_data.get("price"),
        event_data.get("risk_level", "low"),
        1 if event_data.get("success", True) else 0,
        event_data.get("tool_name"),
        json.dumps(event_data.get("metadata", {}))
    ))

    conn.commit()
    return cursor.lastrowid


def create_alert(conn, agent: str, alert_type: str, severity: str, message: str):
    """Create a trading alert."""
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trading_alerts
        (timestamp, agent, alert_type, severity, message, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        agent,
        alert_type,
        severity,
        message,
        json.dumps({"source": "trading-observer"})
    ))

    conn.commit()

    # Also log to file for visibility
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{datetime.now().isoformat()} ALERT [{severity}]: {message}\n")
    except Exception:
        pass


def update_session_stats(conn, session_id: str, agent: str, success: bool, amount: float = 0):
    """Update trading session statistics."""
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute("""
        SELECT id, total_trades, successful_trades, failed_trades, total_volume
        FROM trading_sessions WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()

    if row:
        # Update existing session
        total = row[1] + 1
        successful = row[2] + (1 if success else 0)
        failed = row[3] + (0 if success else 1)
        volume = row[4] + amount

        cursor.execute("""
            UPDATE trading_sessions
            SET total_trades = ?, successful_trades = ?, failed_trades = ?,
                total_volume = ?, end_time = ?
            WHERE session_id = ?
        """, (total, successful, failed, volume, datetime.now().isoformat(), session_id))
    else:
        # Create new session
        cursor.execute("""
            INSERT INTO trading_sessions
            (session_id, agent, start_time, total_trades, successful_trades, failed_trades, total_volume)
            VALUES (?, ?, ?, 1, ?, ?, ?)
        """, (
            session_id,
            agent,
            datetime.now().isoformat(),
            1 if success else 0,
            0 if success else 1,
            amount
        ))

    conn.commit()


def main():
    """Main hook entry point."""
    # Read hook input
    try:
        raw_input = sys.stdin.read(MAX_INPUT_SIZE)
        hook_input = json.loads(raw_input)
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Extract tool info
    tool_name = hook_input.get("tool", hook_input.get("tool_name", "unknown"))
    tool_input = hook_input.get("input", hook_input.get("tool_input", {}))
    tool_output = hook_input.get("output", hook_input.get("result", {}))

    # Check if this is a trading operation
    if not is_trading_operation(tool_name, tool_input):
        # Not trading-related, just pass through
        print(json.dumps({"continue": True}))
        return

    # Identify the agent
    agent = identify_agent()
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

    # Determine success
    success = True
    if isinstance(tool_output, dict):
        success = not tool_output.get("error", False)
    elif isinstance(tool_output, str) and "error" in tool_output.lower():
        success = False

    # Extract trading metadata
    metadata = extract_trading_metadata(tool_name, tool_input if isinstance(tool_input, dict) else {})
    risk_level = calculate_risk_level(metadata)

    # Build event data
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "agent": agent,
        "action": metadata.get("action"),
        "token": metadata.get("token"),
        "token_address": metadata.get("token_address"),
        "pair": metadata.get("pair"),
        "amount": metadata.get("amount"),
        "price": metadata.get("price"),
        "risk_level": risk_level,
        "success": success,
        "tool_name": tool_name[:100],
        "metadata": metadata
    }

    try:
        conn = get_connection()

        # Log the trading event
        log_trading_event(conn, event_data)

        # Update session stats
        update_session_stats(
            conn, session_id, agent, success,
            metadata.get("amount", 0)
        )

        # Generate alerts for high-risk operations
        if risk_level in ALERT_ON_RISK_LEVELS:
            alert_msg = format_alert_message(
                agent,
                metadata.get("action", "trade"),
                metadata,
                risk_level
            )
            create_alert(
                conn, agent,
                alert_type="high_risk_trade",
                severity=risk_level,
                message=alert_msg
            )

        # Alert on failures
        if not success:
            create_alert(
                conn, agent,
                alert_type="trade_failure",
                severity="medium",
                message=f"Trade failed: {tool_name} for {agent}"
            )

        conn.close()

    except Exception as e:
        # Log error but don't fail the hook
        try:
            with open(LOG_PATH, "a") as f:
                f.write(f"{datetime.now().isoformat()} ERROR: {str(e)[:200]}\n")
        except Exception:
            pass

    # Always continue
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
