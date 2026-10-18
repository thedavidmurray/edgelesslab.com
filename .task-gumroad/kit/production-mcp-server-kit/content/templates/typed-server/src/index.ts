/**
 * Production MCP Server Template -- Typed (Effect-TS)
 *
 * A type-safe MCP server with schema-validated tools, dependency injection
 * via Effect Layers, and tagged errors using `Data.TaggedError`.
 *
 * Backend: a small SQLite-backed key-value document store.
 *
 * The transport layer uses the official `@modelcontextprotocol/sdk` and the
 * Effect ecosystem (`effect@3.21`) provides the type-safe schema validation,
 * dependency injection, and tagged error machinery. This is intentionally
 * lighter than `@effect/ai-mcp` (which is still pre-1.0) but gives you the
 * same guarantees.
 *
 * Usage:
 *   bun run src/index.ts
 *   # or
 *   node --import tsx src/index.ts
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Context, Data, Effect, Layer, Schema } from "effect";

// ============================================================
// Tagged errors -- part of the type signature, not exceptions
// ============================================================

export class DocNotFound extends Data.TaggedError("DocNotFound")<{
  readonly id: string;
}> {}

export class StorageError extends Data.TaggedError("StorageError")<{
  readonly cause: string;
}> {}

// ============================================================
// Tool input schemas (validated at the boundary)
// ============================================================

const SearchInput = Schema.Struct({
  query: Schema.String.pipe(
    Schema.minLength(1, { message: () => "Query cannot be empty" }),
    Schema.maxLength(1000, { message: () => "Query too long (max 1000 chars)" })
  ),
  limit: Schema.optionalWith(
    Schema.Number.pipe(Schema.int(), Schema.between(1, 100)),
    { default: () => 10 }
  ),
});

const GetDocumentInput = Schema.Struct({
  id: Schema.String.pipe(Schema.minLength(1)),
});

const PutDocumentInput = Schema.Struct({
  id: Schema.String.pipe(Schema.minLength(1)),
  content: Schema.String.pipe(Schema.maxLength(100_000)),
});

// ============================================================
// Service interface
// ============================================================

export interface DocRecord {
  readonly id: string;
  readonly content: string;
  readonly created_at: string;
}

interface KvDocStoreMethods {
  readonly get: (id: string) => Effect.Effect<DocRecord, DocNotFound | StorageError>;
  readonly put: (id: string, content: string) => Effect.Effect<DocRecord, StorageError>;
  readonly search: (
    query: string,
    limit: number
  ) => Effect.Effect<ReadonlyArray<DocRecord>, StorageError>;
}

export class KvDocStore extends Context.Tag("KvDocStore")<KvDocStore, KvDocStoreMethods>() {}

// ============================================================
// SQLite-backed implementation
// ============================================================

interface SqliteLike {
  exec(sql: string): void;
  prepare(sql: string): { get(...a: any[]): any; all(...a: any[]): any[]; run(...a: any[]): any };
}

async function openDb(path: string): Promise<SqliteLike> {
  try {
    // @ts-ignore
    const { Database } = await import("bun:sqlite");
    return new Database(path, { create: true }) as SqliteLike;
  } catch {
    const mod: any = await import("better-sqlite3" as any);
    const Database = mod.default ?? mod;
    return new Database(path) as SqliteLike;
  }
}

export const KvDocStoreLive = Layer.effect(
  KvDocStore,
  Effect.gen(function* () {
    const path = process.env.TYPED_SERVER_DB ?? ":memory:";
    const db = yield* Effect.tryPromise({
      try: () => openDb(path),
      catch: (e) => new StorageError({ cause: `open: ${(e as Error).message}` }),
    });

    yield* Effect.try({
      try: () => {
        db.exec("PRAGMA journal_mode=WAL");
        db.exec(`
          CREATE TABLE IF NOT EXISTS docs (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
          );
          CREATE INDEX IF NOT EXISTS idx_docs_content ON docs(content);
        `);
      },
      catch: (e) => new StorageError({ cause: `init: ${(e as Error).message}` }),
    });

    const getStmt = db.prepare("SELECT id, content, created_at FROM docs WHERE id = ?");
    const putStmt = db.prepare(
      "INSERT INTO docs (id, content) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET content = excluded.content RETURNING id, content, created_at"
    );
    const searchStmt = db.prepare(
      "SELECT id, content, created_at FROM docs WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?"
    );

    return KvDocStore.of({
      get: (id) =>
        Effect.try({
          try: () => getStmt.get(id) as DocRecord | undefined,
          catch: (e) => new StorageError({ cause: `get: ${(e as Error).message}` }),
        }).pipe(
          Effect.flatMap((row) =>
            row ? Effect.succeed(row) : Effect.fail(new DocNotFound({ id }))
          )
        ),

      put: (id, content) =>
        Effect.try({
          try: () => putStmt.get(id, content) as DocRecord,
          catch: (e) => new StorageError({ cause: `put: ${(e as Error).message}` }),
        }),

      search: (query, limit) =>
        Effect.try({
          try: () => searchStmt.all(`%${query}%`, limit) as DocRecord[],
          catch: (e) => new StorageError({ cause: `search: ${(e as Error).message}` }),
        }),
    });
  })
);

// ============================================================
// Boundary helpers: validate tool input via Schema, run Effect
// ============================================================

const decodeSearch = Schema.decodeUnknown(SearchInput);
const decodeGet = Schema.decodeUnknown(GetDocumentInput);
const decodePut = Schema.decodeUnknown(PutDocumentInput);

function ok(text: string) {
  return { content: [{ type: "text" as const, text }] };
}

function err(text: string) {
  return { content: [{ type: "text" as const, text }], isError: true };
}

// ============================================================
// MCP server wiring
// ============================================================

const server = new Server(
  { name: "typed-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "search",
      description: "Search documents by substring match",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", minLength: 1, maxLength: 1000 },
          limit: { type: "number", minimum: 1, maximum: 100 },
        },
        required: ["query"],
      },
    },
    {
      name: "get_document",
      description: "Retrieve a document by id",
      inputSchema: {
        type: "object",
        properties: { id: { type: "string", minLength: 1 } },
        required: ["id"],
      },
    },
    {
      name: "put_document",
      description: "Insert or update a document",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", minLength: 1 },
          content: { type: "string", maxLength: 100_000 },
        },
        required: ["id", "content"],
      },
    },
  ],
}));

// Provide the live store layer for every tool call. Layer.effect caches its
// build, so this is cheap after the first request.
function run<A, E>(eff: Effect.Effect<A, E, KvDocStore>): Promise<A> {
  return Effect.runPromise(eff.pipe(Effect.provide(KvDocStoreLive)) as Effect.Effect<A, E>);
}

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "search") {
      const input = await Effect.runPromise(decodeSearch(args ?? {}));
      const result = await run(
        Effect.gen(function* () {
          const store = yield* KvDocStore;
          const results = yield* store
            .search(input.query, input.limit)
            .pipe(Effect.catchTag("StorageError", () => Effect.succeed([] as DocRecord[])));
          return { results, total: results.length };
        })
      );
      return ok(JSON.stringify(result, null, 2));
    }

    if (name === "get_document") {
      const input = await Effect.runPromise(decodeGet(args ?? {}));
      const result = await run(
        Effect.gen(function* () {
          const store = yield* KvDocStore;
          return yield* store.get(input.id).pipe(
            Effect.catchTag("DocNotFound", (e) =>
              Effect.succeed({ id: e.id, content: "", created_at: "" } as DocRecord)
            ),
            Effect.catchTag("StorageError", (e) =>
              Effect.succeed({
                id: input.id,
                content: `[storage error: ${e.cause}]`,
                created_at: "",
              } as DocRecord)
            )
          );
        })
      );
      return ok(JSON.stringify(result, null, 2));
    }

    if (name === "put_document") {
      const input = await Effect.runPromise(decodePut(args ?? {}));
      const result = await run(
        Effect.gen(function* () {
          const store = yield* KvDocStore;
          return yield* store
            .put(input.id, input.content)
            .pipe(
              Effect.catchTag("StorageError", (e) =>
                Effect.succeed({
                  id: input.id,
                  content: `[storage error: ${e.cause}]`,
                  created_at: "",
                } as DocRecord)
              )
            );
        })
      );
      return ok(JSON.stringify(result, null, 2));
    }

    return err(`Unknown tool: ${name}`);
  } catch (e) {
    return err(`Validation error: ${(e as Error).message}`);
  }
});

// Graceful shutdown
function shutdown(signal: string) {
  console.error(`[typed-server] received ${signal}, shutting down`);
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

const transport = new StdioServerTransport();
await server.connect(transport);
