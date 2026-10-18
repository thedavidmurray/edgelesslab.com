#!/usr/bin/env python3
"""
Event Log Pattern

Append-only JSONL event log for multi-agent observability.
Every meaningful event (task routed, completed, failed, worker timeout)
gets logged with enough context to debug issues after the fact.
"""

import json
from datetime import datetime
from pathlib import Path


class EventLog:
    """Append-only event log backed by daily JSONL files."""

    def __init__(self, log_dir: str = ".agent-logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _log_file(self) -> Path:
        return self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    def log(self, event_type: str, **data):
        """Write an event to the log."""
        entry = {
            "ts": datetime.now().isoformat(),
            "type": event_type,
            **data,
        }
        with open(self._log_file(), "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def read(self, date: str | None = None, event_type: str | None = None) -> list[dict]:
        """Read events, optionally filtered by date and type."""
        if date:
            files = [self.log_dir / f"{date}.jsonl"]
        else:
            files = sorted(self.log_dir.glob("*.jsonl"))

        events = []
        for f in files:
            if not f.exists():
                continue
            for line in f.read_text().strip().split("\n"):
                if not line:
                    continue
                event = json.loads(line)
                if event_type and event.get("type") != event_type:
                    continue
                events.append(event)
        return events

    def summary(self, date: str | None = None) -> dict:
        """Generate a summary of events."""
        events = self.read(date=date)
        by_type: dict[str, int] = {}
        for e in events:
            t = e.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total_events": len(events),
            "by_type": by_type,
            "date": date or "all",
        }


# Usage:
# log = EventLog()
# log.log("task_routed", task_id="rss-001", from_agent="dispatch", to_agent="worker-content")
# log.log("task_complete", task_id="rss-001", duration_s=45, worker="worker-content")
# log.log("worker_timeout", worker="worker-trading", last_seen="2026-04-02T14:00:00")
# print(log.summary())
