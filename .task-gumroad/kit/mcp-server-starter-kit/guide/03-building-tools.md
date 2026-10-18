# 03 — Building Tools

Tools are what makes MCP servers useful. They let Claude take actions and retrieve data on demand.

## Anatomy of a tool

Every tool has four parts:

1. **Name** — The identifier. Use snake_case. Must be unique within your server.
2. **Description** — How Claude decides when to call this tool. Write it from Claude's perspective: "Use this when you need to…"
3. **Input schema** — Defines the parameters. Claude reads this to know what arguments to provide.
4. **Handler** — The function that executes when Claude calls the tool.

## Writing descriptions

The description is the most important part. A vague description leads to Claude calling the wrong tool or not calling it when it should.

Bad:
```
"Searches files"
```

Good:
```
"Search for files matching a glob pattern in a directory.
Returns a list of matching file paths with their sizes and
modification times. Use this when the user wants to find
files by name pattern or extension."
```

Include:
- What the tool does
- What it returns
- When to use it (and optionally when not to)

## Input schema

### TypeScript — Zod

The TypeScript template uses Zod for schema definition. The SDK converts it to JSON Schema automatically.

```typescript
import { z } from "zod";

const SearchInputSchema = z.object({
  directory: z.string().describe("Absolute path to search in"),
  pattern: z.string().describe("Glob pattern, e.g. '**/*.ts'"),
  max_results: z
    .number()
    .int()
    .min(1)
    .max(100)
    .optional()
    .default(20)
    .describe("Maximum number of results to return"),
});
```

### Python — type annotations (FastMCP)

FastMCP generates the JSON Schema from your function signature and docstring:

```python
@mcp.tool()
async def search_files(
    directory: str,
    pattern: str,
    max_results: int = 20,
) -> str:
    """
    Search for files matching a glob pattern.

    Args:
        directory: Absolute path to search in.
        pattern: Glob pattern, e.g. '**/*.ts'.
        max_results: Maximum number of results (1–100).
    """
    ...
```

### Python — explicit JSON Schema

If you need more control, pass a schema dict:

```python
from mcp.server import Server
from mcp.types import Tool

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_files",
            description="Search for files matching a glob pattern.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "pattern": {"type": "string"},
                },
                "required": ["directory", "pattern"],
            },
        )
    ]
```

## Return values

Tool handlers return a list of content blocks. Each block has a type.

**Text**
```python
return [{"type": "text", "text": "Found 3 files."}]
```

**Structured data** — return JSON as text when the caller needs to parse it:
```python
import json
results = [{"path": "/a/b.ts", "size": 1234}]
return [{"type": "text", "text": json.dumps(results)}]
```

**Image** (TypeScript):
```typescript
import fs from "fs";
const imageData = fs.readFileSync("chart.png").toString("base64");
return [{ type: "image", data: imageData, mimeType: "image/png" }];
```

**Multiple blocks** — mix text and images:
```python
return [
    {"type": "text", "text": "Here is the chart:"},
    {"type": "image", "data": base64_data, "mimeType": "image/png"},
]
```

## Error handling

Throw (TypeScript) or raise (Python) any exception to signal failure. The SDK sets `isError: true` in the response and passes your error message to Claude.

```python
async def handle_search(directory: str, pattern: str) -> list:
    if not os.path.isabs(directory):
        raise ValueError(f"directory must be an absolute path, got: {directory}")
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    ...
```

Do not return error messages as successful responses. Raise exceptions so Claude knows the tool failed and can react accordingly.

## Tool design guidelines

**One tool, one purpose.** A tool that does five different things based on a `mode` parameter is hard for Claude to use correctly. Create five tools instead.

**Return what Claude needs, not everything.** If a search returns 10,000 results, Claude cannot use all of them. Return the top N with a `total_count` field so Claude knows there are more.

**Be idempotent where possible.** Tools that can be safely called twice without side effects are safer. When a tool has side effects (writes, deletes, sends requests), say so in the description.

**Validate inputs early.** Check required fields, value ranges, and path safety before doing any real work. Fail fast with a clear message.

**Keep latency reasonable.** Tools that take more than a few seconds will degrade the user experience. For slow operations, consider returning a job ID and providing a second tool to check status.

Next: [Building Resources](04-building-resources.md).
