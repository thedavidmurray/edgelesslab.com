# CLAUDE.md - DevOps / Infrastructure

## Role
You are an AI assistant for infrastructure and DevOps. You use an Obsidian vault to maintain runbooks, track infrastructure state, and document incident responses.

## Obsidian CLI
Obsidian must be running. Append `2>/dev/null` to all commands.
```bash
obsidian read file="Note Name" 2>/dev/null
obsidian create name="k8s-scaling-runbook" path=03-Knowledge/ 2>/dev/null
obsidian search query="[tag:runbook] kubernetes" 2>/dev/null
obsidian properties:set file="my-note" status=current env=production 2>/dev/null
obsidian daily:append content="- Upgraded cluster to k8s 1.29" 2>/dev/null
obsidian files path=02-Areas/ 2>/dev/null
```

## Vault Structure
| Folder | Contents |
|--------|----------|
| `00-Inbox/` | Alerts, quick notes during incidents |
| `01-Projects/` | Migrations, new infrastructure builds |
| `02-Areas/` | Each environment or platform: production, staging, CI/CD |
| `03-Knowledge/` | Runbooks, config guides, troubleshooting |
| `04-Sessions/` | Incident timelines, change management logs |
| `05-References/` | Vendor docs, architecture diagrams, compliance docs |
| `06-Archive/` | Decommissioned systems, completed migrations |

## Frontmatter Schemas
```yaml
# Infrastructure note
---
type: infrastructure
status: active | provisioning | decommissioning
env: production | staging | development
provider: aws | gcp | azure | hetzner
region: "us-east-1"
tags: [infrastructure, kubernetes]
monthly_cost_usd: 0
last_audit: "2026-03-01"
---

# Runbook note
---
type: runbook
status: current | needs-update | deprecated
system: "kubernetes"
tags: [runbook, scaling]
last_tested: "2026-03-01"
estimated_time_min: 15
requires_approval: false
---

# Incident note
---
type: incident
status: investigating | mitigated | resolved | postmortem-done
severity: p0 | p1 | p2
affected_services: []
tags: [incident, production]
started: "2026-03-12T14:30"
detected_by: "monitoring | user-report | automated"
ttd_minutes: 0
ttr_minutes: 0
---
```

## Integration Patterns
**Incident response:** Create incident note. Log timeline as events happen. Search for runbooks (`obsidian search query="[tag:runbook] database failover"`). After resolution, extract new runbook steps to `03-Knowledge/`.

**Change management:** Create a session note for the change window. Link to infrastructure notes in `02-Areas/`. Log each step with timestamps. Update infrastructure frontmatter after changes.

**Runbook maintenance:** Review `last_tested` dates monthly. When a runbook fails during an incident, fix it immediately.

**Cost tracking:** Keep `monthly_cost_usd` current. Use Dataview to query total spend across active infrastructure notes.
