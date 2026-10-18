# Frontmatter Reference

Every note in the vault uses YAML frontmatter for structured metadata. Dataview queries depend on these fields being consistent.

## Universal Fields

These fields apply to every note type.

```yaml
---
type: ""        # note type (see below)
status: ""      # lifecycle state
tags: []        # categorization tags
created: ""     # YYYY-MM-DD
updated: ""     # YYYY-MM-DD (optional, update on major edits)
---
```

### Status Values by Type

| Type | Valid Statuses |
|------|---------------|
| General | `draft`, `active`, `review`, `done`, `archived` |
| Project | `active`, `paused`, `done`, `archived` |
| Incident | `investigating`, `mitigated`, `resolved`, `postmortem-done` |
| Paper | `queued`, `reading`, `read`, `summarized` |
| Runbook | `current`, `needs-update`, `deprecated` |

---

## Note Type Schemas

### Daily Note

```yaml
---
type: daily
date: "2026-03-12"
tags: [daily]
---
```

### Project

```yaml
---
type: project
status: active
priority: p0 | p1 | p2 | p3
tags: [project]
repo: ""
deadline: ""
depends_on: []
blocks: []
created: "2026-03-12"
updated: "2026-03-12"
---
```

### Knowledge / How-To

```yaml
---
type: knowledge
status: draft
tags: [knowledge]
confidence: low | medium | high
applies_to: []
created: "2026-03-12"
---
```

### Research

```yaml
---
type: research
status: draft
topic: ""
tags: [research]
sources: []
confidence: low | medium | high
created: "2026-03-12"
---
```

### Session Plan

```yaml
---
type: session
status: active
goal: ""
tags: [session]
started: "2026-03-12T14:30"
completed: ""
phases_total: 0
phases_done: 0
---
```

### Book Note

```yaml
---
type: book
status: reading
title: ""
author: ""
tags: [book]
started: "2026-03-12"
finished: ""
rating: 0
genre: ""
format: physical | kindle | audiobook | pdf
---
```

### Paper (Academic)

```yaml
---
type: paper
status: queued
title: ""
authors: []
year: 2026
venue: ""
arxiv_id: ""
tags: [paper]
relevance: low | medium | high
key_contribution: ""
created: "2026-03-12"
---
```

### Service / Infrastructure

```yaml
---
type: service
status: active
port: 0
repo: ""
tags: [service]
owner: ""
dependencies: []
health_endpoint: ""
created: "2026-03-12"
---
```

### Incident

```yaml
---
type: incident
status: investigating
severity: p0 | p1 | p2
affected_services: []
tags: [incident]
started: ""
resolved: ""
root_cause: ""
ttd_minutes: 0
ttr_minutes: 0
---
```

### Runbook

```yaml
---
type: runbook
status: current
system: ""
tags: [runbook]
last_tested: ""
estimated_time_min: 0
requires_approval: false
---
```

### Pipeline

```yaml
---
type: pipeline
status: active
schedule: ""
source: ""
destination: ""
tags: [pipeline]
owner: ""
sla_minutes: 0
created: "2026-03-12"
---
```

### ADR (Architecture Decision Record)

```yaml
---
type: adr
status: proposed | accepted | superseded
adr_number: 1
tags: [adr]
superseded_by: ""
context: ""
decision: ""
consequences: []
---
```

### Component (Frontend)

```yaml
---
type: component
status: draft | review | stable | deprecated
framework: react | vue | svelte | vanilla
tags: [component]
figma_url: ""
storybook: true
a11y_reviewed: false
created: "2026-03-12"
---
```

### Hypothesis

```yaml
---
type: hypothesis
status: proposed | testing | supported | refuted
tags: [hypothesis]
confidence: low | medium | high
evidence_for: []
evidence_against: []
related_papers: []
created: "2026-03-12"
---
```

---

## Custom Fields

Add any fields you need. Dataview can query them. Keep field names:
- Lowercase
- Hyphenated (not camelCase, not underscored)
- Consistent across notes of the same type

Example: if you add `reviewer` to one ADR, add it to all ADRs.
