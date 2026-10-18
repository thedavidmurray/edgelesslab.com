#!/usr/bin/env python3
"""
Dispatch/Worker Reference Implementation -- Worker Agent

A worker agent that claims tasks from its inbox, processes them,
and reports results back to dispatch.

Usage:
    python worker.py --name worker-content --inbox .inboxes/worker-content/inbox
"""

import argparse
import shutil
import time
from datetime import datetime
from pathlib import Path


def process_inbox(inbox_dir: Path) -> list[dict]:
    """Read pending tasks from inbox directory."""
    tasks = []
    if not inbox_dir.exists():
        return tasks

    for f in sorted(inbox_dir.glob("*.md")):
        content = f.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                meta = {}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        meta[key.strip()] = val.strip()

                if meta.get("status") == "queued":
                    tasks.append({
                        "file": f,
                        "meta": meta,
                        "body": parts[2].strip() if len(parts) > 2 else "",
                    })
    return tasks


def ack_task(task_file: Path):
    """Mark a task as acked by updating its frontmatter."""
    content = task_file.read_text()
    content = content.replace("status: queued", "status: running")
    task_file.write_text(content)


def complete_task(task: dict, outbox_dir: Path, result: str, archive_dir: Path):
    """Mark task as done, write result, archive the task file."""
    task_file: Path = task["file"]
    task_id = task["meta"].get("id", task_file.stem)

    # Write result to outbox
    outbox_dir.mkdir(parents=True, exist_ok=True)
    result_filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}-result-{task_id}.md"
    result_content = f"""---
id: {task_id}
from: {task["meta"].get("to", "worker")}
to: {task["meta"].get("from", "dispatch")}
status: done
completed: {datetime.now().isoformat()}
---

## Result: {task_id}

{result}
"""
    (outbox_dir / result_filename).write_text(result_content)

    # Archive the inbox task file
    archive_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(task_file), str(archive_dir / task_file.name))


def fail_task(task: dict, outbox_dir: Path, error: str, archive_dir: Path):
    """Mark task as failed, write error, archive the task file."""
    task_file: Path = task["file"]
    task_id = task["meta"].get("id", task_file.stem)

    outbox_dir.mkdir(parents=True, exist_ok=True)
    result_filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}-error-{task_id}.md"
    error_content = f"""---
id: {task_id}
from: {task["meta"].get("to", "worker")}
to: {task["meta"].get("from", "dispatch")}
status: failed
failed_at: {datetime.now().isoformat()}
---

## Error: {task_id}

{error}
"""
    (outbox_dir / result_filename).write_text(error_content)

    archive_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(task_file), str(archive_dir / task_file.name))


def do_work(task: dict) -> str:
    """
    Process a task. Replace this with your actual work logic.

    This is where you'd call your tools, APIs, or run computations.
    The function should return a string summary of the result.
    """
    task_id = task["meta"].get("id", "unknown")
    title = task["meta"].get("title", task["body"][:50])

    # Placeholder: simulate work
    print(f"  Processing: {title}")
    time.sleep(1)

    return f"Completed task {task_id}: {title}"


def main():
    parser = argparse.ArgumentParser(description="Worker Agent")
    parser.add_argument("--name", required=True, help="Worker name")
    parser.add_argument("--inbox", required=True, help="Inbox directory path")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval (seconds)")
    parser.add_argument("--max-concurrent", type=int, default=1, help="Max concurrent tasks")
    args = parser.parse_args()

    inbox_dir = Path(args.inbox)
    outbox_dir = inbox_dir.parent / "outbox"
    archive_dir = inbox_dir.parent / "archive"

    print(f"[{args.name}] Starting worker")
    print(f"  Inbox: {inbox_dir}")
    print(f"  Poll interval: {args.interval}s")

    while True:
        tasks = process_inbox(inbox_dir)

        if tasks:
            print(f"[{args.name}] Found {len(tasks)} pending tasks")

        for task in tasks[:args.max_concurrent]:
            task_id = task["meta"].get("id", "unknown")
            print(f"[{args.name}] Claiming task: {task_id}")
            ack_task(task["file"])

            try:
                result = do_work(task)
                complete_task(task, outbox_dir, result, archive_dir)
                print(f"[{args.name}] Completed: {task_id}")
            except Exception as e:
                fail_task(task, outbox_dir, str(e), archive_dir)
                print(f"[{args.name}] Failed: {task_id} -- {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
