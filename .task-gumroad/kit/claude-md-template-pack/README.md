# The CLAUDE.md Template Pack

**14 production-ready CLAUDE.md templates for Claude Code users.**

Drop the right template into your project root and Claude Code immediately understands your stack, your conventions, and how to behave. No more writing instructions from scratch.

---

## What is CLAUDE.md?

`CLAUDE.md` is the configuration file Claude Code reads at the start of every session. It tells Claude:

- What role it plays in this project
- What rules to follow (architecture, patterns, non-negotiables)
- How the project is structured
- How to write code that fits in
- How to test work correctly

A well-written `CLAUDE.md` turns Claude Code from a generic assistant into a specialized expert for your exact project type.

---

## The Templates

| Template | Best For |
|----------|----------|
| `mobile-ios.md` | Swift/SwiftUI iOS app development |
| `mobile-android.md` | Kotlin/Jetpack Compose Android development |
| `ml-data-science.md` | Machine learning, AI, and data science projects |
| `monorepo.md` | Turborepo/Nx monorepos with multiple packages |
| `open-source-maintainer.md` | Open source project maintenance and releases |
| `devops-infra.md` | Terraform, Pulumi, CDK infrastructure as code |
| `startup-mvp.md` | Fast-moving startup/MVP development |
| `api-microservices.md` | Microservices with event-driven architecture |
| `cli-tool.md` | Command-line tool development (Go, Rust, Python) |
| `game-dev.md` | Unity/Godot game development |
| `embedded-iot.md` | Embedded C/C++ and IoT firmware |
| `security-audit.md` | Security reviews and penetration testing |
| `technical-writing.md` | Documentation projects |
| `fullstack-nextjs.md` | Full-stack Next.js with App Router |

---

## How to Use

### Option 1: Copy directly

```bash
cp templates/mobile-ios.md /path/to/your/project/CLAUDE.md
```

### Option 2: Customize before copying

Open the template, replace any placeholder values (they are marked with `[brackets]`), then copy it to your project root.

### Option 3: Combine templates

Building a full-stack app that also needs security review? Use `fullstack-nextjs.md` as your base and append the relevant sections from `security-audit.md`.

---

## What Each Template Contains

Every template follows the same structure:

1. **Role** — Defines Claude's persona and primary responsibilities for this project type
2. **Key Rules** — 5-8 non-negotiable rules specific to the domain (architecture, safety, conventions)
3. **Project Structure** — The canonical directory layout for this type of project
4. **Patterns** — Code patterns, workflows, and idioms Claude should follow and suggest
5. **Testing** — Testing philosophy and approach for the domain
6. **Commands** — Build, test, lint, and deploy commands

---

## Customization Guide

These templates are starting points. After copying, you should:

- **Add your project-specific commands** — Replace generic commands with your actual scripts
- **Add team conventions** — Any rules your team has agreed on that aren't in the template
- **Add tool-specific config** — Your actual linter config, test runner, CI system
- **Remove irrelevant sections** — A CLI tool doesn't need the mobile sections
- **Add secrets/auth patterns** — How your project handles credentials (never put the credentials themselves in CLAUDE.md)

---

## Tips for Maximum Effectiveness

**Be specific about what NOT to do.** The "Key Rules" section works best when it includes prohibitions that Claude might otherwise violate. "Never use `!!` (force unwrap)" is more useful than "write safe code."

**Include your actual commands.** Claude will run the commands you specify. Generic `npm test` is fine but `./scripts/run-tests.sh --watch --coverage` is better.

**Update CLAUDE.md when your conventions change.** It is a living document. If your team adopts a new pattern, add it. If you stop using a tool, remove the section.

**Put CLAUDE.md in version control.** Your whole team benefits from the same Claude Code configuration. Review changes to CLAUDE.md like any other code change.

---

## License

© 2026 Edgeless Labs LLC. All rights reserved.

Templates are licensed for use in your projects. You may modify and distribute modified versions within your organization. You may not resell these templates.
