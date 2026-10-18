# CLAUDE.md - Solo Developer

## Role
You are an AI development partner. You have access to an Obsidian vault for persistent knowledge and project tracking.

## Obsidian CLI
Obsidian must be running. Append `2>/dev/null` to all commands.
```bash
obsidian read file="Note Name" 2>/dev/null
obsidian create name="my-note" path=00-Inbox/ 2>/dev/null
obsidian search query="search terms" 2>/dev/null
obsidian search query="[tag:project]" 2>/dev/null
obsidian properties:set file="my-note" status=active 2>/dev/null
obsidian daily:append content="- Fixed login bug" 2>/dev/null
obsidian files path=01-Projects/ 2>/dev/null
```

## Vault Structure
| Folder | Contents |
|--------|----------|
| `00-Inbox/` | Quick captures, unsorted notes |
| `01-Projects/` | Active projects (one subfolder each) |
| `02-Areas/` | Ongoing domains: codebase docs, client notes |
| `03-Knowledge/` | Technical references, how-to guides, bug fixes |
| `04-Sessions/` | Session plans, work logs |
| `05-References/` | Book notes, article summaries |
| `06-Archive/` | Completed or inactive items |

## Frontmatter Schemas
```yaml
# Project note
---
type: project
status: active | paused | done
priority: p0 | p1 | p2 | p3
tags: [project, frontend]
repo: "github.com/user/repo"
created: "2026-03-12"
---

# Knowledge note
---
type: knowledge
status: draft | review | done
tags: [python, debugging]
confidence: low | medium | high
created: "2026-03-12"
---
```

## Integration Patterns
**Session start:** Check `00-Inbox/` for unprocessed notes. Read active project notes. Log start with `obsidian daily:append`.

**During work:** Save reusable findings to `03-Knowledge/`. Track decisions in the project note. Append progress to daily note.

**Session end:** Update project status. Move completed items to `06-Archive/`. Log summary to daily note.

**Bug fix:** Search for prior encounters (`obsidian search query="[tag:bug] error-name"`). If new, create a knowledge note with root cause and fix.
