# n8n AI Workflow Templates

5 importable n8n workflows that connect AI to real business processes.

## What's Inside

- **guide.md** -- 12-chapter, ~5,000-word setup and customization guide with 5 mermaid diagrams
- **workflows/** -- 5 importable JSON files (YouTube monitor, RSS intelligence, content digest, health checks, AI code review)
- **docker/** -- Docker Compose setup with Postgres, env template, and start script

## Quick Start

```bash
# 1. Copy docker/ directory and configure
cp docker/.env.example docker/.env
# Edit .env with your API keys

# 2. Start n8n
cd docker/ && bash start.sh

# 3. Import workflows
# Open http://localhost:5678 -> New Workflow -> Import from file
# Select any JSON from workflows/
```

## Prerequisites

- Docker and Docker Compose
- API key for at least one LLM (Gemini, OpenAI, or Anthropic)
- 30 minutes for initial setup

## Workflows

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| YouTube Monitor | Weekly cron | Monitors channels, AI summarizes, emails digest |
| RSS Intelligence | Every 6h | Aggregates feeds, scores relevance, sends high-signal items |
| Content Digest | Weekly cron | Reads saved articles, generates categorized digest |
| Health Check | Every 5min | Monitors service endpoints, alerts on downtime |
| AI Code Review | GitHub webhook | Reviews PR diffs, posts findings as comments |

## Version

1.1.0 -- April 2026. See CHANGELOG.md for the full list of fixes from 1.0.0.
