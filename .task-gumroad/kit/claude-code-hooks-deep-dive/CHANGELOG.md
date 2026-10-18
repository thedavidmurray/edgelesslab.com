# Changelog

All notable changes to Claude Code Hooks Deep Dive.

## 1.0.0 (2026-04-07)

### Shipped

**Guide (`content/guide.md`, ~4,700 words, 15 chapters)**
- Full walkthrough of 11 production hooks plus 4 customizable templates
- 4 mermaid diagrams covering the hook lifecycle, composition chains,
  deployment precedence, and the PostToolUse -> tracker -> alerts pipeline
- The $252 postmortem sidebar (Chapter 5) -- real story, real blocked-output
  example, the rule the hook now enforces
- "Common Gotchas" section covering matcher case-sensitivity, stdin parsing
  on macOS/zsh, exit code 2 vs JSON error format, and silent fail-open behavior
- Installation walkthrough before the appendices
- Appendix A with real terminal output captured from running the hooks

**Production hooks (`content/hooks/`, 15 files)**
- `damage-control.py` -- 25+ dangerous command patterns, 3-tier path protection,
  custom YAML parser with zero pip dependencies
- `verify-completion.py` -- evidence-based task verification, default-to-FAIL
- `post-tool-tracker.py` -- SQLite flight recorder with secret scrubbing
  (now includes the `error_message` column)
- `trading-observer.py` -- multi-agent financial tracking with risk tiers
- `sandbox-observer.py` -- E2B sandbox execution monitoring
- `skill-activation.py` -- progressive disclosure with SHA256 integrity check
- `inbox-auto-claim.py` -- two-phase multi-session dispatch
- `loop-stop-hook.py` -- iterative-loop exit protection
- `pre-compact.py` -- context backup with rotation and secret scrubbing
- `webfetch-archive.py` -- web fetch archival with YAML frontmatter
- `session-end.py` -- forced retrospectives with safety hardening
- Plus the four customizable templates from v0: `pre-commit-quality-gate.py`,
  `cost-tracker.py`, `notification-hook.py`, `secrets-scanner.py`

**Shared libraries (`content/lib/`, 7 modules)**
- `trading_helper.py` -- agent identification and risk tier logic
- `skill_matcher.py` -- YAML + JSON fallback matcher
- `session_plan.py` -- session plan parser
- `retrospective_tracker.py` -- retrospective completion state
- `memory_helper.py` -- memory system integration
- `backlog_checker.py` -- backlog staleness checker
- `e2b_sandbox.py` -- E2B sandbox wrapper

**Configs (`content/configs/`)**
- `patterns.yaml` -- full damage-control rule set (single-quoted regex)
- `schema.sql` -- complete SQLite schema for all observability hooks
- `settings-example.json` -- wiring for all 15 hooks

### Fixed

- `pre-commit-quality-gate.py` collapsed a redundant `if/elif/else` dispatcher
  left over from a refactor. The function now iterates over two small tuples
  of checks: one for staged-file checks, one for standalone checks.
- `notification-hook.py` no longer imports `os` inside `if __name__`. The
  import is at the top of the module where it belongs.
- All copied hooks had hardcoded `/Users/djm/...` paths scrubbed and replaced
  with `CLAUDE_PROJECT_DIR` environment variable fallbacks. Hooks now run
  from any project directory without edits.
- The guide's Chapter 4 post-tool-tracker schema now matches `configs/schema.sql`
  exactly. Both document the `error_message` column.

### Known Limitations

- Hooks assume Python 3.10+. `str | None` type hints will fail under older
  interpreters. If you need 3.8 or 3.9, rewrite the hints as `Optional[str]`.
- `trading-observer.py` has placeholder agent names (`agent_a`, `agent_b`).
  Customize `lib/trading_helper.py` for your own bot directory names before
  enabling the hook on any real trading session.
- `session-end.py`'s forced-retrospective logic assumes a retrospective tracker
  state file exists. On first run you will be prompted to initialize it.
- `skill-activation.py` requires a `skill-rules.json` file with a precomputed
  SHA256 hash. The hook falls back to the YAML matcher if the hash is missing,
  but the integrity check is a no-op in that mode.
- No automated test suite. Each hook is individually runnable with a sample
  stdin JSON payload (see Appendix A and Chapter 15 "Testing Hooks").

### Planned for 1.1

- Unit tests for each hook with golden-file stdin/stderr fixtures
- A `hooks-install` script that copies files, wires settings.json, and
  initializes the SQLite database in one command
- An `events-db-viewer` TUI for exploring `tool_usage` without writing SQL
- Optional pyproject.toml for pip-installable hook distribution
- Hardened `skill-activation.py` that treats missing integrity hash as fatal
- Windows compatibility pass (current hooks are macOS/Linux only)
