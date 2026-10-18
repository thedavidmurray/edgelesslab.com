# Vault Taxonomy

This vault uses a numbered folder structure. Numbers enforce sort order and prevent ambiguity. Every note lives in exactly one folder.

## Folder Structure

| Folder | Purpose | What Goes Here |
|--------|---------|----------------|
| **00-Inbox** | Capture point | New notes, quick thoughts, unsorted items. Process regularly. |
| **01-Projects** | Active work | Time-bound efforts with a clear end state. One subfolder per project. |
| **02-Areas** | Ongoing responsibilities | Domains you maintain indefinitely: health, finances, career, a specific codebase. |
| **03-Knowledge** | Reference material | Research notes, how-to guides, technical references. Stuff you look up. |
| **04-Sessions** | Work logs | Session plans, daily notes, meeting notes. Time-stamped records of work. |
| **05-References** | External content | Book notes, article summaries, course notes. Content from outside your head. |
| **06-Archive** | Cold storage | Completed projects, outdated references. Searchable but out of the way. |
| **_system** | Vault infrastructure | Templates, configuration docs, taxonomy. Not your content. |

## Rules

1. **New notes start in 00-Inbox.** Move them to the right folder during review.
2. **Projects have end dates.** When a project finishes, move it to 06-Archive.
3. **Areas don't have end dates.** Your "Health" area stays in 02-Areas forever.
4. **Knowledge is reusable.** If you wrote it to look up later, it belongs in 03-Knowledge.
5. **Sessions are timestamped.** Use YYYY-MM subfolders inside 04-Sessions.
6. **Archive is not delete.** You can always search 06-Archive. Move freely.

## Frontmatter Convention

Every note should have at minimum:

```yaml
---
type: [note type]
status: [draft | active | review | done | archived]
tags: []
created: "YYYY-MM-DD"
---
```

See `schemas/frontmatter-reference.md` for the full schema by note type.

## Naming Convention

- Use descriptive names: `setting-up-postgres-replication.md`, not `notes.md`
- Lowercase with hyphens for consistency
- Date prefix for session notes: `2026-03-12-database-migration.md`
- No special characters beyond hyphens
