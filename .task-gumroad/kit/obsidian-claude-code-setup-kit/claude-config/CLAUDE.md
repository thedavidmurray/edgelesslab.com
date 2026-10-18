# Claude Configuration — Obsidian-Integrated Project

This file is the single source of truth for Claude Code's behavior in this project.
It integrates Obsidian as the persistent knowledge layer for all agent sessions.

---

## Obsidian Vault

**Vault location**: Set `OBSIDIAN_VAULT` in your shell profile (e.g. `export OBSIDIAN_VAULT=~/my-vault`).

**CLI** (requires Obsidian running):
```bash
~/.local/bin/obsidian <command> 2>/dev/null
```

| Task | Command |
|------|---------|
| Read a note | `obsidian read file="Note Name"` |
| Create a note | `obsidian create name="Title" path=00-Inbox/` |
| Search | `obsidian search query="keyword or tag:review"` |
| Append to daily note | `obsidian daily:append content="- text"` |
| Set frontmatter property | `obsidian properties:set file="Note" status=done` |

**ALWAYS suppress stderr**: append `2>/dev/null` to every obsidian CLI call.

**ALWAYS use the vault for**:
- Session plans before starting complex tasks
- Research notes when investigating a problem
- Decision records when making architectural choices
- Captures when discovering something worth remembering

---

## Session Hooks

Hooks run automatically. Do not trigger them manually.

| Hook | Fires When | What It Does |
|------|-----------|--------------|
| `session-start.sh` | Agent session opens | Creates session log in `01-Projects/<project>/sessions/` |
| `session-end.sh` | Agent session closes | Appends summary + outcomes to session log |

If a hook fails silently, check: is Obsidian running? Is `OBSIDIAN_VAULT` set?

---

## Knowledge Routing Rules

```
New information → where does it live?

Is it a fleeting capture?         → 00-Inbox/
Is it project-specific?           → 01-Projects/<project>/
Is it reusable across projects?   → 02-Knowledge/
Is it done / deprecated?          → 03-Archive/
```

**Never** create notes at the vault root. Every note belongs in a numbered folder.

---

## Obsidian Search Skill

Load the search skill when the user asks to find something in the vault:

```
Skill: obsidian-search
Location: claude-config/skills/obsidian-search/skill.md
Trigger: "search my vault", "find notes about", "what do I know about"
```

---

## Anti-Patterns

| Pattern | Problem | Correct Approach |
|---------|---------|-----------------|
| Creating scratch files in project root | Pollutes repo, lost after session | Use `00-Inbox/` in vault |
| Skipping session log creation | No audit trail | Always run or verify `session-start.sh` |
| Storing credentials in vault notes | Security risk | Use `.env` files, never markdown |
| Writing to `_system/templates/` | Breaks Templater | Templates are read-only at runtime |
| Duplicating knowledge across folders | Drift, confusion | One canonical location per piece of knowledge |

---

## Error Handling

- If `obsidian` CLI is unavailable: fall back to direct file writes into `$OBSIDIAN_VAULT/00-Inbox/`
- If `OBSIDIAN_VAULT` is unset: warn the user explicitly — do not silently skip vault operations
- If a note already exists: append to it rather than overwriting

---

## Testing Knowledge Writes

After any vault write, verify:

```bash
obsidian search query="<key term from what you just wrote>" 2>/dev/null
```

If the note does not appear in search results within 30 seconds, Obsidian may need to reindex. Prompt the user to open Obsidian and wait.

---

## Backlog Integration

Tasks live in `backlog/tasks/` as markdown files (not in the vault). Use the vault for knowledge; use `backlog/` for task tracking.

```bash
ls backlog/tasks/          # list tasks
cat backlog/ACTIVE-BACKLOG.md  # view prioritized backlog
```

---

*© 2026 Edgeless Labs LLC. All rights reserved.*
