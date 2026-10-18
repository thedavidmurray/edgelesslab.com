# Dataview Queries

These queries work with the frontmatter schemas in `frontmatter-reference.md`. Paste them into any note as a `dataview` code block.

Requires the [Dataview plugin](https://github.com/blackmarble/obsidian-dataview) (included in this vault's community plugins config).

---

## 1. Inbox Triage

Show all notes in the Inbox folder, sorted by creation date.

```dataview
TABLE created, tags
FROM "00-Inbox"
SORT created DESC
```

## 2. Active Projects

All projects with status "active", sorted by priority.

```dataview
TABLE priority, repo, updated
FROM ""
WHERE type = "project" AND status = "active"
SORT priority ASC
```

## 3. Recent Sessions

Session notes from the last 14 days.

```dataview
TABLE goal, status, started
FROM ""
WHERE type = "session" AND started >= date(today) - dur(14 days)
SORT started DESC
```

## 4. Reading List

Books and papers you haven't finished yet.

```dataview
TABLE author, status, relevance
FROM ""
WHERE (type = "book" OR type = "paper") AND status != "summarized" AND status != "done"
SORT status ASC
```

## 5. Knowledge by Tag

All knowledge notes tagged with a specific topic. Replace "python" with your tag.

```dataview
TABLE confidence, created
FROM ""
WHERE type = "knowledge" AND contains(tags, "python")
SORT confidence DESC
```

## 6. Stale Runbooks

Runbooks that haven't been tested in 90+ days.

```dataview
TABLE system, last_tested, status
FROM ""
WHERE type = "runbook" AND last_tested <= date(today) - dur(90 days)
SORT last_tested ASC
```

## 7. Open Incidents

Active incidents sorted by severity.

```dataview
TABLE severity, affected_services, started
FROM ""
WHERE type = "incident" AND status != "resolved" AND status != "postmortem-done"
SORT severity ASC
```

## 8. Architecture Decisions

All ADRs in order. Useful as a decision log.

```dataview
TABLE status, context, decision
FROM ""
WHERE type = "adr"
SORT adr_number ASC
```

## 9. Blocked Projects

Projects waiting on dependencies.

```dataview
TABLE priority, depends_on
FROM ""
WHERE type = "project" AND status = "active" AND length(depends_on) > 0
SORT priority ASC
```

## 10. Notes Updated This Week

Everything touched in the last 7 days.

```dataview
TABLE type, status, updated
FROM ""
WHERE updated >= date(today) - dur(7 days)
SORT updated DESC
```

## 11. Tag Cloud (Count by Tag)

How many notes use each tag. Useful for spotting orphan tags.

```dataview
TABLE length(rows) AS "Count"
FROM ""
WHERE tags
FLATTEN tags AS tag
GROUP BY tag
SORT length(rows) DESC
```

## 12. Pipeline Health Dashboard

Overview of all data pipelines and their status.

```dataview
TABLE status, schedule, sla_minutes, source, destination
FROM ""
WHERE type = "pipeline"
SORT status ASC
```

## 13. Papers by Venue

Group academic papers by where they were published.

```dataview
TABLE length(rows) AS "Papers", rows.title AS "Titles"
FROM ""
WHERE type = "paper"
GROUP BY venue
SORT length(rows) DESC
```

## 14. Hypothesis Tracker

Research hypotheses and their current confidence level.

```dataview
TABLE status, confidence, length(evidence_for) AS "Evidence For", length(evidence_against) AS "Against"
FROM ""
WHERE type = "hypothesis"
SORT confidence DESC
```

## 15. Monthly Note Count

How many notes you created each month. Tracks your note-taking momentum.

```dataview
TABLE length(rows) AS "Notes Created"
FROM ""
WHERE created
GROUP BY dateformat(date(created), "yyyy-MM") AS "Month"
SORT "Month" DESC
LIMIT 12
```
