/**
 * Multi-backend search fallback with health-aware routing.
 *
 * Cascade order:
 *   1. ChromaDB (vector search, primary)
 *   2. SQLite FTS5 (lexical, secondary)
 *   3. In-memory TF-IDF (last-resort, always available)
 *
 * Each backend has its own health state. We don't retry a dead backend on
 * every request -- once a backend fails, we wait `checkInterval` ms before
 * trying it again, and we route around it in the meantime.
 *
 * The Chroma client is interface-only here so this file has zero external
 * deps. Wire your real client (e.g. `chromadb` npm package) by passing it to
 * `createFallbackSearch({ chroma: yourClient })`.
 */

// Avoid bun:sqlite at import time so this file is portable to Node + tests.
// We import it lazily inside SqliteBackend.

// ============================================================
// TYPES
// ============================================================

export interface SearchHit {
  id: string;
  content: string;
  score: number;
  source: "chroma" | "sqlite" | "memory";
}

export interface SearchResult {
  hits: SearchHit[];
  backend: SearchHit["source"];
  degraded: boolean;
}

export interface ChromaClient {
  query(args: { query: string; nResults: number }): Promise<{
    ids: string[];
    documents: string[];
    distances: number[];
  }>;
  heartbeat(): Promise<void>;
}

interface BackendHealth {
  healthy: boolean;
  lastCheck: number;
  checkInterval: number;
  consecutiveFailures: number;
}

// ============================================================
// IN-MEMORY TF-IDF (always available)
// ============================================================

export class TfIdfBackend {
  private docs: Array<{ id: string; content: string; tokens: string[] }> = [];
  private df = new Map<string, number>();

  add(id: string, content: string): void {
    const tokens = tokenize(content);
    const seen = new Set(tokens);
    for (const t of seen) this.df.set(t, (this.df.get(t) ?? 0) + 1);
    this.docs.push({ id, content, tokens });
  }

  bulkAdd(docs: Array<{ id: string; content: string }>): void {
    for (const d of docs) this.add(d.id, d.content);
  }

  search(query: string, nResults = 10): SearchHit[] {
    const qTokens = tokenize(query);
    if (qTokens.length === 0 || this.docs.length === 0) return [];
    const N = this.docs.length;

    const scores: Array<{ id: string; content: string; score: number }> = [];
    for (const doc of this.docs) {
      let score = 0;
      const tf = new Map<string, number>();
      for (const t of doc.tokens) tf.set(t, (tf.get(t) ?? 0) + 1);
      for (const qt of qTokens) {
        const f = tf.get(qt) ?? 0;
        if (f === 0) continue;
        const idf = Math.log(1 + N / (1 + (this.df.get(qt) ?? 0)));
        score += (f / doc.tokens.length) * idf;
      }
      if (score > 0) scores.push({ id: doc.id, content: doc.content, score });
    }
    scores.sort((a, b) => b.score - a.score);
    return scores.slice(0, nResults).map((h) => ({ ...h, source: "memory" as const }));
  }

  size(): number {
    return this.docs.length;
  }
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 1);
}

// ============================================================
// SQLITE FTS5 BACKEND
// ============================================================

interface SqliteLike {
  exec(sql: string): void;
  prepare(sql: string): { all(...args: any[]): any[]; run(...args: any[]): any };
  close(): void;
}

export class SqliteBackend {
  private db: SqliteLike | null = null;

  constructor(private dbPath: string = ":memory:") {}

  async init(): Promise<void> {
    // Lazy import so this file is safe to load in test envs without bun:sqlite.
    let Database: any;
    try {
      // @ts-ignore
      ({ Database } = await import("bun:sqlite"));
    } catch {
      try {
        const mod = await import("better-sqlite3" as any);
        Database = mod.default ?? mod;
      } catch {
        throw new Error("No SQLite driver available (need bun:sqlite or better-sqlite3)");
      }
    }
    this.db = new Database(this.dbPath, { create: true });
    this.db!.exec("PRAGMA journal_mode=WAL");
    this.db!.exec(`
      CREATE VIRTUAL TABLE IF NOT EXISTS docs
      USING fts5(id UNINDEXED, content, tokenize='porter');
    `);
  }

  add(id: string, content: string): void {
    if (!this.db) throw new Error("SqliteBackend not initialized");
    this.db.prepare("INSERT INTO docs (id, content) VALUES (?, ?)").run(id, content);
  }

  search(query: string, nResults = 10): SearchHit[] {
    if (!this.db) throw new Error("SqliteBackend not initialized");
    const rows = this.db
      .prepare(
        `SELECT id, content, bm25(docs) AS score
           FROM docs
          WHERE docs MATCH ?
          ORDER BY score
          LIMIT ?`
      )
      .all(query, nResults) as Array<{ id: string; content: string; score: number }>;
    // bm25 returns LOWER = better; flip sign so larger = better.
    return rows.map((r) => ({ id: r.id, content: r.content, score: -r.score, source: "sqlite" as const }));
  }

  ping(): boolean {
    if (!this.db) return false;
    try {
      this.db.prepare("SELECT 1").all();
      return true;
    } catch {
      return false;
    }
  }

  close(): void {
    this.db?.close();
    this.db = null;
  }
}

// ============================================================
// CHROMA BACKEND (interface only -- inject your client)
// ============================================================

export class ChromaBackend {
  constructor(private client: ChromaClient | null) {}

  available(): boolean {
    return this.client !== null;
  }

  async search(query: string, nResults = 10): Promise<SearchHit[]> {
    if (!this.client) throw new Error("ChromaBackend has no client");
    const res = await this.client.query({ query, nResults });
    return res.ids.map((id, i) => ({
      id,
      content: res.documents[i] ?? "",
      // Chroma returns distance (lower = better); convert to similarity score.
      score: 1 - (res.distances[i] ?? 0),
      source: "chroma" as const,
    }));
  }

  async ping(): Promise<boolean> {
    if (!this.client) return false;
    try {
      await this.client.heartbeat();
      return true;
    } catch {
      return false;
    }
  }
}

// ============================================================
// CASCADE WITH HEALTH-AWARE ROUTING
// ============================================================

export interface FallbackOptions {
  chroma?: ChromaClient | null;
  sqlitePath?: string;
  chromaCheckInterval?: number;
  sqliteCheckInterval?: number;
}

export class FallbackSearch {
  private chroma: ChromaBackend;
  private sqlite: SqliteBackend;
  private memory: TfIdfBackend;

  private health: Record<"chroma" | "sqlite", BackendHealth> = {
    chroma: {
      healthy: true,
      lastCheck: 0,
      checkInterval: 30000,
      consecutiveFailures: 0,
    },
    sqlite: {
      healthy: true,
      lastCheck: 0,
      checkInterval: 10000,
      consecutiveFailures: 0,
    },
  };

  constructor(opts: FallbackOptions = {}) {
    this.chroma = new ChromaBackend(opts.chroma ?? null);
    this.sqlite = new SqliteBackend(opts.sqlitePath ?? ":memory:");
    this.memory = new TfIdfBackend();
    if (opts.chromaCheckInterval) this.health.chroma.checkInterval = opts.chromaCheckInterval;
    if (opts.sqliteCheckInterval) this.health.sqlite.checkInterval = opts.sqliteCheckInterval;
  }

  async init(): Promise<void> {
    try {
      await this.sqlite.init();
    } catch (err) {
      this.health.sqlite.healthy = false;
      console.error("[fallback] sqlite init failed:", (err as Error).message);
    }
  }

  /** Mirror a doc across all available backends so fallbacks have data. */
  async indexDoc(id: string, content: string): Promise<void> {
    this.memory.add(id, content);
    if (this.health.sqlite.healthy) {
      try {
        this.sqlite.add(id, content);
      } catch (err) {
        this.markUnhealthy("sqlite", err);
      }
    }
    // Chroma indexing is the caller's responsibility (vectors need embeddings).
  }

  async search(query: string, nResults = 10): Promise<SearchResult> {
    // 1. Chroma first (if healthy or due for recheck)
    if (this.shouldTry("chroma") && this.chroma.available()) {
      try {
        const hits = await this.chroma.search(query, nResults);
        this.markHealthy("chroma");
        return { hits, backend: "chroma", degraded: false };
      } catch (err) {
        this.markUnhealthy("chroma", err);
      }
    }

    // 2. SQLite FTS
    if (this.shouldTry("sqlite")) {
      try {
        const hits = this.sqlite.search(query, nResults);
        this.markHealthy("sqlite");
        return { hits, backend: "sqlite", degraded: true };
      } catch (err) {
        this.markUnhealthy("sqlite", err);
      }
    }

    // 3. In-memory TF-IDF (always works)
    const hits = this.memory.search(query, nResults);
    return { hits, backend: "memory", degraded: true };
  }

  health_state() {
    return JSON.parse(JSON.stringify(this.health));
  }

  private shouldTry(backend: "chroma" | "sqlite"): boolean {
    const h = this.health[backend];
    if (h.healthy) return true;
    return Date.now() - h.lastCheck > h.checkInterval;
  }

  private markHealthy(backend: "chroma" | "sqlite") {
    const h = this.health[backend];
    h.healthy = true;
    h.lastCheck = Date.now();
    h.consecutiveFailures = 0;
  }

  private markUnhealthy(backend: "chroma" | "sqlite", err: unknown) {
    const h = this.health[backend];
    h.healthy = false;
    h.lastCheck = Date.now();
    h.consecutiveFailures += 1;
    // Exponential backoff up to 5 minutes
    h.checkInterval = Math.min(h.checkInterval * 2, 5 * 60 * 1000);
    console.error(`[fallback] ${backend} failed (${h.consecutiveFailures}):`, (err as Error)?.message);
  }
}

export function createFallbackSearch(opts: FallbackOptions = {}): FallbackSearch {
  return new FallbackSearch(opts);
}
