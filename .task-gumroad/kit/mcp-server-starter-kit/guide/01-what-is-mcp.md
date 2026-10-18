# 01 — What Is MCP

MCP stands for **Model Context Protocol**. It is an open protocol that lets language models communicate with external processes in a structured way.

Before MCP, giving a model access to external data or actions required custom integrations per tool. Every model, every vendor, every use case needed its own glue code. MCP standardizes this.

## The core idea

An MCP server is a process that exposes capabilities to a model via a defined protocol. The model (Claude) connects to the server, asks what capabilities it has, and then calls them as needed.

Three capability types:

| Type | What it is | Example |
|------|-----------|---------|
| **Tool** | A function Claude can call | `search_files(query)` |
| **Resource** | Content Claude can read | `file:///docs/README.md` |
| **Prompt** | A reusable prompt template | `summarize_document(doc_id)` |

## How it fits into Claude Code

Claude Code is Anthropic's CLI. When you register an MCP server in `.mcp.json`, Claude Code starts the server process at launch and keeps a persistent connection to it via stdio. During a session, Claude can call tools on the server, read resources from it, or use prompt templates from it.

From Claude's perspective, your MCP server's tools appear alongside built-in capabilities like Read, Write, and Bash. Claude decides when to call them based on their descriptions.

## Transport

MCP supports two transports:

**stdio** (default) — Claude Code launches your server as a child process. Communication happens over stdin/stdout as newline-delimited JSON. This is the simplest deployment model and what both templates use.

**HTTP + SSE** — Your server listens on an HTTP port. Useful when multiple clients connect, or when the server runs on a remote machine. Not covered in depth here; see the MCP SDK docs for server-sent events setup.

## Protocol overview

The protocol is JSON-RPC 2.0. Requests look like:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_files",
    "arguments": { "query": "authentication" }
  }
}
```

You do not need to write JSON-RPC by hand. The SDK handles framing, dispatch, and serialization. You write handler functions; the SDK handles the rest.

## What makes a good MCP server

A good MCP server:

1. Does one thing well — avoid building a monolith
2. Has descriptions that are precise enough for Claude to know when to use each tool
3. Returns structured data when the caller needs to parse it, plain text when it does not
4. Fails loudly with clear error messages rather than silently returning empty results
5. Starts fast — Claude Code starts it on every session launch

Next: [Architecture](02-architecture.md) — how the connection lifecycle works.
