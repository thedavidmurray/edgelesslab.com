# MCP Server Starter Kit

**Edgeless Labs LLC** — Build MCP servers for Claude Code in TypeScript or Python.

---

## What You Get

- **TypeScript template** — fully typed, ready to run in under 5 minutes
- **Python template** — minimal dependencies, works with `uv` or `pip`
- **Guide** — 8 chapters covering every MCP concept with working examples
- **3 working example servers** — file search, SQLite queries, REST API proxy

## Quick Start

### TypeScript

```bash
cd typescript-template
npm install
npm run build
npm start
```

Register with Claude Code by adding to your `.mcp.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["dist/index.js"]
    }
  }
}
```

### Python

```bash
cd python-template
uv sync          # or: pip install -e .
python -m src.server
```

Register with Claude Code:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/python-template"
    }
  }
}
```

---

## Guide

| Chapter | What It Covers |
|---------|---------------|
| [01 — What Is MCP](guide/01-what-is-mcp.md) | Protocol overview, why it matters |
| [02 — Architecture](guide/02-architecture.md) | How servers connect to Claude Code |
| [03 — Building Tools](guide/03-building-tools.md) | Tool definitions, parameters, responses |
| [04 — Building Resources](guide/04-building-resources.md) | Resource URIs, templates, content types |
| [05 — Building Prompts](guide/05-building-prompts.md) | Prompt templates, arguments |
| [06 — Testing](guide/06-testing.md) | Local testing without Claude Code |
| [07 — Deployment](guide/07-deployment.md) | stdio vs HTTP, Docker, production |
| [08 — Recipes](guide/08-recipes.md) | 10 practical MCP server ideas |

---

## Examples

| Example | What It Demonstrates |
|---------|---------------------|
| [file-search-server](examples/file-search-server/) | Read files, search content, list directories |
| [database-query-server](examples/database-query-server/) | Query SQLite, return structured data |
| [api-proxy-server](examples/api-proxy-server/) | Wrap any REST API as MCP tools |

---

## Requirements

**TypeScript**: Node.js 18+, npm or pnpm
**Python**: Python 3.11+, uv (recommended) or pip

---

## License

MIT — Copyright 2026 Edgeless Labs LLC. See [LICENSE](LICENSE).
