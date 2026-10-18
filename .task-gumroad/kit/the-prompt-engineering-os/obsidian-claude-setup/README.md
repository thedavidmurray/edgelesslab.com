# Obsidian + Claude Code Setup Kit

A deployable Obsidian vault pre-configured for Claude Code integration. Not a tutorial. A working system.

**By Edgeless** | Add-on to The Prompt Engineering OS

---

## What You Get

| Component | Description |
|-----------|-------------|
| `vault-template/` | Obsidian vault with 7 folders, 4 templates, plugin configs, and frontmatter schemas |
| `claude-md/` | 6 CLAUDE.md templates that teach Claude Code how to use your vault |
| `schemas/` | Frontmatter reference (14 note types) and 15 Dataview queries |
| `scripts/` | 5 shell scripts for daily capture, weekly review, tag audit, search, and backup |

## Prerequisites

- [Obsidian](https://obsidian.md) installed (free)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- macOS or Linux (Windows via WSL)

## Setup (5 minutes)

### 1. Copy the Vault Template

```bash
cp -r vault-template/ ~/my-vault
```

Open `~/my-vault` as a vault in Obsidian.

### 2. Install Community Plugins

Open Obsidian Settings, go to Community Plugins, and install these 6 plugins:

1. **Dataview** - Query your notes like a database
2. **Templater** - Template engine with variables and dates
3. **Omnisearch** - Full-text search across the vault
4. **Tag Wrangler** - Rename, merge, and manage tags
5. **Auto Link Title** - Paste a URL, get the page title automatically
6. **Pretty Properties** - Better frontmatter display

The config files in `.obsidian/` are already set up. You just need to install the plugins.

### 3. Enable the Obsidian CLI

Obsidian has a built-in CLI (v1.7+, free).

1. Open Settings > General > Advanced
2. Toggle **CLI** on
3. Create the symlink:

```bash
# macOS
ln -sf "/Applications/Obsidian.app/Contents/MacOS/Obsidian" ~/.local/bin/obsidian

# Linux (AppImage)
ln -sf ~/Applications/Obsidian.AppImage ~/.local/bin/obsidian
```

Make sure `~/.local/bin` is in your PATH.

Test it:

```bash
obsidian search query="test" 2>/dev/null
```

### 4. Add CLAUDE.md to Your Project

Pick the template that matches your work from `claude-md/`:

| Template | Best For |
|----------|----------|
| `solo-dev.md` | Individual developers, full-stack work |
| `data-engineer.md` | Pipelines, ETL, data quality |
| `frontend.md` | React, Vue, Svelte, component libraries |
| `backend-api.md` | REST/GraphQL services, microservices |
| `devops.md` | Infrastructure, CI/CD, incident response |
| `research.md` | Academic research, ML experiments, literature review |

Copy it to your project root as `CLAUDE.md`:

```bash
cp claude-md/solo-dev.md ~/my-project/CLAUDE.md
```

Edit the file to match your vault path and project specifics.

### 5. Set Up Scripts

```bash
chmod +x scripts/*.sh

# Optional: add to PATH
cp scripts/*.sh ~/.local/bin/
```

Each script has `--help`:

```bash
./scripts/daily-capture.sh --help
./scripts/weekly-review.sh --help
./scripts/tag-audit.sh --help
./scripts/search-vault.sh --help
./scripts/backup-vault.sh --help
```

## How It Works

### The Vault Structure

```
00-Inbox/       New notes land here. Process during review.
01-Projects/    Active, time-bound work.
02-Areas/       Ongoing responsibilities (no end date).
03-Knowledge/   Reusable reference material.
04-Sessions/    Work logs and session plans.
05-References/  Book notes, paper summaries, external content.
06-Archive/     Done or inactive. Still searchable.
_system/        Templates and vault config. Not your content.
```

Full explanation: `vault-template/_system/TAXONOMY.md`

### The CLAUDE.md Templates

Each template gives Claude Code:
- Obsidian CLI commands it can run
- Your vault's folder structure and what goes where
- Frontmatter schemas for the note types you use
- Integration patterns (what to do at session start, during work, at session end)

Claude Code reads CLAUDE.md at the start of every session. It will use your vault without you asking.

### The Frontmatter Schemas

Every note type has a defined YAML frontmatter schema. Dataview queries depend on these fields. See `schemas/frontmatter-reference.md` for all 14 note types.

Example:

```yaml
---
type: project
status: active
priority: p1
tags: [project, backend]
repo: "github.com/user/repo"
created: "2026-03-12"
---
```

### The Dataview Queries

15 ready-to-use queries in `schemas/dataview-queries.md`. Paste them into any note. They query your frontmatter fields to show:

- Active projects by priority
- Stale runbooks (not tested in 90+ days)
- Open incidents by severity
- Reading list (unfinished books and papers)
- Weekly note count and tag frequency

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `daily-capture.sh` | Append text to today's daily note. Supports tasks, bullets, quotes. |
| `weekly-review.sh` | Generate a summary of vault activity over the last N days. |
| `tag-audit.sh` | Find orphan tags, show frequency, detect duplicates. |
| `search-vault.sh` | Full-text search with type and status filters. |
| `backup-vault.sh` | Timestamped backup with optional zip and pruning. |

## Customizing

### Adding Folders

Add numbered folders to the vault. Keep the number prefix for sort order. Update the taxonomy doc and your CLAUDE.md template.

### Adding Note Types

1. Create a template in `_system/templates/`
2. Add the frontmatter schema to `schemas/frontmatter-reference.md`
3. Write a Dataview query for the new type
4. Update your CLAUDE.md with the new schema

### Combining Templates

The CLAUDE.md templates are starting points. If you do both frontend and DevOps, merge the relevant sections from both templates.

---

© 2026 Edgeless Labs LLC. All rights reserved. Part of The Prompt Engineering OS.
