/**
 * Example resource implementation.
 *
 * A resource is a piece of content Claude can read. Resources have:
 *  - a URI (string) that uniquely identifies them
 *  - a name and optional description
 *  - a mimeType
 *  - content returned by a handler
 *
 * Resources can be static (fixed URI) or dynamic (URI templates with parameters).
 *
 * Static example: "config://app/settings"
 * Template example: "file://{path}" where {path} is filled in by Claude
 */

// ──────────────────────────────────────────────
// Static resource — fixed URI, no parameters
// ──────────────────────────────────────────────

export const staticResourceDefinition = {
  uri: "example://status",
  name: "Server Status",
  description: "Current status and uptime of the MCP server",
  mimeType: "application/json",
} as const;

export async function handleStaticResource(): Promise<string> {
  const status = {
    status: "ok",
    startedAt: new Date().toISOString(),
    version: "0.1.0",
  };
  return JSON.stringify(status, null, 2);
}

// ──────────────────────────────────────────────
// Template resource — parameterized URI
// ──────────────────────────────────────────────
// URI template follows RFC 6570: "example://items/{id}"
// Claude fills in {id} based on context or user request.

export const templateResourceDefinition = {
  uriTemplate: "example://items/{id}",
  name: "Example Item",
  description:
    "Retrieve a named item by ID. Replace {id} with the item identifier.",
  mimeType: "application/json",
} as const;

export async function handleTemplateResource(
  uri: string
): Promise<string> {
  // Parse the ID out of the URI.
  const match = uri.match(/^example:\/\/items\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid resource URI: ${uri}`);
  }
  const id = match[1];

  // In a real server, look up the item from a database or API.
  const item = {
    id,
    name: `Item ${id}`,
    createdAt: new Date().toISOString(),
    data: "Replace this with real data from your data source",
  };

  return JSON.stringify(item, null, 2);
}
