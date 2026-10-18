# Vault Getting Started Guide

Welcome to your Claude Code-integrated Obsidian vault. This guide explains the folder structure, how the agent interacts with your vault, and how to get the most out of the system.

---

## Folder Structure

```
vault/
├── 00-Inbox/          ← everything lands here first
├── 01-Projects/       ← active work, one subfolder per project
├── 02-Knowledge/      ← evergreen notes, distilled research
├── 03-Archive/        ← done / deprecated / reference only
└── _system/
    └── templates/     ← Templater templates (do not rename)
        ├── session-plan.md
        ├── research-session.md
        └── daily-note.md
```

### The Golden Rule

> Every piece of knowledge has exactly one canonical location. When in doubt, drop it into `00-Inbox/` first — Claude will help you route it.

---

## Folder Descriptions

### `00-Inbox/`
Unprocessed input. Claude Code drops captures here during sessions. Review daily and move notes to their permanent home. Nothing should live here longer than 48 hours.

### `01-Projects/`
One subfolder per active project. Structure within each project folder is up to you, but a consistent pattern helps the agent:

```
01-Projects/my-project/
├── README.md          ← project overview, status, goals
├── sessions/          ← session logs (auto-created by hook)
├── research/          ← research sessions specific to this project
└── decisions/        ← ADRs or lightweight decision records
```

### `02-Knowledge/`
Distilled, reusable knowledge. Notes here should be written to be useful in 6 months with no context. Good candidates:

- How-to guides (the "correct" way to do something you've figured out)
- API patterns and gotchas
- Mental models
- Technology evaluations

Suggested sub-structure:
```
02-Knowledge/
├── Engineering/
├── Research-Sessions/
├── Mental-Models/
└── Tools/
```

### `03-Archive/`
Completed projects, deprecated approaches, old session logs. Never delete — archive. The agent can still search here.

### `_system/templates/`
Templater templates. Do not rename or move these files — Claude's `session-start.sh` hook references them by path.

---

## Working with Claude Code

### Session Lifecycle

1. **Session start** — `session-start.sh` hook fires, creates a timestamped session log in `01-Projects/<project>/sessions/`.
2. **During session** — Claude reads and writes notes as needed. All new content goes to `00-Inbox/` unless a clear destination exists.
3. **Session end** — `session-end.sh` hook fires, appends a summary block to the session log and updates the daily note.

### Searching the Vault

Claude uses the `obsidian-search` skill to query your vault semantically. Trigger it with:

```
Search my vault for notes about rate limiting patterns
```

Claude will use the Obsidian CLI (`obsidian search`) under the hood and return relevant excerpts.

### Using Templates

Templates are applied automatically when you create a new note from the correct folder. You can also apply them manually:

1. Open Command Palette (`Cmd+P`)
2. Type `Templater: Open Insert Template Modal`
3. Select the template

---

## Recommended Plugins (Already Configured)

| Plugin | What It Does |
|--------|-------------|
| **Dataview** | SQL-like queries over your notes — powers the task tables in daily notes |
| **Templater** | Dynamic templates with JavaScript — powers session and research note creation |
| **Omnisearch** | Full-text search with fuzzy matching — much faster than built-in search |
| **Excalidraw** | Embedded diagrams — useful for architecture sketches in project notes |
| **Tag Wrangler** | Bulk rename/merge tags — keeps your taxonomy clean as it evolves |
| **Auto Link Title** | Fetches page titles when you paste a URL — saves manual typing |
| **Copilot** | AI completion inside Obsidian — complements Claude Code with in-editor assistance |

---

## Maintenance

### Weekly
- Process `00-Inbox/` to zero
- Review `01-Projects/` — archive anything that's been idle for 2+ weeks
- Run `scripts/sync-to-vault.sh` to pull in any project findings

### Monthly
- Review `02-Knowledge/` — update stale notes, merge duplicates
- Check `03-Archive/` — nothing should need to move back out

---

## Troubleshooting

**Templater not firing on new note?**
Settings → Templater → Enable Folder Templates, then map each folder to its template.

**Dataview queries showing no results?**
Make sure Dataview is enabled and that your notes have the correct YAML frontmatter fields (check the template files for expected keys).

**Obsidian CLI not found?**
Enable it under Settings → General → Advanced → "Enable CLI". Then symlink: `ln -s /Applications/Obsidian.app/Contents/MacOS/Obsidian ~/.local/bin/obsidian`

**Session hooks not firing?**
Verify that `claude-config/hooks/session-start.sh` is executable (`chmod +x`) and that it is referenced in your project's `.claude/hooks/` directory.

---

*© 2026 Edgeless Labs LLC. All rights reserved.*
