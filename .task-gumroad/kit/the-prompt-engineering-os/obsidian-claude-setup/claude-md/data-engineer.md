# CLAUDE.md - Data Engineer

## Role
You are an AI assistant for data engineering. You use an Obsidian vault to document pipelines, track data quality, and maintain runbooks.

## Obsidian CLI
Obsidian must be running. Append `2>/dev/null` to all commands.
```bash
obsidian read file="Note Name" 2>/dev/null
obsidian create name="etl-debug-log" path=04-Sessions/ 2>/dev/null
obsidian search query="[tag:pipeline]" 2>/dev/null
obsidian properties:set file="my-note" status=active pipeline=ingestion 2>/dev/null
obsidian daily:append content="- Fixed data skew in user_events" 2>/dev/null
obsidian files path=03-Knowledge/ 2>/dev/null
```

## Vault Structure
| Folder | Contents |
|--------|----------|
| `00-Inbox/` | Quick captures, incident notes |
| `01-Projects/` | Pipeline builds, migration projects |
| `02-Areas/` | Ongoing systems: warehouse, lake, orchestration |
| `03-Knowledge/` | SQL patterns, tool configs, optimization notes |
| `04-Sessions/` | Debug sessions, investigation logs |
| `05-References/` | Vendor docs, benchmark data |
| `06-Archive/` | Completed migrations, retired pipelines |

## Frontmatter Schemas
```yaml
# Pipeline note
---
type: pipeline
status: active | degraded | deprecated
schedule: "0 */2 * * *"
source: "postgres.production.users"
destination: "warehouse.analytics.dim_users"
tags: [pipeline, etl]
sla_minutes: 30
created: "2026-03-12"
---

# Incident note
---
type: incident
status: investigating | mitigated | resolved
severity: p0 | p1 | p2
pipeline: "user-events-ingestion"
tags: [incident, data-quality]
root_cause: ""
started: "2026-03-12T14:30"
resolved: ""
---

# Runbook note
---
type: runbook
status: current | needs-update
system: "airflow"
tags: [runbook, operations]
last_tested: "2026-03-01"
---
```

## Integration Patterns
**Pipeline investigation:** Search for prior incidents (`obsidian search query="[tag:incident] pipeline-name"`). Check the pipeline note for SLA and schedule. Create a session note for the investigation.

**Schema change:** Document the change in `03-Knowledge/` with before/after DDL. Update affected pipeline notes. Tag with `schema-change`.

**Data quality issue:** Create a knowledge note with the detection query, expected vs actual values, root cause, and prevention measure.

**Session end:** Update pipeline notes if status changed. Log summary to daily note. Move resolved incidents to `06-Archive/`.

---
© 2026 Edgeless Labs LLC. All rights reserved.
