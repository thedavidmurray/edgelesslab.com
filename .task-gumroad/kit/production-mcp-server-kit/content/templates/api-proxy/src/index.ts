/**
 * Production MCP Server Template -- API Proxy
 *
 * Wraps an external REST API with auth, rate limiting,
 * caching, and error sanitization.
 *
 * Usage:
 *   EXTERNAL_API_KEY=your-key bun run src/index.ts
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// ============================================================
// CONFIG
// ============================================================

const config = {
  apiKey: process.env.EXTERNAL_API_KEY || "",
  apiBaseUrl: process.env.API_BASE_URL || "https://api.example.com/v1",
  rateLimit: parseInt(process.env.RATE_LIMIT || "100"),
  rateLimitWindow: parseInt(process.env.RATE_WINDOW || "60000"),
  cacheTtl: parseInt(process.env.CACHE_TTL || "300000"),
};

if (!config.apiKey) {
  console.error("Error: EXTERNAL_API_KEY environment variable is required");
  process.exit(1);
}

// ============================================================
// RATE LIMITER
// ============================================================

const rateLimiter = new Map<string, { count: number; reset: number }>();

function checkRateLimit(key: string): boolean {
  const now = Date.now();
  const entry = rateLimiter.get(key) || { count: 0, reset: now + config.rateLimitWindow };

  if (now > entry.reset) {
    entry.count = 0;
    entry.reset = now + config.rateLimitWindow;
  }

  entry.count++;
  rateLimiter.set(key, entry);
  return entry.count <= config.rateLimit;
}

// ============================================================
// RESPONSE CACHE
// ============================================================

const cache = new Map<string, { data: unknown; expires: number }>();

function getCached(key: string): unknown | null {
  const entry = cache.get(key);
  if (entry && Date.now() < entry.expires) return entry.data;
  cache.delete(key);
  return null;
}

function setCache(key: string, data: unknown): void {
  // Evict oldest entries if cache is too large
  if (cache.size > 1000) {
    const oldest = [...cache.entries()].sort((a, b) => a[1].expires - b[1].expires);
    for (let i = 0; i < 100; i++) cache.delete(oldest[i][0]);
  }
  cache.set(key, { data, expires: Date.now() + config.cacheTtl });
}

// ============================================================
// ERROR SANITIZATION
// ============================================================

export const SECRET_PATTERNS = [
  /sk-[a-zA-Z0-9]{20,}/g,
  /Bearer\s+[a-zA-Z0-9_.+-]+/g,
  /api[_-]?key[=:]\s*\S+/gi,
  /ghp_[a-zA-Z0-9]{36}/g,
  /AKIA[0-9A-Z]{16}/g,
  // JWT tokens (eyJ... header.payload.signature)
  /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,
];

export function sanitizeError(error: unknown): string {
  let message = error instanceof Error ? error.message : String(error);
  for (const pattern of SECRET_PATTERNS) {
    message = message.replace(pattern, "[REDACTED]");
  }
  return message;
}

// ============================================================
// API CLIENT
// ============================================================

function apiHeaders(): Record<string, string> {
  return {
    "Authorization": `Bearer ${config.apiKey}`,
    "Content-Type": "application/json",
  };
}

async function apiCall(path: string, body?: unknown): Promise<unknown> {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    method: body ? "POST" : "GET",
    headers: apiHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// ============================================================
// SERVER
// ============================================================

const server = new Server(
  { name: "api-proxy-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "query",
      description: "Query the external API",
      inputSchema: {
        type: "object",
        properties: {
          endpoint: {
            type: "string",
            description: "API endpoint path (e.g., /search)",
          },
          params: {
            type: "object",
            description: "Query parameters",
          },
        },
        required: ["endpoint"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name !== "query") {
    return {
      content: [{ type: "text", text: `Unknown tool: ${name}` }],
      isError: true,
    };
  }

  // Rate limit check
  if (!checkRateLimit("api")) {
    return {
      content: [{
        type: "text",
        text: `Rate limited. Max ${config.rateLimit} requests per ${config.rateLimitWindow / 1000}s.`,
      }],
      isError: true,
    };
  }

  // Cache check
  const cacheKey = JSON.stringify(args);
  const cached = getCached(cacheKey);
  if (cached) {
    return cached as { content: Array<{ type: string; text: string }> };
  }

  try {
    const data = await apiCall(
      (args as { endpoint: string }).endpoint,
      (args as { params?: unknown }).params
    );

    const result = {
      content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
    };

    setCache(cacheKey, result);
    return result;
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${sanitizeError(error)}` }],
      isError: true,
    };
  }
});

// Start
const transport = new StdioServerTransport();
await server.connect(transport);
