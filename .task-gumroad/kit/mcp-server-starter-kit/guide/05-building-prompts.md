# 05 — Building Prompts

Prompt templates are reusable system prompts or message sequences that users (or Claude) can invoke by name. They are the least commonly used MCP capability but useful for standardizing complex workflows.

## When to use prompts

Prompt templates are useful when:

- You have a complex workflow that always requires a specific framing or persona
- You want users to be able to invoke a multi-step analysis with a short command
- You need to inject structured context (documents, data) into a conversation starter

They are not a replacement for instructions. Think of them as shortcuts to a well-defined starting state.

## Structure

A prompt template has:
- A **name** (used to invoke it)
- A **description** (shown to the user in Claude Code's prompt picker)
- Optional **arguments** (filled in by the user or Claude)
- A **handler** that returns one or more messages

## TypeScript example

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "0.1.0" });

server.prompt(
  "code_review",
  "Review a code snippet for correctness, style, and potential issues.",
  {
    code: z.string().describe("The code to review"),
    language: z.string().optional().describe("Programming language (optional)"),
  },
  async ({ code, language }) => {
    const langNote = language ? ` The code is written in ${language}.` : "";
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Please review the following code.${langNote} Focus on correctness, edge cases, and any style issues.\n\n\`\`\`\n${code}\n\`\`\``,
          },
        },
      ],
    };
  }
);
```

## Python example (FastMCP)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.prompt()
def code_review(code: str, language: str = "") -> str:
    """
    Review a code snippet for correctness, style, and potential issues.

    Args:
        code: The code to review.
        language: Programming language (optional).
    """
    lang_note = f" The code is written in {language}." if language else ""
    return (
        f"Please review the following code.{lang_note} "
        f"Focus on correctness, edge cases, and style issues.\n\n"
        f"```\n{code}\n```"
    )
```

FastMCP handles wrapping the return string into the correct message format.

## Prompts with resource context

A prompt can embed resources to give Claude context alongside instructions:

```typescript
server.prompt(
  "summarize_doc",
  "Summarize a document from the knowledge base",
  { doc_id: z.string() },
  async ({ doc_id }) => {
    const doc = await loadDocument(doc_id);
    return {
      messages: [
        {
          role: "user",
          content: [
            {
              type: "resource",
              resource: {
                uri: `docs://${doc_id}`,
                mimeType: "text/markdown",
                text: doc.content,
              },
            },
            {
              type: "text",
              text: "Summarize the document above in 3–5 bullet points.",
            },
          ],
        },
      ],
    };
  }
);
```

## Invoking prompts

In Claude Code, users can invoke a prompt with:

```
/mcp my-server code_review
```

Claude Code will prompt for any required arguments, then inject the resulting messages into the conversation.

## Design guidelines

Keep prompts focused. A prompt that tries to handle every scenario becomes unwieldy. Build multiple targeted prompts rather than one large one with many branches.

Validate arguments in the handler and raise clear errors for missing or invalid inputs.

Prompts are not tools — they do not return results to Claude as tool output. They set up the conversation. Do not use prompts for operations that should be tool calls.

Next: [Testing](06-testing.md).
