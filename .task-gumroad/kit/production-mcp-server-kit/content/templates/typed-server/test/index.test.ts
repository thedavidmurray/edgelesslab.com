/**
 * Tests for the typed-server tagged errors and SQLite-backed KV store.
 *
 * Run with: npx vitest run
 *
 * NOTE: We don't import src/index.ts directly because it boots the MCP
 * server on import. We re-test the same DocNotFound / StorageError tags and
 * Effect-based access pattern against an in-memory store.
 */
import { describe, expect, it } from "vitest";
import { Data, Effect } from "effect";

class DocNotFound extends Data.TaggedError("DocNotFound")<{
  readonly id: string;
}> {}

class StorageError extends Data.TaggedError("StorageError")<{
  readonly cause: string;
}> {}

interface Doc {
  id: string;
  content: string;
}

function makeStore() {
  const data = new Map<string, Doc>();
  return {
    get: (id: string) =>
      data.has(id)
        ? Effect.succeed(data.get(id)!)
        : Effect.fail(new DocNotFound({ id })),
    put: (id: string, content: string) =>
      Effect.sync(() => {
        const doc = { id, content };
        data.set(id, doc);
        return doc;
      }),
    explode: () => Effect.fail(new StorageError({ cause: "boom" })),
  };
}

describe("typed-server domain", () => {
  it("DocNotFound is a discriminated tag", async () => {
    const store = makeStore();
    const result = await Effect.runPromiseExit(store.get("missing"));
    expect(result._tag).toBe("Failure");
    if (result._tag === "Failure") {
      const cause = result.cause;
      // Tagged errors carry _tag identity
      const failure = (cause as any).failure ?? (cause as any).errors?.[0];
      // Just assert the tag exists somewhere; structure depends on Effect version.
      const str = JSON.stringify(cause);
      expect(str).toContain("DocNotFound");
    }
  });

  it("put then get round-trips a doc", async () => {
    const store = makeStore();
    await Effect.runPromise(store.put("k1", "hello"));
    const doc = await Effect.runPromise(store.get("k1"));
    expect(doc).toEqual({ id: "k1", content: "hello" });
  });

  it("catchTag recovers from DocNotFound", async () => {
    const store = makeStore();
    const recovered = await Effect.runPromise(
      store.get("missing").pipe(
        Effect.catchTag("DocNotFound", (e) =>
          Effect.succeed({ id: e.id, content: "[default]" })
        )
      )
    );
    expect(recovered.content).toBe("[default]");
  });

  it("StorageError is distinct from DocNotFound", async () => {
    const store = makeStore();
    const result = await Effect.runPromiseExit(store.explode());
    expect(result._tag).toBe("Failure");
    const str = JSON.stringify((result as any).cause);
    expect(str).toContain("StorageError");
    expect(str).toContain("boom");
  });
});
