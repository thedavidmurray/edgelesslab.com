# Obsidian + Claude Code Setup Kit

A production-ready companion add-on for Claude Code users who want a structured knowledge management system backed by Obsidian. Drop this in, run one script, and get a fully wired vault + agent configuration in under five minutes.

---

## What's Included

### `vault-template/`
A pre-configured Obsidian vault skeleton ready to copy into place.

| Path | Purpose |
|------|---------|
| `.obsidian/app.json` | Optimal Obsidian app settings for agentic use |
| `.obsidian/community-plugins.json` | Curated plugin list (Dataview, Templater, Copilot, etc.) |
| `_system/templates/` | Session plan, research session, and daily note templates |
| `00-Inbox/` | Unprocessed captures — Claude drops things here first |
| `01-Projects/` | Active project workspaces |
| `02-Knowledge/` | Evergreen notes, research, and distilled findings |
| `03-Archive/` | Completed / deprecated material |
| `VAULT-README.md` | Getting-started guide for the vault structure |

### `claude-config/`
Drop-in configuration for Claude Code that integrates Obsidian into your agent workflow.

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Production CLAUDE.md with Obsidian integration patterns |
| `hooks/session-start.sh` | Auto-creates an Obsidian session log on agent start |
| `hooks/session-end.sh` | Appends a session summary to Obsidian on agent exit |
| `skills/obsidian-search/skill.md` | Skill file teaching Claude to search the vault |

### `scripts/`
Automation scripts to wire everything together.

| Script | Purpose |
|--------|---------|
| `setup.sh` | One-click setup — copies vault, enables plugins, patches CLAUDE.md |
| `sync-to-vault.sh` | Syncs project findings and research notes into the vault |

---

## Quick Start

```bash
# 1. Clone / download this kit
# 2. Run setup (point it at your project root)
bash scripts/setup.sh --vault ~/my-obsidian-vault --project ~/my-claude-project

# 3. Open the vault in Obsidian, accept plugin installs
# 4. Start a Claude Code session — the hooks fire automatically
```

---

## Design Philosophy

- **Agent-first**: every file and folder is named so Claude can reason about it without ambiguity.
- **Minimal surface area**: only the plugins and settings that matter for agentic workflows are included.
- **Extend, don't replace**: the kit layers on top of your existing Claude Code setup — it does not overwrite anything without a backup prompt.
- **Single source of truth**: each piece of knowledge has exactly one canonical location; the vault is the long-term memory layer.

---

## Requirements

| Dependency | Version | Notes |
|-----------|---------|-------|
| Obsidian | ≥ 1.5.0 | Free tier sufficient |
| Obsidian CLI | ≥ 1.12.0 | Ships inside Obsidian app; enable in Settings → General → Advanced |
| Claude Code | Latest | `npm i -g @anthropic-ai/claude-code` |
| bash | ≥ 3.2 | Ships on macOS and all Linux distributions |
| jq | ≥ 1.6 | `brew install jq` / `apt install jq` |

---

## File Inventory

```
obsidian-setup-kit/
├── README.md                                  ← you are here
├── vault-template/
│   ├── .obsidian/
│   │   ├── app.json
│   │   └── community-plugins.json
│   ├── _system/
│   │   └── templates/
│   │       ├── session-plan.md
│   │       ├── research-session.md
│   │       └── daily-note.md
│   ├── 00-Inbox/
│   ├── 01-Projects/
│   ├── 02-Knowledge/
│   ├── 03-Archive/
│   └── VAULT-README.md
├── claude-config/
│   ├── CLAUDE.md
│   ├── hooks/
│   │   ├── session-start.sh
│   │   └── session-end.sh
│   └── skills/
│       └── obsidian-search/
│           └── skill.md
└── scripts/
    ├── setup.sh
    └── sync-to-vault.sh
```

---

## Support

Issues and PRs welcome. See `VAULT-README.md` for vault usage guidance, or `claude-config/CLAUDE.md` for agent configuration patterns.

---

*© 2026 Edgeless Labs LLC. All rights reserved.*
