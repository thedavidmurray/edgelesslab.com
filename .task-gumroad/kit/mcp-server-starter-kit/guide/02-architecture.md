# 02 — Architecture

## Connection lifecycle

When Claude Code starts, it reads `.mcp.json` (or `~/.claude.json`) and launches each registered MCP server as a child process. The startup sequence:

```
Claude Code starts
  → reads .mcp.json
  → for each server: spawn child process
  → send initialize request
  → receive server capabilities
  → send initialized notification
  → session begins
```

From that point, Claude can call tools, read resources, or request prompts at any time during the session. When Claude Code exits, it sends a shutdown notification and the server process terminates.

## Process isolation

Each MCP server runs in its own process. This means:

- A crash in your server does not crash Claude Code
- You can restart a server independently
- Servers cannot share memory with each other (use a shared database or file if needed)

## stdio transport in detail

For stdio transport, the protocol runs over the process's stdin and stdout streams. Each message is a JSON object followed by a newline character.

```
[parent process: Claude Code]
         |
  stdin  |  stdout
   ↓     |     ↑
[child process: your MCP server]
```

Critical rule: **never write anything to stdout except MCP protocol messages**. Any stray output (print statements, log lines) will corrupt the protocol stream and break the connection. Write all debug output to stderr.

```python
# Wrong — breaks the protocol
print("Debug: processing request")

# Right
import sys
print("Debug: processing request", file=sys.stderr)
```

In TypeScript:
```typescript
// Wrong
console.log("Debug: processing request");

// Right
process.stderr.write("Debug: processing request\n");
```

## Capability negotiation

During initialization, your server declares what it supports:

```json
{
  "capabilities": {
    "tools": {},
    "resources": {},
    "prompts": {}
  }
}
```

Each key signals that the server has that capability type. Claude Code will then call `tools/list`, `resources/list`, and `prompts/list` to enumerate them.

The SDK handles this automatically based on what you register. If you register no resources, the resources capability is omitted.

## Request handling flow

For a tool call:

```
Claude decides to call a tool
  → Claude Code sends tools/call request
  → Your server receives it
  → Your handler function runs
  → Handler returns content or throws an error
  → SDK sends response back to Claude Code
  → Claude Code delivers result to Claude
```

The SDK handles threading and queuing. Your handlers can be async. The SDK will await them.

## Environment variables

Environment variables are the right way to pass configuration (API keys, database paths) to an MCP server. Set them in `.mcp.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {
        "DATABASE_URL": "sqlite:///path/to/db.sqlite",
        "API_KEY": "your-key-here"
      }
    }
  }
}
```

Do not hardcode secrets in source code. Read them from environment variables in your server startup code.

## File layout

There is no required file layout. The templates use this structure as a convention:

```
src/
  index.ts (or server.py)   — server setup, registration, entry point
  tools/                    — one file per tool (or logical group)
  resources/                — one file per resource (or logical group)
  prompts/                  — one file per prompt template (optional)
```

This keeps registration logic separate from implementation logic. As your server grows, you can import and register new capabilities without touching existing files.

Next: [Building Tools](03-building-tools.md).
