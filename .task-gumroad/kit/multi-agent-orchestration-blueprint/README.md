# Multi-Agent Orchestration Blueprint

The dispatch/worker architecture for coordinating multiple AI agents. Agent Bus messaging, async inboxes, state machines, and 3 reference implementations from a system that runs 5 agents 24/7.

## What's Inside

- **guide.md / guide.pdf** -- 9-chapter guide + appendices: dispatch/worker topology, Agent Bus protocol with lease-based delivery, async inbox system, state machines, 3 reference implementations, operational patterns
- **reference-implementations/** -- 3 complete, runnable implementations:
  - `dispatch-worker/` -- Coordinator + N workers with file-based inboxes (Python)
  - `message-bus/` -- SQLite-backed message router hub (TypeScript/Bun)
  - `pipeline-orchestrator/` -- Linear pipeline with checkpoint recovery (Python)
- **patterns/** -- Reusable patterns: graceful shutdown, event logging
- **configs/** -- Hub configuration template

## Quick Start

### 1. Dispatch/Worker (Python, no dependencies)

```bash
cd reference-implementations/dispatch-worker

# Create inbox directories
mkdir -p .inboxes/dispatch/inbox .inboxes/worker-content/inbox

# Start dispatch (routes tasks to workers)
python dispatch.py --workers workers.json &

# Start a worker (claims and processes tasks)
python worker.py --name worker-content --inbox .inboxes/worker-content/inbox &

# Drop a task into dispatch's inbox
cat > .inboxes/dispatch/inbox/2026-04-02T14-00-00-task-rss.md << 'EOF'
---
id: rss-digest-001
title: Generate RSS digest
status: queued
priority: normal
---
## Task: Generate RSS Digest
Process RSS feeds and send summary.
EOF
```

### 2. Message Bus Hub (requires Bun)

```bash
cd reference-implementations/message-bus
bun install
bun run hub.ts  # Starts on port 9800

# In another terminal:
curl -X POST http://localhost:9800/register -d '{"name": "dispatch"}'
curl -X POST http://localhost:9800/send -d '{"from": "dispatch", "to": "worker-1", "content": "hello"}'
curl http://localhost:9800/poll/worker-1
```

### 3. Pipeline Orchestrator (Python, no dependencies)

```bash
cd reference-implementations/pipeline-orchestrator

# Create input data
echo '{"feeds": ["https://example.com/feed.xml"]}' > input.json

# Run pipeline
python pipeline.py --config pipeline.json --input input.json --output result.json
```

## Prerequisites

- Python 3.10+ (dispatch/worker, pipeline)
- Bun 1.0+ (message bus hub)
- No external pip dependencies for Python components

## File Structure

```
multi-agent-blueprint/
  guide.md                           -- Full 9-chapter guide + appendices
  guide.pdf                          -- PDF version
  reference-implementations/
    dispatch-worker/
      dispatch.py                    -- Coordinator agent
      worker.py                      -- Worker agent template
      workers.json                   -- Worker definitions
    message-bus/
      hub.ts                         -- Hub server (Bun + SQLite)
      client.ts                      -- TypeScript client library
      schema.sql                     -- Database schema
      package.json
    pipeline-orchestrator/
      pipeline.py                    -- Pipeline executor with checkpoints
      pipeline.json                  -- Example pipeline config
  patterns/
    graceful-shutdown.py             -- Worker shutdown handler
    event-log.py                     -- JSONL event logging
  configs/
    hub-config.env                   -- Hub environment template
  README.md
  CHANGELOG.md
```

## Version

1.0.0 -- Initial release, April 2026
