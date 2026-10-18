# SPEC Template — EdgelessLab

Usage: copy this file to `SPEC.md` at the root of a new feature directory,
then fill in each section before implementation begins.

The structure follows the Kiro spec pattern (requirements → design → tasks)
with Edgeless conventions layered on top: evidence-backed acceptance, goal-loop
transitions, and explicit sign-off gates.

---

## 1. Goal

Outcome-shaped statement — what exists when this spec is done, verified by what.
Not activity-shaped ("work on X").

Goal:

Verification command:

---

## 2. Requirements (Kiro: requirements.md)

### Problem

### Users / Actors

### User Stories

| ID | As a... | I want to... | So that... | Acceptance criteria |
|----|---------|-------------|------------|---------------------|
| US-1 | | | | |
| US-2 | | | | |

### Bugfix variant (Kiro: bugfix.md) — use INSTEAD of user stories for bug work

| Behavior | Description | Regression check |
|----------|-------------|------------------|
| Current (broken) | | repro command that fails today |
| Expected | | same command, passes after fix |
| Unchanged | behavior that must NOT change | existing test(s) that must stay green |

Root cause (evidence, not guess):

### Non-functional requirements

- Performance:
- Security:
- Accessibility:
- Browser compatibility:

---

## 3. Design (Kiro: design.md)

### Architecture overview

### Components / Modules

| Component | Responsibility | Interfaces |
|-----------|---------------|------------|
| | | |

### Data flow / Sequence

### Error handling strategy

### Testing strategy

- Unit test seams:
- Integration test seams:
- E2E / browser checks:
- What "done" looks like for each:

### Out of scope

---

## 4. Tasks (Kiro: tasks.md)

| # | Task | Depends on | Acceptance | Evidence |
|---|------|-----------|------------|----------|
| T1 | | — | | |
| T2 | | T1 | | |
| T3 | | T1 | | |

Wave grouping (parallel-safe batches):
- Wave 1:
- Wave 2:

---

## 5. Evidence & Gate Checklist

Copy this checklist into `goal-loop.md` when implementation begins.

| Gate | Check | Result |
|------|-------|--------|
| LIGHT | Worker self-verification | |
| STANDARD | Diff review + branch coverage | |
| STRICT | Reviewer + David approval | |

### Acceptance-to-test mapping

| ID | Acceptance criterion | Evidence / check | Status |
|----|---------------------|------------------|--------|
| A1 | | | |
| A2 | | | |
| A3 | | | |

---

## 6. Sign-off

| Role | Name | Date | Decision |
|------|------|------|----------|
| Builder | | | ☐ Complete |
| Reviewer | | | ☐ Approved |
| Publisher | | | ☐ Deployed |

---

## 7. Change log

| Date | Author | Change |
|------|--------|--------|
| | | Initial draft |