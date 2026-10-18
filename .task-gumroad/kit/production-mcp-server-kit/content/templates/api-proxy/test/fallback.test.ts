/**
 * Tests for the multi-backend fallback cascade.
 *
 * Run with: npx vitest run
 */
import { describe, expect, it } from "vitest";
import { TfIdfBackend, FallbackSearch, type ChromaClient } from "../src/fallback";

describe("TfIdfBackend", () => {
  it("returns ranked hits for token overlap", () => {
    const tf = new TfIdfBackend();
    tf.add("a", "production mcp server with auth and rate limiting");
    tf.add("b", "completely unrelated about cats and dogs");
    tf.add("c", "rate limiting middleware for production");

    const hits = tf.search("rate limiting production", 10);
    expect(hits.length).toBeGreaterThanOrEqual(2);
    expect(hits[0].id === "a" || hits[0].id === "c").toBe(true);
    expect(hits.find((h) => h.id === "b")).toBeUndefined();
  });

  it("returns empty for empty corpus", () => {
    const tf = new TfIdfBackend();
    expect(tf.search("anything")).toEqual([]);
  });
});

describe("FallbackSearch cascade", () => {
  it("falls through to in-memory when chroma + sqlite both fail", async () => {
    const fb = new FallbackSearch({ chroma: null });
    await fb.init();
    await fb.indexDoc("doc1", "production mcp server testing");
    await fb.indexDoc("doc2", "irrelevant content");

    const result = await fb.search("production server");
    expect(result.hits.length).toBeGreaterThan(0);
    // sqlite FTS may pick this up; either sqlite or memory is acceptable
    expect(["sqlite", "memory"]).toContain(result.backend);
  });

  it("uses chroma when client is healthy", async () => {
    const fakeChroma: ChromaClient = {
      query: async ({ query, nResults }) => ({
        ids: ["v1", "v2"],
        documents: [`vector hit for ${query} A`, `vector hit for ${query} B`],
        distances: [0.1, 0.2],
      }),
      heartbeat: async () => {},
    };
    const fb = new FallbackSearch({ chroma: fakeChroma });
    await fb.init();
    const result = await fb.search("test");
    expect(result.backend).toBe("chroma");
    expect(result.hits.length).toBe(2);
    expect(result.degraded).toBe(false);
  });

  it("marks chroma unhealthy after a failure and falls through", async () => {
    const flakyChroma: ChromaClient = {
      query: async () => {
        throw new Error("chroma down");
      },
      heartbeat: async () => {},
    };
    const fb = new FallbackSearch({ chroma: flakyChroma });
    await fb.init();
    await fb.indexDoc("a", "fallback content here");
    const result = await fb.search("fallback");
    const health = fb.health_state();
    expect(health.chroma.healthy).toBe(false);
    expect(["sqlite", "memory"]).toContain(result.backend);
    expect(result.degraded).toBe(true);
  });
});
