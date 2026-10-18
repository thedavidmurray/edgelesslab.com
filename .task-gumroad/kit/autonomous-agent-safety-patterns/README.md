# Autonomous Agent Safety Patterns

Hard-won guardrails from an agent that lost $252 of real money.

## What's Inside

- **guide.md / guide.pdf** -- 7-chapter guide: the $252 post-mortem, 10 anti-patterns, financial verification protocol, scope containment, destructive operation prevention, incident response playbook, and building safety culture
- **hooks/** -- 3 safety hooks (scope guard, financial gate, reversibility classifier)
- **protocols/** -- 3 printable verification checklists (financial, deployment, data deletion)

## Quick Start

1. Read Chapter 1 (the post-mortem) to understand why these patterns exist
2. Copy the hooks you need to `.claude/hooks/`
3. Print the relevant protocol checklist for your use case
4. Add hooks to `.claude/settings.json` (see guide Chapter 5 for examples)

## Prerequisites

- Claude Code (any version with hooks support)
- Python 3.10+
- No external pip dependencies

## File Structure

```
agent-safety-patterns/
  guide.md                  -- Full 7-chapter guide
  guide.pdf                 -- PDF version
  hooks/
    scope-guard.py          -- Blocks scope expansion
    financial-gate.py       -- Requires verification protocol
    reversibility-classifier.py -- Classifies and gates by reversibility
  protocols/
    financial-verification.md
    deployment-verification.md
    data-deletion-verification.md
  README.md
  CHANGELOG.md
```

## Version

1.0.0 -- Initial release, April 2026
