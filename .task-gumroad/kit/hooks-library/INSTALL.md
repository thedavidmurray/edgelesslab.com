# Installation Guide

Step-by-step instructions for installing Claude Code hooks from this library.

---

## Prerequisites

Before installing any hooks, confirm these are available:

```bash
# Required
which bash          # Should be bash 4+ (see macOS note below)
which python3       # 3.8+
which git

# Required for integration hooks
which curl

# macOS note: system bash is 3.x due to licensing. Hooks use #!/usr/bin/env bash
# which picks up the first bash on PATH. If you have Homebrew:
brew install bash
# Then add /opt/homebrew/bin to the top of your PATH in .zshrc/.bashrc
```

---

## Step 1: Create the hooks directory

Inside your project:

```bash
mkdir -p .claude/hooks
```

If `.claude/settings.json` does not exist, create it:

```bash
cat > .claude/settings.json << 'EOF'
{
  "hooks": {}
}
EOF
```

---

## Step 2: Copy hooks

Copy only the hooks you want. You do not need all of them.

```bash
# Example: copy specific hooks
cp path/to/hooks-library/hooks/safety/damage-control.sh .claude/hooks/
cp path/to/hooks-library/hooks/safety/secret-scanner.sh .claude/hooks/
cp path/to/hooks-library/hooks/quality/pre-commit-lint.sh .claude/hooks/

# Make them executable
chmod +x .claude/hooks/*.sh
```

---

## Step 3: Configure settings.json

Open `.claude/settings.json` and add hook configurations. The structure is:

```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<ToolName>",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/<hook-name>.sh"
          }
        ]
      }
    ]
  }
}
```

Available event names: `PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`, `SubagentStop`

The `matcher` field is a regex matched against tool names: `Bash`, `Write`, `Edit`, `MultiEdit`, `Read`, `Glob`, `Grep`.

---

## Per-Category Installation

### Safety Hooks (install these first)

These protect against irreversible mistakes. Recommended for every project.

**damage-control.sh**
```bash
cp hooks/safety/damage-control.sh .claude/hooks/
chmod +x .claude/hooks/damage-control.sh
```

Edit the `PROTECTED_PATHS` array inside the script to match your project's sensitive directories, then add to `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/damage-control.sh" }
        ]
      }
    ]
  }
}
```

**secret-scanner.sh**
```bash
cp hooks/safety/secret-scanner.sh .claude/hooks/
chmod +x .claude/hooks/secret-scanner.sh
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/secret-scanner.sh" }
        ]
      }
    ]
  }
}
```

Optional: install trufflehog for deeper scanning:
```bash
brew install trufflehog
# Then set in your environment:
export SECRET_USE_TRUFFLEHOG=1
```

**force-push-guard.sh**
```bash
cp hooks/safety/force-push-guard.sh .claude/hooks/
chmod +x .claude/hooks/force-push-guard.sh
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/force-push-guard.sh" }
        ]
      }
    ]
  }
}
```

**backup-before-edit.sh**
```bash
cp hooks/safety/backup-before-edit.sh .claude/hooks/
chmod +x .claude/hooks/backup-before-edit.sh

# Optional: add backup dir to .gitignore
echo ".claude/backups/" >> .gitignore
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/backup-before-edit.sh" }
        ]
      }
    ]
  }
}
```

**dependency-check.sh**
```bash
cp hooks/safety/dependency-check.sh .claude/hooks/
chmod +x .claude/hooks/dependency-check.sh

# Install Python vulnerability scanner
pip install safety

# npm audit is built into npm — no install needed
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/dependency-check.sh" }
        ]
      }
    ]
  }
}
```

---

### Quality Hooks

**pre-commit-lint.sh**
```bash
cp hooks/quality/pre-commit-lint.sh .claude/hooks/
chmod +x .claude/hooks/pre-commit-lint.sh
```

The hook auto-detects your linter. To override:
```bash
export LINT_COMMAND="npm run lint"
# or
export LINT_COMMAND="ruff check ."
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/pre-commit-lint.sh" }
        ]
      }
    ]
  }
}
```

**test-on-edit.sh**
```bash
cp hooks/quality/test-on-edit.sh .claude/hooks/
chmod +x .claude/hooks/test-on-edit.sh
```

Relies on naming conventions to find test files (e.g. `src/auth.py` → `tests/test_auth.py`). Customize `TEST_RUNNER` if needed:
```bash
export TEST_RUNNER="pytest -x"
```

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/test-on-edit.sh" }
        ]
      }
    ]
  }
}
```

**complexity-guard.sh**
```bash
cp hooks/quality/complexity-guard.sh .claude/hooks/
chmod +x .claude/hooks/complexity-guard.sh

# Install for Python
pip install radon

# Install for Go
go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
```

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/complexity-guard.sh" }
        ]
      }
    ]
  }
}
```

**git-conventional.sh**
```bash
cp hooks/quality/git-conventional.sh .claude/hooks/
chmod +x .claude/hooks/git-conventional.sh
```

To customize allowed types:
```bash
export CONVENTIONAL_TYPES="feat:fix:docs:chore:test:refactor:perf"
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/git-conventional.sh" }
        ]
      }
    ]
  }
}
```

---

### Workflow Hooks

**session-logger.sh**
```bash
cp hooks/workflow/session-logger.sh .claude/hooks/
chmod +x .claude/hooks/session-logger.sh

# Set your vault path
export OBSIDIAN_VAULT_PATH="$HOME/your-vault"
```

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/session-logger.sh start" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/session-logger.sh end" }
        ]
      }
    ]
  }
}
```

**time-tracker.sh**
```bash
cp hooks/workflow/time-tracker.sh .claude/hooks/
chmod +x .claude/hooks/time-tracker.sh

# Logs are written to .claude/time-logs/ by default
echo ".claude/time-logs/" >> .gitignore
```

Same SessionStart/Stop pattern as session-logger.sh above, with `time-tracker.sh start` and `time-tracker.sh stop`.

View today's log:
```bash
bash .claude/hooks/time-tracker.sh report
```

**auto-branch.sh**
```bash
cp hooks/workflow/auto-branch.sh .claude/hooks/
chmod +x .claude/hooks/auto-branch.sh
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/auto-branch.sh" }
        ]
      }
    ]
  }
}
```

---

### Integration Hooks

**slack-notify.sh**

1. Create a Slack incoming webhook at https://api.slack.com/messaging/webhooks
2. Copy the webhook URL

```bash
cp hooks/integrations/slack-notify.sh .claude/hooks/
chmod +x .claude/hooks/slack-notify.sh

export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/slack-notify.sh" }
        ]
      }
    ]
  }
}
```

**telegram-notify.sh**

1. Create a bot via @BotFather on Telegram — note the token
2. Message your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to get your chat_id

```bash
cp hooks/integrations/telegram-notify.sh .claude/hooks/
chmod +x .claude/hooks/telegram-notify.sh

export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/telegram-notify.sh start" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/telegram-notify.sh stop" }
        ]
      }
    ]
  }
}
```

**linear-sync.sh**

1. Go to Linear → Settings → API → Personal API keys
2. Create a key with read/write access

```bash
cp hooks/integrations/linear-sync.sh .claude/hooks/
chmod +x .claude/hooks/linear-sync.sh

export LINEAR_API_KEY="lin_api_..."
```

The hook reads the Linear issue ID from your current branch name (e.g. `feat/ENG-123-add-auth`).

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/linear-sync.sh" }
        ]
      }
    ]
  }
}
```

**obsidian-daily.sh**
```bash
cp hooks/integrations/obsidian-daily.sh .claude/hooks/
chmod +x .claude/hooks/obsidian-daily.sh

export OBSIDIAN_VAULT_PATH="$HOME/your-vault"
```

If you have the Obsidian CLI enabled (Settings → General → Advanced → CLI), it will be used automatically. Otherwise the hook writes directly to the vault's daily notes folder.

---

### AI Hooks

**context-preloader.sh**
```bash
cp hooks/ai/context-preloader.sh .claude/hooks/
chmod +x .claude/hooks/context-preloader.sh
```

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/context-preloader.sh" }
        ]
      }
    ]
  }
}
```

**completion-verifier.sh**
```bash
cp hooks/ai/completion-verifier.sh .claude/hooks/
chmod +x .claude/hooks/completion-verifier.sh
```

To block exit on failure (not just warn):
```bash
export VERIFY_BLOCK_ON_FAIL=1
```

**cost-tracker.sh**
```bash
cp hooks/ai/cost-tracker.sh .claude/hooks/
chmod +x .claude/hooks/cost-tracker.sh

# Optional: set your model
export COST_MODEL="claude-sonnet-4-5"

# Optional: alert when total spend exceeds $5
export COST_BUDGET_ALERT=5.00
```

The cost ledger is written to `.claude/costs.json`. Add it to `.gitignore`:
```bash
echo ".claude/costs.json" >> .gitignore
```

**prompt-cache.sh**
```bash
cp hooks/ai/prompt-cache.sh .claude/hooks/
chmod +x .claude/hooks/prompt-cache.sh

# Add entries to the cache
bash .claude/hooks/prompt-cache.sh add "stack" "This project uses FastAPI + PostgreSQL + React. Python 3.12, TypeScript 5.4."
bash .claude/hooks/prompt-cache.sh add "conventions" "Use snake_case for Python, camelCase for TS. Always type function arguments."

# List what's cached
bash .claude/hooks/prompt-cache.sh list
```

---

### Developer Experience Hooks

**auto-format.sh**
```bash
cp hooks/dx/auto-format.sh .claude/hooks/
chmod +x .claude/hooks/auto-format.sh

# Install formatters (install only what you need)
pip install ruff               # Python
npm install -g prettier        # JS/TS
brew install shfmt             # Shell scripts
# gofmt: comes with Go toolchain
# rustfmt: comes with rustup
```

**todo-collector.sh**
```bash
cp hooks/dx/todo-collector.sh .claude/hooks/
chmod +x .claude/hooks/todo-collector.sh

# Add the output file to .gitignore if you don't want to track it
echo "TODO.md" >> .gitignore
# Or commit it and use it as a living document
```

**changelog-updater.sh**
```bash
cp hooks/dx/changelog-updater.sh .claude/hooks/
chmod +x .claude/hooks/changelog-updater.sh

# Optional: include GitHub compare links
export CHANGELOG_REPO_URL="https://github.com/your-org/your-repo"
```

**doc-generator.sh**
```bash
cp hooks/dx/doc-generator.sh .claude/hooks/
chmod +x .claude/hooks/doc-generator.sh

# Install doc generators (install only what you need)
pip install pdoc               # Python
npm install -g typedoc         # TypeScript
# godoc: comes with Go toolchain

# Add generated docs to .gitignore or commit them
mkdir -p docs/api
```

---

## Environment Variables

The cleanest way to set hook configuration is a `.env` file in your project root. Most hooks call `source .env` automatically if the file exists.

```bash
# .env example (do NOT commit this file)
OBSIDIAN_VAULT_PATH=/Users/you/vault
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TELEGRAM_BOT_TOKEN=123456:ABCdef...
TELEGRAM_CHAT_ID=987654321
LINEAR_API_KEY=lin_api_...
COST_MODEL=claude-sonnet-4-5
COST_BUDGET_ALERT=10.00
COMPLEXITY_THRESHOLD=12
```

Add `.env` to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

---

## Troubleshooting

**Hook not running**
- Confirm the file is executable: `ls -la .claude/hooks/`
- Check the event name spelling in `settings.json` (case-sensitive)
- Check the matcher regex matches your tool name

**Hook always blocking**
- Read the hook's stderr output — it explains what triggered the block
- Run the hook manually: `echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m test"}}' | bash .claude/hooks/pre-commit-lint.sh`
- Set `HOOK_WARN_ONLY=1` temporarily while debugging

**python3 not found**
- Hooks use `python3` directly. Make sure it's on PATH.
- On macOS: `brew install python3`
- On some Linux: `sudo apt install python3`

**Hook timeout**
- Long-running hooks (test suites, doc generation) can time out
- Claude Code has a default hook timeout. Adjust with the `timeout` setting in `settings.json`
- Use `TEST_TIMEOUT=30` and similar environment variables to cap individual hook steps

**Permissions denied writing to vault or log directories**
- Verify the directory exists and is writable: `ls -la $OBSIDIAN_VAULT_PATH`
- Some hooks create directories automatically; others require them to exist

---

## Uninstalling

To remove a hook, delete the file and remove its entry from `settings.json`. No other cleanup is required.

```bash
rm .claude/hooks/hook-name.sh
# Then edit .claude/settings.json to remove the hook entry
```
