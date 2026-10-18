# Configs

This directory contains a reference `settings.json` that wires up all three
safety hooks shipped with this product:

- `scope-guard.py` -- blocks actions that exceed the scope of the user's
  original request
- `financial-gate.py` -- blocks money-moving commands until the verification
  protocol is recorded
- `reversibility-classifier.py` -- classifies commands and blocks
  hard-irreversible operations outright

## Installation

1. **Copy the hooks** into your project:

   ```bash
   mkdir -p .claude/hooks
   cp content/hooks/*.py .claude/hooks/
   chmod +x .claude/hooks/*.py
   ```

2. **Merge `settings.json`** into your existing `.claude/settings.json`.

   If you already have a `settings.json`, do not overwrite it. Merge the
   `hooks.PreToolUse` array by hand, keeping your existing entries and
   appending the three hook blocks from this file.

   If you do not have a `settings.json` yet, you can copy this one directly:

   ```bash
   mkdir -p .claude
   cp content/configs/settings.json .claude/settings.json
   ```

3. **Restart Claude Code** so it re-reads `settings.json`. Hooks are loaded at
   session start.

## Matcher syntax

The `matcher` field is a regex matched against the tool name.

- `"Bash"` -- fires on Bash calls only
- `"Bash|Write|Edit"` -- fires on any of the three
- `".*"` -- fires on every tool call (use sparingly; hooks run in-process)

## Verifying the install

With the hooks in place, run a safe probe:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"gh release publish v1.0"}}' \
  | python3 .claude/hooks/scope-guard.py
```

You should see a JSON error and exit code `2`. If you see nothing and exit
code `0`, the hook is not picking up stdin -- check that `python3` is on
your PATH and that the script is executable.

## Uninstalling

Hooks are opt-in. To disable a hook without deleting it, remove its entry
from `settings.json` and restart Claude Code. To nuke everything, remove
`.claude/hooks/` and the `hooks` block from `settings.json`.
