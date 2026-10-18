# Claude Code Hooks Deep Dive

15 production hooks beyond the basics. From the system that runs 5 agents 24/7.

## What's Inside

- **content/guide.md** -- 15-chapter walkthrough (~4,700 words) covering safety, observability, automation, preservation, composition, and deployment. Includes the $252 postmortem sidebar and 4 mermaid diagrams.
- **content/hooks/** -- 15 production hooks: 11 real hooks from a live multi-agent system plus 4 customizable templates
- **content/lib/** -- 7 shared library modules (trading_helper, skill_matcher, session_plan, and more)
- **content/configs/** -- patterns.yaml (damage-control rules), schema.sql (observability database), settings-example.json

## Quick Start

1. Copy `content/hooks/` and `content/lib/` into your project's `.claude/hooks/`
2. Copy `content/configs/patterns.yaml` next to `damage-control.py` (same directory)
3. Copy `content/configs/settings-example.json` to `.claude/settings.json` and trim the hooks you do not want
4. Initialize the tracking database: `sqlite3 .claude/hooks/events.db < content/configs/schema.sql`
5. Test damage-control:
   ```bash
   printf '%s' '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
     | python3 .claude/hooks/damage-control.py
   echo $?   # should print 2 (BLOCKED)

   printf '%s' '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
     | python3 .claude/hooks/damage-control.py
   echo $?   # should print 0 (ALLOWED)
   ```

## Prerequisites

- Claude Code (any version with hooks support)
- Python 3.10+
- No external pip dependencies (by design)

## File Structure

```
hooks-deep-dive/
  content/
    guide.md                            -- Full 15-chapter guide
    hooks/                              -- 15 Python hooks
      damage-control.py                  (production)
      verify-completion.py               (production)
      post-tool-tracker.py               (production)
      trading-observer.py                (production)
      sandbox-observer.py                (production)
      skill-activation.py                (production)
      inbox-auto-claim.py                (production)
      loop-stop-hook.py                  (production)
      pre-compact.py                     (production)
      webfetch-archive.py                (production)
      session-end.py                     (production)
      pre-commit-quality-gate.py         (template)
      cost-tracker.py                    (template)
      notification-hook.py               (template)
      secrets-scanner.py                 (template)
      patterns.yaml                      -- loaded by damage-control.py
    lib/                                -- shared library modules
      trading_helper.py
      skill_matcher.py
      session_plan.py
      retrospective_tracker.py
      memory_helper.py
      backlog_checker.py
      e2b_sandbox.py
    configs/
      patterns.yaml                     -- damage-control rules
      schema.sql                        -- SQLite observability schema
      settings-example.json
  README.md
  CHANGELOG.md
```

## Version

1.0.0 -- Initial release, April 2026
