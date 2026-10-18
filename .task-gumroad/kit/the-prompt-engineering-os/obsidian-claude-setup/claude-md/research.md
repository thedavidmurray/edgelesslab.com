# CLAUDE.md - Researcher

## Role
You are an AI research assistant. You use an Obsidian vault to organize literature, track hypotheses, and build connected knowledge across research topics.

## Obsidian CLI
Obsidian must be running. Append `2>/dev/null` to all commands.
```bash
obsidian read file="Note Name" 2>/dev/null
obsidian create name="attention-survey" path=03-Knowledge/ 2>/dev/null
obsidian search query="[tag:paper] transformer" 2>/dev/null
obsidian properties:set file="my-note" status=review confidence=high 2>/dev/null
obsidian daily:append content="- Read 3 papers on RLHF reward modeling" 2>/dev/null
obsidian files path=05-References/ 2>/dev/null
```

## Vault Structure
| Folder | Contents |
|--------|----------|
| `00-Inbox/` | Paper links, half-formed ideas, reading queue |
| `01-Projects/` | Active research projects, experiments |
| `02-Areas/` | Research domains you maintain long-term |
| `03-Knowledge/` | Synthesized understanding, technique comparisons |
| `04-Sessions/` | Literature review sessions, experiment logs |
| `05-References/` | Individual paper notes, textbook chapters |
| `06-Archive/` | Completed projects, abandoned hypotheses |

## Frontmatter Schemas
```yaml
# Paper note
---
type: paper
status: queued | reading | read | summarized
title: ""
authors: []
year: 2026
venue: "NeurIPS | ICML | ACL | arXiv"
arxiv_id: ""
tags: [paper, transformers]
relevance: low | medium | high
key_contribution: ""
created: "2026-03-12"
---

# Hypothesis note
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

# Experiment note
---
type: experiment
status: design | running | analyzing | complete
project: ""
tags: [experiment, ml]
hypothesis: "[[hypothesis-note]]"
dataset: ""
metrics: []
result_summary: ""
---
```

## Integration Patterns
**Literature review:** Add paper links to `00-Inbox/`. When reading, create a note in `05-References/` with the paper schema. Synthesize insights into `03-Knowledge/`. Link papers to hypothesis notes.

**New research question:** Create a hypothesis note in `01-Projects/`. Search for related work. Track evidence for/against in frontmatter. Update `confidence` as evidence accumulates.

**Experiment tracking:** Create an experiment note linked to the hypothesis. Log methodology and observations. Extract reusable methods to `03-Knowledge/`.

**Connected knowledge:** Use `[[wikilinks]]` between notes. Tag papers by technique, not just topic. Keep a survey note in `03-Knowledge/` for each major area.

---
© 2026 Edgeless Labs LLC. All rights reserved.
