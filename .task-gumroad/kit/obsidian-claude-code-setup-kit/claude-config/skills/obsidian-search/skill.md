# Skill: obsidian-search

**Version**: 1.0.0
**Category**: knowledge
**Trigger phrases**: "search my vault", "find notes about", "what do I know about", "look in the vault for", "check my notes on"

---

## Purpose

Search the user's Obsidian vault and return relevant excerpts. Useful when the user asks about prior research, decisions, or knowledge that may have been captured in notes.

---

## When to Use This Skill

Apply this skill when:
- The user asks what they know about a topic
- You need context from prior sessions before starting a task
- The user references a note or concept that may already exist
- You want to avoid duplicating research that has already been done

Do NOT use this skill when:
- The user is asking about live data (use web search instead)
- The query is clearly about code in the current repo (use Grep/Glob instead)

---

## Prerequisites

```bash
# Verify Obsidian is running and CLI is available
~/.local/bin/obsidian version 2>/dev/null || echo "Obsidian CLI not available"

# Verify vault path
echo "${OBSIDIAN_VAULT:-NOT SET}"
```

If `OBSIDIAN_VAULT` is not set, ask the user: "Where is your Obsidian vault? I need the full path."

---

## Execution Pattern

### Step 1 — Keyword search

```bash
~/.local/bin/obsidian search query="<keyword>" 2>/dev/null
```

Start broad. The Omnisearch plugin (if installed) powers this with fuzzy matching.

### Step 2 — Tag search (if keyword returns no results)

```bash
~/.local/bin/obsidian search query="tag:<tag-name>" 2>/dev/null
```

Common tags in this vault structure: `research`, `session`, `decision`, `knowledge`.

### Step 3 — Direct folder read (for known notes)

```bash
~/.local/bin/obsidian read file="<Note Title>" 2>/dev/null
```

Use when the user references a specific note by name.

### Step 4 — Full-text grep fallback (when CLI unavailable)

```bash
grep -r --include="*.md" -l "<keyword>" "${OBSIDIAN_VAULT}" 2>/dev/null | head -10
```

Then read promising files with the Read tool.

---

## Output Format

After searching, present findings in this structure:

```
Found N relevant notes:

1. **[Note Title]** (`path/to/note.md`)
   > Key excerpt...

2. **[Note Title]** (`path/to/note.md`)
   > Key excerpt...

Recommendation: [what the user should do with this information]
```

If nothing is found:
```
No existing notes found on "<topic>".

Shall I:
a) Create a new research note at 02-Knowledge/<Topic>.md?
b) Search the web and capture findings to the vault?
c) Continue without vault context?
```

---

## Error Handling

| Error | Action |
|-------|--------|
| `OBSIDIAN_VAULT` not set | Ask user for vault path; offer to set it |
| Obsidian not running | Warn user; fall back to grep on vault dir |
| No results from CLI search | Try grep fallback before declaring empty |
| Note file not found | Check for case-sensitive filename mismatch |

---

## Examples

**User**: "Search my vault for notes about rate limiting"
```bash
~/.local/bin/obsidian search query="rate limiting" 2>/dev/null
~/.local/bin/obsidian search query="tag:rate-limit" 2>/dev/null
```

**User**: "What do I know about ChromaDB?"
```bash
~/.local/bin/obsidian search query="ChromaDB" 2>/dev/null
~/.local/bin/obsidian search query="chroma vector database" 2>/dev/null
```

**User**: "Find my session notes from last week's API work"
```bash
~/.local/bin/obsidian search query="tag:session API" 2>/dev/null
# Then read the most relevant result
~/.local/bin/obsidian read file="2026-03-05-1430-session" 2>/dev/null
```

---

## Notes

- Obsidian CLI search is case-insensitive by default
- Omnisearch (if installed) supports fuzzy matching — prefer it over raw grep
- Do not read entire vault contents — search first, read specific notes second
- When writing findings back to the vault, prefer appending to existing notes over creating duplicates

---

*© 2026 Edgeless Labs LLC. All rights reserved.*
