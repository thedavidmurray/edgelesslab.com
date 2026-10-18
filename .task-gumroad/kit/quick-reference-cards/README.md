# Prompt Engineering Quick Reference Cards

**6 printable reference cards for engineers who use Claude Code daily.**

Each card fits one printed page. Dark theme for screens, light for print. No fluff — only patterns that ship working code.

---

## The Cards

| Card | File | Topic |
|------|------|-------|
| 1 | `prompt-patterns.html` | Core prompt patterns with examples |
| 2 | `claude-md-anatomy.html` | CLAUDE.md section-by-section anatomy |
| 3 | `agent-patterns.html` | Agent design patterns + when to use each |
| 4 | `debugging-prompts.html` | Systematic debugging prompt toolkit |
| 5 | `cost-optimization.html` | Token and cost optimization strategies |
| 6 | `hooks-cheatsheet.html` | Hooks quick reference + copy-paste configs |

---

## How to Use

### Print

Open any `.html` file in Chrome or Safari. Press `Cmd+P` (macOS) or `Ctrl+P` (Windows). The print stylesheet switches to a clean light theme optimized for A4/Letter paper.

Set margins to **Minimum** or **None** for best results. Print at 100% scale — each card is sized to fit exactly one page.

### Screen Reference

Open the files directly in a browser. The dark theme is optimized for reading alongside a terminal or editor.

### Laminate and Desk-mount

Print, laminate, and pin to your monitor or desk. The information density is calibrated for quick scanning without reaching for docs.

---

## What is in Each Card

### Card 1 — Core Prompt Patterns

The 6 structural patterns that cover 90% of prompting situations: Chain of Thought, Few-Shot, Role Assignment, Constraint Setting, Output Formatting, and Meta-Prompting. Each with a copy-paste example.

### Card 2 — CLAUDE.md Anatomy

A section-by-section breakdown of what makes a CLAUDE.md effective. Side-by-side good vs bad examples. Use this when setting up a new project or auditing an existing configuration file.

### Card 3 — Agent Design Patterns

The 5 canonical multi-agent patterns: Builder-Validator, Fan-out/Fan-in, Pipeline, Supervisor, and Consensus. CSS-based visual diagram for each. One-line trigger prompt to instantiate each pattern.

### Card 4 — Debugging Prompt Toolkit

A systematic flow for debugging with Claude. Covers hypothesis generation, change isolation, error reading strategy, and the exact prompts that produce the most useful diagnostic output.

### Card 5 — Token and Cost Optimization

Model selection guide (Haiku vs Sonnet vs Opus), context window management, `/compact` usage, file filtering strategies, and estimated cost per task type.

### Card 6 — Hooks Quick Reference

All Claude Code hook event types, the response format, and 5 production-ready hook configurations with copy-paste JSON.

---

## Format

- Self-contained HTML — no external dependencies, no CDN calls
- Works fully offline
- Roboto Mono typeface (embedded via system font fallback stack)
- Print-optimized CSS with `@media print` overrides
- A4 and Letter compatible

---

## License

MIT — see `LICENSE`.

---

*Edgeless Labs LLC — edgeless*
