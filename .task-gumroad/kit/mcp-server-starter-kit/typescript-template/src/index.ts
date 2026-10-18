/**
 * MCP Server Template — Entry Point
 *
 * Wires together tools and resources, then starts the server over stdio.
 * Claude Code launches this process and communicates via stdin/stdout.
 *
 * To add a tool:
 *   1. Create a file in src/tools/
 *   2. Import the definition here
 *   3. Call server.tool() with it
 *
 * To add a resource:
 *   1. Create a file in src/resources/
 *   2. Import and register below
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import {
  exampleToolDefinition,
  handleExampleTool,
  ExampleToolInputSchema,
} from "./tools/example-tool.js";
import {
  staticResourceDefinition,
  handleStaticResource,
  templateResourceDefinition,
  handleTemplateResource,
} from "./resources/example-resource.js";

// ──────────────────────────────────────────────
// Server setup
// ──────────────────────────────────────────────

const server = new McpServer({
  name: "mcp-server-template",
  version: "0.1.0",
});

// ──────────────────────────────────────────────
// Register tools
// ──────────────────────────────────────────────

server.tool(
  exampleToolDefinition.name,
  exampleToolDefinition.description,
  ExampleToolInputSchema.shape,
  async (input) => {
    const content = await handleExampleTool(
      ExampleToolInputSchema.parse(input)
    );
    return { content };
  }
);

// ──────────────────────────────────────────────
// Register static resources
// ──────────────────────────────────────────────

server.resource(
  staticResourceDefinition.name,
  staticResourceDefinition.uri,
  { mimeType: staticResourceDefinition.mimeType },
  async () => {
    const text = await handleStaticResource();
    return {
      contents: [
        {
          uri: staticResourceDefinition.uri,
          mimeType: staticResourceDefinition.mimeType,
          text,
        },
      ],
    };
  }
);

// ──────────────────────────────────────────────
// Register resource templates
// ──────────────────────────────────────────────

server.resource(
  templateResourceDefinition.name,
  templateResourceDefinition.uriTemplate,
  { mimeType: templateResourceDefinition.mimeType },
  async (uri) => {
    const text = await handleTemplateResource(uri.href);
    return {
      contents: [
        {
          uri: uri.href,
          mimeType: templateResourceDefinition.mimeType,
          text,
        },
      ],
    };
  }
);

// ──────────────────────────────────────────────
// Start server
// ──────────────────────────────────────────────

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Write to stderr only — stdout is reserved for MCP protocol messages.
  process.stderr.write("MCP server started\n");
}

main().catch((err) => {
  process.stderr.write(`Fatal error: ${err}\n`);
  process.exit(1);
});
