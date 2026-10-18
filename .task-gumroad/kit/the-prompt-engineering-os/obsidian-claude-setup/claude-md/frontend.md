# CLAUDE.md - Frontend Developer

## Role
You are an AI assistant for frontend development. You use an Obsidian vault to track components, design decisions, and performance benchmarks.

## Obsidian CLI
Obsidian must be running. Append `2>/dev/null` to all commands.
```bash
obsidian read file="Note Name" 2>/dev/null
obsidian create name="button-component-spec" path=03-Knowledge/ 2>/dev/null
obsidian search query="[tag:component]" 2>/dev/null
obsidian properties:set file="my-note" status=stable framework=react 2>/dev/null
obsidian daily:append content="- Shipped new modal component" 2>/dev/null
obsidian files path=01-Projects/ 2>/dev/null
```

## Vault Structure
| Folder | Contents |
|--------|----------|
| `00-Inbox/` | Design feedback, quick UI notes |
| `01-Projects/` | Feature builds, redesign projects |
| `02-Areas/` | Design system, accessibility standards, perf budgets |
| `03-Knowledge/` | Component patterns, CSS tricks, browser quirks |
| `04-Sessions/` | Debug sessions, performance audits |
| `05-References/` | Design specs, brand guidelines, API docs |
| `06-Archive/` | Shipped features, deprecated components |

## Frontmatter Schemas
```yaml
# Component note
---
type: component
status: draft | review | stable | deprecated
framework: react | vue | svelte | vanilla
tags: [component, ui, forms]
figma_url: ""
a11y_reviewed: false
created: "2026-03-12"
---

# Design decision note
---
type: decision
status: proposed | accepted | rejected
tags: [decision, architecture]
alternatives_considered: []
decided_by: ""
date_decided: ""
---

# Performance note
---
type: performance
tags: [performance, core-web-vitals]
lcp_ms: 0
fid_ms: 0
cls: 0.0
bundle_size_kb: 0
measured_date: "2026-03-12"
---
```

## Integration Patterns
**New component:** Search `03-Knowledge/` for existing patterns (`obsidian search query="[tag:component] modal"`). Create a component note. Link to the Figma spec in `05-References/`.

**Performance investigation:** Create a session note. Record baseline metrics in frontmatter. Document each optimization and its measured impact. Save the winning approach to `03-Knowledge/`.

**Design system update:** Keep the overview in `02-Areas/design-system/`. Each component gets its own note in `03-Knowledge/`. Deprecated components move to `06-Archive/` with a note on the replacement.

**Browser bug:** Save to `03-Knowledge/` with affected browsers, reproduction steps, workaround, and tags like `[bug, browser, chrome]`.

---
© 2026 Edgeless Labs LLC. All rights reserved.
