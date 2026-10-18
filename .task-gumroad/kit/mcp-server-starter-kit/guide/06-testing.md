# 06 — Testing

Testing an MCP server does not require Claude Code running. The server is a standalone process and can be tested directly.

## Approach 1: Unit test your handlers

The cleanest approach: keep handler logic in pure functions, test them without any MCP infrastructure.

**Python:**
```python
# src/tools/calculator.py
async def handle_add(a: float, b: float) -> list[dict]:
    return [{"type": "text", "text": str(a + b)}]
```

```python
# tests/test_calculator.py
import pytest
from src.tools.calculator import handle_add

@pytest.mark.asyncio
async def test_add_integers():
    result = await handle_add(2, 3)
    assert result == [{"type": "text", "text": "5.0"}]

@pytest.mark.asyncio
async def test_add_floats():
    result = await handle_add(1.5, 2.5)
    assert result == [{"type": "text", "text": "4.0"}]
```

**TypeScript:**
```typescript
// src/tools/calculator.ts
export async function handleAdd(a: number, b: number) {
  return [{ type: "text" as const, text: String(a + b) }];
}
```

```typescript
// tests/calculator.test.ts
import { handleAdd } from "../src/tools/calculator.js";

test("adds two integers", async () => {
  const result = await handleAdd(2, 3);
  expect(result).toEqual([{ type: "text", text: "5" }]);
});
```

## Approach 2: MCP Inspector

Anthropic provides a CLI tool for interacting with any MCP server:

```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

This starts a local web UI where you can:
- Browse available tools, resources, and prompts
- Call tools with custom inputs
- Read resources
- Inspect the raw JSON-RPC messages

For Python:
```bash
npx @modelcontextprotocol/inspector python -m src.server
```

This is the fastest way to validate that your server starts correctly and that capabilities are registered as expected.

## Approach 3: Raw stdio testing

Since the protocol is newline-delimited JSON, you can test it with a script:

```python
# test_stdio.py
import subprocess
import json

proc = subprocess.Popen(
    ["python", "-m", "src.server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)

def send(msg: dict) -> dict:
    line = json.dumps(msg) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()
    response = proc.stdout.readline()
    return json.loads(response)

# Initialize
send({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "0.0.1"},
    },
})

# List tools
result = send({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {},
})
print(json.dumps(result, indent=2))

proc.terminate()
```

## Approach 4: Register in Claude Code and test interactively

Once basic tests pass, register the server in your project's `.mcp.json` and test it conversationally. Ask Claude to use specific tools and verify the results.

This is the integration test layer — it confirms that descriptions are clear enough for Claude to use the tools correctly.

## Common issues

**Server fails to start**
Check that all imports resolve, environment variables are set, and the entry point exists. Run the server directly from the command line to see startup errors on stderr.

**Tools don't appear in Claude Code**
Verify the `capabilities` declaration includes `"tools": {}` during initialization. With FastMCP and the TypeScript McpServer class this is automatic.

**Tool is called with wrong arguments**
Improve the parameter descriptions. Add examples in the description. Narrow the types (e.g., change `string` to an enum if there are fixed choices).

**Output corrupts the protocol**
Check for any print statements or log output going to stdout. Move everything to stderr.

**Async errors are swallowed**
Ensure your async handlers bubble up exceptions rather than catching and ignoring them. The SDK needs to receive the exception to report `isError: true`.

## Running tests

**Python:**
```bash
# Install dev dependencies
uv sync --dev   # or: pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing
```

**TypeScript:**
```bash
npm install
npm run build
npx jest                    # if using Jest
npx vitest                  # if using Vitest
```

Next: [Deployment](07-deployment.md).
