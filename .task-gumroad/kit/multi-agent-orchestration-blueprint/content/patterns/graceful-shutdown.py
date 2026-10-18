#!/usr/bin/env python3
"""
Graceful Shutdown Pattern

Ensures a worker finishes or escalates current work before exiting.
Use this as a template for your worker's shutdown handler.
"""

import signal
from pathlib import Path


class GracefulShutdown:
    """Context manager for graceful worker shutdown."""

    def __init__(self, worker_name: str, inbox_dir: str):
        self.worker_name = worker_name
        self.inbox_dir = Path(inbox_dir)
        self.shutting_down = False
        self.current_task_id: str | None = None

    def __enter__(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        return self

    def __exit__(self, *_args):
        if self.current_task_id:
            self._escalate_current_task()

    def _handle_signal(self, signum, _frame):
        print(f"[{self.worker_name}] Received signal {signum}, shutting down gracefully...")
        self.shutting_down = True

    def _escalate_current_task(self):
        """Move current task back to dispatch for reassignment."""
        if not self.current_task_id:
            return

        # Find the task file and update status
        for f in self.inbox_dir.glob("*.md"):
            content = f.read_text()
            if self.current_task_id in content:
                content = content.replace("status: running", "status: escalated")
                f.write_text(content)
                print(f"[{self.worker_name}] Escalated task {self.current_task_id}")
                break

    def start_task(self, task_id: str):
        self.current_task_id = task_id

    def finish_task(self):
        self.current_task_id = None

    @property
    def should_continue(self) -> bool:
        return not self.shutting_down


# Usage:
# with GracefulShutdown("worker-content", ".inboxes/worker-content/inbox") as shutdown:
#     while shutdown.should_continue:
#         task = get_next_task()
#         if task:
#             shutdown.start_task(task.id)
#             process(task)
#             shutdown.finish_task()
