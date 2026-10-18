# Autoresearch Program — CLAUDE.md Template Improver

## Goal

Iteratively improve the 6 CLAUDE.md templates in `../claude-md/` using a
frozen LLM-as-judge evaluator (`prepare.py`). Keep only changes that raise the
composite score. Log everything to `results.tsv`.

---

## Loop Structure

```
for each iteration:
    pick a template (round-robin: solo-dev → data-engineer → frontend →
                     backend-api → devops → research)
    record baseline score
    propose ONE specific improvement
    apply improvement to the template file
    run prepare.py → get new score
    if new_score > baseline_score:
        git commit "improve: <template> — <one-line description>"
        log status=KEPT
    else:
        git checkout ../claude-md/<template>.md   # revert
        log status=REJECTED
```

---

## Improvement Categories (pick ONE per iteration)

| Category | Examples |
|----------|---------|
| **Missing CLI command** | Add `obsidian tags:add`, `obsidian properties:list`, `obsidian daily:read`, `obsidian files`, `obsidian rename` |
| **Better example** | Replace a generic example with a persona-specific one (e.g. "my-note" → "auth-service-adr" for backend) |
| **Tighter pattern** | Collapse a verbose Integration Pattern into a 2-line recipe |
| **Missing schema field** | Add a missing frontmatter key that Claude would need (e.g. `updated:` date, `owner:` for devops) |
| **Sharper role statement** | Rewrite the Role section to be more specific about what Claude should do proactively |
| **Fix ambiguity** | Clarify any instruction that could be interpreted two ways |

---

## Constraints

- One change per iteration. Never batch multiple improvements.
- Never change `prepare.py` — it is frozen.
- Template files must stay under 80 lines (conciseness dimension).
- All three hard-constraint commands must remain: `obsidian read`, `obsidian create`, `obsidian search`.
- If a template hits composite >= 9.0, mark it "graduated" in results.tsv and skip it.

---

## Running the Loop

```bash
# 10 full passes across all 6 templates (60 evaluations)
bash run.sh 10

# Single template, one iteration
python3.11 prepare.py ../claude-md/solo-dev.md --id manual-test

# Check best scores
python3.11 prepare.py --best
```

---

## Improvement Log (fill in as experiments run)

| Template | Iteration | Change | Before | After | Status |
|----------|-----------|--------|--------|-------|--------|
| solo-dev | baseline  | —      | —      | —     | —      |

---

## Persona Quick Reference

| Template | Key Focus | Distinctive Frontmatter |
|----------|-----------|------------------------|
| `solo-dev` | Personal projects, debugging | `repo`, `confidence` |
| `data-engineer` | Pipelines, incidents, SLAs | `schedule`, `sla_minutes`, `pipeline` |
| `frontend` | Components, design system, perf | `framework`, `figma_url`, `a11y_reviewed` |
| `backend-api` | Services, ADRs, endpoints | `dependencies`, `health_endpoint`, `adr_number` |
| `devops` | Runbooks, infra, incidents | `env`, `provider`, `ttd_minutes`, `ttr_minutes` |
| `research` | Papers, hypotheses, experiments | `arxiv_id`, `venue`, `evidence_for` |
