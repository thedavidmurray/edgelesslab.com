#!/usr/bin/env python3
"""
Dispatch/Worker Reference Implementation -- Dispatch Agent

The dispatch agent coordinates work across multiple worker agents.
It routes tasks by domain, monitors health, and handles escalations.

Usage:
    python dispatch.py --workers workers.json

The workers.json file defines available workers:
[
  {"name": "worker-content", "domains": ["rss", "youtube"], "max_concurrent": 3},
  {"name": "worker-infra", "domains": ["deploy", "health"], "max_concurrent": 2}
]
"""

import argparse
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class TaskStatus(Enum):
    QUEUED = "queued"
    ACKED = "acked"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    ESCALATED = "escalated"


VALID_TRANSITIONS = {
    TaskStatus.QUEUED: {TaskStatus.ACKED, TaskStatus.ESCALATED},
    TaskStatus.ACKED: {TaskStatus.RUNNING, TaskStatus.ESCALATED},
    TaskStatus.RUNNING: {TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.ESCALATED},
    TaskStatus.DONE: set(),
    TaskStatus.FAILED: {TaskStatus.QUEUED},
    TaskStatus.ESCALATED: {TaskStatus.QUEUED},
}


@dataclass
class TaskTransition:
    from_status: TaskStatus
    to_status: TaskStatus
    timestamp: datetime
    agent: str
    note: str = ""


@dataclass
class Task:
    id: str
    title: str
    status: TaskStatus = TaskStatus.QUEUED
    owner: str | None = None
    priority: str = "normal"
    created: datetime = field(default_factory=datetime.now)
    deadline: datetime | None = None
    transitions: list[TaskTransition] = field(default_factory=list)

    def transition(self, new_status: TaskStatus, agent: str, note: str = ""):
        if new_status not in VALID_TRANSITIONS.get(self.status, set()):
            raise ValueError(
                f"Invalid: {self.status.value} -> {new_status.value}. "
                f"Valid: {[s.value for s in VALID_TRANSITIONS[self.status]]}"
            )
        self.transitions.append(TaskTransition(
            from_status=self.status,
            to_status=new_status,
            timestamp=datetime.now(),
            agent=agent,
            note=note,
        ))
        self.status = new_status
        if new_status == TaskStatus.ACKED:
            self.owner = agent

    def is_stuck(self, timeout_minutes: int = 30) -> bool:
        if not self.transitions:
            elapsed = (datetime.now() - self.created).total_seconds() / 60
        else:
            elapsed = (datetime.now() - self.transitions[-1].timestamp).total_seconds() / 60
        return elapsed > timeout_minutes

    def time_in_state(self) -> float:
        if self.transitions:
            return (datetime.now() - self.transitions[-1].timestamp).total_seconds() / 60
        return (datetime.now() - self.created).total_seconds() / 60

    def total_duration(self) -> float | None:
        if self.status not in (TaskStatus.DONE, TaskStatus.FAILED):
            return None
        return (self.transitions[-1].timestamp - self.created).total_seconds() / 60

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "owner": self.owner,
            "priority": self.priority,
            "created": self.created.isoformat(),
            "transitions": [
                {
                    "from": t.from_status.value,
                    "to": t.to_status.value,
                    "at": t.timestamp.isoformat(),
                    "agent": t.agent,
                    "note": t.note,
                }
                for t in self.transitions
            ],
        }


@dataclass
class WorkerInfo:
    name: str
    domains: list[str]
    max_concurrent: int
    active_task_count: int = 0
    last_heartbeat: float = 0.0


# Domain classification keywords
DOMAIN_KEYWORDS = {
    "content": ["rss", "youtube", "newsletter", "digest", "article", "blog", "content"],
    "trading": ["market", "position", "trade", "price", "portfolio", "risk", "exchange"],
    "infra": ["deploy", "health", "cron", "docker", "server", "backup", "monitor"],
    "research": ["analyze", "investigate", "review", "report", "compare", "research"],
}


def classify_domain(task_title: str) -> str:
    """Classify a task into a domain based on keywords."""
    title_lower = task_title.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in title_lower)
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "research"


def route_task(task: Task, workers: dict[str, WorkerInfo]) -> str:
    """Route a task to the best available worker."""
    domain = classify_domain(task.title)
    candidates = [w for w in workers.values() if domain in w.domains]
    if not candidates:
        return "dispatch"
    candidates.sort(key=lambda w: w.active_task_count)
    best = candidates[0]
    if best.active_task_count >= best.max_concurrent:
        return "dispatch"
    return best.name


def check_stuck_tasks(tasks: list[Task], timeout: int = 30):
    """Find stuck tasks and escalate them."""
    for task in tasks:
        if task.status in (TaskStatus.ACKED, TaskStatus.RUNNING) and task.is_stuck(timeout):
            task.transition(
                TaskStatus.ESCALATED, "dispatch",
                f"Stuck for {task.time_in_state():.0f}min, reassigning",
            )
            task.transition(TaskStatus.QUEUED, "dispatch", "Reassigned after timeout")


def load_workers(path: str) -> dict[str, WorkerInfo]:
    """Load worker definitions from JSON."""
    with open(path) as f:
        data = json.load(f)
    workers = {}
    for w in data:
        info = WorkerInfo(
            name=w["name"],
            domains=w["domains"],
            max_concurrent=w.get("max_concurrent", 3),
        )
        workers[info.name] = info
    return workers


def process_inbox(inbox_dir: Path, tasks: list[Task]):
    """Read new tasks from the inbox directory."""
    if not inbox_dir.exists():
        return

    for f in sorted(inbox_dir.glob("*.md")):
        content = f.read_text()
        # Parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                meta = {}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        meta[key.strip()] = val.strip()

                task_id = meta.get("id", f.stem)
                # Skip if already known
                if any(t.id == task_id for t in tasks):
                    continue

                task = Task(
                    id=task_id,
                    title=meta.get("title", f.stem),
                    priority=meta.get("priority", "normal"),
                )
                tasks.append(task)
                print(f"[dispatch] New task: {task.id} -- {task.title}")


def write_assignment(outbox_dir: Path, task: Task, target: str):
    """Write a task assignment to the worker's inbox."""
    worker_inbox = outbox_dir.parent.parent / target / "inbox"
    worker_inbox.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}-task-{task.id}.md"
    content = f"""---
id: {task.id}
from: dispatch
to: {target}
status: queued
priority: {task.priority}
created: {task.created.isoformat()}
---

## Task: {task.title}
"""
    (worker_inbox / filename).write_text(content)
    print(f"[dispatch] Routed {task.id} -> {target}")


def generate_report(tasks: list[Task], workers: dict[str, WorkerInfo]) -> str:
    """Generate a status summary."""
    lines = [f"## Status Report -- {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]

    by_status = {}
    for task in tasks:
        by_status.setdefault(task.status.value, []).append(task)

    for status, status_tasks in sorted(by_status.items()):
        lines.append(f"**{status}**: {len(status_tasks)}")
        for t in status_tasks[:5]:
            lines.append(f"  - {t.id}: {t.title} (owner: {t.owner or 'unassigned'})")

    lines.append("")
    lines.append("### Workers")
    for name, w in workers.items():
        lines.append(f"- **{name}**: {w.active_task_count}/{w.max_concurrent} active")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Dispatch Agent")
    parser.add_argument("--workers", required=True, help="Path to workers.json")
    parser.add_argument("--inbox", default=".inboxes/dispatch/inbox", help="Inbox directory")
    parser.add_argument("--interval", type=int, default=10, help="Check interval (seconds)")
    parser.add_argument("--timeout", type=int, default=30, help="Stuck task timeout (minutes)")
    args = parser.parse_args()

    workers = load_workers(args.workers)
    inbox_dir = Path(args.inbox)
    outbox_dir = inbox_dir.parent / "outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)

    tasks: list[Task] = []

    print(f"[dispatch] Starting with {len(workers)} workers")
    for name, w in workers.items():
        print(f"  {name}: domains={w.domains}, max={w.max_concurrent}")

    while True:
        # 1. Check inbox for new tasks
        process_inbox(inbox_dir, tasks)

        # 2. Route queued tasks
        for task in tasks:
            if task.status == TaskStatus.QUEUED:
                target = route_task(task, workers)
                if target != "dispatch":
                    task.transition(TaskStatus.ACKED, target)
                    workers[target].active_task_count += 1
                    write_assignment(outbox_dir, task, target)

        # 3. Check for stuck tasks
        check_stuck_tasks(tasks, args.timeout)

        # 4. Sleep
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
