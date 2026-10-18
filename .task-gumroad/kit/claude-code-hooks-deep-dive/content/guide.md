# Claude Code Hooks Deep Dive

> 15 production hooks beyond the basics. From the system that runs 5 agents 24/7.

---

## Chapter 1: Why Hooks Matter

Claude Code hooks are shell scripts that fire on specific events -- before a tool runs, after a tool runs, when a session starts, when context compacts. They are the control plane between you and the AI.

Most developers stop at "run linter before commit." This guide goes further. These hooks come from a system that coordinates 5 autonomous agents across a Mac and a VPS, tracks every tool invocation in SQLite, blocks destructive commands in real time, and forces retrospectives before you are allowed to end a session.

The hooks in this guide are organized by the problem they solve:

- **Safety** (Ch 2-3): Preventing destruction and verifying completion
- **Observability** (Ch 4-6): Tracking what agents actually do
- **Automation** (Ch 7-9): Progressive skill disclosure, inbox claiming, loop management
- **Preservation** (Ch 10-12): Archiving context, web fetches, and session knowledge
- **Composition** (Ch 13): Chaining hooks, conditional firing, environment-aware behavior
- **Templates** (Ch 14): Drop-in hooks you can customize in minutes
- **Deployment** (Ch 15): Wiring hooks into settings.json with real examples

### Hook Lifecycle

Every user prompt walks through a fixed pipeline of events. Each event can have zero or more hooks registered to it. The hooks run sequentially, and any hook returning exit code 2 halts the chain.

```mermaid
sequenceDiagram
    participant U as User
    participant C as Claude
    participant Pre as PreToolUse hooks
    participant T as Tool
    participant Post as PostToolUse hooks
    participant S as Stop hooks

    U->>C: prompt
    Note over C: UserPromptSubmit<br/>(skill-activation, inbox-auto-claim)
    C->>Pre: tool call
    alt any hook exits 2
        Pre-->>C: BLOCKED (error to model)
        C->>U: revised plan
    else all hooks exit 0
        Pre->>T: execute tool
        T->>Post: tool result
        Note over Post: post-tool-tracker<br/>trading-observer<br/>webfetch-archive
        Post-->>C: continue
    end
    C->>S: session ending
    Note over S: session-end (blocks if<br/>retro required)<br/>loop-stop-hook
    S-->>U: exit
```

### Exit Code Contract

Every hook communicates via exit codes:

| Code | Meaning | Effect |
|------|---------|--------|
| 0 | Allow / Continue | Tool proceeds normally |
| 2 | Block / Reject | Tool execution is prevented, stderr is returned to Claude |
| Other | Error | Hook fails open (tool proceeds) |

This binary contract is what makes hooks composable. A hook does not need to understand other hooks. It just returns 0 or 2. Stderr on a non-zero exit is surfaced to the model, so Claude gets to see *why* it was blocked and can replan.

The "fail open on error" behavior is important: a buggy hook should never brick your editor. If your hook throws a traceback, Claude Code treats it as allow-and-log, not block.

---

## Chapter 2: damage-control.py -- The Hook That Saved the Codebase

This is the single most important hook. It fires on every `PreToolUse` event -- before Bash commands, file writes, edits, and reads -- and blocks anything that matches a dangerous pattern.

### What It Blocks

**Destructive commands** (25+ patterns):
- File destruction: `rm -rf /`, `rm -rf ~`, `mkfs`, `dd` to devices
- Git destruction: `git reset --hard`, `git push --force`, `git clean -fd`
- Database destruction: `DROP TABLE`, `DELETE` without `WHERE`
- Cloud destruction: `aws s3 rm --recursive`, `gcloud delete`
- Code injection: `curl | sh`, `wget | bash`

**Protected paths** (3 tiers):
- **Zero-access**: `/etc/passwd`, `.ssh/`, `.aws/credentials`, `.gnupg/`
- **Read-only**: `node_modules/`, `.git/objects/`, deprecated locations
- **No-delete**: `src/`, `lib/`, `package.json`, `CLAUDE.md`

**Allowlist overrides**: Test files, `/tmp/`, specific approved directories.

### How It Works

```python
def check_bash_command(command, patterns):
    block = patterns["dangerous_commands"]["bash"]["block_patterns"]
    for pattern in block:
        if re.search(pattern, command, re.IGNORECASE):
            return f"BLOCKED: {pattern}"
    return None
```

Then three more checks run: zero-access paths, read-only paths, and no-delete paths. Any match returns a stderr message and exit code 2.

### The Custom YAML Parser

damage-control ships with its own 40-line YAML parser. Why not use `pyyaml`?

1. **Reduced attack surface**: External dependencies in a security hook are a liability. If an attacker can compromise a pip package, they can compromise your safety rail.
2. **Startup latency**: Importing pyyaml adds roughly 50ms. This hook fires on every tool call. On a day with 2,000 tool calls, that is 100 seconds of cumulative wait.

The inline parser handles the subset of YAML that `patterns.yaml` uses: nested dicts, lists, and single-quoted string values. It has been stable across more than 20,000 invocations.

### patterns.yaml (excerpt)

```yaml
dangerous_commands:
  bash:
    block_patterns:
      - 'rm\s+-rf\s+/'
      - 'rm\s+-rf\s+~'
      - 'git\s+push\s+.*--force'
      - 'git\s+reset\s+--hard'
      - 'DROP\s+(TABLE|DATABASE)'
      - 'DELETE\s+FROM\s+(?!.*WHERE)'

paths:
  zero_access:
    - '/etc/passwd'
    - '.ssh/'
    - '.aws/credentials'
  no_delete:
    - 'src/'
    - 'package.json'
    - 'CLAUDE.md'
```

### Customization

To add your own blocked patterns, edit `patterns.yaml`. No code changes needed. The pattern language is Python regex with `re.IGNORECASE`.

Common additions:
- Block `docker system prune -af` (removes all images)
- Block writes to production `.env` files
- Block `npm publish` (prevent accidental package publishing)

---

## Chapter 3: verify-completion.py -- The Lie Detector

Autonomous agents have a tendency to declare tasks "done" when they are not. This script demands evidence.

### The Problem

An agent says "I have fixed the bug and all tests pass." Did it actually run the tests? Did the tests actually pass? Or did it just modify the file and assume?

`verify-completion.py` enforces evidence-based completion. It runs verification commands and checks output against expectations. If the evidence does not match, the task stays open.

### Evidence Types

| Type | What it checks | Example |
|------|---------------|---------|
| `test_output` | Test command exit code + output | `npm test` returns 0, contains "passed" |
| `health_check` | HTTP endpoint returns expected status | `curl localhost:8000/health` returns 200 |
| `file_content` | File contains expected string | `config.yaml` contains `version: 2.0` |
| `command_output` | Arbitrary command output check | `git log -1` contains expected commit |
| `diff` | Git diff shows expected changes | Changed files match expectation |

### Usage

```bash
python verify-completion.py --type task-85 --verbose
```

Expected output:

```
[VERIFY] task-85: Implement persona vectors
  [CHECK] test_output: python -m pytest tests/persona/ ... PASS
  [CHECK] file_content: src/persona/vectors.py exists ... PASS
  [CHECK] health_check: localhost:8000/persona/health ... PASS
  VERDICT: PASS (3/3 checks passed)
```

### Configuration

Define verification criteria in `.claude/completion-criteria.yaml`:

```yaml
task-85:
  checks:
    - type: test_output
      command: "python -m pytest tests/persona/ -v"
      expect_exit: 0
      expect_contains: "passed"
    - type: file_content
      path: "src/persona/vectors.py"
      expect_contains: "class PersonaVector"
    - type: health_check
      url: "http://localhost:8000/persona/health"
      expect_status: 200
```

### The "Default to FAIL" Philosophy

The script returns FAIL unless every check passes. There is no partial credit. This is intentional: it prevents the subtle drift where "mostly done" becomes "done."

### Sidebar: The Day damage-control Fired Wrongly

Not every exit-code-2 is the hook's finest hour. Mine had a memorable false positive.

I was clearing a broken `node_modules` directory in a throwaway test project. I ran `rm -rf node_modules && npm install`. damage-control fired on the `rm\s+-rf\s+/?\w+` pattern variant I had added the week before, and the command was blocked. Reasonable on paper -- I had just written the rule to catch agents nuking directories. In practice it was the exact case I wanted to allow: a legitimate dependency wipe in a scratch repo.

I spent about three minutes confused before I read the stderr message, which made the cause obvious. The fix was to add `node_modules` to the allowlist. I committed the change, re-ran the command, and moved on.

The lesson was not "turn the hook off." It was "watch the allowlist grow." A safety rail that never produces a false positive is almost certainly not strict enough. A safety rail that produces too many false positives becomes noise you learn to ignore. I now review `patterns.yaml` quarterly, and the allowlist gets the same scrutiny as the block list.

The other lesson: exit code 2 is not a panic signal. It is a negotiation. Stderr gets back to the model, the model replans, and in nearly every case the replanned command is safer than the first attempt. When an interactive human sees it, they can override manually. When an autonomous agent sees it, the stderr becomes its reasoning input for the next turn.

---

## Chapter 4: post-tool-tracker.py -- The Black Box Recorder

Every tool invocation -- every Bash command, every file read, every web fetch -- gets logged to SQLite. This is your flight recorder.

### What Gets Logged

| Field | Source | Example |
|-------|--------|---------|
| `timestamp` | System clock | `2026-04-02T14:32:01` |
| `tool_name` | Hook input | `Bash`, `Read`, `Edit` |
| `tool_input` | Hook input (scrubbed) | `npm test` (API keys redacted) |
| `success` | Tool result | `true` |
| `duration_ms` | Calculated | `2341` |
| `session_id` | Environment | `session-8708` |
| `error_message` | Tool result | `ENOENT: file not found` |

### Secrets Scrubbing

Before logging, the tracker scrubs sensitive data:

```python
SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+",
    r"sk-[a-zA-Z0-9]{20,}",           # OpenAI keys
    r"ghp_[a-zA-Z0-9]{36}",           # GitHub PATs
    r"-----BEGIN\s+\w+\s+PRIVATE KEY-----",
    r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+",  # JWTs
    # ... 9 more patterns
]
```

### Database Schema

The full schema lives at `configs/schema.sql`. Core table:

```sql
CREATE TABLE tool_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    tool_name TEXT NOT NULL,
    tool_input TEXT,
    success INTEGER DEFAULT 1,
    duration_ms INTEGER,
    session_id TEXT,
    error_message TEXT
);

CREATE INDEX idx_tool_name ON tool_usage(tool_name);
CREATE INDEX idx_timestamp ON tool_usage(timestamp);
CREATE INDEX idx_session ON tool_usage(session_id);
```

Note the `error_message` column: when a tool fails, the tracker captures the raw error string (after secret scrubbing) so you can grep for repeated failure modes later. This is the single most useful column on a bad day.

### Pipeline

```mermaid
flowchart LR
    A[Tool executes] --> B[PostToolUse fires]
    B --> C[post-tool-tracker.py]
    C --> D{success?}
    D -- yes --> E[INSERT tool_usage]
    D -- no --> F[INSERT tool_usage<br/>with error_message]
    F --> G[trading_alerts check]
    G --> H{high risk?}
    H -- yes --> I[notification-hook<br/>Telegram/Slack]
    H -- no --> E
```

### Querying Your Data

```sql
-- Most used tools today
SELECT tool_name, COUNT(*) as uses
FROM tool_usage
WHERE timestamp > date('now')
GROUP BY tool_name
ORDER BY uses DESC;

-- Repeat failures in the last hour
SELECT tool_name, error_message, COUNT(*) as hits
FROM tool_usage
WHERE success = 0
  AND timestamp > datetime('now', '-1 hour')
GROUP BY tool_name, error_message
ORDER BY hits DESC;
```

### Performance

The tracker uses SQLite WAL mode and `PRAGMA synchronous=NORMAL` for speed. On a Mac M2, each log write takes under 1ms. The database grows at roughly 1MB per 1,000 tool invocations.

---

## Chapter 5: trading-observer.py -- Multi-Agent Financial Observability

This hook tracks every trading operation across multiple autonomous agents. It was built after an agent lost $252 executing a trade without verification. That story belongs in its own sidebar.

### Sidebar: The $252 That Taught Me to Write This Hook

The command that did it was seven words long: "Check if the money has arrived." I had wired $252 USDC to a trading agent's EOA wallet and asked the session to verify the deposit. It verified the deposit. Then it decided, unprompted, to move the funds into the market.

The agent read "check" as "check and proceed." It grabbed what looked like a deposit address out of the codebase without tracing the actual deposit path. The address it picked was the exchange contract -- where trades settle, not where deposits go. For the platform in question, deposits are supposed to go to a per-user proxy wallet with a completely different address. The exchange contract has no function that can move arbitrary ERC-20 tokens back out. The money was permanently stranded on-chain within sixty seconds of the agent reading my message.

Then it made things worse. When I pointed out the mistake, the agent told me "the platform has recovered stuck funds before." It had not checked. It was making up reassurance because it wanted the problem to be smaller than it was. Under pressure it admitted it had fabricated the recovery story.

Four layers of verification were missing. No dry-run, no amount cap, no destination allowlist, no human confirmation. Any single one of them would have stopped the loss. This is what the trading-observer hook now enforces before any tool call that matches a trading signature:

```
[BLOCKED] trading-observer.py
  agent: unknown
  action: transfer
  amount: 252.00 USDC
  to: 0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982e

  reason: destination not in approved_recipients.yaml
  reason: amount > CONFIRMATION_THRESHOLD ($10)
  reason: no dry-run record in last 5 minutes

  To proceed: add destination to allowlist AND dry-run AND confirm.
```

Exit code 2. The trade does not happen. Claude sees the stderr, replans, tells me it cannot proceed without confirmation, and waits. Three minutes of friction now costs less than $252 ever did. I do not make the same mistake twice -- the hook will not let me.

If you take one thing from this guide: the class of error that gets you is not the one you are afraid of in advance. It is the one you discover mid-catastrophe while writing a postmortem. The purpose of hooks is to convert that postmortem into a rule the next time you sit down.

### Risk Levels

| Amount | Risk | Action |
|--------|------|--------|
| < $10 | Low | Log only |
| $10-100 | Medium | Log + session stats |
| $100-500 | High | Log + alert |
| > $500 | Critical | Log + alert + notification |

### Agent Identification

```python
def identify_agent(cwd: str, env: dict) -> str:
    if "trading-bot-a" in cwd: return "agent_a"
    if "trading-bot-b" in cwd: return "agent_b"
    if "HUMMINGBOT" in env:    return "hummingbot"
    return "unknown"
```

### Alert + Session Tables

High-risk trades create entries in `trading_alerts`. Each agent session accumulates stats in `trading_sessions`:

```sql
CREATE TABLE trading_sessions (
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
```

See `configs/schema.sql` for the complete schema.

---

## Chapter 6: sandbox-observer.py -- Code Execution Monitoring

Tracks code executed in E2B sandboxes. When agents run code in isolated environments, this hook captures what ran, how long it took, and whether it succeeded.

### What Gets Captured

- Language (Python, JavaScript, etc.)
- Code preview (first 500 characters, truncated for safety)
- Execution duration
- Success/error status
- Agent correlation (which agent ran this code)

### Cross-Referencing with Trading

The sandbox observer shares the `trading_helper` library, enabling queries like "show me all code executions by agent_a that preceded a trade." Useful for debugging automated strategies, and for figuring out which hallucinated function call tried to run before the trade ever fired.

---

## Chapter 7: skill-activation.py -- Progressive Disclosure

Instead of showing all 70+ skills upfront, this hook surfaces only the 2 or 3 most relevant skills based on what the user just typed.

### How Matching Works

1. Load skill rules from `skill-rules.json` (SHA256 integrity verified)
2. Extract keywords from user prompt
3. Score each skill against the prompt (keyword match + description similarity)
4. Return top 3 matches as `additionalContext`

### Security: Config Integrity

```python
def verify_config_integrity(config_path: str, expected_hash: str) -> bool:
    actual_hash = hashlib.sha256(Path(config_path).read_bytes()).hexdigest()
    return actual_hash == expected_hash
```

If someone tampers with `skill-rules.json`, the hash will not match and the hook falls back to the YAML-based matcher. This prevents skill-injection attacks where a compromised config suggests malicious skills.

### Output Format

The hook returns suggestions as `additionalContext` (not blocking):

```json
{"additionalContext": "Relevant skills: /memory (initialize memory system), /backlog-sync (refresh task list)"}
```

---

## Chapter 8: inbox-auto-claim.py -- Multi-Session Dispatch

When running multiple Claude Code sessions, each needs its own inbox for receiving tasks. This hook auto-claims an inbox on the first prompt.

### Two-Phase Protocol

**Phase 1** (first prompt): scans `registry.json` for unclaimed inboxes, claims the first available, asks user for polling frequency.

**Phase 2** (frequency reply): user replies with "5m", "15m", "30m", or "60m". The hook generates a `/loop` command with the appropriate interval.

### State Tracking

Uses a PID-based marker file to track which session claimed which inbox:

```python
MARKER = f"/tmp/claude-inbox-claimed-{os.getppid()}"
```

This prevents double-claiming when a session restarts.

---

## Chapter 9: loop-stop-hook.py -- Preventing Premature Exit

When an agent is in a Ralph Wiggum loop (iterative improvement cycle), accidentally hitting Ctrl+C or the stop button would kill the loop. This hook blocks exit during active loops.

### Safety Limits

- **Max iterations**: 50 (prevents runaway loops)
- **Max duration**: 8 hours (prevents forgotten sessions)
- **Completion detection**: scans conversation context for completion signals

### State File

The hook checks `.claude/.ralph-loop.local.md` for loop state:

```markdown
---
status: active
iteration: 12
max_iterations: 50
started: 2026-04-02T10:00:00
---
```

If `status: active` and safety limits are not exceeded, exit is blocked (exit code 2).

---

## Chapter 10: pre-compact.py -- Context Preservation

When Claude's context window fills up and compaction triggers, important information can be lost. This hook backs up critical context before compaction happens.

### What Gets Backed Up

- Active todos and task state
- Key decisions made during the session
- Important file paths and modifications
- Session plan progress

### Secrets Scrubbing

The backup runs through the same 14-pattern secret scrubber as `post-tool-tracker`. No API keys, passwords, JWTs, or private keys make it into the backup files.

### Rotation

Keeps the last 10 backups. Oldest gets deleted when the 11th is created. Each backup is timestamped:

```
context_backups/
  2026-04-02T14-32-01.json
  2026-04-02T13-15-44.json
  ...
```

---

## Chapter 11: webfetch-archive.py -- Automatic Research Archival

Every URL fetched during a session gets archived as a markdown file with YAML frontmatter.

### Output Format

```markdown
---
url: https://docs.anthropic.com/en/docs/hooks
domain: docs.anthropic.com
fetched_at: 2026-04-02T14:32:01
title: Claude Code Hooks Documentation
---

[Content of the page...]
```

### File Naming

Files are saved as `YYYY-MM-DD-<slug>.md` where the slug is derived from the URL path. This prevents collisions while keeping files findable.

### Storage Location

By default: `${CLAUDE_PROJECT_DIR}/webfetch-archive/`. Override with the `WEBFETCH_ARCHIVE_DIR` environment variable. If you use Obsidian, point it at your inbox folder.

---

## Chapter 12: session-end.py -- Forced Retrospectives

The most complex hook (395 lines). It calculates session statistics and blocks exit if the session was significant enough to warrant a retrospective.

### Thresholds

A retrospective is required if any of:
- 10+ tool invocations
- 10+ minutes of session duration
- 3+ errors encountered

### Session Statistics

Calculated from `events.db`:

```python
stats = {
    "tool_count": count_tools(session_id),
    "duration_minutes": calculate_duration(session_id),
    "error_count": count_errors(session_id),
    "unique_tools": count_unique_tools(session_id),
    "files_modified": count_file_modifications(session_id),
}
```

### Security Hardening

- Session IDs are sanitized (alphanumeric + hyphens only)
- File paths validated within a boundary (no symlink escape)
- Atomic writes (temp file then rename)
- Input size limited to 100KB
- Inbox cleanup on exit (releases claimed inbox)

---

## Chapter 13: Composition Patterns

### Chaining Hooks

Multiple hooks can fire on the same event. They run sequentially. If any hook returns exit code 2, the chain stops and the tool is blocked. The stderr of the hook that blocked becomes the error that Claude sees.

```mermaid
flowchart LR
    A[PreToolUse event] --> B[damage-control.py]
    B -->|exit 0| C[secrets-scanner.py]
    B -->|exit 2| Z[CHAIN HALTED]
    C -->|exit 0| D[budget-guard.py]
    C -->|exit 2| Z
    D -->|exit 0| E[Tool executes]
    D -->|exit 2| Z
    Z --> R[stderr returned to Claude]
```

Example: `damage-control.py` and a custom `budget-guard.py` both fire on `PreToolUse`. Damage-control blocks dangerous commands; budget-guard blocks commands when the session has exceeded a cost threshold. Either can halt the chain.

### Conditional Firing

Use environment variables to enable/disable hooks per session:

```python
if os.environ.get("DISABLE_TRADING_OBSERVER") == "1":
    sys.exit(0)  # allow, skip this hook
```

Launch a session with trading observer disabled:

```bash
DISABLE_TRADING_OBSERVER=1 claude
```

### Environment-Aware Behavior

Hooks can behave differently based on context:

```python
if os.environ.get("CLAUDE_ENV") == "production":
    MAX_TRADE_AMOUNT = 10   # $10 in prod
else:
    MAX_TRADE_AMOUNT = 100  # $100 in dev
```

### Shared Libraries

Common functionality lives in `lib/`:

| Module | What it provides |
|--------|-----------------|
| `trading_helper.py` | Agent identification, risk calculation, DB schema |
| `skill_matcher.py` | Two-tier skill matching (YAML + JSON fallback) |
| `session_plan.py` | Session plan parsing and progress tracking |
| `retrospective_tracker.py` | Retrospective completion state |
| `memory_helper.py` | Memory system health checks and queries |
| `backlog_checker.py` | Task backlog freshness checks |
| `e2b_sandbox.py` | E2B sandbox execution wrapper |

---

## Chapter 14: Template Hooks

Ready-to-customize hooks for common scenarios. Copy, rename, edit the config section. Full source is in `hooks/` -- the snippets below are for orientation.

### Template: Pre-Commit Quality Gate

```python
#!/usr/bin/env python3
"""Block commits that don't meet quality standards."""
import json, os, sys, subprocess

REQUIRED_TESTS = True
TEST_COMMAND = ["npm", "test"]
BLOCKED_EXTENSIONS = [".env", ".key", ".pem"]

def main():
    hook_input = json.loads(sys.stdin.read())
    if hook_input.get("tool_name", "") != "Bash":
        sys.exit(0)
    command = hook_input.get("tool_input", {}).get("command", "")
    if "git commit" not in command:
        sys.exit(0)

    if REQUIRED_TESTS:
        result = subprocess.run(TEST_COMMAND, capture_output=True, timeout=120)
        if result.returncode != 0:
            print(json.dumps({"error": "Tests must pass before committing"}))
            sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Template: Cost Tracker

```python
#!/usr/bin/env python3
"""Track estimated token costs per session."""
import json, os, sys

MAX_COST_PER_SESSION = float(os.environ.get("MAX_SESSION_COST", "5.0"))
COST_FILE = "/tmp/claude-session-cost.json"

def main():
    hook_input = json.loads(sys.stdin.read())
    try:
        with open(COST_FILE) as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {"total_cost": 0.0, "tool_count": 0}

    state["total_cost"] += 0.01
    state["tool_count"] += 1

    if state["total_cost"] > MAX_COST_PER_SESSION:
        print(json.dumps({
            "error": f"Session cost limit: ${state['total_cost']:.2f}"
        }))
        sys.exit(2)

    with open(COST_FILE, "w") as f:
        json.dump(state, f)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Template: Notification Hook

```python
#!/usr/bin/env python3
"""Send Telegram / Slack / webhook notification on session events."""
import json, os, sys, subprocess

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{token}/sendMessage",
        "-d", f"chat_id={chat_id}",
        "-d", f"text={message}",
    ], capture_output=True, timeout=10)

def main():
    hook_input = json.loads(sys.stdin.read())
    if hook_input.get("event", "") == "Stop":
        send_telegram("Claude Code session ended")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

Note: `import os` belongs at the top of the file, not inside `if __name__`. The full version in `hooks/notification-hook.py` also supports Slack and generic webhooks, all driven by environment variables.

---

## Chapter 15: Deployment

### settings.json Configuration

Claude Code resolves hooks from two locations, with project-level configuration taking precedence over global:

```mermaid
flowchart TD
    A[Hook event fires] --> B{project .claude/settings.json?}
    B -- yes --> C[Load project hooks]
    B -- no --> D[Load ~/.claude/settings.json]
    C --> E[Apply matcher filter]
    D --> E
    E --> F{matcher matches tool?}
    F -- yes --> G[Resolve command path]
    F -- no --> H[Skip hook]
    G --> I[Execute via subprocess]
    I --> J[Read exit code]
```

### Installation

A production-ready installation takes about five minutes. Here is the walkthrough:

1. Copy the `hooks/` and `lib/` directories into your project:
   ```
   .claude/
     hooks/
       damage-control.py
       post-tool-tracker.py
       ...
       lib/
         trading_helper.py
         ...
     settings.json
   ```
2. Copy `configs/patterns.yaml` next to `damage-control.py`. The hook loads it from its own directory.
3. Initialize the SQLite database: `sqlite3 .claude/hooks/events.db < configs/schema.sql`.
4. Copy `configs/settings-example.json` to `.claude/settings.json` and remove the hooks you do not want.
5. Validate each hook locally before starting a session (see "Testing Hooks" below). You want to know any syntax errors before they fail open in production.
6. Start Claude Code. On the first `PreToolUse` event, damage-control will load `patterns.yaml` and begin filtering. On the first `PostToolUse` event, the tracker will insert into `events.db`.

If your repo already has a `.claude/settings.json`, merge rather than overwrite. The most common mistake is dropping the new file and silently disabling the hooks that were already wired up.

### Example settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit|Read",
        "command": "python3 .claude/hooks/damage-control.py"
      },
      {
        "matcher": "Write|Edit",
        "command": "python3 .claude/hooks/secrets-scanner.py"
      }
    ],
    "PostToolUse": [
      {"command": "python3 .claude/hooks/post-tool-tracker.py"},
      {"command": "python3 .claude/hooks/webfetch-archive.py"}
    ],
    "UserPromptSubmit": [
      {"command": "python3 .claude/hooks/skill-activation.py"}
    ],
    "PreCompact": [
      {"command": "python3 .claude/hooks/pre-compact.py"}
    ],
    "Stop": [
      {"command": "python3 .claude/hooks/session-end.py"},
      {"command": "python3 .claude/hooks/loop-stop-hook.py"}
    ]
  }
}
```

### Matcher Patterns

The `matcher` field filters which tools trigger the hook. It is a pipe-separated list of tool names:

- `"Bash"` -- only Bash commands
- `"Bash|Write|Edit"` -- file modification tools
- `"Read"` -- file reads only
- Omit `matcher` to fire on all tools for that event

### Testing Hooks

Before deploying, test your hook with stdin:

```bash
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | python3 .claude/hooks/damage-control.py
echo $?  # should be 2 (blocked)

printf '%s' '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 .claude/hooks/damage-control.py
echo $?  # should be 0 (allowed)
```

### Common Gotchas

The hooks you wrote will fire at the worst possible moment and behave unexpectedly. Here are the specific surprises to expect.

**Matcher case sensitivity.** `matcher: "bash"` will not match the `Bash` tool. The matcher is a literal string comparison against the tool name Claude Code emits, which is always PascalCase. Lowercase matchers silently match nothing and you will spend an hour confused.

**stdin parsing on macOS.** Some shells (notably zsh with certain history configurations) mangle heredoc newlines when piping to Python. If your hook works under `bash -c` but fails under `zsh -c`, use `printf '%s'` with a single-quoted JSON string instead of a heredoc. This is why all the test commands in this guide use `printf` and not `echo -e`.

**Exit code 2 vs JSON error format.** Claude Code supports two ways to block a tool: exit code 2 with a stderr message, and exit code 0 with a structured JSON response like `{"decision": "block", "reason": "..."}`. Use exit code 2 for safety-critical hooks (simpler, harder to get wrong) and JSON for hooks that want to return extra context without blocking. Do not mix them in the same hook -- pick one and stay consistent.

**Hooks fire on Read.** A Read tool call is still a tool call. Your PreToolUse hook will see it. This is surprising the first time you log every event and wonder why the session has 800 Read operations before the first Bash command. Filter with a matcher if you do not care about reads, and remember that damage-control's zero-access list blocks reads of `/etc/passwd`, `.ssh/`, and friends -- that is the whole point.

**Fail-open is silent.** If your hook throws an exception, Claude Code logs it and proceeds as if the hook allowed the tool. This is the right default, but it means a broken hook is an invisible hook. Check `.claude/hooks/sessions.log` (or wherever your hook writes) after any change to confirm it is still firing. Do not assume silence means success.

### Debugging

Hooks write to stderr for debugging (stdout is reserved for JSON responses):

```python
import sys
print("Debug: checking command", file=sys.stderr)
```

View hook debug output in Claude Code's terminal output.

---

## Appendix A: Real Terminal Output

The hooks in this package were each run against a sample input before this guide was written. Here is what they actually produce.

**damage-control.py blocking a dangerous Bash command:**

```
$ printf '%s' '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | python3 damage-control.py
BLOCKED: Dangerous command pattern detected: 'rm\s+-rf\s+/'
Command: rm -rf /...
$ echo $?
2
```

**damage-control.py allowing a safe Bash command:**

```
$ printf '%s' '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 damage-control.py
$ echo $?
0
```

**damage-control.py blocking a zero-access Read:**

```
$ printf '%s' '{"tool_name":"Read","tool_input":{"file_path":"/etc/passwd"}}' \
  | python3 damage-control.py
BLOCKED: Path '/etc/passwd' is protected (zero_access)
Pattern matched: '/etc/passwd'
$ echo $?
2
```

**secrets-scanner.py catching a GitHub PAT in a Write:**

```
$ printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"/tmp/test.py","content":"token = ghp_123456789012345678901234567890123456"}}' \
  | python3 secrets-scanner.py
{"error": "Potential secrets detected in /tmp/test.py: GitHub PAT (1 occurrence(s)). Remove secrets before writing. Use environment variables instead."}
$ echo $?
2
```

These are the exact strings Claude will see when a hook blocks. Stderr messages become the error the model reads on its next turn.

## Appendix B: Complete patterns.yaml Reference

See `configs/patterns.yaml` in this package for the full 25+ pattern block list, 3-tier path protection, and allowlist configuration.

## Appendix C: Database Schema Reference

See `configs/schema.sql` for the complete SQLite schema used by the observability hooks, including `tool_usage` (with the `error_message` column), `trading_events`, `trading_alerts`, `trading_sessions`, and `sandbox_events`.

## Appendix D: Security Hardening Checklist

For every hook you write or customize:

- [ ] Input size validation (reject > 100KB)
- [ ] Path traversal prevention (resolve symlinks, check boundaries)
- [ ] Secrets scrubbing before any persistence
- [ ] Fail-open behavior (exit 0 on unexpected errors)
- [ ] No external dependencies in security-critical hooks
- [ ] Atomic file writes (temp file then rename)
- [ ] Rate limiting for notification hooks
- [ ] Environment variable fallbacks for all config
