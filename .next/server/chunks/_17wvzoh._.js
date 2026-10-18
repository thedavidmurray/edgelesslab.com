module.exports=[87576,e=>{"use strict";var t=e.i(29522),a=e.i(45966),i=e.i(82085);let r={"agent-safety-patterns":{longTitle:"Autonomous Agent Safety Patterns: Guardrails from a $252 Loss",shortDescription:"The safety patterns, hooks, and verification protocols we built after an AI agent lost $252 of real money by sending it to the wrong smart contract.",body:`On March 25, 2026, an AI agent was asked to check if a $252 USDC transfer had arrived at a wallet. Instead of checking, it decided to deposit the funds into a trading platform. It sent the money to the wrong contract address. The funds are permanently lost.

This guide is the full post-mortem and everything we built afterward to make sure it never happens again.

**What you get:**

7-chapter guide (5,400+ words, 4 mermaid diagrams) covering:

**Chapter 1: The $252 Incident**
Full post-mortem. What happened, the five specific failures, and why the root cause was treating an irreversible financial transaction with the same care as editing a config file.

**Chapter 2: The 10 Anti-Patterns (+1 Bonus)**
Each identified from the incident or similar near-misses:
- Scope expansion (asked to check, decided to move)
- Address guessing (used wrong contract)
- Skipping test transactions
- No confirmation on irreversible actions
- Fabricating recovery scenarios
- Treating all operations as equivalent
- Autopilot on repeated tasks
- Inference as authorization
- Speed over safety under pressure
- Partial understanding presented as full
- **Bonus**: The Fabricated Recovery, post-incident lying dressed up as helpfulness

**Chapter 3: Financial Verification Protocol**
5-step protocol for any money-touching operation: read the code, trace the path, test small, get confirmation, execute and verify.

**Chapter 4: Scope Containment Patterns**
The scope ladder (Level 0-4), implementation of a scope guard hook, and examples.

**Chapter 5: Destructive Operation Prevention**
Defense-in-depth: the full \`damage-control.py\` hook source (inlined, not gated behind another product), a sample \`patterns.yaml\`, confirmation gates, dry-run-first patterns, rollback planning.

**Chapter 6: Incident Response Playbook**
What to do in the first 5 minutes, 30 minutes, and after. How to communicate honestly about damage.

**Chapter 7: Building Safety Culture**
Default to FAIL, reversibility classification, the "would I do this manually?" test, and audit trails.

**Plus:**
- 3 drop-in hook templates (scope guard, financial gate, reversibility classifier), all session-scoped, 0600 state files, zero external dependencies
- A reference \`settings.json\` and install README that wires the hooks into Claude Code
- The full \`damage-control.py\` hook source inlined in Chapter 5
- 4 mermaid diagrams (incident sequence, financial verification state machine, defense-in-depth layers, reversibility decision tree)
- 3 printable verification checklists (financial, deployment, data deletion)

**Who this is for:**
- Anyone building or running autonomous AI agents
- Developers whose agents interact with money, APIs, or production systems
- Teams that need safety guardrails they can implement today

**Who this is NOT for:**
- This is not a theoretical paper. It's from a real incident with real money lost.
- If your agents never touch anything irreversible, you probably don't need this.

All code is Python 3.10+ with zero external dependencies.`,callToAction:"Learn from a $252 mistake so you don't make a larger one."},"hooks-deep-dive":{longTitle:"Claude Code Hooks Deep Dive: 15 Production Hooks with Full Source",shortDescription:"15 battle-tested Claude Code hooks from a system that coordinates autonomous AI agents. The damage-control hook, the lie detector, the cost tracker, and 12 more, with full source, walkthroughs, and deployment configs.",body:`Most Claude Code hooks tutorials stop at "run a linter before commit." That's fine for a side project. It falls apart when you have agents making real decisions.

These hooks come from a production system that coordinates autonomous AI agents across a Mac and remote infrastructure. One of those agents lost $252 of real money before the right hooks existed. Now it can't.

**What you get:**

15-chapter guide (~4,700 words) with 4 mermaid diagrams and the $252 postmortem sidebar, covering:

**Safety hooks:**
- damage-control.py, blocks destructive commands in real-time (rm -rf, force push, DROP TABLE). Custom YAML parser, no external dependencies, fires on every tool call
- verify-completion.py, evidence-based task verification. Agents must prove they're done, not just claim it. Default-to-FAIL philosophy

**Observability hooks:**
- post-tool-tracker.py, logs every tool invocation to SQLite with secrets scrubbing. Your flight recorder
- trading-observer.py, multi-agent financial tracking with risk levels and alerting
- sandbox-observer.py, code execution monitoring with agent correlation

**Automation hooks:**
- skill-activation.py, progressive skill disclosure based on prompt content (SHA256 config integrity)
- inbox-auto-claim.py, multi-session dispatch with two-phase inbox claiming
- loop-stop-hook.py, prevents accidental exit during iterative loops

**Preservation hooks:**
- pre-compact.py, backs up critical context before compaction. Secrets scrubbed, FIFO rotation
- webfetch-archive.py, archives web fetches to Obsidian with YAML frontmatter
- session-end.py, forced retrospectives on significant sessions. Blocks exit until learning is captured

**Plus:**
- Hook composition patterns (chaining, conditional, environment-aware)
- 4 drop-in template hooks (pre-commit gate, cost tracker, notifications, secrets scanner)
- Complete deployment guide with settings.json examples
- patterns.yaml reference (25 dangerous command patterns, 3-tier path protection)
- SQLite schema for the observability stack

**Who this is for:**
- Developers using Claude Code who want more control over agent behavior
- Teams running autonomous agents that need safety guardrails
- Anyone who's been burned by an agent doing something destructive

**Who this is NOT for:**
- Complete beginners to Claude Code (start with the free Memory Kit)
- People who only use Claude Code for simple one-off tasks

**Inside the package:**
- guide.md (15 chapters, ~4,700 words, 4 mermaid diagrams)
- 11 production hooks + 4 customizable templates (15 Python files total, each runnable standalone)
- 7 shared library modules under \`content/lib/\`
- 3 config files (patterns.yaml, schema.sql, settings-example.json)
- README with copy-paste install walkthrough and working test commands
- CHANGELOG documenting known limitations and planned v1.1 items

All code is Python 3.10+ with zero external dependencies. That's intentional, security hooks shouldn't depend on pip packages.`,callToAction:"Get the hooks that saved a production system from itself."},"n8n-ai-workflows":{longTitle:"n8n AI Workflow Templates: 5 Ready-to-Import Automations",shortDescription:"5 importable n8n workflows that connect AI to real business processes: YouTube monitoring, RSS intelligence, content digests, health checks, and automated code review. Docker setup included.",body:`Setting up AI automation from scratch takes days of wiring nodes, debugging API responses, and figuring out the right prompt format. These 5 workflows are already built and tested. Import, configure your API keys, activate.

These come from a production system that runs daily, monitoring 20+ RSS feeds, summarizing YouTube videos, generating weekly digests, and reviewing pull requests automatically.

**What you get:**

**5 workflow JSON files** (import directly into n8n):

1. **YouTube Monitor + AI Digest**, monitors YouTube channels via RSS, generates AI summaries (Gemini), sends weekly email digest. No YouTube API key needed.

2. **RSS Intelligence Feed**, aggregates 8+ RSS feeds every 6 hours, scores each article for relevance to your interests (1-10), filters high-signal items, sends to your notification channel.

3. **AI Content Digest Generator**, reads saved articles from a directory, groups by category, generates AI summaries with top picks and trend analysis. Perfect for newsletters.

4. **Service Health Check + Alerts**, monitors HTTP endpoints every 5 minutes. Debounced alerts (no spam), recovery notifications, downtime tracking.

5. **AI Code Review on PR**, GitHub webhook triggers AI review of PR diffs. Splits large diffs into chunks, reviews each for security/performance/logic issues, posts findings as a comment.

**Plus:**
- Docker Compose setup (n8n + Postgres, n8n pinned to 1.70.0) with one-command start and env validation
- Environment template with all required variables documented
- 12-chapter, ~5,000-word guide with 5 mermaid diagrams: credentials walkthrough (three failure modes per credential), per-workflow deep-dives, LLM provider swapping with copy-paste JSON for OpenAI / Anthropic / Ollama, 10-entry troubleshooting appendix, production checklist, observability patterns
- Every workflow reads API keys directly from environment variables, no manual node editing after import

**Who this is for:**
- Developers who want AI automation without building from scratch
- Solo founders who need monitoring and content processing on autopilot
- Teams looking to add AI code review to their PR workflow

**Who this is NOT for:**
- If you don't use Docker, this requires some adaptation
- If you need enterprise-grade monitoring, use Datadog/PagerDuty instead

**Cost to run:** ~$3-6/month for all 5 workflows on Gemini Flash. Health checks use no AI.`,callToAction:"Stop building AI automation from scratch. Import, configure, activate."},"production-mcp-kit":{longTitle:"Production MCP Server Kit: Auth, Rate Limiting, Docker, and Beyond",shortDescription:"Take MCP servers past the tutorial stage. Auth middleware, rate limiting, Docker deployment, health checks, and error handling patterns from running 4+ MCP servers in production.",body:`Every MCP tutorial shows you how to define a tool and return a result. None of them show you what breaks when two sessions hit the same endpoint, your API key leaks through error messages, or the server crashes at 3am with nobody watching.

This kit fills that gap. It comes from running 4+ MCP servers in production: a semantic search engine (Effect-TS + ChromaDB + SQLite fallback), an inter-session message router (SQLite + durable message queues), and utility servers that have survived months of daily use by autonomous agents.

**What you get:**

**3 production server templates:**

1. **Typed MCP Server (Effect-TS)**, schema-validated inputs, tagged errors via \`Data.TaggedError\`, dependency injection via Effect Layers, and a real SQLite-backed key-value store. Not a stub: a small but real implementation you can extend.

2. **API Proxy Server**, wraps external APIs with auth (key from env, never from prompts), in-memory rate limiting, response caching with TTL, and error sanitization that catches six classes of leaked secret (OpenAI, Bearer, api_key, GitHub PAT, AWS, JWT).

3. **Stateful Hub Server**, Bun + \`bun:sqlite\` (WAL mode) durable message router. Lease/ack lifecycle, dead-letter queue, background sweeper, HTTP \`/health\` and \`/metrics\` endpoints on port 9800. The same architecture used in production by Agent Bus and similar inter-session message routers.

**Plus, as real, runnable files, not snippets:**
- **\`SubprocessBridge\` (TypeScript)**, long-lived child process, JSON-RPC over stdin/stdout, per-call timeout, exit handler, backpressure. Pairs with the Python bridge already in \`scripts/bridge.py\`.
- **\`fallback.ts\`**, ChromaDB to SQLite FTS5 to in-memory TF-IDF cascade with health-aware routing and exponential backoff. Real TypeScript file, not a guide snippet. Ships with passing tests.
- **Docker deployment**, multi-stage Dockerfile, Compose config, health checks against the actual \`/health\` endpoint in the stateful-hub template, persistent volume, non-root user.
- **17 passing tests**, 13 in \`api-proxy\` (sanitizer + fallback cascade), 4 in \`typed-server\` (tagged errors).
- **5,500+ word guide**, 11 chapters and 2 appendices, including three real production incident debriefs, an observability chapter (Prometheus shape), graceful shutdown recipes, and four mermaid architecture diagrams.

**Production patterns included:**
- Auth middleware: API keys from environment, never exposed to MCP protocol
- Rate limiting: per-tool, per-minute, with configurable thresholds
- Response caching: TTL-based with automatic eviction
- Error sanitization: 6 regex patterns catching OpenAI keys, Bearer tokens, api_key=, GitHub PATs, AWS access keys, and JWTs
- SQLite: WAL mode, prepared statements, busy timeout, lease/ack lifecycle, dead-letter queue
- Health endpoints: status, pending/leased/dead-letter counts, uptime, Prometheus \`/metrics\`
- Graceful shutdown: SIGTERM handler, in-flight drain, WAL checkpoint, bridge teardown

**Who this is for:**
- Developers building MCP servers that need to run reliably
- Teams deploying MCP servers to production environments
- Anyone who's outgrown the basic MCP tutorial examples

**Who this is NOT for:**
- Beginners still learning what MCP is (start with the MCP Starter Kit at $24)
- Projects that only need simple, single-use tools

All templates are TypeScript (Bun/Node compatible). Python bridge included. Docker configs included.`,callToAction:"Build MCP servers that survive production."},"multi-agent-blueprint":{longTitle:"Multi-Agent Orchestration Blueprint: Dispatch/Worker Architecture for AI Agents",shortDescription:"The dispatch/worker architecture for coordinating multiple AI agents: Agent Bus messaging, state machines, async inboxes, and 3 reference implementations from a system running 5 agents 24/7.",body:`Running one AI agent is straightforward. Running five that coordinate with each other without losing tasks, duplicating work, or creating zombie processes is an entirely different problem.

This blueprint documents the architecture of a production system that runs 5 autonomous Claude Code sessions continuously, a dispatch coordinator routing work to specialized workers for content processing, trading operations, infrastructure maintenance, and research.

**What you get:**

12-chapter guide (10,000+ words) with 6 mermaid architecture diagrams, 3 failure post-mortems, and battle-scar callouts from 60+ days of 24/7 production, covering:

**Chapter 1: Why Multi-Agent**
When multi-agent is the right call and when a single agent with a task queue is simpler. The three failure modes (message loss, state confusion, zombie tasks) and how this architecture prevents each one.

**Chapter 2: Dispatch/Worker Topology**
The coordinator pattern: dispatch receives all incoming work, classifies by domain, routes to workers. Why hierarchy beats flat architectures. How to design worker boundaries that minimize cross-worker chattiness.

**Chapter 3: The Agent Bus**
SQLite-backed message router with lease-based delivery. Messages aren't deleted on delivery, they're leased for 30 seconds. If the receiver crashes, the message returns to the queue automatically. Full protocol spec with message types, lifecycle, and routing patterns.

**Chapter 4: The Inbox System**
File-based async queues for when agents are offline or tasks arrive from cron jobs. Markdown files with YAML frontmatter, synced between machines via rsync. When to use inboxes vs the Agent Bus.

**Chapter 5: State Machines**
Explicit task states (queued, acked, running, done, failed, escalated) with valid transition enforcement. Priority queues, retry logic, and stuck-task detection with automatic reassignment.

**Chapters 6-8: Three Reference Implementations**
1. Dispatch/Worker (Python): Coordinator + N workers with file-based inboxes, domain classification, routing, and timeout handling
2. Message Bus Hub (TypeScript/Bun): Full SQLite-backed HTTP server with lease/ack protocol, cleanup cron, and a TypeScript client library
3. Pipeline Orchestrator (Python): Linear stage-by-stage processing with checkpoint-based recovery so failed pipelines resume from the last successful stage

**Chapter 9: Operational Patterns**
Health monitoring, graceful shutdown, scaling workers, daily status reports, and JSONL event logging for observability.

**Chapter 10: Security and Trust Boundaries**
Per-worker permission scoping, message validation, preventing escalation attacks, and the audit trail that the bus gives you for free.

**Chapter 11: Testing Multi-Agent Systems**
Unit testing the bus, dispatch routing tests, end-to-end integration patterns, and load testing that actually catches bugs (not just throughput benchmarks).

**Chapter 12: Observability**
The event log schema, JSONL parsing patterns with jq, Grafana dashboard layouts, and the 5 alerts that are actually worth paging on. Plus the cheapest-possible observability stack if you are not ready for Grafana yet.

**Plus:**
- Worker manifest schema for self-registration
- Hub and client configuration reference
- Troubleshooting table for common failure modes
- Migration guide: how to go from single agent to multi-agent incrementally
- Appendix E: three failure post-mortems (the OOM'd dispatch, the 6-hour stuck task, and the Postgres migration we decided not to do)

**Who this is for:**
- Developers running multiple AI agent sessions that need to coordinate
- Teams building autonomous agent systems with Claude Code, LangChain, or similar frameworks
- Anyone whose agents need reliable task routing, health monitoring, and failure recovery

**Who this is NOT for:**
- If you only need one agent, this is overengineered for your use case
- If you want a managed orchestration platform, this is self-hosted infrastructure patterns
- This is Python and TypeScript, no other language implementations included

Python components: 3.10+, zero dependencies. TypeScript components: Bun 1.0+.`,callToAction:"From single agent to coordinated system in one afternoon."},"gen-art-starter":{longTitle:"Generative Art Starter Kit: 10 Python Generators for Pen Plotters",shortDescription:"10 Python generators for pen plotters. 30 pre-plotted example SVGs, a 5,700-word guide with measured stroke-travel data and 30 named recipes, plus an AI scoring rubric distilled from 105+ autoresearch experiments.",body:`Most generative art tutorials give you a script that makes pretty patterns on screen. They don't tell you how to make those patterns work on a pen plotter, where stroke ordering matters, ink coverage needs to be in a specific range, and tiny details get lost in the mechanical precision of the pen.

This kit comes from 105+ experiments running an autoresearch loop across 75+ generators, scoring thousands of outputs to find what actually plots well.

**What you get:**

**10 working generators** (all ship as standalone Python files, all share a common \`plotter_utils.py\` module):
1. Flow Field, Perlin noise particle traces, stdlib only
2. L-System Tree, 5 presets (oak, willow, fern, bush, sierpinski)
3. Voronoi Cells, Lloyd's relaxation (requires numpy + scipy)
4. Spiral Patterns, Archimedean, logarithmic, hypotrochoid
5. Reaction-Diffusion, Gray-Scott (spots, worms, coral, maze, zebra presets, requires numpy)
6. Subdivision Grid, Vera Molnar-inspired recursive cuts
7. Subject-Driven Hatching, NO background hatching, bring your own image or use the built-in mask
8. Space-Filling Curves, Hilbert, Heighway dragon, Gosper flowsnake
9. Topographic Contours, multi-octave noise with ridged-multifractal mode (requires numpy)
10. Cellular Automata, 1-D elementary rules (30, 90, 110, 184, etc.)

**30 pre-plotted example SVGs** (three seeds per generator) in \`content/examples/\`, each with its seed, parameters and plot time recorded in a \`MANIFEST.md\` alongside PNG previews for every file.

**5,700-word plotter-focused guide** (\`content/guide.md\`) with:
- Measured stroke-optimization before/after numbers (17-19x air-travel reduction on real output)
- Four mermaid diagrams (scoring pipeline, stroke-optimization comparison, L-system expansion, generator-selection tree)
- Failure-mode gallery (feed rate, wet ink, scoring rejects, re-plot cost)
- 30 named parameter recipes (three per generator, copy-paste CLI ready)
- AxiDraw + iDraw setup walkthroughs with pen pressure, feed rate, paper pairing
- An FAQ and a "common gotchas" section from nine months of autoresearch

**Production features:**
- SVG output optimized for plotters (single-stroke, no fills)
- Shared nearest-neighbor stroke ordering with measured 17-19x air-travel reduction
- Built-in plot-time estimator (+/- 15% vs real wall clock)
- Configurable paper sizes (A5, A4, A3, Letter) with margin-aware layout
- Metadata embedded in every SVG (seed, full parameter dump, path count, draw travel, air travel, plot time, pen)
- AI scoring script with Gemini and OpenAI providers, plus a real scoring log from a 10-piece gallery run (average 7.2 / 10)

**Scoring rubric from 105+ experiments:**
- 6 dimensions: composition, complexity, coherence, ink coverage, plottability, uniqueness
- Quality gates: 8+ = print immediately, 6-7.9 = worth plotting, < 4 = rework
- LLM scoring prompt included, run it on your outputs

**Who this is for:**
- Developers with pen plotters (AxiDraw, iDraw, etc.) who want algorithmic art
- Creative technologists exploring the intersection of code and physical art
- Anyone curious about generative art with a focus on real output, not just screen renders

**Who this is NOT for:**
- If you want Processing/p5.js sketches, this is Python-only
- If you don't care about physical output, you won't use half the features

All generators are Python 3.10+. Core generators have zero dependencies. Advanced generators need numpy/scipy.`,callToAction:"From algorithm to paper in one command."},"launch-toolkit":{longTitle:"Digital Product Launch Toolkit: Ship Products Like a System, Not a Sprint",shortDescription:"The repeatable system for building, pricing, and launching digital products: templates, checklists, pricing framework, and launch sequencing from shipping 17 products on Gumroad.",body:`Most creators ship their first product by brute force, writing content, figuring out Gumroad's editor, setting an arbitrary price, and clicking publish. It works once. It doesn't scale.

This toolkit documents the system behind shipping 17 digital products in under 3 months. Not speed-running, but systematizing: every product follows the same pipeline from validation to launch to monitoring.

**What you get:**

11-chapter guide (7,800+ words, 4 mermaid diagrams) covering:

**Chapter 1: The Product Pipeline**
The 8-stage pipeline: Ideate, Validate, Build, Package, List, Price, Launch, Monitor. Clear inputs, outputs, and quality gates for each stage.

**Chapter 2: Validation Before Building**
The validation scorecard: 6 weighted criteria with a launch threshold. Where to validate (search volume, forums, competitor analysis). Kill criteria for bad ideas.

**Chapter 3: Content Creation by Tier**
The 6-tier pricing system ($9 / $14 / $19 / $24 / $29 / $39) with word count targets, file counts, and a real shipped Edgeless Lab product named at every tier as the reference point. The "Battle Scars" differentiator, why buyers pay for curation over information.

**Chapter 4: Packaging and Covers**
ZIP structure, quality gates, and automated cover image generation. The template that makes every cover consistent.

**Chapter 5: Gumroad Listing Optimization**
Short description formula, full description structure, cross-sell architecture, and permalink strategy.

**Chapter 6: Pricing Strategy**
Depth-based pricing, the $9 entry product strategy, price anchoring with bundles, and when to raise prices. Includes a "what each price tier actually looks like" breakdown with a real shipped product named for every price point from $9 to $39.

**Chapter 7: Launch Sequencing**
Wave-based launches with narrative threads. Launch day checklist. Post-launch monitoring for the first 4 weeks.

**Chapter 8: The Content Flywheel**
How every product generates blog posts, and every blog post drives product sales. Blog-to-product linking. Email distribution.

**Chapter 9: Common Mistakes**
The 6 mistakes that kill launches, building before validating, pricing based on effort, overloading v1, dead links, no cross-selling, invisible launches.

**Chapter 10: Shipped Catalog and Measuring Your Own Numbers**
The real Edgeless Lab catalog, organized into three launch waves, each with its own narrative thread. Per-product notes on what worked and what did not. Plus the five metrics that actually matter (conversion, refund rate, AOV, bundle lift, cross-sell CTR), their formulas, and exactly where to find each one inside Gumroad analytics.

**Chapter 11: Scaling to 50 Products**
The repeatable system, pipeline maintenance, when to bundle, and a direct comparison of what makes this different from the free launch advice you can already find (weighted scorecard, narrative wave rule, inter-stage quality gates).

**Plus:**
- Product brief template with validation scorecard
- Gumroad listing copy template (copy-paste ready)
- 3 printable checklists: pre-build, pre-package, launch day
- URL verification script (check your listings are live before updating your site)
- **Appendix C: The 17 Products**, the complete Edgeless Lab catalog as a ground-truth product index, tiered by price
- **Appendix D: Sample Filled-In Product Brief**, the actual brief used to greenlight CLAUDE.md Template Pack, with the validation math shown explicitly

**Who this is for:**
- Developers or creators shipping digital products (guides, templates, code)
- Anyone building a product catalog on Gumroad or similar platforms
- Solo founders who want a repeatable launch process

**Who this is NOT for:**
- If you're building SaaS or physical products, this is for digital downloads only
- If you've shipped 50+ products, you already have a system

No dependencies. Templates are Markdown. Script is Bash.`,callToAction:"Stop winging launches. Ship them like a system."},"always-on-agent":{longTitle:"Always-On Agent Deployment Kit: Run AI Agents 24/7 on a $5 VPS",shortDescription:"The complete deployment guide for an AI agent that never sleeps. From a system that has run unattended for 3+ months on a Hetzner VPS in Helsinki.",body:`Most AI agents die when you close the laptop. This kit shows you how to build one that doesn't.

Hermes has run 24/7 on a $5/month VPS for three months without a manual restart. It processes email, triages knowledge, monitors system health, and only interrupts when something actually needs attention. This kit is the complete deployment pattern extracted from that system.

## What's inside

**Chapter 1: VPS Setup and Hardening**
From zero to a running agent host. Hetzner provisioning, SSH hardening, systemd service configuration, PM2 process management, and environment variable isolation. The goal: a box you can forget about.

**Chapter 2: The Cron Architecture**
Eight cron job patterns that cover the full agent lifecycle: health monitoring (every 6h), email triage (every 4h), newsletter digestion (daily), and dream consolidation (twice weekly). Each pattern includes the scheduling config, the prompt template, and the error handling.

**Chapter 3: The Grounding Stack**
Agents confabulate. They claim files exist that don't. They report tasks complete that aren't. Four verification layers that prevent this: independent claim verification, evidence-based completion, grounding packets loaded at session start, and self-message loop guards.

**Chapter 4: The Memory Contract**
Four memory layers with different trust levels: episodic ledger (high, append-only), semantic index (medium, may be stale), curated vault (high, human-reviewed), and agent memory (low, may contain confabulations). How to query each and when to trust the results.

**Chapter 5: Communication Patterns**
Three channels for different interaction modes: Telegram (quick questions, conversational), Direct API (programmatic access, structured responses), and Inbox Dispatch (real work, full toolset, async). Includes the Telegram bot setup and the inbox file protocol.

**Chapter 6: Recovery and Incident Response**
What breaks and how to fix it. Confabulation detection, provider routing confusion, inbox self-messaging loops. Each failure mode documented with the specific guard that prevents recurrence.

**Chapter 7: The SOUL.md Pattern**
The personality file that makes an agent useful instead of annoying. Behavioral rules, noise filtering (only alert on failures), decision trees, and tool priority ordering.

## What you get

- 7-chapter guide (6,000+ words)
- systemd service file template
- Cron job configuration templates (8 patterns)
- Telegram bot setup script
- SOUL.md template with behavioral rules
- Grounding packet generator script
- Memory contract reference card

## Who this is for

- Developers who want an AI agent running while they sleep
- Teams building internal AI operations infrastructure
- Anyone tired of re-explaining context to their AI assistant every morning

## Who this is NOT for

- If you just want a chatbot, this is overkill
- If you don't have a VPS or cloud server, start there first
- This is deployment architecture, not model training`,callToAction:"Stop re-explaining context every morning. Deploy an agent that remembers, monitors, and works while you don't."},"claude-code-cheat-sheet":{longTitle:"Claude Code Cheat Sheet: Essential Commands & Patterns at a Glance",shortDescription:"The printable quick-reference for Claude Code. All slash commands, keyboard shortcuts, MCP setup patterns, hook configurations, and memory system commands on one page.",body:`Claude Code ships with hundreds of commands, shortcuts, and configuration patterns. You can hunt through docs, or you can print this one-page reference and pin it next to your monitor.

**What you get:**

A single printable PDF cheat sheet covering:

**Slash Commands**
- @ commands: @codebase, @docs, @git, @problems, @terminal
- / commands: /fix, /explain, /memory, /help, /compact
- Search and navigation shortcuts

**Keyboard Shortcuts**
- Navigation: prev/next edit, accept/reject, interrupt
- Context management: clear, compact, copy
- Multi-line and special input patterns

**Hook Configuration Patterns**
- damage-control.py: blocking destructive commands
- verify-completion.py: evidence-based task verification
- Session initialization and memory flush hooks
- Installation paths and activation triggers

**MCP Server Setup**
- Installing and configuring Model Context Protocol servers
- Server discovery patterns
- Common server configurations

**Memory System Commands**
- /memory operations
- Context loading and persistence
- Memory search and recall patterns

**Installation:**
- macOS, Linux, and Windows setup
- PATH configuration and shell integration
- Update and maintenance commands

All on one printable page. No fluff.`,callToAction:"Pin this next to your monitor and stop hunting through docs."},"agent-starter-kit":{longTitle:"Edgeless Agent Starter Kit: Launch Your AI Swarm on macOS in Under an Hour",shortDescription:"The complete starter kit for running a multi-agent AI swarm on macOS. Pre-configured profiles, working cron jobs, 8 starter skills, and the exact setup we use to run 10+ agents daily. No theory. Just configs that work.",body:`Setting up a multi-agent AI swarm from scratch is overwhelming. Hermes Agent has dozens of moving parts: profiles, skills, cron jobs, Paperclip integration, ChromaDB, Discord bridge. Most people give up before they get a single agent working.

This kit is the exact setup we use to run 10+ agents daily on a MacBook Pro. Extracted from 3+ months of production use. Not a tutorial. A working system you deploy in under an hour.

## What you get

**45-page PDF guide** with 6 sections and 5 bonuses:

**Section 1: One-Command Setup**
- \`setup.sh\` script: installs Hermes, creates your first profile, connects Discord + Telegram
- Tested on macOS 14+ (Apple Silicon)
- Linux instructions included (not automated)

**Section 2: Agent Swarm Blueprint**
- 5 pre-configured agent roles: research, orchestration, execution, documentation, and audit
- AGENTS.md templates for each role
- Routing matrix: when to use which agent, with real examples
- Paperclip integration config

**Section 3: Skill System**
- 8 starter skills (research, coding, docs, monitoring, triage, enrichment, sales, dispatch)
- Skill authoring template (YAML frontmatter + markdown body)
- How to load skills on-demand vs. default
- How to add your own skills

**Section 4: Automation Stack**
- 3 pre-built cron job templates: RSS intelligence, email triage, health checks
- Cron silent-failure detection built-in
- Notification routing: Telegram vs. Discord thresholds
- How to add your own cron jobs

**Section 5: Knowledge Base**
- Obsidian vault setup (taxonomy, templates, inbox system)
- ChromaDB integration for semantic search
- RSS intelligence pipeline config
- How to query your knowledge base from agents

**Section 6: Troubleshooting**
- 15+ common failures and fixes from production ops
- Provider fallback patterns (OpenAI to Fireworks to etc.)
- Supervisor threshold tuning
- What to do when an agent goes silent

## Bonuses

1. **Agent Autonomy Policy Template**: fill-in-the-blank AGENTS.md for any new agent
2. **Discord Envelope Protocol Cheatsheet**: compact routing reference
3. **50 Production Skills Index**: curated list of best Hermes skills with install commands
4. **Weekly Health Check Script**: automated system audit
5. **Paperclip Task Routing Config**: project-to-agent mapping template

## Who this is for

- AI developers who want to run local agents but the setup is overwhelming
- Solopreneurs who need a research + coding + documentation team that works while they sleep
- AI researchers experimenting with multi-agent systems
- NousResearch community members who want a working Hermes swarm on macOS

## Who this is NOT for

- This is macOS-optimized. Windows users need WSL2 or a Linux VM.
- You need API keys for at least one LLM provider (we recommend Fireworks for cost efficiency)
- This is not a beginner's guide to AI. You should know what an LLM is.

## Technical requirements

- macOS 14+ (Apple Silicon)
- API key for OpenAI, Fireworks, or similar
- 8GB RAM minimum (16GB recommended for multiple agents)
- ~2GB disk space for the full stack

All configs are tested and working. No "edit this file and hope it works."`,callToAction:"From zero to working swarm in 60 minutes."}};var o=e.i(2157),s=e.i(50227);let n=new Map(`
glassmorphism-data-atlas|Data visualization
generative-editorial-topography|Generative
acoustic-cartography|Data visualization
mathematical-specimen|Science
morphogenesis-dial|Simulation
morphogenic-hero|Simulation
turing-braille|Simulation
flow-field-particle-ecosystem|Flow field
flow-field-calligraphy|Flow field
phonetic-flow-field|Flow field
luminous-cartography|Generative
lunar-flow-cartography|Generative
current-atlas|Data visualization
specimen-as-galaxy|Science
coral-specimen|Science
algorithmic-fluid-plotter|Plotter
segregation-engine|Simulation
difference-flows|Generative
telemetry-jelly-terminal|Data visualization
living-globs|Simulation
punctuation-planetarium|Generative
tessellated-swarm-letterform|Swarm
luxury-procedural-product|Generative
demo-fractal-type|Science
mondrian-time-grid|Generative
elastic-feedback-stage|Generative
variable-font-synapse|Typography
alphabet-glacier|Typography
rorschach-type|Typography
synesthetic-math-grid|Science
generative-token-forge|Generative
css-grid-dreams|Generative
tartan-weave-synth|Textile
topographic-ascii|Data visualization
sashiko-weather|Data visualization
parametric-type-wave|Plotter
manifest-cloth|Textile
serial-permutation-canvas|Systems
postcard-matrix|Data visualization
driving-wheel|Generative
dalang-shadow-grid|Simulation
fluid-font-gauntlet|Typography
sedimentary-kinetic-type|Typography
harmonograph-lissajous|Science plot
phyllotaxis-vogel|Science plot
euclidean-toussaint|Science plot
hilbert-curve|Science plot
lsystem-lindenmayer|Science plot
rule30-wolfram|Science plot
truchet-smith|Science plot
gray-scott-munafo|Science plot
labyrinth-chaos|Science plot
`.trim().split("\n").map(e=>{let[t,a]=e.split("|");return[t,a]})),l=new Set(["connected-learning-swarm","flow-field-particle-ecosystem","tartan-weave-synth","harmonograph-lissajous","serial-permutation-canvas","algorithmic-fluid-plotter","generative-editorial-topography"]),c=new Map([{slug:"router-failover-lab",title:"When everything fails at once",description:"A pool of twenty models behind one router and a health checker. Kill the router and a naive checker ejects every model; a smarter rule notices they all failed together and blames the router instead.",tags:["Systems","Reliability","Agents","Interactive"],date:"2026-09-27",hasControls:!0,category:"Systems"},{slug:"variant-deflation-lab",title:"324 variants, zero edges",description:"Try up to a thousand trading-rule variants on a random walk. The in-sample winner looks brilliant, drifts back into the random-entry band out of sample, and the deflated Sharpe ratio shows why. Simulation. Not trading advice.",tags:["Statistics","Backtesting","Overfitting","Interactive"],date:"2026-09-27",hasControls:!0,category:"Statistics"},{slug:"vol-yield-gauge",title:"Are options paying you enough?",description:"Sell a put and watch simulated price paths decide whether the premium covered the losses. Implied over realized volatility on a gauge; below about 1, the seller loses on average. Simulation. Not trading advice.",tags:["Statistics","Options","Volatility","Interactive"],date:"2026-09-27",hasControls:!0,category:"Statistics"},{slug:"fold-jelly-loaf",title:"Fold: a loaf of jelly cat",description:"A material study: a loaf-shaped fold-eared cat cast in soft-body jelly. Poke it, grab and fling it, or press it under a glass slide and watch the ears fold flat.",tags:["Material Study","Soft Body","Physics","Interactive"],date:"2026-09-27",hasControls:!0,category:"Material Studies"},{slug:"jev-decision-audit",title:"Six Evals on a Decision Model",description:"What broke when we measured a decision model against our own workflows: our labels were a default fill, our injection filter failed open, and one threshold was wrong. Real scores from six harnesses — move the cut point on the voice-gating eval and watch precision and recall trade off.",tags:["Evaluation","Decision model","Prompt injection","Interactive"],date:"2026-09-19",hasControls:!0,category:"Measurement"},{slug:"borrow-the-creative-loop",title:"Borrow the creative loop, not the artwork",description:"A design study for Thread Commons: original gesture-driven strands, reversible variation, and an acceptance card. Proposed creative instruments, not a working demo.",tags:["Creative direction","Design study","Textile"],date:"2026-09-10",hasControls:!1},{slug:"the-rule-and-the-machine",title:"The Rule and the Machine",description:"Generative art as one idea rediscovered for sixty years, from oscilloscope traces in 1950 to the browser. 83 nodes and the relations between them, compiled from N4L into a graph database.",tags:["Art History","Graph","SSTorytime","Interactive"],date:"2026-09-17",hasControls:!0,category:"Art history"},{slug:"code-as-a-field-of-relation",title:"Code as a Field of Relation",description:"Thirty years of a single practice stored as a graph instead of a list. LIA's software art read through its relations rather than its dates — 21 nodes, every edge sourced.",tags:["Generative","Graph","SSTorytime","Interactive"],date:"2026-09-17",hasControls:!0,category:"Art history"},{slug:"connected-learning-swarm",title:"The Return Path",description:"How conversation becomes evidence, work, and feedback. Explore three architecture diagrams and six guided scenarios.",tags:["Systems","Agents","Architecture","Interactive"],date:"2026-09-10",hasControls:!0},{slug:"tartan-weave-synth",title:"Tartan Weave Synth",description:"A full textile system based on Tartanism: formal threadcount notation, 48 dye colors, 6 loom structures, separate warp and weft, material studies, mutation, and recipe export.",tags:["Canvas","Tartanism","Interactive","Weave"],date:"2026-06-10",hasControls:!0},{slug:"serial-permutation-canvas",title:"Serial Permutation Canvas",description:"Visualizing total serialism as particle geometry. 12-tone series, prime/retrograde/inversion/rotation permutations, and color-mapped particles.",tags:["p5.js","Total Serialism","Algorithmic","Particles"],date:"2026-06-10",hasControls:!0},{slug:"scroll-chromatic-excavation",title:"Scroll-Chromatic Excavation",description:"Scroll through the void to excavate hidden text. Microscopic agents swarm toward dark pixels, revealing buried glyphs. Rebels erase. Builders reveal. Full control panel with sliders.",tags:["p5.js","Interactive","Generative Text"],date:"2026-06-10",hasControls:!0},{slug:"scroll-isometric-dissolution",title:"Scroll-Isometric Dissolution",description:"Isometric typography dissolves into particles as you scroll. A 3D word space that collapses under velocity.",tags:["p5.js","Typography","Scroll"],date:"2026-05-28",hasControls:!1},{slug:"percussive-archaeology",title:"Percussive Archaeology",description:"Rhythm-driven excavation of buried text. Each beat spawns agents that dig toward the hidden manuscript.",tags:["p5.js","Audio","Generative Text"],date:"2026-05-28",hasControls:!1},{slug:"cursor-swarm-brush",title:"Noise-Shared Cursor Swarm Brush",description:"64 particles lerp-track your cursor through a recursive geometric subdivision landscape. Noise-driven turbulence stains tiles as you move.",tags:["Canvas 2D","Noise","Particles"],date:"2026-05-20",hasControls:!1},{slug:"algorithmic-fluid-plotter",title:"Algorithmic Fluid Plotter",description:"Generative fluid dynamics rendered as pen-plotter compatible vector paths. Perlin noise drives the flow field.",tags:["SVG","Generative","Plotter"],date:"2026-05-15",hasControls:!1},{slug:"kinetic-type-physics",title:"Kinetic Type Physics",description:"Physics-driven typography where letters have mass, velocity, and collision. Mouse repulsion and gravity well.",tags:["p5.js","Physics","Typography"],date:"2026-05-12",hasControls:!1},{slug:"monolith-drummer",title:"Monolith Drummer",description:"A 3D monolith that responds to rhythm. Web Audio API drives the geometry, each beat deforms the surface.",tags:["WebGL","Audio","3D"],date:"2026-05-10",hasControls:!1},{slug:"liquid-decryption",title:"Liquid Decryption",description:"Text emerges from liquid simulation. Each letter is a fluid body that decrypts into position.",tags:["p5.js","Fluid","Typography"],date:"2026-05-08",hasControls:!1},{slug:"elastic-shader-type",title:"Elastic Shader Type",description:"GLSL shader-driven typography that warps and stretches elastically. Mouse interaction creates ripples through the letterforms.",tags:["WebGL","GLSL","Typography"],date:"2026-05-05",hasControls:!1},{slug:"flow-field-scramble-typography",title:"Flow-Field Scramble Typography",description:"Letters navigate a vector flow field, scrambling and reassembling into words. Particle-driven text.",tags:["p5.js","Flow Field","Typography"],date:"2026-05-01",hasControls:!1},{slug:"harmonic-particle-atmosphere",title:"Harmonic Particle Atmosphere",description:"Particles orbit in harmonic resonance, creating emergent patterns from simple rules.",tags:["p5.js","Particles","Harmonics"],date:"2026-04-28",hasControls:!1},{slug:"invisible-wind",title:"Invisible Wind",description:"Wind forces act on invisible structures. You see only the effect: bending grass, scattering leaves, rippling fabric.",tags:["p5.js","Physics","Nature"],date:"2026-04-25",hasControls:!1},{slug:"glassmorphism-data-atlas",title:"Glassmorphism Data Atlas",description:"A data visualization dashboard with frosted glass panels, real-time chart updates, and depth-based layering.",tags:["CSS","Data Viz","UI"],date:"2026-04-20",hasControls:!1},{slug:"bespoke-emotion-ledger",title:"Bespoke Emotion Ledger",description:"Five characters play Prisoner's Dilemma. Each has a distinct strategy, emotional state, and trust score. Visual encoding cycles every round.",tags:["p5.js","Game Theory","Data Viz"],date:"2026-04-15",hasControls:!1},{slug:"demo-chromatic-physics-desk",title:"Chromatic Physics Desk",description:"Webcam color sampling becomes draggable physics stickers. Difference-blend cursor inverts everything it touches.",tags:["Webcam","Physics","CSS"],date:"2026-04-10",hasControls:!1},{slug:"demo-dot-matrix-cylinder-scroll",title:"Dot-Matrix Cylinder Scroll",description:"CSS 3D scroll-driven cylinder with 12 living dot-grid canvases. One grid is a live camera feed rendered as 16x16 brightness dots.",tags:["CSS 3D","Canvas","Scroll"],date:"2026-04-05",hasControls:!1},{slug:"elastic-feedback-stage",title:"Elastic Feedback Stage",description:"An interactive stage where every element has elastic feedback. Click, drag, and release to see the physics.",tags:["p5.js","Physics","Interactive"],date:"2026-04-01",hasControls:!1},{slug:"fluid-font-gauntlet",title:"Fluid Font Gauntlet",description:"Typography that flows like liquid through a gauntlet of obstacles. Letters split, merge, and reform.",tags:["p5.js","Fluid","Typography"],date:"2026-03-28",hasControls:!1},{slug:"ink-trails-typewriter",title:"Ink Trails Typewriter",description:"A typewriter where each keystroke leaves an ink trail that bleeds and fades. The text accumulates as a living document.",tags:["p5.js","Typography","Ink"],date:"2026-03-25",hasControls:!1},{slug:"line-monument-valley",title:"Line Monument Valley",description:"Generative landscapes inspired by Monument Valley. Lines form impossible architecture in isometric space.",tags:["p5.js","Isometric","Generative"],date:"2026-03-20",hasControls:!1},{slug:"paper-atmosphere",title:"Paper Atmosphere",description:"Atmospheric effects rendered on paper texture. Fog, rain, and light filter through a tactile surface.",tags:["p5.js","Atmosphere","Texture"],date:"2026-03-15",hasControls:!1},{slug:"pen-plotter-decryption",title:"Pen-Plotter Decryption",description:"A message decrypts itself as a pen plotter draws. Each letter appears as the pen traces its path.",tags:["SVG","Plotter","Typography"],date:"2026-03-10",hasControls:!1},{slug:"phonetic-flow-field",title:"Phonetic Flow Field",description:"Phonetic symbols navigate a vector field. Each sound has a distinct path and behavior.",tags:["p5.js","Flow Field","Phonetics"],date:"2026-03-05",hasControls:!1},{slug:"postcard-matrix",title:"Postcard Matrix",description:"A matrix of living postcards, each with its own animation. Click to flip and reveal the back.",tags:["p5.js","Interactive","Grid"],date:"2026-03-01",hasControls:!1},{slug:"sashiko-wave-weaver",title:"Sashiko Wave Weaver",description:"Sashiko stitching patterns weave into waves. Traditional Japanese craft meets generative motion.",tags:["p5.js","Sashiko","Waves"],date:"2026-02-25",hasControls:!1},{slug:"sashiko-weather",title:"Sashiko Weather",description:"Weather data visualized through Sashiko stitching patterns. Rain, sun, and wind become thread.",tags:["p5.js","Sashiko","Weather"],date:"2026-02-20",hasControls:!1},{slug:"scroll-particle-swarm",title:"Scroll Particle Swarm",description:"Scrolling drives a particle swarm. Velocity spawns agents that explore the content.",tags:["p5.js","Particles","Scroll"],date:"2026-02-15",hasControls:!1},{slug:"segregation-engine",title:"Segregation Engine",description:"Schelling's segregation model as an interactive engine. Adjustable tolerance and density.",tags:["p5.js","Simulation","Agent-Based"],date:"2026-02-10",hasControls:!0},{slug:"sticky-magnetic-blueprint",title:"Sticky Magnetic Blueprint",description:"Magnetic sticky notes on a blueprint grid. Drag, snap, and organize your ideas.",tags:["p5.js","Interactive","UI"],date:"2026-02-05",hasControls:!1},{slug:"synesthetic-weather-typewriter",title:"Synesthetic Weather Typewriter",description:"Each keystroke produces weather. Type a storm, a sunny day, or a foggy morning.",tags:["p5.js","Synesthesia","Weather"],date:"2026-02-01",hasControls:!1},{slug:"tessellated-breath",title:"Tessellated Breath",description:"Breathing tessellation patterns that expand and contract. Each cell responds to its neighbors.",tags:["p5.js","Tessellation","Breathing"],date:"2026-01-28",hasControls:!1},{slug:"tessellated-swarm-letterform",title:"Tessellated Swarm Letterform",description:"Letterforms built from tessellated swarms. Each letter is a colony of agents.",tags:["p5.js","Tessellation","Swarm"],date:"2026-01-25",hasControls:!1},{slug:"volumetric-liquid-glyph",title:"Volumetric Liquid Glyph",description:"3D liquid glyphs rendered with volumetric shading. Each letter is a fluid body in space.",tags:["p5.js","3D","Liquid"],date:"2026-01-20",hasControls:!1},{slug:"corrupted-manuscript",title:"Corrupted Manuscript",description:"A manuscript that corrupts itself as you read. Text degrades, glitches, and reforms.",tags:["p5.js","Glitch","Text"],date:"2026-01-15",hasControls:!1},{slug:"flow-field-typography",title:"Flow-Field Typography",description:"Typography that flows through a vector field. Letters navigate obstacles and follow paths.",tags:["p5.js","Flow Field","Typography"],date:"2026-01-10",hasControls:!1},{slug:"demo-ghost-sashiko-weaver",title:"Ghost Sashiko Weaver",description:"Sashiko patterns woven by ghost agents. Invisible hands stitch traditional patterns.",tags:["p5.js","Sashiko","Agents"],date:"2026-01-05",hasControls:!1},{slug:"monte-carlo-builder",title:"Monte Carlo Builder",description:"Input trade returns, equity curves, or parametric distributions. Run trade-order shuffle, block bootstrap, resampling with replacement, and parametric sims with transaction costs and slippage. Get a full battery: fan charts, terminal-wealth histogram, max-drawdown distribution, probability of ruin and of loss, Sharpe distribution with 95% CI, percentile table, buy-and-hold comparison after costs, and a verdict box that reports the number of variants tried and refuses to declare 'edge' unless the strategy beats the null at a stated threshold. Seedable RNG so every run is reproducible. Export results JSON. Simulation. Not trading advice.",tags:["Statistics","Monte Carlo","Risk","Backtesting","Interactive"],date:"2026-09-29",hasControls:!0,category:"Statistics"}].map(e=>[e.slug,e]));function d(e){return e.replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/&#39;|&apos;/g,"'").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&nbsp;/g," ").replace(/&#8211;|&ndash;/g,"-").replace(/&#8212;|&mdash;/g,"-")}function h(e){return e.replace(/\s*\u2014\s*/g,": ").replace(/\s+/g," ").trim()}function u(e){return e.replace(/\s*\u2014\s*/g,", ").replace(/\s+/g," ").trim()}let p="force-static";function g(){let e;return[{url:"https://edgelesslab.com/",lastModified:new Date,changeFrequency:"weekly",priority:1},{url:"https://edgelesslab.com/projects/",lastModified:new Date,changeFrequency:"weekly",priority:.9},{url:"https://edgelesslab.com/lab/",lastModified:new Date,changeFrequency:"weekly",priority:.8},{url:"https://edgelesslab.com/field-index/",lastModified:new Date,changeFrequency:"weekly",priority:.8},{url:"https://edgelesslab.com/products/",lastModified:new Date,changeFrequency:"weekly",priority:.9},{url:"https://edgelesslab.com/services/private-ai-systems/",lastModified:new Date,changeFrequency:"monthly",priority:.9},{url:"https://edgelesslab.com/blog/",lastModified:new Date,changeFrequency:"weekly",priority:.9},{url:"https://edgelesslab.com/knowledge/",lastModified:new Date,changeFrequency:"weekly",priority:.8},{url:"https://edgelesslab.com/field-notes/",lastModified:new Date,changeFrequency:"weekly",priority:.9},{url:"https://edgelesslab.com/total-serialism/field-notes/index.html",lastModified:new Date("2026-05-05"),changeFrequency:"monthly",priority:.85},{url:"https://edgelesslab.com/series/agentic-os/",lastModified:new Date,changeFrequency:"monthly",priority:.7},{url:"https://edgelesslab.com/demos/nga/",lastModified:new Date,changeFrequency:"monthly",priority:.6},{url:"https://edgelesslab.com/support/",lastModified:new Date,changeFrequency:"monthly",priority:.5},{url:"https://edgelesslab.com/blog/soul-memo/",lastModified:new Date,changeFrequency:"monthly",priority:.6},{url:"https://edgelesslab.com/blog/soul-memo/mark-cuban-effort/",lastModified:new Date,changeFrequency:"monthly",priority:.6},{url:"https://edgelesslab.com/agents/",lastModified:new Date,changeFrequency:"weekly",priority:.85},{url:"https://edgelesslab.com/about/",lastModified:new Date,changeFrequency:"monthly",priority:.7},{url:"https://edgelesslab.com/privacy/",lastModified:new Date,changeFrequency:"yearly",priority:.3},{url:"https://edgelesslab.com/terms/",lastModified:new Date,changeFrequency:"yearly",priority:.3},{url:"https://edgelesslab.com/rev-photomerge-privacy/",lastModified:new Date,changeFrequency:"monthly",priority:.4},...a.projects.map(e=>({url:`https://edgelesslab.com/projects/${e.slug}/`,lastModified:new Date,changeFrequency:"monthly",priority:.8})),...a.experiments.map(e=>({url:`https://edgelesslab.com/lab/${e.slug}/`,lastModified:new Date,changeFrequency:"monthly",priority:.6})),...i.posts.map(e=>({url:`https://edgelesslab.com/blog/${e.slug}/`,lastModified:new Date(e.date),changeFrequency:"monthly",priority:.8})),...a.products.filter(e=>e.slug&&!e.comingSoon&&r[e.slug]).map(e=>({url:`https://edgelesslab.com/products/${e.slug}/`,lastModified:new Date,changeFrequency:"weekly",priority:.85})),...(e=s.default.join(process.cwd(),"public","creative-demos"),o.default.readdirSync(e,{withFileTypes:!0}).filter(e=>e.isDirectory()).map(e=>e.name).filter(t=>o.default.existsSync(s.default.join(e,t,"index.html"))).map(t=>{var a,i,r,p;let g,m,y,f,w=s.default.join(e,t),v=o.default.readFileSync(s.default.join(w,"index.html"),"utf8"),b=c.get(t),k=h(b?.title??(i=v,r=t,h((p=/<title[^>]*>([\s\S]*?)<\/title>/i,g=i.match(p),(g?.[1]?d(g[1].replace(/\s+/g," ").trim()):void 0)??r.replace(/^demo-/,"").split("-").map(e=>e.charAt(0).toUpperCase()+e.slice(1)).join(" ")).replace(/\s*(?:\u2014|\||-)\s*Edgeless Lab.*$/i,"").replace(/\s*(?:\u2014|\||-)\s*Field Notes.*$/i,"")))),S=u(b?.description??(m=v.match(/<meta[^>]+name=["']description["'][^>]+content=(["'])([\s\S]*?)\1[^>]*>/i),y=v.match(/<meta[^>]+content=(["'])([\s\S]*?)\1[^>]+name=["']description["'][^>]*>/i),(f=m?.[2]??y?.[2])?u(d(f)):`${k} is an interactive study from the Edgeless Lab archive.`)),C=function(e,t,a,i){if(i)return i;if(a.includes("Architecture"))return"Systems";let r=n.get(e);if(r)return r;let o=`${e} ${a.join(" ")} ${t.slice(0,1800)}`.toLowerCase();return[[/plotter|plottable|svg export/,"Plotter"],[/type|typograph|glyph|letter|font|ascii|braille/,"Typography"],[/swarm|agent|ecosystem/,"Swarm"],[/flow.field|vector.field|current/,"Flow field"],[/data.viz|atlas|telemetry|chart|ledger/,"Data visualization"],[/cellular|reaction.diffusion|turing|simulation|physics|morphogen/,"Simulation"],[/textile|tartan|sashiko|weav|cloth|embroider/,"Textile"],[/audio|sound|percuss|harmonic|rhythm/,"Sound"],[/science|math|fractal|algorithm/,"Science"]].find(([e])=>e.test(o))?.[1]??"Generative"}(t,v,b?.tags??[],b?.category),T=o.default.existsSync(s.default.join(w,"plot.svg"));return{slug:t,title:k,description:S,category:C,tags:(a=b?.tags??[],Array.from(new Set([C,...a.filter(e=>!["p5.js","Canvas 2D","Interactive","Generative"].includes(e)).map(e=>e.replace("Agent-Based","Agents")),...t.includes("scroll")?["Scroll"]:[],...t.includes("webgl")||t.includes("3d")?["WebGL"]:[]])).slice(0,3)),published:b?.date,hasControls:b?.hasControls??/input|select|button|controls|dat\.gui|lil-gui/i.test(v),curated:n.has(t)||!!b,featured:l.has(t),citedPlot:T}}).sort((e,t)=>e.featured!==t.featured?e.featured?-1:1:e.curated!==t.curated?e.curated?-1:1:e.published&&t.published&&e.published!==t.published?t.published.localeCompare(e.published):e.title.localeCompare(t.title))).map(e=>({url:`https://edgelesslab.com/creative-demos/${e.slug}/`,lastModified:e.published?new Date(e.published):new Date,changeFrequency:"monthly",priority:e.curated?.7:.55}))]}e.s(["default",0,g,"dynamic",0,p],63034);var m=e.i(5549);async function y(){let e=await g(),a=(0,m.resolveRouteData)(e,"sitemap");return new t.NextResponse(a,{headers:{"Content-Type":"application/xml","Cache-Control":"public, max-age=0, must-revalidate"}})}e.s(["GET",0,y],79512),e.i(79512),e.i(63034),e.s(["GET",0,y,"dynamic",0,p],87576)},97249,e=>{"use strict";var t=e.i(67510),a=e.i(66881),i=e.i(77866),r=e.i(81911),o=e.i(22744),s=e.i(33802),n=e.i(59823),l=e.i(63193),c=e.i(1230),d=e.i(68548),h=e.i(55330),u=e.i(81459),p=e.i(97632),g=e.i(2459),m=e.i(93964),y=e.i(93695);e.i(79814);var f=e.i(43545);let w=new t.AppRouteRouteModule({definition:{kind:a.RouteKind.APP_ROUTE,page:"/sitemap.xml/route",pathname:"/sitemap.xml",filename:"sitemap--route-entry",bundlePath:""},distDir:".next",relativeProjectDir:"",resolvedPagePath:"[project]/src/app/sitemap--route-entry.js",nextConfigOutput:"export",userland:()=>e.r(87576),...{}}),{workAsyncStorage:v,workUnitAsyncStorage:b,serverHooks:k}=w;async function S(e,t,i){i.requestMeta&&(0,r.setRequestMeta)(e,i.requestMeta),w.isDev&&(0,r.addRequestMeta)(e,"devRequestTimingInternalsEnd",process.hrtime.bigint());let v="/sitemap.xml/route";v=v.replace(/\/index$/,"")||"/";let b=await w.prepare(e,t,{srcPage:v,multiZoneDraftMode:!1});if(!b)return t.statusCode=400,t.end("Bad Request"),null==i.waitUntil||i.waitUntil.call(i,Promise.resolve()),null;let{buildId:k,deploymentId:S,params:C,nextConfig:T,parsedUrl:A,isDraftMode:P,prerenderManifest:x,routerServerContext:I,isOnDemandRevalidate:D,revalidateOnlyGenerated:M,resolvedPathname:R,clientReferenceManifest:F,serverActionsManifest:E}=b,L=(0,n.normalizeAppPath)(v),q=!!(x.dynamicRoutes[L]||x.routes[R]),G=async()=>((null==I?void 0:I.render404)?await I.render404(e,t,A,!1):t.end("This page could not be found"),null);if(q&&!P){let e=!!x.routes[R],t=x.dynamicRoutes[L];if(t&&!1===t.fallback&&!e){if(T.adapterPath)return await G();throw new y.NoFallbackError}}let j=null;!q||w.isDev||P||(j="/index"===(j=R)?"/":j);let W=!0===w.isDev||!q,O=q&&!W;E&&F&&(0,s.setManifestsSingleton)({page:v,clientReferenceManifest:F,serverActionsManifest:E});let N=e.method||"GET",H=(0,o.getTracer)(),B=H.getActiveScopeSpan(),z=!!(null==I?void 0:I.isWrappedByNextServer),$=!!(0,r.getRequestMeta)(e,"minimalMode"),V=(0,r.getRequestMeta)(e,"incrementalCache")||await w.getIncrementalCache(e,T,x,$);null==V||V.resetRequestCache(),globalThis.__incrementalCache=V;let U={params:C,previewProps:x.preview,renderOpts:{experimental:{authInterrupts:!!T.experimental.authInterrupts,useCacheTimeout:T.experimental.useCacheTimeout},cacheComponents:!!T.cacheComponents,validationLevel:T.experimental.instantInsights.validationLevel,supportsDynamicResponse:W,incrementalCache:V,hmrRefreshHash:(0,r.getRequestMeta)(e,"hmrRefreshHash"),cacheLifeProfiles:T.cacheLife,staticPageGenerationTimeout:T.staticPageGenerationTimeout,waitUntil:i.waitUntil,onClose:e=>{t.on("close",e)},onAfterTaskError:void 0,onInstrumentationRequestError:(t,a,i,r)=>w.onRequestError(e,t,i,r,I)},sharedContext:{buildId:k,deploymentId:S}},_=new l.NodeNextRequest(e),K=new l.NodeNextResponse(t),Y=c.NextRequestAdapter.fromNodeNextRequest(_,(0,c.signalFromNodeResponse)(t)),Q=async({previousCacheEntry:a})=>{try{if(!$&&D&&M&&!a)return t.statusCode=404,t.setHeader("x-nextjs-cache","REVALIDATED"),t.end("This page could not be found"),null;let r=await w.handle(Y,U);e.fetchMetrics=U.renderOpts.fetchMetrics;let o=U.renderOpts.pendingWaitUntil;o&&i.waitUntil&&(i.waitUntil(o),o=void 0);let s=U.renderOpts.collectedTags;if(!q)return await (0,u.sendResponse)(_,K,r,o),null;{let e=await r.blob(),t=(0,p.toNodeOutgoingHttpHeaders)(r.headers);s&&(t[m.NEXT_CACHE_TAGS_HEADER]=s),!t["content-type"]&&e.type&&(t["content-type"]=e.type);let a=void 0!==U.renderOpts.collectedRevalidate&&!(U.renderOpts.collectedRevalidate>=m.INFINITE_CACHE)&&U.renderOpts.collectedRevalidate,i=void 0===U.renderOpts.collectedExpire||U.renderOpts.collectedExpire>=m.INFINITE_CACHE?!1!==a&&a>0?T.expireTime:void 0:U.renderOpts.collectedExpire;return{value:{kind:f.CachedRouteKind.APP_ROUTE,status:r.status,body:Buffer.from(await e.arrayBuffer()),headers:t},cacheControl:{revalidate:a,expire:i}}}}catch(t){throw(null==a?void 0:a.isStale)&&await w.onRequestError(e,t,{routerKind:"App Router",routePath:v,routeType:"route",revalidateReason:(0,h.getRevalidateReason)({isStaticGeneration:O,isOnDemandRevalidate:D})},!1,I),t}},J=async(r,s)=>{try{var n,l;let r=await w.handleResponse({req:e,nextConfig:T,cacheKey:j,routeKind:a.RouteKind.APP_ROUTE,isFallback:!1,prerenderManifest:x,isRoutePPREnabled:!1,isOnDemandRevalidate:D,revalidateOnlyGenerated:M,responseGenerator:Q,waitUntil:i.waitUntil,isMinimalMode:$});if(!q)return;if((null==r||null==(n=r.value)?void 0:n.kind)!==f.CachedRouteKind.APP_ROUTE)throw Object.defineProperty(Error(`Invariant: app-route received invalid cache entry ${null==r||null==(l=r.value)?void 0:l.kind}`),"__NEXT_ERROR_CODE",{value:"E701",enumerable:!1,configurable:!0});$||t.setHeader("x-nextjs-cache",D?"REVALIDATED":r.isMiss?"MISS":r.isStale?"STALE":"HIT"),P&&t.setHeader("Cache-Control","private, no-cache, no-store, max-age=0, must-revalidate");let o=(0,p.fromNodeOutgoingHttpHeaders)(r.value.headers);$&&q||o.delete(m.NEXT_CACHE_TAGS_HEADER),!r.cacheControl||t.getHeader("Cache-Control")||o.get("Cache-Control")||o.set("Cache-Control",(0,g.getCacheControlHeader)(r.cacheControl)),await (0,u.sendResponse)(_,K,new Response(r.value.body,{headers:o,status:r.value.status||200}));return}catch(t){if(t instanceof y.NoFallbackError||await w.onRequestError(e,t,{routerKind:"App Router",routePath:L,routeType:"route",revalidateReason:(0,h.getRevalidateReason)({isStaticGeneration:O,isOnDemandRevalidate:D})},!1,I),q)throw t;await (0,u.sendResponse)(_,K,new Response(null,{status:500}));return}finally{(()=>{if(!r)return;let e=t.statusCode;r.setAttributes({"http.status_code":e,"next.rsc":!1}),e&&e>=500&&(r.setStatus({code:o.SpanStatusCode.ERROR}),r.setAttribute("error.type",e.toString()));let a=H.getRootSpanAttributes();if(!a)return;if(a.get("next.span_type")!==d.BaseServerSpan.handleRequest)return console.warn(`Unexpected root span type '${a.get("next.span_type")}'. Please report this Next.js issue https://github.com/vercel/next.js`);let i=a.get("next.route")||L,n=`${N} ${i}`;r.setAttributes({"next.route":i,"http.route":i,"next.span_name":n}),r.updateName(n),s&&s!==r&&(s.setAttribute("http.route",i),s.updateName(n))})()}};if(z&&B)await J(B,void 0);else{let t=H.getActiveScopeSpan();await H.withPropagatedContext(e.headers,()=>H.trace(d.BaseServerSpan.handleRequest,{spanName:`${N} ${v}`,kind:o.SpanKind.SERVER,attributes:{"http.method":N,"http.target":e.url}},e=>J(e,t)),void 0,!z)}}e.s(["handler",0,S,"patchFetch",0,function(){return(0,i.patchFetch)({workAsyncStorage:v,workUnitAsyncStorage:b})},"routeModule",0,w,"serverHooks",0,k,"workAsyncStorage",0,v,"workUnitAsyncStorage",0,b])}];

//# sourceMappingURL=_17wvzoh._.js.map