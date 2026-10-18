# 07 — Deployment

## stdio (default)

stdio is the simplest deployment. Claude Code launches your server as a child process on every session start.

**TypeScript `.mcp.json`:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/dist/index.js"],
      "env": {
        "DATABASE_URL": "sqlite:///Users/you/data/app.db",
        "API_KEY": "your-key"
      }
    }
  }
}
```

**Python `.mcp.json`:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/python-template",
      "env": {
        "DATABASE_URL": "sqlite:///Users/you/data/app.db"
      }
    }
  }
}
```

Always use absolute paths. Relative paths depend on Claude Code's working directory which may not be where you expect.

### Using uv (recommended for Python)

`uv` handles virtual environment activation automatically:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--project", "/absolute/path/to/python-template", "python", "-m", "src.server"]
    }
  }
}
```

### Using npx (TypeScript, no build step)

For TypeScript packages published to npm:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "your-mcp-package-name"]
    }
  }
}
```

## Config file locations

`.mcp.json` can live in two places:

| Location | Scope |
|----------|-------|
| `~/.claude.json` (under `mcpServers` key) | All Claude Code sessions for the user |
| `.mcp.json` in project directory | That project only |

Project-level config is checked into version control and shared with collaborators. User-level config stays on your machine.

## Docker deployment

Docker is useful when your server has complex dependencies or you want reproducible builds.

**Dockerfile (Python):**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install uv && uv pip install --system -e .

CMD ["python", "-m", "src.server"]
```

**Dockerfile (TypeScript):**
```dockerfile
FROM node:22-slim

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY dist/ dist/

CMD ["node", "dist/index.js"]
```

**`.mcp.json` with Docker:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "docker",
      "args": ["run", "--rm", "-i",
        "-e", "DATABASE_URL",
        "-v", "/Users/you/data:/data",
        "my-mcp-server:latest"
      ],
      "env": {
        "DATABASE_URL": "sqlite:///data/app.db"
      }
    }
  }
}
```

`-i` is required for stdin to work. `--rm` removes the container after the session ends.

## HTTP transport (advanced)

HTTP transport is useful when:
- Multiple clients connect to the same server
- The server runs on a remote machine
- You need persistent state between sessions

**Python (FastMCP HTTP mode):**
```python
# Change the run call in server.py
mcp.run(transport="sse", host="0.0.0.0", port=8080)
```

**`.mcp.json` for HTTP:**
```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

HTTP transport requires you to manage the server process separately (keep it running, handle restarts). Use a process manager like pm2, systemd, or Docker.

## Publishing to npm

To share a TypeScript MCP server:

```json
// package.json additions
{
  "bin": {
    "my-mcp-server": "dist/index.js"
  },
  "files": ["dist/"],
  "publishConfig": { "access": "public" }
}
```

Add `#!/usr/bin/env node` to the top of `dist/index.js` (or the source `src/index.ts` before compiling).

Then users can run it with `npx`:
```json
{
  "command": "npx",
  "args": ["-y", "my-mcp-server"]
}
```

## Security considerations

- Validate all tool inputs rigorously. An MCP server that accepts file paths can be tricked into reading arbitrary files if it does not validate the path.
- Scope file access: if your server reads files, restrict it to a specific directory. Reject paths containing `..`.
- Treat environment variables as secrets. Do not log them or return them through tools.
- For HTTP transport, add authentication (e.g., a shared API key in a header) if the server is accessible beyond localhost.
- Limit tool side effects to what the user explicitly authorizes. When in doubt, add a confirmation parameter.

Next: [Recipes](08-recipes.md).
