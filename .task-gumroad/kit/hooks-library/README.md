# Claude Code Hooks Library

**24 production-ready hooks for Claude Code. Drop in, configure, ship.**

Hooks are shell scripts that run automatically at specific points in Claude Code's lifecycle — before tool calls, after file edits, on session start/end. This library gives you a battle-tested collection covering safety, quality, workflow automation, and integrations.

Price: $9–19 on Gumroad. MIT licensed.

---

## What are Claude Code hooks?

Claude Code hooks let you intercept and respond to agent events:

| Event | When it fires |
|-------|---------------|
| `PreToolUse` | Before any tool executes (Bash, Write, Edit, etc.) |
| `PostToolUse` | After a tool completes |
| `SessionStart` | When a Claude Code session begins |
| `Stop` | When a session ends |
| `SubagentStop` | When a subagent completes |

A hook is a shell script that reads JSON from stdin (the event payload) and optionally outputs a JSON `{"decision": "block", "reason": "..."}` to prevent the action.

---

## Hook Categories

### Quality (`hooks/quality/`)

Prevent bad code from accumulating.

| Hook | Event | What it does |
|------|-------|--------------|
| `pre-commit-lint.sh` | PreToolUse(Bash) | Runs your linter before any `git commit`. Blocks if linter fails. Auto-detects ruff, ESLint, golangci-lint, RuboCop. |
| `test-on-edit.sh` | PostToolUse(Edit) | After editing a source file, finds and runs the corresponding test file. Catches regressions immediately. |
| `complexity-guard.sh` | PostToolUse(Edit) | Measures cyclomatic complexity after edits. Warns (or blocks) when a function exceeds your threshold. Uses radon (Python), gocyclo (Go). |
| `secret-scanner.sh` | PreToolUse(Bash) | Scans staged changes for API keys, tokens, and passwords before `git commit`. Blocks with matched pattern shown. |

### Workflow (`hooks/workflow/`)

Automate the routine parts of a development session.

| Hook | Event | What it does |
|------|-------|--------------|
| `session-logger.sh` | SessionStart / Stop | Creates a structured session log in your Obsidian vault. Tracks project, timestamps, and duration. |
| `auto-branch.sh` | PreToolUse(Bash) | Detects when you're on `main`/`master` and creates a feature branch before any git operation. Never work directly on main again. |
| `time-tracker.sh` | SessionStart / Stop | Records session start/end in a local JSON ledger. Appends to a daily Markdown time log. |
| `git-conventional.sh` | PreToolUse(Bash) | Validates commit messages against Conventional Commits format. Blocks non-conforming messages and shows examples. |

### Safety (`hooks/safety/`)

Last line of defence against irreversible mistakes.

| Hook | Event | What it does |
|------|-------|--------------|
| `damage-control.sh` | PreToolUse(Write/Edit/Bash) | Blocks any write to configured protected directories. Also blocks destructive shell commands on those paths. |
| `backup-before-edit.sh` | PreToolUse(Edit) | Creates a timestamped backup before every file edit. Keeps last N versions. Quick undo without git. |
| `force-push-guard.sh` | PreToolUse(Bash) | Blocks `git push --force` targeting protected branches (main, master, production). Force push to feature branches is still allowed. |
| `dependency-check.sh` | PreToolUse(Bash) | Intercepts `npm install`, `pip install`, etc. and runs a vulnerability scan before packages are added. |

### Integrations (`hooks/integrations/`)

Connect Claude Code sessions to your existing tools.

| Hook | Event | What it does |
|------|-------|--------------|
| `slack-notify.sh` | Stop | Posts a session-end summary to Slack via webhook. Includes project, duration, and timestamp. |
| `telegram-notify.sh` | SessionStart / Stop | Sends Telegram messages on session start and end. Works with personal bots and group chats. |
| `linear-sync.sh` | Stop / PostToolUse(Bash) | Detects Linear issue IDs in branch names and commits. Updates issue state to "In Review" on session end. |
| `obsidian-daily.sh` | SessionStart / Stop | Appends activity entries to your Obsidian daily note. Uses Obsidian CLI if available, falls back to direct file write. |

### AI (`hooks/ai/`)

Make Claude Code sessions more context-aware and cost-efficient.

| Hook | Event | What it does |
|------|-------|--------------|
| `context-preloader.sh` | SessionStart | Outputs CLAUDE.md, README summary, recent git log, open TODOs, and active tasks at session start. Grounds Claude without manual prompting. |
| `completion-verifier.sh` | Stop | Runs a pre-close checklist: tests pass, lint clean, git tree clean, required files exist. Reports results and optionally blocks exit. |
| `cost-tracker.sh` | Stop | Reads token usage from session data and writes to a local cost ledger (JSON). Shows per-session and cumulative costs. |
| `prompt-cache.sh` | SessionStart | Maintains a tagged cache of context snippets. Injects relevant cached prompts at session start to reduce repeated context-setting. |

### Developer Experience (`hooks/dx/`)

Remove friction from the edit/verify loop.

| Hook | Event | What it does |
|------|-------|--------------|
| `auto-format.sh` | PostToolUse(Edit/Write) | Formats the edited file automatically. Supports ruff/black (Python), prettier (JS/TS), gofmt (Go), rustfmt (Rust), shfmt (shell). |
| `todo-collector.sh` | PostToolUse(Edit) | Scans edited files for TODO/FIXME/HACK/XXX comments. Appends new ones to a central `TODO.md`. No duplicates. |
| `changelog-updater.sh` | PostToolUse(Edit) | Detects version bumps in `package.json`, `pyproject.toml`, `Cargo.toml`. Generates a new CHANGELOG.md section from git commits. |
| `doc-generator.sh` | PostToolUse(Edit) | Runs pdoc (Python), TypeDoc (TS), or `go doc` after source edits. Keeps API docs in sync with code. |

---

## Quick Start

The fastest path to value: install the three hooks that should be universal.

**1. Create the hooks directory**

```bash
mkdir -p .claude/hooks
```

**2. Copy the essential hooks**

```bash
cp hooks/safety/damage-control.sh .claude/hooks/
cp hooks/safety/secret-scanner.sh .claude/hooks/
cp hooks/quality/pre-commit-lint.sh .claude/hooks/
chmod +x .claude/hooks/*.sh
```

**3. Configure `.claude/settings.json`**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/damage-control.sh"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/secret-scanner.sh"
          },
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-commit-lint.sh"
          }
        ]
      }
    ]
  }
}
```

**4. Configure protected paths in `damage-control.sh`**

Edit the `PROTECTED_PATHS` array near the top of the file. Add any directories that should never be touched by Claude.

See `INSTALL.md` for full installation details for each hook category.

---

## Configuration

Every hook follows the same conventions:

**Environment variables**: All configuration is via environment variables. Sensible defaults are built in. Override by exporting from your shell or sourcing a `.env` file.

**Opt-out**: Every hook checks `HOOK_NAME_DISABLED=1` to disable without removing the file.

**Warn vs block**: Safety hooks block by default. Use `HOOK_WARN_ONLY=1` to switch to warning mode while you evaluate behavior.

**Extensibility**: These are shell scripts. Read them, modify them, combine them. Nothing is compiled.

---

## Combining Hooks

Multiple hooks can share the same event. They run in sequence. Example: run all three quality checks on Bash commands:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/damage-control.sh" },
          { "type": "command", "command": "bash .claude/hooks/secret-scanner.sh" },
          { "type": "command", "command": "bash .claude/hooks/pre-commit-lint.sh" },
          { "type": "command", "command": "bash .claude/hooks/git-conventional.sh" },
          { "type": "command", "command": "bash .claude/hooks/force-push-guard.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/backup-before-edit.sh" },
          { "type": "command", "command": "bash .claude/hooks/auto-format.sh" },
          { "type": "command", "command": "bash .claude/hooks/test-on-edit.sh" }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/context-preloader.sh" },
          { "type": "command", "command": "bash .claude/hooks/session-logger.sh start" },
          { "type": "command", "command": "bash .claude/hooks/time-tracker.sh start" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/completion-verifier.sh" },
          { "type": "command", "command": "bash .claude/hooks/cost-tracker.sh" },
          { "type": "command", "command": "bash .claude/hooks/session-logger.sh end" },
          { "type": "command", "command": "bash .claude/hooks/time-tracker.sh stop" }
        ]
      }
    ]
  }
}
```

---

## Requirements

- **Claude Code** (any version supporting hooks)
- **bash** 4.0+ (macOS ships bash 3 — use `brew install bash` or `#!/usr/bin/env bash` with system zsh)
- **python3** (3.8+) — used for JSON parsing in most hooks
- **curl** — required for Slack, Telegram, Linear integration hooks
- **git** — required for all quality, workflow, and safety hooks

Language-specific tools (ruff, prettier, gofmt, etc.) are optional — hooks skip gracefully when tools are not installed.

---

## Hook Development Reference

**Reading the event payload:**
```bash
INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))")"
FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('path',''))")"
```

**Blocking a tool call:**
```bash
python3 -c "import json; print(json.dumps({'decision': 'block', 'reason': 'Your reason here'}))"
```

**Passing through (allow):**
```bash
exit 0
```

**Hook stdout vs stderr**: Use stderr (`>&2`) for log messages. Stdout is used for the JSON decision output.

---

## License

MIT — Copyright 2026 Edgeless Labs LLC

Use in personal and commercial projects. No warranty. See `LICENSE`.
