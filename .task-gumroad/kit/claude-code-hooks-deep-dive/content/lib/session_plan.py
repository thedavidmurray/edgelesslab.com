#!/usr/bin/env python3
"""
session_plan.py - Library for Manus-style session plan operations
Provides utilities for reading, parsing, and managing session plans in the Obsidian vault.
"""

import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Configuration
PROJECT_DIR = Path(__file__).parent.parent.parent.parent
VAULT_SESSIONS_PATH = PROJECT_DIR / "claude-vault" / "01-Sessions"


class SessionPlan:
    """Represents a parsed session plan from the vault."""

    def __init__(self, filepath: Path, frontmatter: dict, content: str):
        self.filepath = filepath
        self.frontmatter = frontmatter
        self.content = content

    @property
    def session_id(self) -> str:
        return self.frontmatter.get("session_id", "unknown")

    @property
    def status(self) -> str:
        return self.frontmatter.get("status", "unknown")

    @property
    def type(self) -> str:
        return self.frontmatter.get("type", "unknown")

    @property
    def current_phase(self) -> int:
        return self.frontmatter.get("current_phase", 0)

    @property
    def total_phases(self) -> int:
        return self.frontmatter.get("total_phases", 0)

    @property
    def goal(self) -> str:
        """Extract the goal section from content."""
        match = re.search(r'## Goal\s*\n(.+?)(?=\n##|\Z)', self.content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    @property
    def phases(self) -> List[Dict]:
        """Extract phases with their checkboxes."""
        phases = []
        pattern = r'### Phase (\d+): (.+?)\n((?:- \[[ x]\].+?\n?)+)'

        for match in re.finditer(pattern, self.content, re.MULTILINE):
            phase_num = int(match.group(1))
            phase_name = match.group(2).strip()
            checkboxes = match.group(3).strip()

            # Count completed vs total checkboxes
            total = checkboxes.count('- [')
            completed = checkboxes.count('- [x]')

            phases.append({
                "number": phase_num,
                "name": phase_name,
                "total_steps": total,
                "completed_steps": completed,
                "is_complete": completed == total and total > 0
            })

        return phases

    @property
    def is_all_phases_complete(self) -> bool:
        """Check if all phases are complete."""
        phases = self.phases
        if not phases:
            return False
        return all(p["is_complete"] for p in phases)

    def get_summary(self, max_lines: int = 30) -> str:
        """Get a summary of the session plan for attention refresh."""
        lines = []
        lines.append(f"# Active Session Plan: {self.filepath.stem}")
        lines.append(f"Status: {self.status} | Phase {self.current_phase}/{self.total_phases}")
        lines.append("")

        # Add goal
        if self.goal:
            lines.append("## Goal")
            lines.append(self.goal)
            lines.append("")

        # Add phases summary
        phases = self.phases
        if phases:
            lines.append("## Phases Progress")
            for phase in phases:
                status = "✓" if phase["is_complete"] else "○"
                progress = f"{phase['completed_steps']}/{phase['total_steps']}"
                lines.append(f"{status} Phase {phase['number']}: {phase['name']} ({progress})")
            lines.append("")

        # Add recent decisions (last 3)
        decisions_match = re.search(r'## Decisions\s*\n(.+?)(?=\n##|\Z)', self.content, re.DOTALL)
        if decisions_match:
            decisions = decisions_match.group(1).strip()
            if decisions and decisions != "*Record key decisions with rationale as you go*":
                lines.append("## Recent Decisions")
                decision_lines = [l for l in decisions.split('\n') if l.strip()][-3:]
                lines.extend(decision_lines)
                lines.append("")

        # Limit to max_lines
        result = '\n'.join(lines[:max_lines])
        if len(lines) > max_lines:
            result += f"\n... ({len(lines) - max_lines} more lines)"

        return result


def parse_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return None, content

    # Find the closing ---
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return None, content

    frontmatter_text = content[3:3 + end_match.start()]
    body = content[3 + end_match.end():]

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        return frontmatter, body
    except yaml.YAMLError:
        return None, content


def find_active_session_plan() -> Optional[SessionPlan]:
    """Find the active session plan (status=in_progress, type=session_plan)."""
    if not VAULT_SESSIONS_PATH.exists():
        return None

    # Search in current month and last month
    now = datetime.now()
    search_dirs = [
        VAULT_SESSIONS_PATH / now.strftime("%Y-%m"),
    ]

    # Add last month
    last_month = now.replace(day=1) - timedelta(days=1)
    search_dirs.append(VAULT_SESSIONS_PATH / last_month.strftime("%Y-%m"))

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Search for markdown files
        for md_file in search_dir.glob("*.md"):
            try:
                content = md_file.read_text()
                frontmatter, body = parse_frontmatter(content)

                if frontmatter:
                    # Check if it's an active session plan
                    if (frontmatter.get("type") == "session_plan" and
                        frontmatter.get("status") == "in_progress"):
                        return SessionPlan(md_file, frontmatter, body)
            except Exception:
                continue

    return None


def get_completion_warnings(plan: SessionPlan) -> List[str]:
    """Get warnings about incomplete items in the plan."""
    warnings = []

    # Check phases
    incomplete_phases = [p for p in plan.phases if not p["is_complete"]]
    if incomplete_phases:
        warnings.append(f"Incomplete phases: {len(incomplete_phases)}/{plan.total_phases}")
        for phase in incomplete_phases:
            warnings.append(f"  - Phase {phase['number']}: {phase['name']} ({phase['completed_steps']}/{phase['total_steps']} steps)")

    # Check completion checklist
    checklist_match = re.search(r'## Completion Checklist\s*\n(.+?)(?=\n##|\n---|\Z)', plan.content, re.DOTALL)
    if checklist_match:
        checklist = checklist_match.group(1)
        unchecked = [line.strip() for line in checklist.split('\n') if '- [ ]' in line]
        if unchecked:
            warnings.append(f"Completion checklist: {len(unchecked)} items remaining")
            for item in unchecked[:3]:  # Show first 3
                warnings.append(f"  {item}")

    return warnings


# Example usage and testing
if __name__ == "__main__":
    plan = find_active_session_plan()
    if plan:
        print(f"Found active plan: {plan.filepath.name}")
        print(f"Status: {plan.status}")
        print(f"Phase: {plan.current_phase}/{plan.total_phases}")
        print(f"\n{plan.get_summary()}")

        warnings = get_completion_warnings(plan)
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(warning)
    else:
        print("No active session plan found")
