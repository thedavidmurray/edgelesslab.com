# AI Code Review Playbook

**Tier 2 product — $19–29 | Edgeless Labs LLC**

Patterns for using AI assistants effectively in code review workflows. No fluff, no theory — working configs, real prompts, copy-paste integrations.

---

## What's Included

| File | Description |
|------|-------------|
| `ai-code-review-playbook.html` | Single-file HTML guide — open in browser or print to PDF |
| `LICENSE` | MIT License |
| `README.md` | This file |

---

## What the Playbook Covers

**Part 1: Foundations**
- Why AI code review differs from human review
- What AI catches well (patterns, consistency, security) vs what it misses (business logic, UX)
- Setting up Claude Code for code review workflows

**Part 2: Review Patterns**
- Pre-commit review — hook configs and skill.md templates
- PR review — structured review with `gh pr diff | claude`
- Security audit — OWASP Top 10 checklist prompts
- Architecture review — pattern compliance, coupling analysis
- Performance review — N+1 detection, memory leak patterns

**Part 3: Integration**
- CI/CD — complete GitHub Actions workflows for automated PR review
- Team workflows — gradual adoption, confidence levels, escalation rules
- Custom review rules — CLAUDE.md sections, pattern libraries
- Measuring quality — false positive tracking, time-to-review metrics

**Part 4: Ready-to-Use Configs**
Copy-paste configurations for five stacks:
- Python / Django
- TypeScript / React
- Ruby / Rails
- Go
- Rust

Each config includes: CLAUDE.md snippet, review skill, hook config, and CI workflow.

---

## How to Use

### Read in browser

Open `ai-code-review-playbook.html` in Chrome or Firefox. The table of contents links scroll to each chapter. Code blocks have one-click copy buttons.

### Print to PDF

1. Open in Chrome
2. `Cmd+P` → Save as PDF
3. Paper: Letter or A4, margins: Default
4. Uncheck "Headers and footers"

Print styles are included — the dark theme converts to clean black-on-white for print.

### Copy configs directly

Each chapter with configuration content has standalone code blocks. Copy the snippet, adapt the paths, and drop it into your project.

---

## Who This Is For

- Individual developers who want faster, more consistent code review
- Tech leads introducing AI tooling to their team
- Platform engineers building review automation into CI/CD
- Anyone who has tried `claude -p "review this"` and wants structured patterns instead

---

## Pricing

| Channel | Price |
|---------|-------|
| Gumroad | $19 |
| Payhip | $24 |
| Direct / Bundle | $29 |

---

## License

MIT — see `LICENSE`. Configs and templates are free to use in commercial projects. Attribution appreciated, not required.

---

*Product of Edgeless Labs LLC | edgeless.ai*
