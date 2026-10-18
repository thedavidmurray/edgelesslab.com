/**
 * Example tool implementation.
 *
 * A tool is a function Claude can call. It has:
 *  - a name (string, snake_case recommended)
 *  - a description Claude uses to decide when to call it
 *  - an inputSchema defining the parameters
 *  - a handler that executes when Claude calls the tool
 */

import { z } from "zod";

// Define the input schema using Zod for runtime validation.
// The MCP SDK converts this to JSON Schema for Claude automatically.
export const ExampleToolInputSchema = z.object({
  message: z.string().describe("The message to echo back"),
  repeat: z
    .number()
    .int()
    .min(1)
    .max(10)
    .optional()
    .default(1)
    .describe("How many times to repeat the message (1–10)"),
});

export type ExampleToolInput = z.infer<typeof ExampleToolInputSchema>;

/**
 * Tool handler — receives validated input, returns content blocks.
 *
 * Return types:
 *  - { type: "text", text: string }         — plain text
 *  - { type: "image", data: string, mimeType: string } — base64 image
 *  - { type: "resource", resource: { uri, text } }    — embedded resource
 *
 * Throw an error to signal failure. The MCP SDK wraps it as isError: true.
 */
export async function handleExampleTool(
  input: ExampleToolInput
): Promise<{ type: "text"; text: string }[]> {
  const lines: string[] = [];

  for (let i = 0; i < input.repeat; i++) {
    lines.push(input.message);
  }

  return [
    {
      type: "text",
      text: lines.join("\n"),
    },
  ];
}

/**
 * Tool definition — passed to server.tool() in index.ts.
 */
export const exampleToolDefinition = {
  name: "example_echo",
  description:
    "Echoes a message back, optionally repeated. Use this to test that the server is working.",
  inputSchema: ExampleToolInputSchema,
  handler: handleExampleTool,
} as const;
